from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services.auth_service import CurrentUser, get_current_user

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("/{violation_id}")
def get_violation(violation_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM violations WHERE id = ?", (violation_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Violation not found")
        violation = dict(row)
        asset = db.execute(
            "SELECT id, title, owner, owner_uid, sport, ai_summary, gcs_uri, synthid_token FROM assets WHERE id = ?",
            (violation["asset_id"],),
        ).fetchone()
        if asset and user.uid != "demo-user" and asset["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Violation belongs to a different Firebase user")
        violation["asset"] = dict(asset) if asset else None
        return violation
