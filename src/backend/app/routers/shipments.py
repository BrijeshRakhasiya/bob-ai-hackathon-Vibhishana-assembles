from fastapi import APIRouter, HTTPException

from app.models import demo_data
from app.models.schemas import Shipment

router = APIRouter()


@router.get("", response_model=list[Shipment])
def list_shipments():
    return demo_data.SHIPMENTS


@router.get("/{shipment_id}", response_model=Shipment)
def get_shipment(shipment_id: str):
    shipment = demo_data.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment
