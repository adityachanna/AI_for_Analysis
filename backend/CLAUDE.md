# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (requires uv)
uv sync

# Start dev server (port 8000, hot-reload)
python main.py

# Run tests
python -m unittest discover -s tests -v

# Run a single test
python -m unittest tests.test_core.TestFingerprinting -v

# Syntax check
python -m compileall app tests
```

## Architecture

SentinelAI is a video rights-infringement detection backend. It registers source assets with multi-modal fingerprints, then scans suspect clips through a 3-stage confidence pipeline to detect piracy.

### Entry Points
- `main.py` — creates the uvicorn server, loads `.env`
- `app/main.py` — FastAPI app, router registration, CORS (`localhost:3000`)

### Data Layer (`app/db.py`)
SQLite is the primary store. Tables:
- `assets` — registered source videos (owner, hashes, AI summaries, GCS URI, synthid_token)
- `asset_keyframes` — extracted frames with dHash + semantic metadata
- `demo_clips` — generated piracy variants (5 per asset)
- `violations` — scan matches with per-signal confidence scores
- `audit_log` — stage decisions + estimated AI costs

### Registration Pipeline (`POST /api/assets/register`)
1. Upload validation + SHA-256 hash + SynthID token
2. Keyframe extraction via OpenCV + PySceneDetect
3. dHash fingerprinting per frame
4. Gemini Content Passport (semantic enrichment + text embedding → Pinecone)
5. Optional Vision AI enrichment (labels/OCR/logos) and Video Intelligence (shots, transcripts)
6. 5 demo clip variants generated to simulate piracy mutations

### Scan Pipeline (`app/services/scan_service.py`)
3-stage pipeline with escalating cost:
- **Stage A** (visual, $0.0001): dHash Hamming distance — confirmed if distance < 10
- **Stage B** (semantic, $0.005): Pinecone embedding similarity + Gemini reasoning — confirmed if score ≥ 0.72
- **Stage C** (multimodal, $0.05): Gemini video-level analysis handling re-encodes/overlays — probable if score ≥ 0.7
- Overall confidence: visual 45% + semantic 25% + audio 10% + gemini 20%
- Violations persist to SQLite + Neo4j graph

### Graph Layer (`app/services/neo4j_service.py`, `graph_service.py`)
Neo4j Aura stores relationships:
- Nodes: `ASSET`, `SUSPECT`, `DOMAIN`
- Edges: `DETECTED_IN`, `HOSTED_ON`, `RIGHTS_INFRINGEMENT`

### Demo Clips (`app/services/demo_clip_service.py`)
5 variants per asset simulating piracy mutations: exact repost, 480p re-encode, vertical crop, overlay/meme, screen-recorded capture. Each stores a transform manifest used by Stage C.

### Services Map
| Service | Responsibility |
|---|---|
| `video_service.py` | Keyframe extraction, file hashing, upload validation |
| `fingerprint_service.py` | dHash generation, Hamming distance scoring |
| `gemini_service.py` | Content Passport, semantic matching, text embeddings |
| `vision_ai_service.py` | Cloud Vision (labels/OCR/logos), Video Intelligence (shots/transcripts), deterministic fallback |
| `scan_service.py` | 3-stage pipeline orchestration |
| `graph_service.py` | Neo4j node/edge upserts |
| `pinecone_service.py` | Vector upsert and query |
| `gcs_service.py` | GCS upload for videos and demo clips |
| `auth_service.py` | Firebase ID token verification; falls back to `demo-user` |
| `audit_service.py` | Per-stage cost tracking and decision logging |

### Authentication
- `Authorization: Bearer <firebase-id-token>` header
- When `FIREBASE_AUTH_REQUIRED=false`, unauthenticated requests fall back to `demo-user`
- Assets are scoped by `owner_uid`

## Environment Variables (`.env`)

```
# Core
PORT=8000
DATABASE_URL=sqlite:///data/sentinelai.db
MAX_UPLOAD_MB=50

# Gemini (required)
GEMINI_API_KEY=

# Google Cloud
GOOGLE_CLOUD_PROJECT=aditya-12835
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=   # ADC path for Vision/Video Intelligence/GCS

# Firebase
FIREBASE_PROJECT_ID=aditya-12835
FIREBASE_STORAGE_BUCKET=aditya-12835.firebasestorage.app
FIREBASE_ADMIN_CREDENTIALS=       # path to service account JSON
FIREBASE_ADMIN_ENABLED=true
FIREBASE_AUTH_REQUIRED=false

# GCS
GCS_BUCKET_NAME=aditya-12835.firebasestorage.app
USE_GCS=true

# Vision AI (optional, deterministic fallback when disabled)
VISION_AI_ENABLED=false
VIDEO_INTELLIGENCE_ENABLED=false

# Neo4j
NEO4J_ENABLED=true
NEO4J_URI=neo4j+s://a7dc516f.databases.neo4j.io
NEO4J_USER=a7dc516f
NEO4J_PASSWORD=
NEO4J_DATABASE=a7dc516f

# Pinecone (dimension must match gemini-embedding-2 = 3072)
PINECONE_ENABLED=true
PINECONE_API_KEY=
PINECONE_INDEX_NAME=radiant-alder
PINECONE_DIMENSION=3072

# Demo
DEMO_VARIANT_COUNT=5
ENABLE_COST_TRACKING=true
```

## Key Conventions

- Cloud services (Vision AI, Video Intelligence, Neo4j, Pinecone, GCS, Firebase) all have `_ENABLED` toggles and deterministic/local fallbacks so the app runs without cloud credentials.
- The Firebase service account JSON is committed to `app/routes/` — do not expose it or add additional credentials to the repo.
- Routes live in `app/routes/`, business logic in `app/services/`, Pydantic models in `app/models.py`, DB schema in `app/db.py`, and settings in `app/config.py`.
