import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SUSPECT_DIR = DATA_DIR / "suspects"
EVIDENCE_DIR = DATA_DIR / "evidence"


class Settings:
    app_name = "SentinelAI"
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sentinelai.db'}")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    allowed_video_types = {
        "video/mp4",
        "video/quicktime",
        "video/webm",
        "application/octet-stream",
    }

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()


def ensure_data_dirs() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, SUSPECT_DIR, EVIDENCE_DIR):
        path.mkdir(parents=True, exist_ok=True)
