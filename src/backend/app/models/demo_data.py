"""
In-memory demo data store.

For the hackathon demo this stands in for a real database. Seeded with a
handful of realistic Indian domestic freight shipments and a small fleet.
Swap for a real DB (see docs/setup-guide.md) for anything beyond the demo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.schemas import CargoSensitivity, FleetAsset, IoTSensorLog, Location, Shipment

_now = datetime.now(timezone.utc)

SHIPMENTS: list[Shipment] = [
    Shipment(
        id="SHP-1001",
        origin=Location(name="Mumbai JNPT", lat=18.9490, lng=72.9525),
        destination=Location(name="Delhi Okhla", lat=28.5494, lng=77.2724),
        route_waypoints=[Location(name="Vadodara", lat=22.3072, lng=73.1812)],
        cargo_description="Pharma cold-chain shipment (vaccines)",
        cargo_value_inr=6_500_000,
        sensitivity=CargoSensitivity.COLD_CHAIN,
        carrier_id="carrier-trust",
        eta=_now + timedelta(hours=30),
    ),
    Shipment(
        id="SHP-1002",
        origin=Location(name="Ahmedabad GIDC", lat=23.0225, lng=72.5714),
        destination=Location(name="Surat Hazira", lat=21.1167, lng=72.6500),
        route_waypoints=[],
        cargo_description="Textile machinery parts",
        cargo_value_inr=1_800_000,
        sensitivity=CargoSensitivity.HIGH_VALUE,
        carrier_id="carrier-value",
        eta=_now + timedelta(hours=6),
    ),
    Shipment(
        id="SHP-1003",
        origin=Location(name="Chennai Port", lat=13.0827, lng=80.2707),
        destination=Location(name="Bengaluru Whitefield", lat=12.9698, lng=77.7500),
        route_waypoints=[],
        cargo_description="Electronics components for JIT assembly line",
        cargo_value_inr=3_200_000,
        sensitivity=CargoSensitivity.TIME_CRITICAL,
        carrier_id="carrier-swift",
        eta=_now + timedelta(hours=8),
    ),
]

FLEET: list[FleetAsset] = [
    FleetAsset(
        id="TRK-201",
        type="truck_reefer",
        current_location=Location(name="Vadodara Yard", lat=22.30, lng=73.19),
        idle_since=_now - timedelta(hours=5),
        capacity_tons=12,
    ),
    FleetAsset(
        id="TRK-202",
        type="truck_dry",
        current_location=Location(name="Ahmedabad Yard", lat=23.02, lng=72.57),
        idle_since=_now - timedelta(hours=1),
        capacity_tons=18,
    ),
    FleetAsset(
        id="TRK-203",
        type="truck_dry",
        current_location=Location(name="Surat Depot", lat=21.17, lng=72.83),
        idle_since=None,
        capacity_tons=15,
    ),
]

# Seeded 24-hour IoT Telemetry Logs for SHP-1001 (Vaccine Cold Chain)
COLD_CHAIN_LOGS: dict[str, list[IoTSensorLog]] = {
    "SHP-1001": [
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=6),
            temperature_c=4.1,
            humidity_pct=62.0,
            battery_pct=98.0,
            door_open=False,
            lat=18.9490,
            lng=72.9525,
        ),
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=5),
            temperature_c=4.3,
            humidity_pct=63.5,
            battery_pct=95.0,
            door_open=False,
            lat=19.8000,
            lng=73.0000,
        ),
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=4),
            temperature_c=4.5,
            humidity_pct=61.0,
            battery_pct=92.0,
            door_open=False,
            lat=20.5000,
            lng=73.0500,
        ),
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=3),
            temperature_c=5.2,
            humidity_pct=65.0,
            battery_pct=88.0,
            door_open=False,
            lat=21.2000,
            lng=73.1000,
        ),
        # Delay / Highway Closure near Vadodara causes reefer ambient heat buildup
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=2),
            temperature_c=8.8,  # Temperature breach > 8°C
            humidity_pct=75.0,
            battery_pct=82.0,
            door_open=True,  # Brief door inspection
            lat=22.3072,
            lng=73.1812,
        ),
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now - timedelta(hours=1),
            temperature_c=10.4, # Peak excursion spike
            humidity_pct=78.0,
            battery_pct=76.0,
            door_open=False,
            lat=22.3072,
            lng=73.1812,
        ),
        IoTSensorLog(
            sensor_id="IOT-VACCINE-99",
            shipment_id="SHP-1001",
            timestamp=_now,
            temperature_c=7.6,  # Recovering after auxiliary power reset
            humidity_pct=68.0,
            battery_pct=72.0,
            door_open=False,
            lat=22.3072,
            lng=73.1812,
        ),
    ]
}


def get_shipment(shipment_id: str) -> Shipment | None:
    return next((s for s in SHIPMENTS if s.id == shipment_id), None)


def get_cold_chain_logs(shipment_id: str) -> list[IoTSensorLog]:
    return COLD_CHAIN_LOGS.get(shipment_id, [])

