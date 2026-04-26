import json
from datetime import datetime, timezone
from uuid import uuid4

from .fingerprint_service import hamming_distance, similarity_from_distance
from .audit_service import write_stage_audit
from .demo_clip_service import load_demo_clips
from .firebase_service import sync_violation_doc
from .gemini_service import semantic_match
from .graph_service import upsert_graph_for_violation
from .mock_suspects import materialize_suspect_hashes


def run_scan(db, asset_id: str, suspect_url: str | None = None) -> dict:
    asset_row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not asset_row:
        return {"asset_id": asset_id, "scanned": 0, "stages": [], "violations": []}

    asset = dict(asset_row)
    keyframes = [dict(row) for row in db.execute("SELECT * FROM asset_keyframes WHERE asset_id = ?", (asset_id,))]
    asset_hashes = [row["dhash"] for row in keyframes]
    asset_analysis = json.loads(asset["structured_analysis"])
    suspects = load_demo_clips(db, asset_id) or materialize_suspect_hashes(asset_hashes)
    if suspect_url:
        suspects.insert(
            0,
            {
                "id": f"submitted-{uuid4().hex[:8]}",
                "platform": "Submitted URL",
                "url": suspect_url,
                "title": "User submitted suspect URL",
                "mutation_type": "audio_or_semantic_reuse",
                "semantic_tags": ["highlight", "broadcast", "rights-managed"],
                "dhashes": [asset_hashes[0] if asset_hashes else "0"],
                "graph_metadata": {
                    "ai_summary": "User submitted URL is treated as semantic/audio reuse until pipeline evidence is computed.",
                    "distribution_context": {"platform": "Submitted URL"},
                },
            },
        )

    stages = []
    violations = []
    for suspect in suspects:
        min_distance = min(
            hamming_distance(asset_hash, suspect_hash)
            for asset_hash in asset_hashes[:3]
            for suspect_hash in suspect["dhashes"]
        )
        visual = similarity_from_distance(min_distance)
        synthid_match = 1 if min_distance < 10 else 0
        embedding_similarity = round(max(0.0, min(1.0, visual - 0.04 if min_distance <= 20 else visual * 0.78)), 3)
        stage = "A"
        semantic = 0.0
        gemini = 0.0
        audio = 0.15
        status = "no_match"
        explanation = f"Stage A dHash distance was {min_distance}."

        if min_distance < 10:
            status = "confirmed"
            gemini = 0.35
            semantic = 0.75
            audio = 0.35
            explanation = "Stage A confirmed a strong visual fingerprint match and simulated SynthID token continuity."
        elif min_distance <= 20:
            stage = "B"
            semantic_result = semantic_match(asset_analysis, suspect, visual * 0.6)
            semantic = semantic_result["confidence"]
            explanation = semantic_result["explanation"]
            status = "confirmed" if semantic >= 0.72 else "probable" if semantic >= 0.58 else "no_match"
            gemini = 0.45 if status != "no_match" else 0.2
            audio = 0.4 if status != "no_match" else 0.1
        else:
            stage = "C"
            semantic_result = semantic_match(asset_analysis, suspect, visual * 0.35)
            semantic = semantic_result["confidence"]
            gemini = 0.78 if semantic >= 0.5 and suspect["mutation_type"] != "unrelated" else 0.18
            audio = 0.55 if suspect["mutation_type"] == "audio_or_semantic_reuse" else 0.25
            status = "probable" if gemini >= 0.7 else "no_match"
            explanation = (
                f"Stage C Gemini-style reasoning reviewed edited or recaptured media signals. "
                f"{semantic_result['explanation']}"
            )

        overall = round((visual * 0.45) + (semantic * 0.25) + (audio * 0.1) + (gemini * 0.2), 3)
        if status == "confirmed":
            overall = max(overall, 0.86)
        if status == "probable":
            overall = max(overall, 0.71)

        stage_record = {
            "suspect_id": suspect["id"],
            "title": suspect["title"],
            "platform": suspect["platform"],
            "stage": stage,
            "status": status,
            "min_hamming_distance": min_distance,
            "visual_confidence": visual,
            "semantic_confidence": semantic,
            "gemini_confidence": gemini,
            "overall_confidence": overall,
            "synthid_match": synthid_match,
            "dhash_distance": min_distance,
            "embedding_similarity": embedding_similarity,
            "semantic_description_similarity": semantic,
            "audio_transcript_match": audio,
            "gcs_uri": suspect.get("gcs_uri"),
            "ai_details": suspect.get("ai_details", {}),
            "graph_metadata": suspect.get("graph_metadata", {}),
        }
        stages.append(stage_record)
        write_stage_audit(
            db,
            stage=stage,
            asset_id=asset_id,
            suspect_id=suspect["id"],
            video_hash=suspect["dhashes"][0],
            score=overall,
            decision=status,
            details=stage_record,
        )

        if status in {"confirmed", "probable"}:
            existing = db.execute(
                "SELECT * FROM violations WHERE asset_id = ? AND suspect_id = ?",
                (asset_id, suspect["id"]),
            ).fetchone()
            violation_id = existing["id"] if existing else uuid4().hex
            violation = {
                "id": violation_id,
                "asset_id": asset_id,
                "suspect_id": suspect["id"],
                "platform": suspect["platform"],
                "url": suspect["url"],
                "title": suspect["title"],
                "mutation_type": suspect["mutation_type"],
                "status": status,
                "stage": stage,
                "confidence_visual": visual,
                "confidence_semantic": semantic,
                "confidence_audio": audio,
                "confidence_gemini": gemini,
                "confidence_overall": overall,
                "synthid_match": synthid_match,
                "dhash_distance": min_distance,
                "embedding_similarity": embedding_similarity,
                "semantic_description_similarity": semantic,
                "audio_transcript_match": audio,
                "explanation": explanation,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            db.execute(
                """
                INSERT OR REPLACE INTO violations(
                    id, asset_id, suspect_id, platform, url, title, mutation_type, status, stage,
                    confidence_visual, confidence_semantic, confidence_audio, confidence_gemini,
                    confidence_overall, synthid_match, dhash_distance, embedding_similarity,
                    semantic_description_similarity, audio_transcript_match, explanation, created_at
                ) VALUES (
                    :id, :asset_id, :suspect_id, :platform, :url, :title, :mutation_type, :status, :stage,
                    :confidence_visual, :confidence_semantic, :confidence_audio, :confidence_gemini,
                    :confidence_overall, :synthid_match, :dhash_distance, :embedding_similarity,
                    :semantic_description_similarity, :audio_transcript_match, :explanation, :created_at
                )
                """,
                violation,
            )
            upsert_graph_for_violation(db, asset, violation)
            sync_violation_doc(violation)
            violations.append(violation)

    return {"asset_id": asset_id, "scanned": len(suspects), "stages": stages, "violations": violations}
