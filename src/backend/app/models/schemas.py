"""
Core data models for RouteGuard AI.

These are intentionally simple, explicit dataclasses/Pydantic models —
the risk and matching logic downstream must be auditable, so the shapes
that feed it need to be equally transparent.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CargoSensitivity(str, Enum):
    STANDARD = "standard"
    HIGH_VALUE = "high_value"
    COLD_CHAIN = "cold_chain"
    TIME_CRITICAL = "time_critical"


class ExcursionSeverity(str, Enum):
    NOMINAL = "NOMINAL"                   # 0 excursions, full compliance
    STABILITY_OK = "STABILITY_OK"         # Minor excursion (<15m), within stability budget
    QUARANTINE_REQUIRED = "QUARANTINE_REQUIRED"  # Moderate excursion, WHO GDP QA review needed
    CARGO_SPOILED = "CARGO_SPOILED"       # Critical excursion (>2h or temp >15C), cargo compromised


class IoTSensorLog(BaseModel):
    sensor_id: str
    shipment_id: str
    timestamp: datetime
    temperature_c: float
    humidity_pct: float
    battery_pct: float
    door_open: bool = False
    lat: float
    lng: float


class ColdChainAnalysisReport(BaseModel):
    shipment_id: str
    min_temp_threshold_c: float = 2.0
    max_temp_threshold_c: float = 8.0
    min_recorded_c: float
    max_recorded_c: float
    avg_recorded_c: float
    degree_hours_out_of_range: float
    total_excursion_minutes: int
    door_open_events: int
    severity: ExcursionSeverity
    compliance_standard: str = "WHO TRS 961 / FDA 21 CFR GDP Guidelines"
    action_recommended: str
    computed_at: datetime


class DisruptionType(str, Enum):
    HIGHWAY_CLOSURE = "highway_closure"      # NHAI advisories
    WEATHER = "weather"                       # IMD / GDACS
    PORT_STRIKE = "port_strike"
    FUEL_SHORTAGE = "fuel_shortage"


class DisruptionSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Disruption(BaseModel):
    id: str
    type: DisruptionType
    severity: DisruptionSeverity
    title: str
    description: str
    lat: float
    lng: float
    radius_km: float = Field(..., description="Affected radius around lat/lng")
    source: str = Field(..., description="e.g. 'NHAI', 'IMD', 'GDACS' — real feed origin")
    source_url: Optional[str] = None
    reported_at: datetime


class Location(BaseModel):
    name: str
    lat: float
    lng: float


class Shipment(BaseModel):
    id: str
    origin: Location
    destination: Location
    route_waypoints: list[Location] = Field(default_factory=list)
    cargo_description: str
    cargo_value_inr: float
    sensitivity: CargoSensitivity
    carrier_id: str
    eta: datetime
    status: str = "in_transit"


class RiskFactor(BaseModel):
    name: str
    contribution: float = Field(..., description="Points contributed to the 0-100 score")
    explanation: str


class RiskAssessment(BaseModel):
    shipment_id: str
    score: int = Field(..., ge=0, le=100)
    band: str  # LOW / MEDIUM / HIGH / CRITICAL
    factors: list[RiskFactor]
    triggering_disruption_ids: list[str]
    computed_at: datetime


class FleetAsset(BaseModel):
    id: str
    type: str  # e.g. "truck_reefer", "truck_dry", "rail_wagon"
    current_location: Location
    idle_since: Optional[datetime] = None
    capacity_tons: float


class CarrierBid(BaseModel):
    carrier_id: str
    carrier_name: str
    price_inr: float
    eta_hours: float
    reliability_score: float = Field(..., ge=0, le=1)
    rationale: str


class RerouteOption(BaseModel):
    shipment_id: str
    corridor_description: str
    delta_time_hours: float
    delta_cost_inr: float
    projected_risk_after: int
    carrier_bids: list[CarrierBid] = Field(default_factory=list)
    recommended: bool = False
