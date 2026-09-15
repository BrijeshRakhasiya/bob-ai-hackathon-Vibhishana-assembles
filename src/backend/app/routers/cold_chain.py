"""
FastAPI router for Cold Chain IoT Telemetry & Excursion Analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.engines.cold_chain_engine import analyze_cold_chain_telemetry
from app.models.demo_data import COLD_CHAIN_LOGS, get_cold_chain_logs, get_shipment
from app.models.schemas import ColdChainAnalysisReport, IoTSensorLog

router = APIRouter()


class SpikeSimRequest(BaseModel):
    shipment_id: str
    spike_temp_c: float
    duration_minutes: int = 45


@router.get("/telemetry/{shipment_id}", response_model=list[IoTSensorLog])
def get_shipment_telemetry(shipment_id: str):
    shipment = get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{shipment_id}' not found.")
    logs = get_cold_chain_logs(shipment_id)
    return logs


@router.get("/report/{shipment_id}", response_model=ColdChainAnalysisReport)
def get_cold_chain_report(shipment_id: str):
    shipment = get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{shipment_id}' not found.")
    logs = get_cold_chain_logs(shipment_id)
    report = analyze_cold_chain_telemetry(shipment, logs)
    return report


@router.post("/simulate-spike", response_model=ColdChainAnalysisReport)
def simulate_temperature_spike(req: SpikeSimRequest):
    shipment = get_shipment(req.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{req.shipment_id}' not found.")

    existing_logs = get_cold_chain_logs(req.shipment_id)
    now = datetime.now(timezone.utc)

    # Append simulated spike telemetry reading
    new_log = IoTSensorLog(
        sensor_id=f"IOT-SPIKE-SIM",
        shipment_id=req.shipment_id,
        timestamp=now,
        temperature_c=req.spike_temp_c,
        humidity_pct=85.0,
        battery_pct=65.0,
        door_open=True if req.spike_temp_c > 12.0 else False,
        lat=shipment.origin.lat,
        lng=shipment.origin.lng,
    )

    updated_logs = list(existing_logs) + [new_log]
    COLD_CHAIN_LOGS[req.shipment_id] = updated_logs

    return analyze_cold_chain_telemetry(shipment, updated_logs)
