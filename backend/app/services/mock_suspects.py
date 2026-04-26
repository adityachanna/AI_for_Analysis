from .fingerprint_service import hamming_distance


MOCK_SUSPECTS = [
    {
        "id": "mock-exact-repost",
        "platform": "YouTube Shorts",
        "url": "https://mock.platform/youtube/exact-repost",
        "title": "Full highlight reposted without license",
        "mutation_type": "exact_repost",
        "semantic_tags": ["highlight", "broadcast", "rights-managed"],
        "hash_distance": 3,
    },
    {
        "id": "mock-cropped-reencode",
        "platform": "TikTok",
        "url": "https://mock.platform/tiktok/cropped-reencode",
        "title": "Cropped vertical reupload",
        "mutation_type": "cropped_or_reencoded",
        "semantic_tags": ["highlight", "broadcast", "sports"],
        "hash_distance": 14,
    },
    {
        "id": "mock-overlay-meme",
        "platform": "Instagram Reels",
        "url": "https://mock.platform/instagram/overlay-meme",
        "title": "Meme overlay on broadcast clip",
        "mutation_type": "overlay_or_meme_edit",
        "semantic_tags": ["highlight", "meme", "broadcast"],
        "hash_distance": 24,
    },
    {
        "id": "mock-screen-record",
        "platform": "X",
        "url": "https://mock.platform/x/screen-record",
        "title": "Screen recorded sports clip",
        "mutation_type": "screen_recorded_recapture",
        "semantic_tags": ["highlight", "broadcast", "screen-record"],
        "hash_distance": 21,
    },
    {
        "id": "mock-unrelated",
        "platform": "YouTube",
        "url": "https://mock.platform/youtube/unrelated",
        "title": "Different sports clip",
        "mutation_type": "unrelated",
        "semantic_tags": ["training", "interview", "unrelated"],
        "hash_distance": 42,
    },
]


def materialize_suspect_hashes(asset_hashes: list[str]) -> list[dict]:
    base = asset_hashes[0] if asset_hashes else "0000000000000000"
    suspects = []
    for item in MOCK_SUSPECTS:
        target = _flip_bits(base, int(item["hash_distance"]))
        suspects.append({**item, "dhashes": [target], "actual_distance": hamming_distance(base, target)})
    return suspects


def _flip_bits(hex_value: str, count: int) -> str:
    value = int(hex_value, 16)
    for bit in range(min(count, 64)):
        value ^= 1 << bit
    return f"{value:016x}"
