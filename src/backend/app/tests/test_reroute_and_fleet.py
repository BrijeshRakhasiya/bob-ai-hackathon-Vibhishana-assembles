from datetime import datetime, timedelta, timezone

from app.engines.fleet_engine import compute_fleet_utilisation, find_redeployment_candidates, idle_hours
from app.engines.reroute_engine import simulate_reroutes
from app.engines.risk_engine import assess_risk
from app.models.schemas import CargoSensitivity, DisruptionSeverity, FleetAsset, Location, Shipment
from app.tests.test_risk_engine import _make_disruption, _make_shipment


def test_simulate_reroutes_returns_options_with_one_recommended():
    shipment = _make_shipment()
    assessment = assess_risk(shipment, [_make_disruption(severity=DisruptionSeverity.HIGH)])
    options = simulate_reroutes(shipment, assessment)

    assert len(options) >= 1
    recommended = [o for o in options if o.recommended]
    assert len(recommended) == 1


def test_simulate_reroutes_reduces_projected_risk():
    shipment = _make_shipment()
    assessment = assess_risk(shipment, [_make_disruption(severity=DisruptionSeverity.CRITICAL)])
    options = simulate_reroutes(shipment, assessment)

    for option in options:
        assert option.projected_risk_after < assessment.score


def test_idle_hours_zero_when_not_idle():
    asset = FleetAsset(
        id="A1", type="truck_dry", current_location=Location(name="X", lat=0, lng=0),
        idle_since=None, capacity_tons=10,
    )
    assert idle_hours(asset) == 0.0


def test_idle_hours_positive_when_idle():
    asset = FleetAsset(
        id="A1", type="truck_dry", current_location=Location(name="X", lat=0, lng=0),
        idle_since=datetime.now(timezone.utc) - timedelta(hours=3),
        capacity_tons=10,
    )
    assert 2.9 < idle_hours(asset) < 3.1


def test_find_redeployment_candidates_excludes_far_assets():
    near_asset = FleetAsset(
        id="NEAR", type="truck_dry", current_location=Location(name="Near", lat=22.30, lng=73.18),
        idle_since=datetime.now(timezone.utc) - timedelta(hours=5), capacity_tons=10,
    )
    far_asset = FleetAsset(
        id="FAR", type="truck_dry", current_location=Location(name="Far", lat=10.0, lng=76.0),
        idle_since=datetime.now(timezone.utc) - timedelta(hours=5), capacity_tons=10,
    )
    target = Location(name="Target", lat=22.31, lng=73.19)

    candidates = find_redeployment_candidates([near_asset, far_asset], target, max_distance_km=50)
    ids = [c["asset"].id for c in candidates]
    assert "NEAR" in ids
    assert "FAR" not in ids


def test_find_redeployment_candidates_excludes_active_assets():
    active_asset = FleetAsset(
        id="ACTIVE", type="truck_dry", current_location=Location(name="X", lat=22.30, lng=73.18),
        idle_since=None, capacity_tons=10,
    )
    target = Location(name="Target", lat=22.31, lng=73.19)
    candidates = find_redeployment_candidates([active_asset], target)
    assert candidates == []


def test_compute_fleet_utilisation():
    fleet = [
        FleetAsset(id=f"A{i}", type="truck_dry", current_location=Location(name="X", lat=0, lng=0),
                   idle_since=None, capacity_tons=10)
        for i in range(4)
    ]
    assert compute_fleet_utilisation(fleet, active_assignments=2) == 50.0
    assert compute_fleet_utilisation([], active_assignments=0) == 0.0
