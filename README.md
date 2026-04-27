# SentinelAI (AI_for_Analysis)

SentinelAI is an MVP for **sports media rights protection**.

A rights holder registers an official video. The backend extracts **keyframes + perceptual fingerprints**, generates a controlled set of **mutated “suspect” clips**, and runs a **multi-stage detection cascade** to flag likely reposts/edits. Results are presented in a Next.js UI with evidence, audit logs, and a simple graph model (nodes/edges) to support future expansion.

> This repository contains both the **frontend (Next.js)** and **backend (FastAPI)**, plus optional integrations with **Gemini/Vertex AI**, **Cloud Vision**, **Video Intelligence**, and **Firebase/GCS**.

---

## Live demo (Cloud Run)

These deployments are **not local-only**; the demo is deployed on Google Cloud Run:

- **Frontend (Cloud Run):** https://sentinelai-frontend-zexgzh6owq-uc.a.run.app/
- **Backend (Cloud Run):** https://sentinelai-backend-1009519954306.us-central1.run.app/

### Quick check

- Backend health: `GET https://sentinelai-backend-1009519954306.us-central1.run.app/health`

---

## What this MVP demonstrates

### 1) Registration pipeline (official asset)
When an official video is registered, SentinelAI:

1. Computes a **SHA-256** hash for identity and deduplication.
2. Registers a **simulated SynthID token** (demo placeholder for provenance/watermark continuity).
3. Extracts **~8–12 keyframes**.
4. Computes **dHash perceptual fingerprints** for keyframes.
5. Optionally enriches visual evidence via:
   - **Cloud Vision API** (labels, OCR, logos, objects)
   - **Video Intelligence API** (shots, text, logos, transcript)
6. Generates structured metadata:
   - With **Gemini** when `GEMINI_API_KEY` is set
   - With a **deterministic fallback** when it is not

### 2) Seeded suspect clips (controlled “platform” results)
For each registered asset, the backend generates five deterministic demo clips that represent common infringement patterns:

- Exact repost
- 480p re-encode
- ~10% crop + color grade
- Overlay / meme edit
- Screen-recorded recapture

Each clip includes:

- A mutation manifest
- Local or GCS/Firebase Storage URI
- Fingerprints at different distances
- AI-generated (or fallback) semantic details
- Graph metadata for relationships and evidence

### 3) Detection cascade
Scanning uses a staged cascade:

- **Stage A:** SynthID continuity (simulated) + dHash distance
- **Stage B:** Semantic tag / structured metadata comparisons
- **Stage C:** Gemini reasoning (or fallback) for mutation explanation + classification

Every stage writes an append-only record to `audit_log` (SQLite) with a schema shaped for a later BigQuery pipeline.

---

## Repository layout

> The project lives under the `sentinelai/` directory.

- `sentinelai/frontend/` — Next.js (TypeScript) UI
- `sentinelai/backend/` — FastAPI (Python) API
- `sentinelai/backend/data/` — local demo storage (SQLite DB, generated clips, keyframes)

---

## Tech stack

- **Frontend:** Next.js + TypeScript
- **Backend:** FastAPI
- **AI layer:** Gemini / Vertex AI via `GEMINI_API_KEY` with deterministic offline fallback
- **Vision enrichment (optional):** Cloud Vision API + Video Intelligence API
- **Storage:** Firebase Storage / GCS when `USE_GCS=true`, else local filesystem
- **Database:** SQLite for demo state; optional Firestore sync when Admin credentials are available
- **Graph model:** SQLite `graph_nodes` / `graph_edges` (designed for later Neo4j migration)

---

## Using the deployed demo

1. Open the **frontend**:
   - https://sentinelai-frontend-zexgzh6owq-uc.a.run.app/
2. Upload an official sports highlight video (≤ `MAX_UPLOAD_MB`, default 50MB).
3. Review:
   - Extracted keyframes
   - Fingerprints (dHash)
   - Content passport summary (Gemini or fallback)
4. Run a scan for suspected reposts/edits.
5. Inspect violations:
   - Evidence timeline
   - Stage A/B/C decisions
   - Confidence breakdown
   - Graph relationships

---

## API (backend)

Base URL (deployed):

- `https://sentinelai-backend-1009519954306.us-central1.run.app`

Endpoints:

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

---

## Local development

### Backend (FastAPI)

```powershell
cd sentinelai\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)

```powershell
cd sentinelai\frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Open http://localhost:3000.

---

## Configuration

### Backend environment variables

- `GEMINI_API_KEY` (optional)
  - When set, calls Gemini for content passport text + embeddings.
  - When absent, a deterministic fallback keeps the demo working offline.
- `GOOGLE_APPLICATION_CREDENTIALS` (optional)
  - Firebase Admin service-account JSON path for Firebase Auth verification, Firestore writes, and GCS access.
- `FIREBASE_PROJECT_ID` (default: `aditya-12835`)
- `FIREBASE_STORAGE_BUCKET` (default: `aditya-12835.firebasestorage.app`)
- `FIREBASE_ADMIN_ENABLED` (default: `false`)
  - Set `true` on Cloud Run or when local ADC/service-account credentials are available.
- `FIREBASE_AUTH_REQUIRED` (default: `false`)
  - Set `true` in deployment to reject requests without a valid frontend Firebase ID token.
- `USE_GCS` (default: `false`)
  - Set `true` to upload originals and generated demo suspects to Firebase/GCS.
- `VISION_AI_ENABLED` (default: `false`)
  - Set `true` to call Cloud Vision API on extracted keyframes.
- `VIDEO_INTELLIGENCE_ENABLED` (default: `false`)
  - Set `true` with `USE_GCS=true` to call Video Intelligence API on the uploaded `gs://` video.
- `MAX_UPLOAD_MB` (default: `50`)
- `DATABASE_URL` (default: `sqlite:///backend/data/sentinelai.db`)

### Frontend environment variables

- `NEXT_PUBLIC_API_BASE_URL` (default: `http://127.0.0.1:8000`)

---

## Notes / roadmap

- Replace the seeded demo platform results with real ingestion (crawler, partner feeds, platform APIs).
- Replace the simulated SynthID token with official provenance/marker APIs when available.
- Move SQLite → Cloud SQL / AlloyDB.
- Move `graph_nodes` / `graph_edges` → Neo4j.
- Keep Cloud Run for backend and optionally move frontend to Vercel / Firebase Hosting.

---

## License

Add a license file if you intend to open-source this project.
