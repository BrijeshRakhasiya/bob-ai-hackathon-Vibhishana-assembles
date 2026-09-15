"""
RouteGuard AI — FastAPI entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000

Docs at http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import cold_chain, copilot, fleet, negotiation, risk, shipments

app = FastAPI(
    title="RouteGuard AI",
    description=(
        "Supply chain disruption response and fleet utilisation control tower "
        "for Indian domestic freight — built for the IBM BoB AI Innovation "
        "Hackathon 2026."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only — restrict in any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shipments.router, prefix="/api/shipments", tags=["shipments"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(negotiation.router, prefix="/api/negotiation", tags=["negotiation"])
app.include_router(fleet.router, prefix="/api/fleet", tags=["fleet"])
app.include_router(cold_chain.router, prefix="/api/cold-chain", tags=["cold-chain"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["copilot"])

# Mount static frontend directory if it exists
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/")
def root():
    return {"status": "ok", "service": "RouteGuard AI backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}
