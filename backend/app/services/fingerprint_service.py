import hashlib
from pathlib import Path


def dhash_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    bits = []
    for i in range(8):
        left = digest[i]
        right = digest[i + 8]
        bits.append(f"{left ^ right:08b}")
    return f"{int(''.join(bits), 2):016x}"


def dhash_file(path: Path) -> str:
    return dhash_bytes(path.read_bytes())


def hamming_distance(hex_a: str, hex_b: str) -> int:
    return (int(hex_a, 16) ^ int(hex_b, 16)).bit_count()


def similarity_from_distance(distance: int, max_bits: int = 64) -> float:
    return round(max(0.0, min(1.0, 1 - (distance / max_bits))), 3)
