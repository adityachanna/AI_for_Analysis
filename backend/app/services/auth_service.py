from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException

from ..config import settings


@dataclass
class CurrentUser:
    uid: str
    email: str | None = None
    provider: str = "demo"


_firebase_initialized = False


def _init_firebase_admin() -> bool:
    global _firebase_initialized
    if not settings.firebase_admin_enabled:
        return False
    if _firebase_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials
    except Exception:
        return False

    if firebase_admin._apps:
        _firebase_initialized = True
        return True

    options = {"projectId": settings.firebase_project_id, "storageBucket": settings.firebase_storage_bucket}
    try:
        if settings.firebase_admin_creds:
            firebase_admin.initialize_app(credentials.Certificate(settings.firebase_admin_creds), options)
        else:
            firebase_admin.initialize_app(options=options)
        _firebase_initialized = True
        return True
    except Exception:
        return False


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if token and _init_firebase_admin():
        try:
            from firebase_admin import auth

            decoded = auth.verify_id_token(token)
            return CurrentUser(
                uid=decoded["uid"],
                email=decoded.get("email"),
                provider=decoded.get("firebase", {}).get("sign_in_provider", "firebase"),
            )
        except Exception as exc:
            if settings.firebase_auth_required:
                raise HTTPException(status_code=401, detail="Invalid Firebase ID token") from exc

    if settings.firebase_auth_required:
        raise HTTPException(status_code=401, detail="Firebase Bearer token required")

    return CurrentUser(uid="demo-user", email="demo@sentinelai.local", provider="local-demo")
