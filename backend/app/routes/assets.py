import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..db import get_db
from ..models import AssetCreateResponse, ScanRequest, ScanResponse
from ..services.audit_service import write_registration_audit
from ..services.auth_service import CurrentUser, get_current_user
from ..services.cloud_storage_service import upload_to_bucket
from ..services.demo_clip_service import create_demo_clips_for_asset, load_demo_clips
from ..services.firebase_service import sync_asset_doc
from ..services.gemini_service import analyze_registered_media, dumps_analysis
from ..services.scan_service import run_scan
from ..services.video_service import extract_keyframes, file_sha256, register_synthid_token, validate_and_save_upload
from ..services.vision_ai_service import analyze_video_evidence, enrich_keyframes_with_vision_metadata
from ..services.vision_product_service import registration_vision_plan

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("/register", response_model=AssetCreateResponse)
async def register_asset(
    title: str = Form(...),
    sport: str | None = Form(None),
    owner: str | None = Form(None),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    filename, path, _size = await validate_and_save_upload(file)
    asset_id = uuid4().hex
    source_hash = file_sha256(path)
    synthid_token = register_synthid_token(asset_id, source_hash)
    keyframes = extract_keyframes(path, asset_id)
    upload = upload_to_bucket(path, f"sentinelai-assets/{user.uid}/{asset_id}{path.suffix}", file.content_type or "video/mp4")
    vision_evidence = analyze_video_evidence(path, upload["uri"], keyframes, title, sport)
    keyframes = enrich_keyframes_with_vision_metadata(keyframes, vision_evidence)
    analysis = analyze_registered_media(title, sport, keyframes, vision_evidence)
    created_at = datetime.now(timezone.utc).isoformat()
    asset = {
        "id": asset_id,
        "title": title,
        "sport": sport,
        "owner": owner,
        "owner_uid": user.uid,
        "filename": filename,
        "file_path": str(path),
        "source_hash": source_hash,
        "gcs_uri": upload["uri"],
        "firebase_doc_path": None,
        "synthid_token": synthid_token,
        "ai_summary": analysis["summary"],
        "structured_analysis": dumps_analysis(analysis),
        "vision_analysis": json.dumps(vision_evidence["vision"]),
        "video_intelligence_analysis": json.dumps(vision_evidence["video_intelligence"]),
        "content_passport": json.dumps(analysis["content_passport"]),
        "passport_embedding": json.dumps(analysis["passport_embedding"]),
        "created_at": created_at,
    }

    with get_db() as db:
        db.execute(
            """
            INSERT INTO assets(
                id, title, sport, owner, owner_uid, filename, file_path, source_hash, gcs_uri, firebase_doc_path,
                synthid_token, ai_summary, structured_analysis, vision_analysis, video_intelligence_analysis,
                content_passport, passport_embedding, created_at
            )
            VALUES (
                :id, :title, :sport, :owner, :owner_uid, :filename, :file_path, :source_hash, :gcs_uri, :firebase_doc_path,
                :synthid_token, :ai_summary, :structured_analysis, :vision_analysis, :video_intelligence_analysis,
                :content_passport, :passport_embedding, :created_at
            )
            """,
            asset,
        )
        for frame in keyframes:
            db.execute(
                """
                INSERT INTO asset_keyframes(asset_id, frame_index, timestamp_ms, dhash, evidence_path, semantic_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    frame["frame_index"],
                    frame["timestamp_ms"],
                    frame["dhash"],
                    frame.get("evidence_path"),
                    json.dumps(frame.get("semantic_metadata", {})),
                ),
            )
        firebase_doc_path = sync_asset_doc({**asset, "structured_analysis": analysis}, keyframes)
        if firebase_doc_path:
            db.execute("UPDATE assets SET firebase_doc_path = ? WHERE id = ?", (firebase_doc_path, asset_id))
            asset["firebase_doc_path"] = firebase_doc_path
        demo_clips = create_demo_clips_for_asset(db, asset, keyframes, analysis)
        vision_ai_plan = registration_vision_plan(len(keyframes), len(demo_clips))
        write_registration_audit(
            db,
            asset_id=asset_id,
            source_hash=source_hash,
            estimated_cost_usd=vision_ai_plan["estimated_cost_usd"],
            details=vision_ai_plan,
        )

    return {
        **asset,
        "structured_analysis": analysis,
        "vision_analysis": vision_evidence["vision"],
        "video_intelligence_analysis": vision_evidence["video_intelligence"],
        "vision_ai_plan": vision_ai_plan,
        "content_passport": analysis["content_passport"],
        "passport_embedding": analysis["passport_embedding"],
        "keyframes": keyframes,
        "demo_clips": demo_clips,
    }


@router.get("")
def list_assets(user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        if user.uid == "demo-user":
            rows = db.execute("SELECT * FROM assets ORDER BY created_at DESC")
        else:
            rows = db.execute("SELECT * FROM assets WHERE owner_uid = ? ORDER BY created_at DESC", (user.uid,))
        assets = [dict(row) for row in rows]
        for asset in assets:
            asset["structured_analysis"] = json.loads(asset["structured_analysis"])
            asset["vision_analysis"] = json.loads(asset.get("vision_analysis") or "{}")
            asset["video_intelligence_analysis"] = json.loads(asset.get("video_intelligence_analysis") or "{}")
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
def get_asset(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        asset = dict(row)
        if user.uid != "demo-user" and asset["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        asset["structured_analysis"] = json.loads(asset["structured_analysis"])
        asset["vision_analysis"] = json.loads(asset.get("vision_analysis") or "{}")
        asset["video_intelligence_analysis"] = json.loads(asset.get("video_intelligence_analysis") or "{}")
        asset["content_passport"] = json.loads(asset["content_passport"])
        asset["passport_embedding"] = json.loads(asset["passport_embedding"])
        asset["keyframes"] = [
            dict(frame) for frame in db.execute("SELECT * FROM asset_keyframes WHERE asset_id = ?", (asset_id,))
        ]
        for frame in asset["keyframes"]:
            frame["semantic_metadata"] = json.loads(frame.get("semantic_metadata") or "{}")
        asset["demo_clips"] = load_demo_clips(db, asset_id)
        return asset


@router.post("/{asset_id}/scan", response_model=ScanResponse)
def scan_asset(asset_id: str, request: ScanRequest | None = None, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        if user.uid != "demo-user" and row["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        return run_scan(db, asset_id, request.suspect_url if request else None)


@router.get("/{asset_id}/violations")
def list_asset_violations(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        if user.uid != "demo-user" and row["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        return [
            dict(row)
            for row in db.execute("SELECT * FROM violations WHERE asset_id = ? ORDER BY confidence_overall DESC", (asset_id,))
        ]


@router.post("/{asset_id}/demo-clips")
def regenerate_demo_clips(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        asset = dict(row)
        if user.uid != "demo-user" and asset["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        keyframes = [dict(frame) for frame in db.execute("SELECT * FROM asset_keyframes WHERE asset_id = ?", (asset_id,))]
        analysis = json.loads(asset["structured_analysis"])
        clips = create_demo_clips_for_asset(db, asset, keyframes, analysis)
        return {"asset_id": asset_id, "created": len(clips), "clips": clips}


@router.get("/{asset_id}/demo-clips")
def list_demo_clips(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        if user.uid != "demo-user" and row["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        return load_demo_clips(db, asset_id)
