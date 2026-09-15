from fastapi import APIRouter, HTTPException

from app.engines.disruption_feed import fetch_all_disruptions
from app.engines.reroute_engine import simulate_reroutes
from app.engines.risk_engine import assess_risk, find_affected_shipments
from app.models import demo_data

router = APIRouter()


@router.get("/disruptions")
async def get_active_disruptions():
    """Live GDACS weather feed + seeded NHAI highway advisories."""
    disruptions = await fetch_all_disruptions()
    return {"count": len(disruptions), "disruptions": disruptions}


@router.get("/assessments")
async def get_all_risk_assessments():
    """Stage 1 + 2: correlate every shipment against active disruptions and score it."""
    disruptions = await fetch_all_disruptions()
    affected = find_affected_shipments(demo_data.SHIPMENTS, disruptions)

    results = []
    for shipment in demo_data.SHIPMENTS:
        hits = affected.get(shipment.id, [])
        assessment = assess_risk(shipment, hits)
        results.append(assessment)

    results.sort(key=lambda a: a.score, reverse=True)
    return {"assessments": results}


@router.get("/reroute/{shipment_id}")
async def get_reroute_options(shipment_id: str):
    """Stage 3: alternative corridors for an at-risk shipment."""
    shipment = demo_data.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    disruptions = await fetch_all_disruptions()
    affected = find_affected_shipments([shipment], disruptions)
    hits = affected.get(shipment.id, [])
    assessment = assess_risk(shipment, hits)

    options = simulate_reroutes(shipment, assessment)
    return {"assessment": assessment, "reroute_options": options}
