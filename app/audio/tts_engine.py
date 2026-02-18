import io
import subprocess
import logging

import numpy as np
import edge_tts

from app.audio.mulaw_converter import mulaw_encode

logger = logging.getLogger(__name__)

VOICE = "en-US-JennyNeural"


async def text_to_mulaw_chunks(text: str, voice: str = VOICE) -> list[bytes]:
    """Convert text to a list of 160-byte mu-law chunks for Twilio Media Streams.

    Pipeline: text -> edge-tts (MP3) -> ffmpeg (PCM 8kHz) -> mu-law encode -> chunk
    """
    # Step 1: Generate MP3 with edge-tts
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    mp3_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_buffer.write(chunk["data"])

    if mp3_buffer.tell() == 0:
        logger.warning("edge-tts returned no audio for: %s", text[:50])
        return []

    # Step 2: Decode MP3 to raw PCM 8kHz mono via ffmpeg
    mp3_buffer.seek(0)
    process = subprocess.run(
        [
            "ffmpeg", "-i", "pipe:0",
            "-f", "s16le", "-ar", "8000", "-ac", "1",
            "-acodec", "pcm_s16le", "pipe:1",
        ],
        input=mp3_buffer.read(),
        capture_output=True,
    )

    if process.returncode != 0:
        logger.error("ffmpeg failed: %s", process.stderr.decode()[:200])
        return []

    pcm_data = np.frombuffer(process.stdout, dtype=np.int16)

    # Step 3: Encode PCM to mu-law
    mulaw_data = mulaw_encode(pcm_data)

    # Step 4: Split into 160-byte chunks (20ms at 8kHz mu-law)
    chunk_size = 160
    chunks = []
    for i in range(0, len(mulaw_data), chunk_size):
        chunk = mulaw_data[i : i + chunk_size]
        if len(chunk) < chunk_size:
            # Pad last chunk with mu-law silence (0xFF)
            chunk = chunk + b"\xff" * (chunk_size - len(chunk))
        chunks.append(chunk)

    return chunks
