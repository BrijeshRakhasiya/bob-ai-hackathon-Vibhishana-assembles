# RouteGuard AI — Frontend

Dispatcher-facing dashboard for RouteGuard AI.

## Planned pages

- **Risk dashboard** — ranked list of shipments by live risk score
- **Shipment detail** — risk factors, reroute options, negotiate button
- **Fleet view** — idle assets and redeployment candidates
- **Copilot brief panel** — grounded natural-language summary per shipment

## Suggested stack

Any framework works against the FastAPI backend's REST API (`../backend/`, see `http://localhost:8000/docs` for the full OpenAPI schema once the backend is running). A minimal React + Vite or plain HTML/JS dashboard is enough for a hackathon demo — prioritise the risk dashboard and shipment detail views first, since those carry the most demo value.

## Setup

_Fill in once the frontend implementation is added — e.g._

```bash
cd src/frontend
npm install
npm run dev
```

Point API calls at `http://localhost:8000/api/...` (see backend `.env` for the port, if changed).
