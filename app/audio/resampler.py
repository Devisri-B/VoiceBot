import numpy as np
from scipy.signal import resample_poly


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio from orig_sr to target_sr using polyphase filtering."""
    if orig_sr == target_sr:
        return audio

    from math import gcd
    g = gcd(orig_sr, target_sr)
    up = target_sr // g
    down = orig_sr // g

    resampled = resample_poly(audio.astype(np.float64), up, down)
    return np.clip(resampled, -32768, 32767).astype(np.int16)
