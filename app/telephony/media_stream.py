import asyncio
import base64
import json
import logging
import time

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from app import config
from app.audio.mulaw_converter import mulaw_decode, mulaw_encode
from app.audio.resampler import resample_audio
from app.audio.audio_buffer import AudioBuffer
from app.audio.tts_engine import text_to_mulaw_chunks
from app.speech.stt_engine import STTEngine
from app.speech.vad import VADDetector
from app.speech.turn_detector import TurnDetector, TurnState
from app.brain.conversation import Conversation
from app.brain.response_generator import ResponseGenerator
from app.analysis.transcript_logger import save_transcript, format_transcript_text

logger = logging.getLogger(__name__)

# Global state for the current call scenario (set before each call)
_current_scenario: dict | None = None
_call_complete_event: asyncio.Event | None = None
_last_transcript: dict | None = None


def set_scenario(scenario: dict):
    global _current_scenario, _call_complete_event, _last_transcript
    _current_scenario = scenario
    _call_complete_event = asyncio.Event()
    _last_transcript = None


def get_call_complete_event() -> asyncio.Event | None:
    return _call_complete_event


def get_last_transcript() -> dict | None:
    return _last_transcript


async def handle_media_stream(websocket: WebSocket):
    """Handle a Twilio Media Stream WebSocket connection.

    This is the core real-time audio processing loop.
    """
    global _last_transcript

    await websocket.accept()
    logger.info("WebSocket connected")

    scenario = _current_scenario
    if not scenario:
        logger.error("No scenario set for this call")
        await websocket.close()
        return

    # Initialize components
    stt = STTEngine()
    vad = VADDetector()
    turn_detector = TurnDetector(
        silence_threshold_ms=config.SILENCE_THRESHOLD_MS,
        min_speech_ms=300,
    )
    audio_buffer = AudioBuffer(max_duration_seconds=30, sample_rate=16000)
    conversation = Conversation(scenario["id"])
    response_gen = ResponseGenerator(scenario)

    stream_sid: str | None = None
    stream_start_time: float | None = None
    trial_ended = False
    chunk_count = 0
    speaking = False
    call_start = time.time()

    # Queue for outbound audio chunks
    outbound_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def send_loop():
        """Send audio chunks from the outbound queue to Twilio."""
        nonlocal speaking
        try:
            while True:
                chunk = await outbound_queue.get()
                if chunk is None:
                    break  # Poison pill - call ended

                payload = base64.b64encode(chunk).decode("ascii")
                msg = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": payload},
                }
                await websocket.send_json(msg)

                # Pace at 20ms per chunk (real-time playback)
                await asyncio.sleep(0.02)
        except (WebSocketDisconnect, Exception) as e:
            logger.debug("Send loop ended: %s", e)

    async def speak_text(text: str):
        """Convert text to audio and queue it for sending."""
        nonlocal speaking
        speaking = True
        turn_detector.mark_speaking()

        chunks = await text_to_mulaw_chunks(text)
        for chunk in chunks:
            # Check if agent interrupted us (VAD detected speech during our turn)
            if turn_detector.state == TurnState.LISTENING:
                logger.info("Interrupted by agent, stopping speech")
                # Clear Twilio's playback buffer
                try:
                    await websocket.send_json({
                        "event": "clear",
                        "streamSid": stream_sid,
                    })
                except Exception:
                    pass
                break
            await outbound_queue.put(chunk)

        speaking = False
        turn_detector.mark_listening()

    # Start the send loop
    send_task = asyncio.create_task(send_loop())

    # VAD chunk accumulator (need 512 samples at 16kHz = 32ms)
    vad_accumulator = np.array([], dtype=np.int16)
    VAD_CHUNK_SIZE = 512

    agent_silence_start: float | None = None
    timeout_count = 0
    opening_sent = False

    try:
        while True:
            # Safety: max call duration
            if time.time() - call_start > config.MAX_CALL_DURATION_S:
                logger.info("Max call duration reached, hanging up")
                break

            raw = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            data = json.loads(raw)
            event = data.get("event")

            if event == "connected":
                logger.info("Stream connected")

            elif event == "start":
                stream_sid = data["start"]["streamSid"]
                stream_start_time = time.time()
                logger.info("Stream started: %s", stream_sid)

            elif event == "media":
                chunk_count += 1

                # Decode audio: base64 -> mu-law -> PCM 8kHz -> PCM 16kHz
                mulaw_bytes = base64.b64decode(data["media"]["payload"])
                pcm_8k = mulaw_decode(mulaw_bytes)
                pcm_16k = resample_audio(pcm_8k, 8000, 16000)

                # Skip trial message period
                elapsed = time.time() - (stream_start_time or time.time())
                if elapsed < config.TRIAL_MESSAGE_DURATION_S:
                    continue

                if not trial_ended:
                    trial_ended = True
                    turn_detector.mark_trial_ended()
                    vad.reset()
                    logger.info("Trial message period ended, listening...")

                # Feed to audio buffer
                await audio_buffer.add_samples(pcm_16k)

                # VAD processing (accumulate to 512 samples)
                vad_accumulator = np.concatenate([vad_accumulator, pcm_16k])
                while len(vad_accumulator) >= VAD_CHUNK_SIZE:
                    vad_chunk = vad_accumulator[:VAD_CHUNK_SIZE]
                    vad_accumulator = vad_accumulator[VAD_CHUNK_SIZE:]

                    is_speech = vad.is_speech(vad_chunk)
                    timestamp_ms = elapsed * 1000

                    prev_state = turn_detector.state
                    new_state = turn_detector.on_vad_result(is_speech, timestamp_ms)

                    if is_speech:
                        agent_silence_start = None

                    # Transition: agent finished speaking -> process
                    if new_state == TurnState.PROCESSING and prev_state != TurnState.PROCESSING:
                        # Get buffered audio and transcribe
                        audio_data = await audio_buffer.get_and_clear()
                        if len(audio_data) > 0:
                            agent_text, confidence = stt.transcribe(audio_data)

                            # Skip empty or trial message artifacts
                            if not agent_text.strip():
                                turn_detector.mark_listening()
                                continue

                            trial_words = {"trial", "twilio", "upgrade", "account"}
                            if any(w in agent_text.lower() for w in trial_words):
                                logger.info("Discarding trial message artifact: %s", agent_text[:50])
                                turn_detector.mark_listening()
                                continue

                            logger.info("Agent said: %s (conf=%.2f)", agent_text, confidence)
                            conversation.add_agent_utterance(agent_text)

                            # Generate patient response
                            if not opening_sent:
                                opening_sent = True
                                patient_text = await response_gen.get_opening_line()
                            else:
                                patient_text = await response_gen.generate_response(
                                    conversation.get_recent_messages()
                                )

                            logger.info("Patient says: %s", patient_text)
                            conversation.add_patient_utterance(patient_text)

                            # Speak the response
                            await speak_text(patient_text)

                            # Check if conversation should end
                            goodbye_words = {"goodbye", "bye", "thank you, goodbye", "have a good"}
                            if any(w in patient_text.lower() for w in goodbye_words):
                                logger.info("Patient said goodbye, ending call")
                                await asyncio.sleep(2.0)  # Let audio finish
                                break

                            vad.reset()
                            agent_silence_start = time.time()

                # Track agent silence (for timeout prompts)
                if not speaking and turn_detector.state == TurnState.LISTENING:
                    if agent_silence_start is None:
                        agent_silence_start = time.time()
                    elif time.time() - agent_silence_start > 15:
                        timeout_count += 1
                        if timeout_count >= 3:
                            prompt = "I think we got disconnected. Thank you, goodbye."
                        else:
                            prompt = "Hello? Are you still there?"

                        logger.info("Agent silent too long, prompting: %s", prompt)
                        conversation.add_patient_utterance(prompt)
                        await speak_text(prompt)
                        agent_silence_start = time.time()

                        if timeout_count >= 3:
                            break

            elif event == "stop":
                logger.info("Stream stopped")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except asyncio.TimeoutError:
        logger.info("WebSocket timeout (no data for 30s)")
    except Exception as e:
        logger.error("Media stream error: %s", e, exc_info=True)
    finally:
        # Signal send loop to stop
        await outbound_queue.put(None)
        send_task.cancel()

        # Save transcript
        transcript = conversation.to_transcript()
        _last_transcript = transcript

        if transcript["turn_count"] > 0:
            filepath = save_transcript(transcript, scenario["id"])
            logger.info("Call complete. Transcript saved: %s", filepath)
            print("\n" + format_transcript_text(transcript))
        else:
            logger.warning("Call ended with no conversation turns")

        await response_gen.close()

        if _call_complete_event:
            _call_complete_event.set()
