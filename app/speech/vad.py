import numpy as np
import torch


class VADDetector:
    """Voice Activity Detection using silero-vad."""

    def __init__(self):
        self.model, _utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        self.model.eval()
        self.SAMPLE_RATE = 16000

    def is_speech(self, audio_chunk_16khz: np.ndarray) -> bool:
        """Check if an audio chunk contains speech.

        The chunk should be 16kHz 16-bit PCM, ideally 512 samples (32ms).
        """
        audio_tensor = torch.from_numpy(
            audio_chunk_16khz.astype(np.float32) / 32768.0
        )
        confidence = self.model(audio_tensor, self.SAMPLE_RATE).item()
        return confidence > 0.5

    def reset(self):
        """Reset model state between utterances."""
        self.model.reset_states()
