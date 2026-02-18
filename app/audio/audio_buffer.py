import asyncio
import numpy as np


class AudioBuffer:
    """Thread-safe buffer that accumulates PCM audio chunks."""

    def __init__(self, max_duration_seconds: int = 30, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.max_samples = max_duration_seconds * sample_rate
        self.chunks: list[np.ndarray] = []
        self.total_samples = 0
        self.lock = asyncio.Lock()

    async def add_samples(self, pcm_samples: np.ndarray):
        async with self.lock:
            self.chunks.append(pcm_samples)
            self.total_samples += len(pcm_samples)
            # Trim if over max duration
            if self.total_samples > self.max_samples:
                self.chunks = self.chunks[-1:]
                self.total_samples = len(self.chunks[0])

    async def get_and_clear(self) -> np.ndarray:
        async with self.lock:
            if not self.chunks:
                return np.array([], dtype=np.int16)
            audio = np.concatenate(self.chunks)
            self.chunks.clear()
            self.total_samples = 0
            return audio

    @property
    def duration_seconds(self) -> float:
        return self.total_samples / self.sample_rate

    @property
    def is_empty(self) -> bool:
        return self.total_samples == 0
