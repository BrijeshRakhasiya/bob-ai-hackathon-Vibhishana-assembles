from datetime import datetime, timedelta, timezone

from app.engines.cold_chain_engine import analyze_cold_chain_telemetry
from app.models.schemas import (
    CargoSensitivity,
    ExcursionSeverity,
    IoTSensorLog,
    Location,
    Shipment,
)

_now = datetime.now(timezone.utc)


def _make_test_shipment() -> Shipment:
    return Shipment(
        id="SHP-TEST-COLD",
        origin=Location(name="Origin", lat=18.94, lng=72.95),
        destination=Location(name="Dest", lat=28.54, lng=77.27),
        route_waypoints=[],
        cargo_description="Vaccines",
        cargo_value_inr=5_000_000,
        sensitivity=CargoSensitivity.COLD_CHAIN,
        carrier_id="carrier-trust",
        eta=_now + timedelta(hours=24),
    )


def test_cold_chain_nominal():
    shipment = _make_test_shipment()
    logs = [
        IoTSensorLog(
            sensor_id="S1",
            shipment_id=shipment.id,
            timestamp=_now - timedelta(hours=2),
            temperature_c=4.0,
            humidity_pct=60.0,
            battery_pct=90.0,
            door_open=False,
            lat=18.94,
            lng=72.95,
        ),
        IoTSensorLog(
            sensor_id="S1",
            shipment_id=shipment.id,
            timestamp=_now,
            temperature_c=5.5,
            humidity_pct=62.0,
            battery_pct=85.0,
            door_open=False,
            lat=19.50,
            lng=73.10,
        ),
    ]

    report = analyze_cold_chain_telemetry(shipment, logs)
    assert report.severity == ExcursionSeverity.NOMINAL
    assert report.total_excursion_minutes == 0
    assert report.min_recorded_c == 4.0
    assert report.max_recorded_c == 5.5


def test_cold_chain_critical_spoiled():
    shipment = _make_test_shipment()
    logs = [
        IoTSensorLog(
            sensor_id="S1",
            shipment_id=shipment.id,
            timestamp=_now - timedelta(hours=4),
            temperature_c=4.0,
            humidity_pct=60.0,
            battery_pct=90.0,
            door_open=False,
            lat=18.94,
            lng=72.95,
        ),
        IoTSensorLog(
            sensor_id="S1",
            shipment_id=shipment.id,
            timestamp=_now - timedelta(hours=1),
            temperature_c=18.5,  # High temperature excursion > 15C
            humidity_pct=80.0,
            battery_pct=40.0,
            door_open=True,
            lat=22.30,
            lng=73.18,
        ),
    ]

    report = analyze_cold_chain_telemetry(shipment, logs)
    assert report.severity == ExcursionSeverity.CARGO_SPOILED
    assert report.max_recorded_c == 18.5
    assert report.degree_hours_out_of_range > 0
