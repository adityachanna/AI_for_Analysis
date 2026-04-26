from fastapi import APIRouter, HTTPException

from ..db import get_db

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("/{violation_id}")
def get_violation(violation_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM violations WHERE id = ?", (violation_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Violation not found")
        violation = dict(row)
        asset = db.execute("SELECT id, title, owner, sport, ai_summary FROM assets WHERE id = ?", (violation["asset_id"],)).fetchone()
        violation["asset"] = dict(asset) if asset else None
        return violation
