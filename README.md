# SentinelAI MVP

SentinelAI is a local demo for sports media rights protection. A rights holder registers an official video, the backend extracts keyframe fingerprints, and the app scans seeded mock platform results through a cost-ordered detection cascade.

## Stack

- Frontend: Next.js app in `frontend/`
- Backend: FastAPI app in `backend/`
- AI layer: Gemini / Vertex AI contract through `GEMINI_API_KEY`, with deterministic fallback when the key is absent
- MVP storage: local filesystem under `backend/data/`
- MVP database: SQLite at `backend/data/sentinelai.db`
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

- `GEMINI_API_KEY`: optional. When set, the backend marks analysis as Gemini-configured. The MVP keeps the external call optional so demos work offline.
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
- `GET /api/violations/{violation_id}`
- `GET /api/graph/{asset_id}`
- `GET /api/audit`
- `GET /api/audit/{asset_id}`

## Detection Cascade

Registration saves the uploaded video, extracts 8-12 keyframes when OpenCV is available, or falls back to deterministic byte-window fingerprints when it is not. Each keyframe gets a 64-bit dHash, a simulated SynthID token, transcript placeholder, structured media summary, and a Gemini Content Passport. The passport is a scene-by-scene semantic reference designed to survive re-encoding, cropping, overlays, color changes, and screen recapture.

Scanning uses seeded mock suspects:

- exact repost
- cropped/reencoded repost
- overlay/meme edit
- screen-recorded recapture
- unrelated sports clip

Stage A checks simulated SynthID continuity plus dHash distance. Stage B compares semantic tags and structured descriptions. Stage C runs Gemini-style explanation and classification for edited or uncertain cases. Confirmed and probable matches are written to `violations` and connected in the graph tables.

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
