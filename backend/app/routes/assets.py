import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..db import get_db
from ..models import AssetCreateResponse, ScanRequest, ScanResponse
from ..services.gemini_service import analyze_registered_media, dumps_analysis
from ..services.scan_service import run_scan
from ..services.video_service import extract_keyframes, validate_and_save_upload

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("/register", response_model=AssetCreateResponse)
async def register_asset(
    title: str = Form(...),
    sport: str | None = Form(None),
    owner: str | None = Form(None),
    file: UploadFile = File(...),
):
    filename, path, _size = await validate_and_save_upload(file)
    asset_id = uuid4().hex
    keyframes = extract_keyframes(path, asset_id)
    analysis = analyze_registered_media(title, sport, keyframes)
    created_at = datetime.now(timezone.utc).isoformat()
    asset = {
        "id": asset_id,
        "title": title,
        "sport": sport,
        "owner": owner,
        "filename": filename,
        "file_path": str(path),
        "synthid_token": f"synthid-demo-{asset_id[:12]}",
        "ai_summary": analysis["summary"],
        "structured_analysis": dumps_analysis(analysis),
        "content_passport": json.dumps(analysis["content_passport"]),
        "passport_embedding": json.dumps(analysis["passport_embedding"]),
        "created_at": created_at,
    }

    with get_db() as db:
        db.execute(
            """
            INSERT INTO assets(
                id, title, sport, owner, filename, file_path, synthid_token,
                ai_summary, structured_analysis, content_passport, passport_embedding, created_at
            )
            VALUES (
                :id, :title, :sport, :owner, :filename, :file_path, :synthid_token,
                :ai_summary, :structured_analysis, :content_passport, :passport_embedding, :created_at
            )
            """,
            asset,
        )
        for frame in keyframes:
            db.execute(
                """
                INSERT INTO asset_keyframes(asset_id, frame_index, timestamp_ms, dhash, evidence_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (asset_id, frame["frame_index"], frame["timestamp_ms"], frame["dhash"], frame.get("evidence_path")),
            )

    return {
        **asset,
        "structured_analysis": analysis,
        "content_passport": analysis["content_passport"],
        "passport_embedding": analysis["passport_embedding"],
        "keyframes": keyframes,
    }


@router.get("")
def list_assets():
    with get_db() as db:
        assets = [dict(row) for row in db.execute("SELECT * FROM assets ORDER BY created_at DESC")]
        for asset in assets:
            asset["structured_analysis"] = json.loads(asset["structured_analysis"])
            asset["content_passport"] = json.loads(asset["content_passport"])
            asset["passport_embedding"] = json.loads(asset["passport_embedding"])
            asset["keyframe_count"] = db.execute(
                "SELECT COUNT(*) AS count FROM asset_keyframes WHERE asset_id = ?", (asset["id"],)
            ).fetchone()["count"]
            asset["violation_count"] = db.execute(
                "SELECT COUNT(*) AS count FROM violations WHERE asset_id = ?", (asset["id"],)
            ).fetchone()["count"]
        return assets


@router.get("/{asset_id}")
def get_asset(asset_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        asset = dict(row)
        asset["structured_analysis"] = json.loads(asset["structured_analysis"])
        asset["content_passport"] = json.loads(asset["content_passport"])
        asset["passport_embedding"] = json.loads(asset["passport_embedding"])
        asset["keyframes"] = [
            dict(frame) for frame in db.execute("SELECT * FROM asset_keyframes WHERE asset_id = ?", (asset_id,))
        ]
        return asset


@router.post("/{asset_id}/scan", response_model=ScanResponse)
def scan_asset(asset_id: str, request: ScanRequest | None = None):
    with get_db() as db:
        if not db.execute("SELECT 1 FROM assets WHERE id = ?", (asset_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Asset not found")
        return run_scan(db, asset_id, request.suspect_url if request else None)


@router.get("/{asset_id}/violations")
def list_asset_violations(asset_id: str):
    with get_db() as db:
        return [
            dict(row)
            for row in db.execute("SELECT * FROM violations WHERE asset_id = ? ORDER BY confidence_overall DESC", (asset_id,))
        ]
