"""
Stage 4: Fleet utilisation & redeployment matching.

Finds idle fleet assets near a disruption zone and matches them to shipments
that need surge capacity (e.g. a rerouted shipment needing a different
vehicle type, or a lane facing sudden demand).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.engines.risk_engine import _distance_km
from app.models.schemas import FleetAsset, Location


def idle_hours(asset: FleetAsset, now: datetime | None = None) -> float:
    if asset.idle_since is None:
        return 0.0
    now = now or datetime.now(timezone.utc)
    return (now - asset.idle_since).total_seconds() / 3600.0


def find_redeployment_candidates(
    fleet: list[FleetAsset],
    target_location: Location,
    min_idle_hours: float = 2.0,
    max_distance_km: float = 250.0,
) -> list[dict]:
    """
    Returns idle assets within range of a target location that need surge
    capacity, ranked by (closer + longer idle = better candidate).
    """
    candidates = []
    for asset in fleet:
        idle_h = idle_hours(asset)
        if idle_h < min_idle_hours:
            continue
        dist = _distance_km(
            asset.current_location.lat,
            asset.current_location.lng,
            target_location.lat,
            target_location.lng,
        )
        if dist > max_distance_km:
            continue
        candidates.append(
            {
                "asset": asset,
                "distance_km": round(dist, 1),
                "idle_hours": round(idle_h, 1),
                "redeployment_score": round(idle_h / max(dist, 1.0), 3),
            }
        )
    candidates.sort(key=lambda c: c["redeployment_score"], reverse=True)
    return candidates


def compute_fleet_utilisation(fleet: list[FleetAsset], active_assignments: int) -> float:
    """Utilisation % = active assets / total fleet."""
    if not fleet:
        return 0.0
    return round(100 * active_assignments / len(fleet), 1)
