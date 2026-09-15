from fastapi import APIRouter, HTTPException

from app.engines.fleet_engine import compute_fleet_utilisation, find_redeployment_candidates
from app.models import demo_data

router = APIRouter()


@router.get("")
def list_fleet():
    return demo_data.FLEET


@router.get("/utilisation")
def get_utilisation():
    active = sum(1 for a in demo_data.FLEET if a.idle_since is None)
    return {"utilisation_pct": compute_fleet_utilisation(demo_data.FLEET, active)}


@router.get("/redeploy/{shipment_id}")
def redeploy_candidates(shipment_id: str):
    shipment = demo_data.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    candidates = find_redeployment_candidates(demo_data.FLEET, shipment.destination)
    return {"shipment_id": shipment_id, "candidates": candidates}
