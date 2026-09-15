from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.carrier_negotiation import run_carrier_negotiation
from app.engines.reroute_engine import simulate_reroutes
from app.engines.risk_engine import assess_risk, find_affected_shipments
from app.engines.disruption_feed import fetch_all_disruptions
from app.models import demo_data

router = APIRouter()


class NegotiationRequest(BaseModel):
    priority: str = "balanced"  # cheapest | fastest | most_reliable | balanced


@router.post("/{shipment_id}")
async def negotiate_reroute(shipment_id: str, req: NegotiationRequest):
    """
    Stage 3b: run the CrewAI multi-agent carrier negotiation for the
    top-recommended reroute option of a given shipment.
    """
    shipment = demo_data.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    disruptions = await fetch_all_disruptions()
    affected = find_affected_shipments([shipment], disruptions)
    hits = affected.get(shipment.id, [])
    assessment = assess_risk(shipment, hits)

    reroutes = simulate_reroutes(shipment, assessment)
    if not reroutes:
        raise HTTPException(status_code=400, detail="No reroute options available")

    top_option = next((r for r in reroutes if r.recommended), reroutes[0])

    result = run_carrier_negotiation(shipment, top_option, priority=req.priority)
    return {
        "shipment_id": shipment_id,
        "reroute_option": top_option,
        "negotiation": result,
    }
