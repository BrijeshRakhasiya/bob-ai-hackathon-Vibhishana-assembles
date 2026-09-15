# RouteGuard AI - Supply Chain Disruption Assistant & Fleet Utilisation Optimizer

> IBM BoB AI Innovation Hackathon 2026 - Team Vibhishana Assembles

---

## Team

| Field | Value |
|---|---|
| **Team Name** | Vibhishana Assembles |
| **Track** | AI |
| **Team Lead** | Brijesh Rakhasiya — 23aiml060@charusat.edu.in |
| **Members** | Vaibhav Tandel, Maulya Soni, Om Choksi |

---

## Problem Statement

Supply chain disruptions — weather events, port strikes, geopolitical crises — cascade across hundreds of active shipments in ways that are impossible to track manually. Fleet assets (trucks, containers, vessels) sit idle while other routes are overloaded. Cold chain shipments (vaccines, perishables) are especially vulnerable: a single temperature excursion across any leg can spoil a $500K+ cargo, but breaches are only discovered at delivery when it is too late.

---

## Solution

RouteGuard AI is an IBM BoB-powered control tower that identifies which shipments are affected by an active disruption, recommends re-routing or carrier alternatives, identifies idle fleet assets for redeployment, and monitors cold chain IoT sensor logs to detect temperature excursions and classify their regulatory severity before delivery. It combines a fully deterministic risk engine with a CrewAI multi-agent carrier negotiation system and an IBM BoB grounded AI copilot that translates computed facts into plain-language dispatcher briefs with a strict zero-hallucination policy.

---

## Key Features

- **Live Disruption Risk Engine:** Integrates GDACS public disaster alerts and correlates them with active shipment coordinates via Haversine geometry to produce a 0-100 auditable risk score per shipment.
- **Cold Chain IoT Excursion Detector:** Real-time sensor log monitor that detects temperature and humidity breaches pre-delivery and classifies regulatory severity against WHO Vaccine Protocols and USFDA 21 CFR Part 11.
- **CrewAI Multi-Agent Carrier Auction:** Three autonomous carrier agents (Speed, Cost, Reliability personas) bid on reroute corridors; a negotiator agent selects the optimal contract automatically.
- **Fleet Utilisation Optimizer:** Geo-proximity matching of idle trucks and containers near disruption nodes to overloaded freight corridors, with utilisation percentage scoring.
- **IBM BoB Grounded AI Copilot:** Sends only pre-computed deterministic facts to the LLM; the copilot is explicitly forbidden from inventing numbers not present in the payload.

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.13, JavaScript (ES6), HTML5, CSS3 |
| **Frameworks** | FastAPI, Pydantic v2, pytest-asyncio |
| **IBM Technologies** | IBM BoB, IBM watsonx.ai (Granite via Groq endpoint) |
| **AI / Agents** | CrewAI 1.15, Groq API (openai/gpt-oss-120b) |
| **Live Data** | GDACS Public Disaster & Weather API (aiohttp) |
| **Other** | GitHub Actions, uv (dependency manager) |

---

## Repository Structure

```
├── src/                        # All source code
│   ├── backend/                # FastAPI application
│   │   ├── app/
│   │   │   ├── agents/         # CrewAI carrier negotiation agent
│   │   │   ├── engines/        # Deterministic risk, reroute, fleet, cold-chain engines
│   │   │   ├── models/         # Pydantic schemas and demo data
│   │   │   ├── routers/        # API endpoints
│   │   │   └── tests/          # 16 unit tests (all passing)
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── frontend/               # Vanilla JS Control Tower dashboard
├── docs/                       # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                       # Demo artifacts
│   ├── screenshots/            # App screenshots
│   └── demo-video-link.txt     # Link to demo video
├── presentation/               # Slide deck
│   ├── slides.html             # 10-slide interactive HTML deck
│   └── RouteGuard_AI_Presentation.pptx
└── submission.yaml             # Structured submission metadata
```

---

## How to Run

```bash
# 1. Clone the repo
git clone https://github.com/BrijeshRakhasiya/bob-ai-hackathon-Vibhishana-assembles.git
cd bob-ai-hackathon-Vibhishana-assembles

# 2. Enter backend directory and create virtual environment
cd src/backend
uv venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# 5. Run the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Open the frontend
# Open src/frontend/index.html in any browser
```

- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Frontend Dashboard:** Open `src/frontend/index.html` directly in browser

---

## Demo

| Artifact | Link |
|---|---|
| Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| Screenshots | [See demo/screenshots/](demo/screenshots/) |
| Presentation | [See presentation/slides.html](presentation/slides.html) |

---

## Known Limitations

- Live demo is not cloud-deployed — the app runs locally; no public hosted URL is available for this submission.
- The GDACS disruption feed is live but read-only; in production this would be supplemented with proprietary carrier APIs and port authority feeds.
- Cold chain sensor data uses realistic simulated IoT logs — integration with real hardware sensor streams (e.g., Sensitech, Testo) would be required for production.

---

## What We're Most Proud Of

The core risk engine, cold chain excursion detector, and reroute optimizer are **100% deterministic and fully auditable** — every risk point and regulatory alert can be traced to a named, inspectable factor. The IBM BoB AI copilot layer sits strictly on top as a plain-language explainer, grounded to cite only numbers already computed by the engine. This hybrid architecture — deterministic engines + grounded LLM — is what makes RouteGuard AI trustworthy and safe for real-world dispatcher decisions, not just a chatbot that sounds confident.
