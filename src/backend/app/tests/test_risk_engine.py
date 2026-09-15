from datetime import datetime, timezone

from app.engines.risk_engine import assess_risk, find_affected_shipments, shipment_intersects_disruption
from app.models.schemas import (
    CargoSensitivity,
    Disruption,
    DisruptionSeverity,
    DisruptionType,
    Location,
    Shipment,
)


def _make_shipment(sensitivity=CargoSensitivity.STANDARD, value=500_000) -> Shipment:
    return Shipment(
        id="TEST-1",
        origin=Location(name="Origin", lat=22.30, lng=73.18),
        destination=Location(name="Destination", lat=23.02, lng=72.57),
        route_waypoints=[],
        cargo_description="Test cargo",
        cargo_value_inr=value,
        sensitivity=sensitivity,
        carrier_id="carrier-test",
        eta=datetime.now(timezone.utc),
    )


def _make_disruption(severity=DisruptionSeverity.HIGH, lat=22.30, lng=73.18, radius=50.0) -> Disruption:
    return Disruption(
        id="D-1",
        type=DisruptionType.HIGHWAY_CLOSURE,
        severity=severity,
        title="Test disruption",
        description="test",
        lat=lat,
        lng=lng,
        radius_km=radius,
        source="TEST",
        reported_at=datetime.now(timezone.utc),
    )


def test_shipment_intersects_disruption_within_radius():
    shipment = _make_shipment()
    disruption = _make_disruption(lat=22.30, lng=73.18, radius=10.0)
    assert shipment_intersects_disruption(shipment, disruption) is True


def test_shipment_does_not_intersect_far_disruption():
    shipment = _make_shipment()
    disruption = _make_disruption(lat=10.0, lng=76.0, radius=5.0)  # far away, small radius
    assert shipment_intersects_disruption(shipment, disruption) is False


def test_risk_score_zero_with_no_disruptions():
    shipment = _make_shipment()
    assessment = assess_risk(shipment, [])
    assert assessment.score == 0
    assert assessment.band == "LOW"


def test_risk_score_increases_with_severity():
    shipment = _make_shipment()
    low = assess_risk(shipment, [_make_disruption(severity=DisruptionSeverity.LOW)])
    critical = assess_risk(shipment, [_make_disruption(severity=DisruptionSeverity.CRITICAL)])
    assert critical.score > low.score


def test_risk_score_increases_with_cold_chain_sensitivity():
    standard = _make_shipment(sensitivity=CargoSensitivity.STANDARD)
    cold_chain = _make_shipment(sensitivity=CargoSensitivity.COLD_CHAIN)
    disruption = _make_disruption()
    standard_score = assess_risk(standard, [disruption]).score
    cold_chain_score = assess_risk(cold_chain, [disruption]).score
    assert cold_chain_score > standard_score


def test_risk_score_never_exceeds_100():
    shipment = _make_shipment(sensitivity=CargoSensitivity.COLD_CHAIN, value=10_000_000)
    disruptions = [
        _make_disruption(severity=DisruptionSeverity.CRITICAL),
        _make_disruption(severity=DisruptionSeverity.CRITICAL, lat=22.31, lng=73.19),
        _make_disruption(severity=DisruptionSeverity.CRITICAL, lat=22.29, lng=73.17),
    ]
    assessment = assess_risk(shipment, disruptions)
    assert assessment.score <= 100


def test_find_affected_shipments_filters_correctly():
    affected_shipment = _make_shipment()
    affected_shipment.id = "AFFECTED"
    far_shipment = _make_shipment()
    far_shipment.id = "FAR"
    far_shipment.origin = Location(name="Far", lat=10.0, lng=76.0)
    far_shipment.destination = Location(name="Far2", lat=10.1, lng=76.1)

    disruption = _make_disruption(lat=22.30, lng=73.18, radius=10.0)
    result = find_affected_shipments([affected_shipment, far_shipment], [disruption])

    assert "AFFECTED" in result
    assert "FAR" not in result
