import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


DATA_DIR = Path("/tmp/sentinelai")
UPLOAD_DIR = DATA_DIR / "uploads"
SUSPECT_DIR = DATA_DIR / "suspects"
EVIDENCE_DIR = DATA_DIR / "evidence"


class Settings:
    app_name = "SentinelAI"
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/sentinelai.db")

    # Gemini API (AI services)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    # Google Cloud Project
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "aditya-12835")
    google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    # Firebase (Auth + Firestore DB)
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "aditya-12835")
    firebase_storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "aditya-12835.firebasestorage.app")
    firebase_api_key = os.getenv("FIREBASE_API_KEY", "")

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

    # Neo4j (Graph Database — Aura cloud instance)
    neo4j_uri      = os.getenv("NEO4J_URI",      "neo4j+s://a7dc516f.databases.neo4j.io")
    neo4j_user     = os.getenv("NEO4J_USER",     "a7dc516f")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")          # set via env var — never hardcode
    neo4j_database = os.getenv("NEO4J_DATABASE", "a7dc516f")
    neo4j_enabled  = os.getenv("NEO4J_ENABLED",  "false").lower() == "true"

    # Pinecone (Vector Search)
    pinecone_api_key    = os.getenv("PINECONE_API_KEY",    "")              # set via env var
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "radiant-alder")
    pinecone_dimension  = int(os.getenv("PINECONE_DIMENSION", "3072"))      # gemini-embedding-2
    pinecone_enabled    = os.getenv("PINECONE_ENABLED",    "false").lower() == "true"

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
    for path in (DATA_DIR, UPLOAD_DIR, SUSPECT_DIR, EVIDENCE_DIR):
        path.mkdir(parents=True, exist_ok=True)