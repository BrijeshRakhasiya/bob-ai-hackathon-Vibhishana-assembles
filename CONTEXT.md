# RouteGuard AI — Project Context & Handover Document

**IBM BoB AI Innovation Hackathon 2026 | Team Vibhishana Assembles | CHARUSAT**

> This document is the single source of truth for what is built, how it works,
> what is tested, and what remains to be implemented. Any teammate picking up
> this project should read this file first.

---

## 1. Project Overview

RouteGuard AI is a supply chain disruption response and fleet utilisation control
tower. It solves one specific real-world problem: supply chain disruptions —
weather events, port strikes, highway closures — cascade across hundreds of active
shipments in ways that are impossible to track manually. Cold chain cargo (vaccines,
pharmaceuticals) is especially vulnerable because temperature excursions are only
discovered at delivery, when it is already too late.

The system is built in three layers:

```
Layer 1 (Bottom) — Deterministic Engines
  Risk Engine, Reroute Engine, Fleet Engine, Cold Chain Engine
  Pure Python math, fully auditable, no LLM, 16 tests passing.

Layer 2 (Middle) — Multi-Agent Negotiation
  CrewAI 1.15 with 3 carrier agents + 1 negotiator agent.
  Agents bid on reroute corridors, negotiator picks the best contract.
  Grounded: agents only reason over Layer 1 outputs, never invent numbers.

Layer 3 (Top) — IBM BoB AI Copilot
  Translates Layer 1 facts into plain-language dispatcher briefs.
  System prompt enforces zero-hallucination: cite only numbers in the payload.
  Uses Groq API (openai/gpt-oss-120b) via OpenAI-compatible endpoint.
```

---

## 2. Repository Structure

```
routeguard/
├── .github/
│   ├── workflows/validate.yml        GitHub Actions submission validator (6 steps)
│   └── ISSUE_TEMPLATE/config.yml
│
├── docs/
│   ├── problem-statement.md          Full problem breakdown
│   ├── solution-overview.md          Solution design rationale
│   ├── architecture.md               Three-layer architecture detail
│   └── setup-guide.md                Step-by-step local setup with uv
│
├── demo/
│   ├── demo-video-link.txt           UPDATE THIS with real YouTube URL
│   ├── live-demo-url.txt             NOT DEPLOYED (local only)
│   └── screenshots/                  SVG + PNG screenshots of all 5 tabs
│
├── presentation/
│   ├── slides.html                   10-slide HTML presentation deck
│   ├── RouteGuard_AI_Presentation.pptx
│   └── RouteGuard_AI_Hackathon_Presentation.md
│
├── src/
│   ├── backend/
│   │   ├── .env.example              LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
│   │   ├── requirements.txt          All Python dependencies (crewai>=1.15.0)
│   │   ├── pytest.ini                asyncio_mode=auto configured
│   │   └── app/
│   │       ├── main.py               FastAPI app, CORS, router registration, static mount
│   │       ├── agents/
│   │       │   └── carrier_negotiation.py   CrewAI multi-agent auction
│   │       ├── engines/
│   │       │   ├── risk_engine.py           Stage 1+2: Haversine impact + 0-100 scoring
│   │       │   ├── reroute_engine.py        Stage 3: Corridor alternatives + ranking
│   │       │   ├── fleet_engine.py          Stage 4: Idle asset geo-proximity matching
│   │       │   ├── cold_chain_engine.py     IoT log analysis + WHO/FDA severity
│   │       │   └── disruption_feed.py       Live GDACS API async fetcher
│   │       ├── models/
│   │       │   ├── schemas.py               All Pydantic v2 models (Shipment, etc.)
│   │       │   └── demo_data.py             In-memory demo shipments, fleet, IoT logs
│   │       ├── routers/
│   │       │   ├── risk.py                  GET /api/risk/assess/{id}
│   │       │   ├── reroute (in risk.py)     GET /api/risk/reroute/{id}
│   │       │   ├── fleet.py                 GET /api/fleet/redeployment-candidates
│   │       │   ├── cold_chain.py            GET /api/cold-chain/analyze/{id}
│   │       │   ├── negotiation.py           POST /api/negotiation/run
│   │       │   ├── copilot.py               POST /api/copilot/brief (LLM layer)
│   │       │   └── shipments.py             GET /api/shipments/
│   │       └── tests/
│   │           ├── test_risk_engine.py      7 tests
│   │           ├── test_reroute_and_fleet.py 7 tests
│   │           └── test_cold_chain.py       2 tests
│   └── frontend/
│       ├── index.html                5-tab Control Tower SPA
│       ├── app.js                    All tab logic, API calls, chart rendering
│       └── styles.css                HSL design system, glassmorphism
│
├── .gitignore                        Excludes .env, .venv, __pycache__, secrets
├── .gitattributes                    LF enforcement for YAML/YML on Linux CI
├── LICENSE                           MIT
├── README.md                         Follows official IBM BoB template structure
├── CONTRIBUTING.md                   Team contribution guide
└── submission.yaml                   All hackathon metadata fields filled
```

---

## 3. What Is Fully Implemented and Working

### 3.1 Backend Engines (Layer 1) — All Tested

#### Risk Engine (`app/engines/risk_engine.py`)
- Haversine geometry: calculates great-circle distance between any two lat/lng
  coordinates to determine if a shipment's route intersects a disruption zone.
- `find_affected_shipments()`: checks origin, destination, and all route waypoints
  against every active disruption's radius.
- `assess_risk()`: produces a deterministic 0-100 score with named factors:
  - `disruption_severity`: 10/25/40/55 points for LOW/MODERATE/HIGH/CRITICAL
  - `cargo_sensitivity`: 0/10/15/20 points for STANDARD/HIGH_VALUE/TIME_CRITICAL/COLD_CHAIN
  - `cargo_value`: 0/8/15 points tiered by value (under 10L / 10L-50L / above 50L)
  - `compounding_disruptions`: up to 10 bonus points for multiple simultaneous hits
- Output: `RiskAssessment` with band (LOW/MEDIUM/HIGH/CRITICAL), full factor list,
  and list of triggering disruption IDs.
- **Tests:** 7 passing tests covering intersection geometry, score calculation,
  sensitivity weighting, value tiering, and score cap at 100.

#### Reroute Engine (`app/engines/reroute_engine.py`)
- `simulate_reroutes()`: given an at-risk shipment and its assessment, generates
  3 alternative corridor options from a static knowledge base:
  - NH48 bypass (+3.5h, +Rs2200, 55% risk reduction)
  - Rail transshipment (+9h, +Rs6800, 80% risk reduction)
  - Secondary state highway detour (+5h, +Rs3100, 65% risk reduction)
- Ranks corridors by risk-reduction-per-hour-of-delay ratio.
- Marks the top-ranked option as `recommended=True`.
- Projects the post-reroute risk score for each option.
- **Tests:** 2 tests — verifies at least one option is recommended and that
  projected risk is lower than the original score.

#### Fleet Engine (`app/engines/fleet_engine.py`)
- `idle_hours()`: computes how long a fleet asset has been idle from `idle_since`.
- `find_redeployment_candidates()`: filters fleet by minimum idle hours (2h default)
  and maximum distance (250km default), ranks by `idle_hours / distance` score.
- `compute_fleet_utilisation()`: percentage of fleet currently active.
- **Tests:** 5 tests covering idle hours, distance exclusion, active asset exclusion,
  and utilisation percentage.

#### Cold Chain Engine (`app/engines/cold_chain_engine.py`)
- `analyze_cold_chain_telemetry()`: processes a sequence of `IoTSensorLog` records
  sorted by timestamp. Calculates:
  - Min/max/avg temperature recorded
  - Total excursion minutes (time spent outside 2-8°C window)
  - Degree-hours out of range (integral of temperature excess)
  - Door open event count
- Classifies severity against WHO TRS 961 / FDA 21 CFR GDP standards:
  - `NOMINAL`: zero excursion minutes
  - `STABILITY_OK`: under 15 minutes, temp under 10°C (within stability budget)
  - `QUARANTINE_REQUIRED`: under 2 hours, temp under 15°C (QA review needed)
  - `CARGO_SPOILED`: over 2 hours or temp above 15°C (reject delivery)
- Returns `ColdChainAnalysisReport` with recommended action text.
- **Tests:** 2 tests — nominal case (no breach) and critical spoiled case.

#### Disruption Feed (`app/engines/disruption_feed.py`)
- Async GDACS API client using `aiohttp`.
- `fetch_all_disruptions()`: fetches live disaster/weather events and maps them
  to internal `Disruption` schema with type, severity, coordinates, and radius.
- Falls back gracefully if the GDACS feed is unavailable (returns empty list so
  all other endpoints still work offline).

### 3.2 Multi-Agent Layer (Layer 2) — Implemented

#### Carrier Negotiation (`app/agents/carrier_negotiation.py`)
- Uses CrewAI 1.15 (`from crewai import Agent, Crew, LLM, Process, Task`).
- Three carrier agent personas:
  - **Swift Freight Co.**: speed-optimised, premium pricing, moderate reliability
  - **ValueHaul Logistics**: lowest price, longer ETAs, solid reliability
  - **TrustLine Carriers**: reliability and cold-chain compliance focus, best on-time
- Each agent receives the reroute corridor data (from Layer 1) and produces a bid
  as JSON: `{price_inr, eta_hours, reliability_score, rationale}`.
- A fourth Negotiator agent receives all three bids and the dispatcher's priority
  (cheapest / fastest / most_reliable / balanced) and picks the best contract.
- `_parse_bid_json()`: safe JSON extractor with deterministic fallback if LLM
  output cannot be parsed.
- Full deterministic fallback mode when `LLM_API_KEY` is not set (demo works offline).
- **Not directly unit-tested** (requires live LLM for full coverage).

### 3.3 IBM BoB Copilot Layer (Layer 3) — Implemented

#### Copilot Router (`app/routers/copilot.py`)
- `POST /api/copilot/brief`: accepts `{"shipment_id": "SHP-1001"}`.
- Internally calls all Layer 1 engines: fetch disruptions, assess risk, simulate
  reroutes, find fleet candidates.
- Assembles a `grounding_facts` JSON payload containing only the computed numbers.
- Sends that payload to the LLM with a strict system prompt:
  > "Cite ONLY numbers present in the payload. Never invent a price, ETA, distance,
  > or risk score that is not in the JSON you were given."
- Uses OpenAI Python SDK with Groq endpoint, `max_tokens=1024`.
- `model_dump(mode="json")` used throughout to handle `datetime` serialization.
- Returns `{"shipment_id", "brief", "grounding_facts"}`.
- Stub response when `LLM_API_KEY` is not set.

### 3.4 API Endpoints — All Registered

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/shipments/` | List all demo shipments |
| GET | `/api/risk/assess/{shipment_id}` | Run risk assessment for one shipment |
| GET | `/api/risk/reroute/{shipment_id}` | Get reroute options for one shipment |
| GET | `/api/fleet/redeployment-candidates` | Get ranked idle fleet assets |
| GET | `/api/fleet/utilisation` | Fleet utilisation percentage |
| GET | `/api/cold-chain/analyze/{shipment_id}` | Analyze IoT logs for cold chain |
| POST | `/api/negotiation/run` | Run CrewAI carrier auction |
| POST | `/api/copilot/brief` | Get IBM BoB dispatcher brief |

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

### 3.5 Frontend — Implemented

Five-tab single-page application at `src/frontend/index.html`:

| Tab | What it shows |
|-----|--------------|
| Control Tower Overview | Stat boxes, shipments table with risk scores, live disruption feed panel, reroute modal |
| Cold Chain IoT & Excursions | Temperature sensor bar chart, CRITICAL excursion alert box, regulatory classification, emergency reroute button |
| Multi-Agent Carrier Auction | 3 bidding cards (one per carrier agent), RECOMMENDED badge on winning bid |
| Fleet Asset Redeployment | Idle asset table with distance, idle hours, match score, Deploy Now button |
| IBM BoB Dispatcher Briefs | Chat interface, grounded response badge, live LLM call via backend API |

### 3.6 Demo Data — Seeded

Three shipments in `app/models/demo_data.py`:
- `SHP-1001`: Mumbai JNPT to Delhi Okhla, Pharma vaccines (COLD_CHAIN, Rs65L)
- `SHP-1002`: Ahmedabad GIDC to Surat Hazira, Textile machinery (HIGH_VALUE, Rs18L)
- `SHP-1003`: Chennai Port to Bengaluru Whitefield, Electronics JIT (TIME_CRITICAL, Rs32L)

Three fleet assets: TRK-201 (reefer, idle 5h Vadodara), TRK-202 (dry, idle 1h Ahmedabad),
TRK-203 (dry, active Surat).

Seven IoT sensor logs for SHP-1001 showing:
- Hours 1-4: Normal range (4.1°C to 5.2°C)
- Hour 5: Breach begins (8.8°C, door open at Vadodara due to highway delay)
- Hour 6: Peak excursion (10.4°C)
- Hour 7: Recovering (7.6°C after auxiliary power reset)

### 3.7 Test Suite

```
src/backend/app/tests/
  test_risk_engine.py         — 7 tests (geometry, scoring, capping, sensitivity)
  test_reroute_and_fleet.py   — 7 tests (reroute options, idle hours, candidates)
  test_cold_chain.py          — 2 tests (nominal, critical spoiled)

Result: 16/16 PASSED (Python 3.13, pytest 8.3.3)
```

Run with:
```bash
cd src/backend
.\.venv\Scripts\python.exe -m pytest app/tests/ -v
```

### 3.8 Submission Compliance

All IBM BoB template requirements are met and verified by the GitHub Actions
`validate.yml` workflow (6 steps):
- All required files present
- `submission.yaml` is valid YAML with all required fields
- `src/` contains source code
- `demo-video-link.txt` is not a placeholder
- README.md has no `[Your Team Name]` or `[Your Project Title Here]` text

---

## 4. What Is Not Yet Implemented (Remaining Work for Teammates)

The following items are identified, designed, and partially scaffolded.
Each teammate can pick one and work independently.

---

### 4.1 Real Database Backend (replaces in-memory demo_data.py)

**Current state:** All shipment, fleet, and IoT data is hard-coded in
`app/models/demo_data.py` as Python lists. Works for demo but cannot persist
changes or scale.

**What to do:**
- Add SQLite (simple) or PostgreSQL (production-grade) via SQLAlchemy or Tortoise ORM.
- Create migration scripts for `shipments`, `fleet_assets`, and `iot_sensor_logs` tables.
- Replace `demo_data.get_shipment()` calls with async DB queries.
- Add a `POST /api/shipments/` endpoint to create new shipments.
- Add a `POST /api/cold-chain/ingest` endpoint to receive real IoT sensor pushes.

**Files to touch:**
`app/models/demo_data.py`, create `app/db/` directory with models and session.

---

### 4.2 Live IoT Sensor WebSocket Stream

**Current state:** IoT sensor logs are static demo data sampled at hourly intervals.
The cold chain tab shows a static chart.

**What to do:**
- Add a WebSocket endpoint `ws://localhost:8000/ws/cold-chain/{shipment_id}`.
- Push a new `IoTSensorLog` every 30 seconds (simulated) or receive from a real
  MQTT/HTTP webhook from a sensor device.
- Frontend: update the sensor bar chart in real time using the WebSocket connection.
- Trigger automatic cold chain analysis and push a browser notification if severity
  changes from NOMINAL to QUARANTINE_REQUIRED or CARGO_SPOILED.

**Files to touch:**
`app/main.py` (add WebSocket), `app/routers/cold_chain.py`,
`src/frontend/app.js` (WebSocket client, live chart update).

---

### 4.3 User Authentication and Role-Based Access

**Current state:** All endpoints are open with no authentication. CORS is set to
`allow_origins=["*"]` (demo-only setting in `app/main.py`).

**What to do:**
- Add JWT authentication using `python-jose` and `passlib`.
- Two roles: `dispatcher` (read + action endpoints) and `admin` (full access).
- Protect all `/api/` endpoints with a `Depends(get_current_user)` FastAPI dependency.
- Add `POST /auth/login` and `POST /auth/register` endpoints.
- Frontend: add a simple login screen before the Control Tower loads.

**Files to touch:**
`app/main.py`, create `app/auth/` directory, all routers to add `Depends()`.

---

### 4.4 Cloud Deployment (Make the Live Demo URL Real)

**Current state:** `demo/live-demo-url.txt` says `NOT DEPLOYED`. The app only
runs locally. This is the single biggest gap for the second round evaluation.

**What to do:**
- Deploy the FastAPI backend to **Render** (free tier) or **Railway** (free tier):
  - Add a `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Add `runtime.txt`: `python-3.13`
  - Set environment variables `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` in the
    platform dashboard (never in code).
- Update `demo/live-demo-url.txt` with the real deployed URL.
- Update `submission.yaml` `artifacts.live_demo_url` field.
- The frontend `app.js` already reads `API_BASE` — change it from
  `http://localhost:8000` to the deployed URL.

**Files to touch:**
`src/frontend/app.js` (API_BASE), `demo/live-demo-url.txt`,
`submission.yaml`, add `Procfile` and `runtime.txt` at repo root.

---

### 4.5 Expanded Shipment Dataset and Real Corridor Map

**Current state:** Only 3 demo shipments and 3 corridor options hardcoded in
`reroute_engine.py`. The disruption feed uses live GDACS data but shipment routes
are fictional.

**What to do:**
- Expand demo data to 10-15 shipments covering more Indian corridors (Golden
  Quadrilateral, coastal routes, rail corridors).
- Replace the hardcoded `_ALT_CORRIDORS` in `reroute_engine.py` with a call to
  the OpenRouteService API (free tier) or OSRM to compute real alternative routes.
- Add corridor distance (km) to `RerouteOption` schema.
- Update the frontend shipments table to show carrier name, not just ID.

**Files to touch:**
`app/models/demo_data.py`, `app/engines/reroute_engine.py`,
`app/models/schemas.py`, `src/frontend/app.js`.

---

### 4.6 Notification and Alert System

**Current state:** Alerts are visible only if the dispatcher has the dashboard open.
No push notification or email exists.

**What to do:**
- Add a background task (FastAPI `BackgroundTasks` or APScheduler) that polls
  risk scores every 5 minutes for all active shipments.
- If any shipment crosses from MEDIUM to HIGH or CRITICAL, send an alert via:
  - Email (SMTP using `aiosmtplib`)
  - Slack webhook (HTTP POST to a Slack incoming webhook URL)
- Store alert history in the database (see 4.1).
- Add `GET /api/alerts/` endpoint to list recent alerts.

**Files to touch:**
`app/main.py` (scheduler), create `app/services/alert_service.py`,
create `app/routers/alerts.py`.

---

## 5. How to Run Locally

```bash
# Clone and enter backend
cd src/backend

# Create virtual environment and install dependencies
uv venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Linux / macOS

uv pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env: set LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# Start the server
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

# Open frontend (separate step — no build required)
# Open src/frontend/index.html in any browser

# Run tests
.\.venv\Scripts\python.exe -m pytest app/tests/ -v
```

API docs: http://localhost:8000/docs

---

## 6. Environment Variables

All configured in `src/backend/.env` (copy from `.env.example`):

| Variable | Value | Purpose |
|----------|-------|---------|
| `LLM_API_KEY` | `gsk_...` (Groq key) | Enables Copilot and CrewAI agents |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible endpoint |
| `LLM_MODEL` | `openai/gpt-oss-120b` | Groq reasoning model |

Without `LLM_API_KEY`, all deterministic endpoints still work. Only the Copilot
brief and CrewAI negotiation return stub/fallback responses.

---

## 7. Key Design Decisions (Important for Teammates)

1. **Deterministic first, AI on top.** Every number shown to the dispatcher comes
   from a Python math function, not from the LLM. The LLM only translates those
   numbers into words. This is called out explicitly in `docs/architecture.md`.

2. **`model_dump(mode="json")` is required.** Pydantic models containing `datetime`
   fields must use `model_dump(mode="json")` before JSON serialization. Using plain
   `model_dump()` will cause a `TypeError: datetime is not JSON serializable` crash.

3. **CrewAI 1.x API.** The installed version is `crewai==1.15.21`. It uses
   `from crewai import LLM` and requires passing `llm=llm` explicitly to each `Agent`.
   The old 0.x API (`agent = Agent(model="...")`) does not work.

4. **`max_tokens=1024` is required for `openai/gpt-oss-120b`.** This is a reasoning
   model that uses internal tokens before producing output. Without headroom the
   response is empty (`finish_reason: length`).

5. **Tests are in `app/tests/`, not `tests/`.** pytest is configured in `pytest.ini`
   at `src/backend/`. Always run pytest from the `src/backend/` directory.

---

## 8. Team

| Role | Name | Email |
|------|------|-------|
| Team Lead | Brijesh Rakhasiya | 23aiml060@charusat.edu.in |
| Member 2 | Vaibhav Tandel | 23dit073@charusat.edu.in |
| Member 3 | Maulya Soni | 23dit072@charusat.edu.in |
| Member 4 | Om Choksi | 23aiml010@charusat.edu.in |

**GitHub Repository:**
https://github.com/BrijeshRakhasiya/bob-ai-hackathon-Vibhishana-assembles
