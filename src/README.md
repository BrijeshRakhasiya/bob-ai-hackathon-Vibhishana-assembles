# src/ layout

```
src/
├── backend/            FastAPI backend — the core of RouteGuard AI
│   ├── app/
│   │   ├── main.py          FastAPI app entrypoint
│   │   ├── routers/         API route handlers (shipments, risk, negotiation, fleet, copilot)
│   │   ├── engines/         Deterministic logic: disruption feed, risk scoring, reroute, fleet matching
│   │   ├── agents/          CrewAI multi-agent carrier negotiation
│   │   ├── models/          Pydantic schemas + seeded demo data
│   │   └── tests/           pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/            Dispatcher-facing dashboard (see src/frontend/README.md)
└── mcp/                 (optional) MCP server configuration, if wired up
```

Run `uvicorn app.main:app --reload` from inside `src/backend/` to start the API. See `../docs/setup-guide.md` for full instructions.
