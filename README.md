# DiaRisk AI

DiaRisk AI is an agentic diabetes complication risk system that analyzes lab data, retinal images, and cognitive notes to produce multi-complication risk scores and actionable recommendations. The project provides a FastAPI backend, a static frontend dashboard, and an optional serverless proxy for hosted demos.

## Architecture

### Agent Workflow

1. Intake Agent
   - Parses lab reports (PDF/JPG) with OCR and validates values
2. Lab Value Agent (MedGemma)
   - Interprets lab values and produces concise highlights
3. Retinal Agent (MedSigLIP + MedGemma)
   - Generates embeddings and grades diabetic retinopathy
4. Cognitive Agent (MedGemma)
   - Scores cognitive screening notes
5. Orchestrator
   - Runs agents, captures trace timings, manages warnings
6. Risk Scoring Agent
   - Computes complication risk scores
7. Recommendation Agent (MedGemma)
   - Generates prioritized actions
8. Clinical Dashboard
   - Displays risks, trends, vitals, and action plan

### Data Flow

User uploads or enters data in the frontend:
- Lab report (PDF/JPG)
- Optional retinal image (JPG/PNG)
- Optional cognitive notes

Backend processes:
- OCR extraction and validation
- Agent execution with trace tracking
- Risk scoring and recommendations
- SQLite persistence for recent runs

Frontend renders:
- Risk cards and summary
- Agent trace panel
- Trend sparkline and vitals grid
- Action plan and recent history

## Project Structure

- `backend/` FastAPI service, agents, model registry, SQLite storage
- `frontend/` Static dashboard, Vercel proxy, styles
- `render.yaml` Render deployment configuration
- `diarisk_prd.md` Product requirements document

## Backend Setup (Local)

1) Create environment and install dependencies:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2) Install OCR dependencies (macOS):

```
brew install tesseract poppler
```

3) Run the API:

```
cd backend
uvicorn app.main:app --reload
```

## Frontend Setup (Local)

```
cd frontend
python3 -m http.server 5173
```

Open `http://localhost:5173/frontend/`.

## Environment Variables

Backend:
- `MODEL_DEVICE` (`auto`, `cuda`, `mps`, `cpu`)
- `MEDGEMMA_MODEL_ID` (default: `google/medgemma-1.5-4b-it`)
- `MEDSIGLIP_MODEL_ID` (default: `google/medsiglip`)
- `ENABLE_RETINAL` (default: `true`)
- `ENABLE_TEXT_LLM` (default: `true`)
- `OFFLINE_ONLY` (default: `true`)
- `DB_PATH` (default: `backend/data/diarisk.db`)

Frontend (Vercel proxy):
- `BACKEND_URL` (for the serverless proxy)

## API Endpoints

- `GET /health`
- `POST /api/labs/parse`
- `POST /api/analyze`
- `GET /api/history`

## Deployment

### Render (Backend)

This repo includes `render.yaml`. Render installs OCR dependencies and runs FastAPI.

### Vercel (Frontend)

The frontend includes a Vercel serverless proxy at `/api/*` that forwards to `BACKEND_URL`.

## Notes

- Model weights are not included in the repo. When `OFFLINE_ONLY=true`, the backend expects local cached weights.
- For hosted demos, consider disabling heavy model inference and using the proxy to reach a lightweight backend.
