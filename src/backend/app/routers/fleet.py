from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.engines.fleet_engine import compute_fleet_utilisation, find_redeployment_candidates
from app.models import demo_data

router = APIRouter()


class DispatchRequest(BaseModel):
    asset_id: str
    shipment_id: str


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


@router.post("/dispatch")
def dispatch_asset(req: DispatchRequest):
    """Mark an idle asset as dispatched to a shipment (in-memory demo store)."""
    shipment = demo_data.get_shipment(req.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    asset = next((a for a in demo_data.FLEET if a.id == req.asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{req.asset_id}' not found")

    already_active = asset.idle_since is None
    asset.idle_since = None  # now on active duty
    active = sum(1 for a in demo_data.FLEET if a.idle_since is None)
    return {
        "asset_id": asset.id,
        "shipment_id": shipment.id,
        "status": "dispatched",
        "already_active": already_active,
        "asset": asset,
        "utilisation_pct": compute_fleet_utilisation(demo_data.FLEET, active),
    }
