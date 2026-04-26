from fastapi import APIRouter

from ..db import get_db
from ..services.audit_service import audit_summary

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def get_audit():
    with get_db() as db:
        return audit_summary(db)


@router.get("/{asset_id}")
def get_asset_audit(asset_id: str):
    with get_db() as db:
        return audit_summary(db, asset_id)
