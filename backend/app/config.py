import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SUSPECT_DIR = DATA_DIR / "suspects"
EVIDENCE_DIR = DATA_DIR / "evidence"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"


class Settings:
    app_name = "SentinelAI"
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sentinelai.db'}")

    # Gemini API (AI services)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    # Google Cloud Project
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "aditya-12835")
    google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    # Firebase (Auth + Firestore DB)
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "aditya-12835")
    firebase_storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "aditya-12835.firebasestorage.app")
    firebase_api_key = os.getenv("FIREBASE_API_KEY", "AIzaSyD_Qq8MrwcIP8V8c8v_uIdbTLA3QmKLeog")

    # GCS (Storage for assets/buckets)
    gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "aditya-12835.firebasestorage.app")
    gcs_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    use_gcs = os.getenv("USE_GCS", "true").lower() == "true"

    # Firebase Admin (for backend auth/DB)
    firebase_admin_enabled = os.getenv("FIREBASE_ADMIN_ENABLED", "true").lower() == "true"
    firebase_auth_required = os.getenv("FIREBASE_AUTH_REQUIRED", "false").lower() == "true"
    firebase_admin_creds = os.getenv("FIREBASE_ADMIN_CREDENTIALS", "")

    # Vision AI / Video Intelligence
    vision_ai_enabled = os.getenv("VISION_AI_ENABLED", "false").lower() == "true"
    video_intelligence_enabled = os.getenv("VIDEO_INTELLIGENCE_ENABLED", "false").lower() == "true"

    # Neo4j (Graph Database)
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    neo4j_enabled = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

    # FAISS (Vector Search)
    faiss_index_path = os.getenv("FAISS_INDEX_PATH", str(FAISS_INDEX_DIR / "embeddings.index"))
    faiss_dimension = int(os.getenv("FAISS_DIMENSION", "768"))
    faiss_enabled = os.getenv("FAISS_ENABLED", "true").lower() == "true"

    # Demo pipeline
    demo_variant_count = int(os.getenv("DEMO_VARIANT_COUNT", "5"))

    # Cost tracking
    enable_cost_tracking = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"

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
    for path in (DATA_DIR, UPLOAD_DIR, SUSPECT_DIR, EVIDENCE_DIR, FAISS_INDEX_DIR):
        path.mkdir(parents=True, exist_ok=True)