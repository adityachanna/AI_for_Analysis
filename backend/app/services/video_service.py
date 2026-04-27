import hashlib
import logging
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from ..config import EVIDENCE_DIR, UPLOAD_DIR, settings
from .fingerprint_service import dhash_bytes

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}


async def validate_and_save_upload(file: UploadFile) -> tuple[str, Path, int]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload mp4, mov, webm, or m4v.")
    if file.content_type not in settings.allowed_video_types:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {file.content_type}")

    asset_file_id = uuid4().hex
    safe_name = f"{asset_file_id}{suffix}"
    target = UPLOAD_DIR / safe_name
    size = 0

    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"Video exceeds {settings.max_upload_mb}MB limit.")
            out.write(chunk)

    return file.filename or safe_name, target, size


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extract_keyframes(path: Path, asset_id: str, count: int = 10) -> list[dict]:
    frames = _extract_with_opencv(path, asset_id, count)
    if frames:
        return frames
    return _extract_from_byte_windows(path, asset_id, count)


def _extract_with_opencv(path: Path, asset_id: str, count: int) -> list[dict]:
    try:
        import cv2  # type: ignore
    except ImportError:
        return []

    frame_dir = EVIDENCE_DIR / asset_id
    frame_dir.mkdir(parents=True, exist_ok=True)

    # Try PySceneDetect ContentDetector for scene-boundary keyframes
    scene_frames: list[int] = []
    try:
        from scenedetect import detect, ContentDetector  # type: ignore

        scene_list = detect(str(path), ContentDetector(threshold=27.0))
        for start_tc, end_tc in scene_list:
            mid = (start_tc.get_frames() + end_tc.get_frames()) // 2
            scene_frames.append(mid)
        logger.debug(f"PySceneDetect found {len(scene_list)} scenes in {path.name}")
    except ImportError:
        logger.debug("scenedetect not available; falling back to evenly-spaced frames.")
    except Exception as e:
        logger.warning(f"PySceneDetect failed for {path.name}: {e}")

    capture = cv2.VideoCapture(str(path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30)
    if total <= 0:
        capture.release()
        return []

    # Fill to `count` with evenly-spaced frames when scene detection yields too few
    evenly_spaced = [int(i * max(total - 1, 1) / max(count - 1, 1)) for i in range(count)]
    if len(scene_frames) < count:
        existing = set(scene_frames)
        for idx in evenly_spaced:
            if idx not in existing:
                scene_frames.append(idx)
                existing.add(idx)
            if len(scene_frames) >= count:
                break
    scene_frames.sort()
    selected = scene_frames[:count]
    scene_frame_set = set(scene_frames[:len(scene_list)] if 'scene_list' in dir() else [])  # noqa: F821

    frames = []
    for out_index, frame_index in enumerate(selected):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            continue
        resized = cv2.resize(frame, (9, 8))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        bits = gray[:, 1:] > gray[:, :-1]
        value = 0
        for bit in bits.flatten():
            value = (value << 1) | int(bit)
        evidence_path = frame_dir / f"frame_{out_index:02d}.jpg"
        cv2.imwrite(str(evidence_path), frame)
        extraction = "scenedetect-content" if frame_index in scene_frame_set else "evenly-spaced"
        frames.append(
            {
                "frame_index": out_index,
                "timestamp_ms": int((frame_index / fps) * 1000),
                "dhash": f"{value:016x}",
                "evidence_path": str(evidence_path),
                "semantic_metadata": {
                    "extraction": extraction,
                    "representative_role": "scene midpoint" if extraction == "scenedetect-content" else "shot midpoint",
                    "graph_hints": ["broadcast_frame", "scoreboard_candidate", "player_action_candidate"],
                },
            }
        )
    capture.release()
    return frames


def _extract_from_byte_windows(path: Path, asset_id: str, count: int) -> list[dict]:
    data = path.read_bytes()
    if not data:
        data = hashlib.sha256(path.name.encode()).digest()

    frame_dir = EVIDENCE_DIR / asset_id
    frame_dir.mkdir(parents=True, exist_ok=True)
    window = max(64, len(data) // count)
    frames = []
    for index in range(count):
        start = min(index * window, max(len(data) - 1, 0))
        chunk = data[start : start + window] or data
        evidence_path = frame_dir / f"fingerprint_{index:02d}.bin"
        evidence_path.write_bytes(hashlib.sha256(chunk).digest())
        frames.append(
            {
                "frame_index": index,
                "timestamp_ms": index * 1500,
                "dhash": dhash_bytes(chunk),
                "evidence_path": str(evidence_path),
                "semantic_metadata": {
                    "extraction": "byte-window-fallback",
                    "representative_role": "synthetic fingerprint window",
                    "graph_hints": ["byte_signature", "content_identity"],
                },
            }
        )
    return frames


def clone_as_suspect(source: Path, suspect_path: Path) -> None:
    suspect_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, suspect_path)
