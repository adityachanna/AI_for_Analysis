from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services.auth_service import CurrentUser, get_current_user
from ..services.audit_service import audit_summary

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def get_audit(user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        if user.uid != "demo-user":
            asset_ids = [row["id"] for row in db.execute("SELECT id FROM assets WHERE owner_uid = ?", (user.uid,))]
            summaries = [audit_summary(db, asset_id) for asset_id in asset_ids]
            rows = [row for summary in summaries for row in summary["rows"]]
            return {
                "total_decisions": len(rows),
                "estimated_cost_usd": round(sum(row["estimated_cost_usd"] for row in rows), 4),
                "rows": rows,
            }
        return audit_summary(db)


@router.get("/{asset_id}")
def get_asset_audit(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        asset = db.execute("SELECT owner_uid FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        if user.uid != "demo-user" and asset["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        return audit_summary(db, asset_id)
