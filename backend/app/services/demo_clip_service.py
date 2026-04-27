import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ..config import SUSPECT_DIR, settings
from .firebase_service import sync_demo_clip_doc
from .fingerprint_service import hamming_distance
from .gemini_service import describe_clip_from_keyframes
from .gcs_service import upload_to_gcs
from .video_service import extract_keyframes

logger = logging.getLogger(__name__)

DEMO_VARIANTS = [
    {
        "id": "demo-exact-repost",
        "platform": "YouTube Shorts",
        "title": "Same highlight reposted from the master feed",
        "mutation_type": "exact_repost",
        "filters": ["copy", "metadata_strip"],
    },
    {
        "id": "demo-480p-reencode",
        "platform": "TikTok",
        "title": "480p re-encode with compression loss",
        "mutation_type": "cropped_or_reencoded",
        "filters": ["scale_480p", "h264_reencode", "color_shift"],
    },
    {
        "id": "demo-crop-color",
        "platform": "Instagram Reels",
        "title": "Vertical crop plus boosted color grade",
        "mutation_type": "cropped_or_reencoded",
        "filters": ["crop_10_percent", "vertical_canvas", "saturation_boost"],
    },
    {
        "id": "demo-overlay-meme",
        "platform": "Facebook Watch",
        "title": "Meme overlay on top of licensed sports footage",
        "mutation_type": "overlay_or_meme_edit",
        "filters": ["caption_overlay", "sticker_overlay", "music_bed"],
    },
    {
        "id": "demo-screen-record",
        "platform": "X",
        "title": "Screen-recorded TV playback of the same play",
        "mutation_type": "screen_recorded_recapture",
        "filters": ["obs_screen_record", "720p_capture", "glare", "room_audio"],
    },
]


def create_demo_clips_for_asset(db, asset: dict, keyframes: list[dict], analysis: dict) -> list[dict]:
    source = Path(asset["file_path"])
    variants = DEMO_VARIANTS[: settings.demo_variant_count]
    base_hash = keyframes[0]["dhash"] if keyframes else "0000000000000000"
    clips = []

    for variant in variants:
        clip_id = f"{asset['id']}-{variant['id']}"
        manifest = {
            "filters": variant["filters"],
            "source_asset_id": asset["id"],
        }

        # Build variant video using real OpenCV frame-level transforms
        clip_path = _build_variant_path(asset["id"], variant["id"], source.suffix or ".mp4")
        clip_path = _create_variant_video(source, clip_path, variant["id"])

        # Extract real keyframes and dhashes from the variant file
        variant_kf_id = f"{asset['id']}-{variant['id']}-kf"
        variant_keyframes = extract_keyframes(clip_path, variant_kf_id, count=5)
        dhashes = [kf["dhash"] for kf in variant_keyframes] if variant_keyframes else [base_hash]

        # Get AI description based on real keyframe data
        ai_details = describe_clip_from_keyframes(
            variant_keyframes or keyframes,
            analysis,
            variant["mutation_type"],
            variant["platform"],
        )

        # Upload variant to GCS
        gcs_dest = f"sentinelai-demo/{asset['owner_uid']}/{asset['id']}/suspects/{variant['id']}{clip_path.suffix}"
        upload = upload_to_gcs(clip_path, gcs_dest)

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


def _build_variant_path(asset_id: str, variant_id: str, suffix: str) -> Path:
    target_dir = SUSPECT_DIR / asset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{variant_id}{suffix}"


def _create_variant_video(source_path: Path, target_path: Path, variant_id: str) -> Path:
    """Apply OpenCV frame-level transform to produce a variant video. Falls back to file copy on failure."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        logger.warning("OpenCV/numpy not available; copying source as variant.")
        shutil.copy(source_path, target_path)
        return target_path

    if not source_path.exists() or source_path.stat().st_size == 0:
        if source_path.exists():
            shutil.copy(source_path, target_path)
        else:
            target_path.write_bytes(b"")
        return target_path

    cap = cv2.VideoCapture(str(source_path))
    if not cap.isOpened():
        logger.warning(f"Cannot open {source_path} with OpenCV; copying as-is.")
        shutil.copy(source_path, target_path)
        return target_path

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    if width <= 0 or height <= 0:
        cap.release()
        shutil.copy(source_path, target_path)
        return target_path

    out_width, out_height = _variant_output_size(variant_id, width, height)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(target_path), fourcc, fps, (out_width, out_height))

    if not out.isOpened():
        logger.warning(f"VideoWriter could not open for {variant_id}; copying source.")
        cap.release()
        shutil.copy(source_path, target_path)
        return target_path

    rng = np.random.default_rng(42)
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        transformed = _apply_variant_transform(frame, variant_id, out_width, out_height, frame_idx, rng)
        out.write(transformed)
        frame_idx += 1

    cap.release()
    out.release()

    # If the writer produced a trivially small file the codec probably silently failed
    if not target_path.exists() or target_path.stat().st_size < 1024:
        logger.warning(f"Variant output for {variant_id} is empty; copying source.")
        shutil.copy(source_path, target_path)

    return target_path


def _variant_output_size(variant_id: str, width: int, height: int) -> tuple[int, int]:
    if variant_id == "demo-480p-reencode" and height > 480:
        h = 480
        w = int(width * h / height)
        w += w % 2  # ensure even for codec compatibility
        return (w, h)
    if variant_id == "demo-crop-color":
        w = int(width * 0.8)
        h = int(height * 0.8)
        w += w % 2
        h += h % 2
        return (max(w, 2), max(h, 2))
    return (width, height)


def _apply_variant_transform(
    frame: "np.ndarray",
    variant_id: str,
    out_w: int,
    out_h: int,
    frame_idx: int,
    rng: "np.random.Generator",
) -> "np.ndarray":
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    if variant_id == "demo-exact-repost":
        # No-op: copy frames losslessly — expected dhash distance 0–3
        return frame

    if variant_id == "demo-480p-reencode":
        # Resize to 480p — expected dhash distance 10–18
        return cv2.resize(frame, (out_w, out_h))

    if variant_id == "demo-crop-color":
        # Crop 10% borders + boost saturation 1.4× — expected dhash distance 16–22
        h, w = frame.shape[:2]
        x0 = int(w * 0.1)
        y0 = int(h * 0.1)
        cropped = frame[y0 : y0 + out_h, x0 : x0 + out_w]
        if cropped.shape[0] < out_h or cropped.shape[1] < out_w:
            cropped = cv2.resize(frame, (out_w, out_h))
        hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.4, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if variant_id == "demo-overlay-meme":
        # Caption bar at bottom — expected dhash distance 20–28
        result = frame.copy()
        h, w = result.shape[:2]
        bar_h = max(40, h // 8)
        cv2.rectangle(result, (0, h - bar_h), (w, h), (0, 0, 0), -1)
        cv2.putText(
            result,
            "EPIC SPORTS MOMENT LOL",
            (10, h - bar_h // 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        return result

    if variant_id == "demo-screen-record":
        # Gaussian noise + brightness reduction 15% — expected dhash distance 24–32
        noise = rng.integers(-20, 20, frame.shape, dtype=np.int16)
        noisy = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(noisy, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 0.85, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return frame
