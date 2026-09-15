# Setup Guide

This guide assumes you have never seen this repo before. Follow it exactly, in order.

## Prerequisites

- Python 3.11 or later (3.13 recommended)
- `uv` package manager (install once: `pip install uv` or see https://docs.astral.sh/uv/)
- Git
- A Groq API key (free at https://console.groq.com) for the copilot and negotiation features

The app runs fully without an LLM key - the deterministic risk, fleet, and reroute endpoints
work offline. Only `/api/copilot/brief` and `/api/negotiation/{id}` need real credentials.

---

## 1. Clone the repo

```bash
git clone https://github.com/[your-github-username]/bob-ai-hackathon-Vibhishana-assembles.git
cd bob-ai-hackathon-Vibhishana-assembles
```

---

## 2. Create a virtual environment and install dependencies

```bash
cd src/backend

# Create an isolated virtual environment with uv
uv venv .venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install all dependencies (much faster than pip)
uv pip install -r requirements.txt
```

---

## 3. Configure environment variables

```bash
# Copy the template
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Description | Required? |
|---|---|---|
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | For copilot and negotiation |
| `LLM_API_KEY` | Your Groq API key (`gsk_...`) | For copilot and negotiation |
| `LLM_MODEL` | `openai/gpt-oss-120b` (or any Groq model) | For copilot and negotiation |

**Where to get a Groq API key:**
1. Go to https://console.groq.com and sign up (free)
2. Navigate to API Keys and click Create API Key
3. Copy the key (starts with `gsk_`) into `LLM_API_KEY` in your `.env`

If you skip this step, the app still runs fully - only the AI features return a stub message.

---

## 4. Run the backend

Make sure the virtual environment is active, then from inside `src/backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 5. Verify it is working

Open `http://localhost:8000/docs` in a browser - you should see the FastAPI Swagger UI
listing all endpoints.

Quick smoke tests from a second terminal (with the venv active):

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# List seeded shipments
curl http://localhost:8000/api/shipments
# Expected: JSON list of 3 shipments

# Risk assessments (live GDACS + seeded NHAI)
curl http://localhost:8000/api/risk/assessments
# Expected: JSON array with a score per shipment

# Active disruptions (calls real GDACS API)
curl http://localhost:8000/api/risk/disruptions
# Expected: JSON list (may be empty if no disasters active right now)
```

Open the control tower dashboard: `http://localhost:8000/app`
(or open `src/frontend/index.html` directly in a browser if you prefer static files)

---

## 6. Run the tests

```bash
# From inside src/backend/ with the venv active
pytest
```

Expected output:
```
................
16 passed in 0.2s
```

---

## 7. Open the presentation

Open `presentation/slides.html` in any browser - no server needed.
Open `presentation/RouteGuard_AI_Presentation.pptx` in PowerPoint or LibreOffice Impress.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Make sure you are running `uvicorn` from inside `src/backend/`, not the repo root |
| `uv: command not found` | Run `pip install uv` to install uv first |
| `uvicorn: command not found` | The venv is not active - run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux) |
| `crewai` install fails | Make sure you are using Python 3.11+ with `uv`. Run `uv venv .venv --python 3.13` |
| Negotiation endpoint returns fallback bids | `LLM_API_KEY` is not set in `.env` - add your Groq key |
| Copilot returns stub response | Same as above - set `LLM_API_KEY` |
| `/api/risk/disruptions` returns 0 results | Either no active GDACS disasters right now, or your network blocks `gdacs.org` |
| Port 8000 already in use | `uvicorn app.main:app --reload --port 8001` and reload the frontend |
