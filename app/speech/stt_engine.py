import numpy as np
from faster_whisper import WhisperModel

from app import config


class STTEngine:
    """Speech-to-text engine using faster-whisper."""

    def __init__(self, model_size: str | None = None):
        size = model_size or config.WHISPER_MODEL_SIZE
        self.model = WhisperModel(size, device="cpu", compute_type="int8")

    def transcribe(self, audio_pcm_16khz: np.ndarray) -> tuple[str, float]:
        """Transcribe 16kHz 16-bit PCM audio to text.

        Returns (text, confidence) where confidence is the average log probability.
        """
        if len(audio_pcm_16khz) == 0:
            return "", 0.0

        audio_float = audio_pcm_16khz.astype(np.float32) / 32768.0

        segments, _info = self.model.transcribe(
            audio_float,
            beam_size=1,
            language="en",
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200,
            ),
        )

        segment_list = list(segments)
        if not segment_list:
            return "", 0.0

        text = " ".join(s.text.strip() for s in segment_list)
        avg_logprob = sum(s.avg_logprob for s in segment_list) / len(segment_list)
        return text, avg_logprob
