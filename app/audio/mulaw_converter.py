import numpy as np


def mulaw_decode(mulaw_bytes: bytes) -> np.ndarray:
    """Convert mu-law encoded bytes to 16-bit PCM numpy array.

    Uses the standard ITU-T G.711 mu-law decompression algorithm.
    """
    mulaw = np.frombuffer(mulaw_bytes, dtype=np.uint8)
    # Invert bits
    mulaw = (~mulaw).astype(np.int32)

    sign = mulaw & 0x80
    exponent = (mulaw >> 4) & 0x07
    mantissa = mulaw & 0x0F

    magnitude = ((mantissa << 1) | 0x21) << (exponent + 2)
    magnitude = magnitude - 0x21  # Remove bias

    pcm = np.where(sign != 0, -magnitude, magnitude).astype(np.int16)
    return pcm


def mulaw_encode(pcm_array: np.ndarray) -> bytes:
    """Convert 16-bit PCM numpy array to mu-law encoded bytes.

    Uses the standard ITU-T G.711 mu-law compression algorithm.
    """
    BIAS = 0x84  # 132
    CLIP = 32635

    pcm = pcm_array.astype(np.int32)
    sign = np.where(pcm < 0, 0x80, 0x00).astype(np.int32)
    magnitude = np.abs(pcm)
    magnitude = np.clip(magnitude + BIAS, 0, CLIP)

    exponent = np.zeros(len(magnitude), dtype=np.int32)
    for i in range(7, 0, -1):
        mask = 1 << (i + 3)
        exponent = np.where((magnitude >= mask) & (exponent == 0), i, exponent)

    mantissa = (magnitude >> (exponent + 3)) & 0x0F
    mulaw = ~(sign | (exponent << 4) | mantissa) & 0xFF
    return mulaw.astype(np.uint8).tobytes()
