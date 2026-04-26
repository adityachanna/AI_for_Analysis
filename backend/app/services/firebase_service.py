from typing import Any

from .auth_service import _init_firebase_admin


def sync_asset_doc(asset: dict, keyframes: list[dict]) -> str | None:
    if not _init_firebase_admin():
        return None
    try:
        from firebase_admin import firestore

        doc_path = f"assets/{asset['id']}"
        firestore.client().document(doc_path).set(
            {
                **_firestore_safe(asset),
                "keyframes": [_firestore_safe(frame) for frame in keyframes],
                "updated_at": asset["created_at"],
            },
            merge=True,
        )
        return doc_path
    except Exception:
        return None


def sync_demo_clip_doc(asset_id: str, clip: dict) -> str | None:
    if not _init_firebase_admin():
        return None
    try:
        from firebase_admin import firestore

        doc_path = f"assets/{asset_id}/demo_clips/{clip['id']}"
        firestore.client().document(doc_path).set(_firestore_safe(clip), merge=True)
        return doc_path
    except Exception:
        return None


def sync_violation_doc(violation: dict) -> str | None:
    if not _init_firebase_admin():
        return None
    try:
        from firebase_admin import firestore

        doc_path = f"violations/{violation['id']}"
        firestore.client().document(doc_path).set(_firestore_safe(violation), merge=True)
        return doc_path
    except Exception:
        return None


def _firestore_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _firestore_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_firestore_safe(item) for item in value]
    if hasattr(value, "as_posix"):
        return value.as_posix()
    return value
