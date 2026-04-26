import json
from datetime import datetime, timezone
from uuid import uuid4


STAGE_COSTS = {
    "A": 0.0001,
    "B": 0.005,
    "C": 0.05,
}


def write_stage_audit(db, *, stage: str, asset_id: str, suspect_id: str, video_hash: str, score: float, decision: str, details: dict) -> None:
    db.execute(
        """
        INSERT INTO audit_log(
            id, stage_id, timestamp, video_hash, similarity_score, decision,
            estimated_cost_usd, matched_asset_id, suspect_id, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            uuid4().hex,
            stage,
            datetime.now(timezone.utc).isoformat(),
            video_hash,
            score,
            decision,
            STAGE_COSTS.get(stage, 0.0),
            asset_id,
            suspect_id,
            json.dumps(details, sort_keys=True),
        ),
    )


def audit_summary(db, asset_id: str | None = None) -> dict:
    params = (asset_id,) if asset_id else ()
    where = "WHERE matched_asset_id = ?" if asset_id else ""
    rows = [dict(row) for row in db.execute(f"SELECT * FROM audit_log {where} ORDER BY timestamp DESC", params)]
    total_cost = round(sum(row["estimated_cost_usd"] for row in rows), 4)
    return {
        "total_decisions": len(rows),
        "estimated_cost_usd": total_cost,
        "rows": rows[:100],
    }
