import json
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import settings
from app.db import get_db, init_db
from app.services.fingerprint_service import dhash_bytes, hamming_distance
from app.services.scan_service import run_scan


class CoreBehaviorTest(unittest.TestCase):
    def test_dhash_exact_match_has_zero_distance(self):
        value = dhash_bytes(b"official highlight")
        self.assertEqual(hamming_distance(value, value), 0)

    def test_scan_creates_expected_mock_matches(self):
        db_path = Path.cwd() / "test_sentinelai.db"
        db_path.unlink(missing_ok=True)
        try:
            analysis = {
                "semantic_tags": ["sports", "highlight", "broadcast", "rights-managed"],
                "summary": "test",
            }
            with patch.object(settings, "database_url", f"sqlite:///{db_path}"):
                init_db()
                asset_id = "asset-test"
                with get_db() as db:
                    db.execute(
                        """
                        INSERT INTO assets(
                            id, title, sport, owner, filename, file_path, synthid_token,
                            ai_summary, structured_analysis, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            asset_id,
                            "Final highlight",
                            "Basketball",
                            "Owner",
                            "clip.mp4",
                            "clip.mp4",
                            "synthid-demo",
                            "summary",
                            json.dumps(analysis),
                            "2026-04-26T00:00:00Z",
                        ),
                    )
                    db.execute(
                        """
                        INSERT INTO asset_keyframes(asset_id, frame_index, timestamp_ms, dhash, evidence_path)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (asset_id, 0, 0, "0f0f0f0f0f0f0f0f", None),
                    )
                    result = run_scan(db, asset_id)

            statuses = {item["suspect_id"]: item["status"] for item in result["stages"]}
            self.assertEqual(statuses["mock-exact-repost"], "confirmed")
            self.assertEqual(statuses["mock-unrelated"], "no_match")
            self.assertGreaterEqual(len(result["violations"]), 3)
        finally:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
