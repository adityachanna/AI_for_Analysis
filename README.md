# SentinelAI MVP

SentinelAI is a local demo for sports media rights protection. A rights holder registers an official video, the backend extracts keyframe fingerprints, and the app scans seeded mock platform results through a cost-ordered detection cascade.

## Stack

- Frontend: Next.js app in `frontend/`
- Backend: FastAPI app in `backend/`
- AI layer: Gemini / Vertex AI contract through `GEMINI_API_KEY`, with deterministic fallback when the key is absent
- Vision layer: optional Cloud Vision API and Video Intelligence API enrichment for keyframe labels, OCR, logos, shots, labels, and transcript evidence
- Storage: Firebase Storage / GCS when `USE_GCS=true`, otherwise local filesystem under `backend/data/`
- Database: Firestore sync when Firebase Admin credentials are available, plus SQLite at `backend/data/sentinelai.db` for local demo state
- Graph: SQLite graph-style `graph_nodes` and `graph_edges`, shaped for a later Neo4j migration

## Local Setup

Backend:

```powershell
cd sentinelai\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd sentinelai\frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Open `http://localhost:3000`.

## Environment Variables

Backend:

- `GEMINI_API_KEY`: optional. When set, the backend calls the Google Gen AI SDK for content passport text and `gemini-embedding-001` embeddings. Deterministic fallback keeps demos working offline.
- `GOOGLE_APPLICATION_CREDENTIALS`: optional Firebase Admin service account JSON path for Firebase Auth verification, Firestore writes, and GCS access.
- `FIREBASE_PROJECT_ID`: default `aditya-12835`.
- `FIREBASE_STORAGE_BUCKET`: default `aditya-12835.firebasestorage.app`.
- `FIREBASE_ADMIN_ENABLED`: default `false`. Set `true` on Cloud Run or when local ADC/service-account credentials are available.
- `FIREBASE_AUTH_REQUIRED`: default `false`. Set `true` in deployment to reject requests without a valid frontend Firebase ID token.
- `USE_GCS`: default `false`. Set `true` to upload originals and generated demo suspects to the Firebase/GCS bucket.
- `VISION_AI_ENABLED`: default `false`. Set `true` to call Cloud Vision API on extracted image keyframes.
- `VIDEO_INTELLIGENCE_ENABLED`: default `false`. Set `true` with `USE_GCS=true` to call Video Intelligence API on the uploaded `gs://` video.
- `MAX_UPLOAD_MB`: default `50`.
- `DATABASE_URL`: default `sqlite:///backend/data/sentinelai.db`.

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`: default `http://127.0.0.1:8000`.

## API

- `GET /health`
- `POST /api/assets/register`
- `GET /api/assets`
- `GET /api/assets/{asset_id}`
- `POST /api/assets/{asset_id}/scan`
- `GET /api/assets/{asset_id}/violations`
- `POST /api/assets/{asset_id}/demo-clips`
- `GET /api/assets/{asset_id}/demo-clips`
- `GET /api/violations/{violation_id}`
- `GET /api/graph/{asset_id}`
- `GET /api/audit`
- `GET /api/audit/{asset_id}`
- `GET /api/vision-ai/capabilities`

## Detection Cascade

Registration now follows the demo pipeline order: compute the source SHA-256 hash, register a simulated SynthID token, extract 8-12 keyframes, compute dHash fingerprints, enrich keyframes/video with Vision AI evidence, generate a Gemini Content Passport plus embedding, sync the asset to Firestore when credentials exist, upload to GCS/Firebase Storage when enabled, and create five transformed demo candidates. The response includes `vision_ai_plan`, which explains selected Google Vision products, enabled backend flags, billable-unit estimates, and estimated registration cost.

SentinelAI uses Google Cloud computer vision products by fit:

- Cloud Vision API: keyframe labels, OCR, logo hints, and object hints.
- Video Intelligence API: shot/video labels, text, logo recognition, and transcript evidence.
- Gemini on Vertex AI / Gemini API: Content Passport, semantic reasoning, and mutation explanation.
- Vertex AI Vision: documented upgrade path for continuous stream ingestion and Vision Warehouse search.
- Document AI: future path for contracts, takedown notices, and rights documents.

The backend creates five demo suspect clips for every registered asset:

- exact repost
- 480p re-encode
- 10% crop plus color grade
- overlay/meme edit
- screen-recorded recapture

Each generated clip has deterministic transformed bytes, a mutation manifest, a GCS/local URI, dHashes at different distances, Gemini/fallback semantic details, and graph metadata for entities, OCR/logo/label evidence, mutation evidence, distribution context, and graph edges.

Stage A checks simulated SynthID continuity plus dHash distance. Stage B compares semantic tags and structured descriptions. Stage C runs Gemini semantic/audio-style explanation and classification for edited or uncertain cases. Confirmed and probable matches are written to `violations`, optionally synced to Firestore, and connected in the graph tables.

Every stage decision is also written to a local append-only `audit_log` table with the same shape intended for BigQuery: `stage_id`, `timestamp`, `video_hash`, `similarity_score`, `decision`, `estimated_cost_usd`, `matched_asset_id`, and `suspect_id`. The dashboard displays total decisions and estimated cost-per-detection from this audit log.

## Demo Script

1. Start the backend and frontend.
2. Upload an official sports highlight under 50MB.
3. Review the generated fingerprints, SynthID demo token, and AI summary.
4. Open the asset workspace and click `Run cascade scan`.
5. Confirm that the timeline shows Stage A, Stage B, and Stage C decisions.
6. Open a violation report and review confidence breakdown plus propagation graph.

The MVP should complete the local demo in under three minutes once dependencies are installed.

## Upgrade Path

- Replace mock platform data with crawler or partner ingestion jobs.
- Replace simulated SynthID with official marker APIs where available.
- Move SQLite to Cloud SQL or AlloyDB.
- Move graph tables to Neo4j using the same node and edge types.
- Deploy backend to Cloud Run and frontend to Vercel or Firebase Hosting.
