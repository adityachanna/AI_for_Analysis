import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import SUSPECT_DIR, settings
from .cloud_storage_service import upload_to_bucket
from .firebase_service import sync_demo_clip_doc
from .fingerprint_service import hamming_distance
from .gemini_service import analyze_demo_clip


DEMO_VARIANTS = [
    {
        "id": "demo-exact-repost",
        "platform": "YouTube Shorts",
        "title": "Same highlight reposted from the master feed",
        "mutation_type": "exact_repost",
        "hash_distance": 3,
        "filters": ["copy", "metadata_strip"],
    },
    {
        "id": "demo-480p-reencode",
        "platform": "TikTok",
        "title": "480p re-encode with compression loss",
        "mutation_type": "cropped_or_reencoded",
        "hash_distance": 14,
        "filters": ["scale_480p", "h264_reencode", "color_shift"],
    },
    {
        "id": "demo-crop-color",
        "platform": "Instagram Reels",
        "title": "Vertical crop plus boosted color grade",
        "mutation_type": "cropped_or_reencoded",
        "hash_distance": 18,
        "filters": ["crop_10_percent", "vertical_canvas", "saturation_boost"],
    },
    {
        "id": "demo-overlay-meme",
        "platform": "Facebook Watch",
        "title": "Meme overlay on top of licensed sports footage",
        "mutation_type": "overlay_or_meme_edit",
        "hash_distance": 24,
        "filters": ["caption_overlay", "sticker_overlay", "music_bed"],
    },
    {
        "id": "demo-screen-record",
        "platform": "X",
        "title": "Screen-recorded TV playback of the same play",
        "mutation_type": "screen_recorded_recapture",
        "hash_distance": 29,
        "filters": ["obs_screen_record", "720p_capture", "glare", "room_audio"],
    },
]


def create_demo_clips_for_asset(db, asset: dict, keyframes: list[dict], analysis: dict) -> list[dict]:
    source = Path(asset["file_path"])
    source_bytes = source.read_bytes() if source.exists() else asset["source_hash"].encode()
    base_hash = keyframes[0]["dhash"] if keyframes else "0000000000000000"
    variants = DEMO_VARIANTS[: settings.demo_variant_count]
    clips = []

    for index, variant in enumerate(variants):
        clip_id = f"{asset['id']}-{variant['id']}"
        manifest = {
            "filters": variant["filters"],
            "source_asset_id": asset["id"],
            "demo_note": "Local MVP transforms bytes deterministically; production uses FFmpeg/OpenCV workers.",
        }
        clip_path = _write_variant_file(asset["id"], variant["id"], source.suffix or ".mp4", source_bytes, manifest)
        dhashes = [_flip_bits(base_hash, variant["hash_distance"])]
        ai_details = analyze_demo_clip(analysis, variant["mutation_type"], variant["platform"], manifest)
        upload = upload_to_bucket(
            clip_path,
            f"sentinelai-demo/{asset['owner_uid']}/{asset['id']}/suspects/{variant['id']}{clip_path.suffix}",
        )
        created_at = datetime.now(timezone.utc).isoformat()
        clip = {
            "id": clip_id,
            "asset_id": asset["id"],
            "title": variant["title"],
            "platform": variant["platform"],
            "url": f"https://demo.sentinelai.local/{variant['platform'].lower().replace(' ', '-')}/{clip_id}",
            "mutation_type": variant["mutation_type"],
            "transform_manifest": manifest,
            "file_path": str(clip_path),
            "gcs_uri": upload["uri"],
            "dhashes": dhashes,
            "semantic_tags": ai_details["semantic_tags"],
            "ai_details": ai_details,
            "graph_metadata": ai_details["graph_metadata"],
            "created_at": created_at,
            "actual_distance": hamming_distance(base_hash, dhashes[0]),
        }
        db.execute(
            """
            INSERT OR REPLACE INTO demo_clips(
                id, asset_id, title, platform, url, mutation_type, transform_manifest, file_path,
                gcs_uri, dhashes, semantic_tags, ai_details, graph_metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clip["id"],
                clip["asset_id"],
                clip["title"],
                clip["platform"],
                clip["url"],
                clip["mutation_type"],
                json.dumps(clip["transform_manifest"]),
                clip["file_path"],
                clip["gcs_uri"],
                json.dumps(clip["dhashes"]),
                json.dumps(clip["semantic_tags"]),
                json.dumps(clip["ai_details"]),
                json.dumps(clip["graph_metadata"]),
                clip["created_at"],
            ),
        )
        sync_demo_clip_doc(asset["id"], clip)
        clips.append(clip)

    return clips


def load_demo_clips(db, asset_id: str) -> list[dict]:
    clips = []
    for row in db.execute("SELECT * FROM demo_clips WHERE asset_id = ? ORDER BY created_at", (asset_id,)):
        item = dict(row)
        item["transform_manifest"] = json.loads(item["transform_manifest"])
        item["dhashes"] = json.loads(item["dhashes"])
        item["semantic_tags"] = json.loads(item["semantic_tags"])
        item["ai_details"] = json.loads(item["ai_details"])
        item["graph_metadata"] = json.loads(item["graph_metadata"])
        clips.append(item)
    return clips


def _write_variant_file(asset_id: str, variant_id: str, suffix: str, source_bytes: bytes, manifest: dict) -> Path:
    target_dir = SUSPECT_DIR / asset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{variant_id}{suffix}"
    marker = json.dumps(manifest, sort_keys=True).encode()
    digest = hashlib.sha256(source_bytes + marker).digest()
    target.write_bytes(source_bytes + b"\nSENTINELAI_DEMO_VARIANT\n" + marker + b"\n" + digest)
    return target


def _flip_bits(hex_value: str, count: int) -> str:
    value = int(hex_value, 16)
    for bit in range(min(count, 64)):
        value ^= 1 << bit
    return f"{value:016x}"
