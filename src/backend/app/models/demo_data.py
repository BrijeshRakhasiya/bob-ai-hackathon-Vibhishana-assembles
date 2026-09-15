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
    Shipment(
        id="SHP-1004",
        origin=Location(name="Delhi NCR Depot", lat=28.6139, lng=77.2090),
        destination=Location(name="Jaipur Express Center", lat=26.9124, lng=75.7873),
        route_waypoints=[Location(name="Neemrana", lat=27.9889, lng=76.3969)],
        cargo_description="Consumer electronics (TV panels)",
        cargo_value_inr=8_200_000,
        sensitivity=CargoSensitivity.TIME_CRITICAL,
        carrier_id="carrier-swift",
        eta=_now + timedelta(hours=10),
    ),
    Shipment(
        id="SHP-1005",
        origin=Location(name="Chennai Port", lat=13.0827, lng=80.2707),
        destination=Location(name="Hyderabad Genome Valley", lat=17.3850, lng=78.4867),
        route_waypoints=[Location(name="Ongole", lat=15.5057, lng=80.0499)],
        cargo_description="Pharma cold-chain shipment (insulin)",
        cargo_value_inr=4_800_000,
        sensitivity=CargoSensitivity.COLD_CHAIN,
        carrier_id="carrier-trust",
        eta=_now + timedelta(hours=14),
    ),
    Shipment(
        id="SHP-1006",
        origin=Location(name="Mundra Port", lat=22.8395, lng=69.6962),
        destination=Location(name="Ahmedabad GIDC", lat=23.0225, lng=72.5714),
        route_waypoints=[Location(name="Vadodara", lat=22.3072, lng=73.1812)],
        cargo_description="Specialty chemicals (hazmat, temp-sensitive)",
        cargo_value_inr=2_400_000,
        sensitivity=CargoSensitivity.HIGH_VALUE,
        carrier_id="carrier-value",
        eta=_now + timedelta(hours=12),
    ),
    Shipment(
        id="SHP-1007",
        origin=Location(name="Mumbai JNPT", lat=18.9490, lng=72.9525),
        destination=Location(name="Pune Chakan", lat=18.6735, lng=73.6832),
        route_waypoints=[],
        cargo_description="Auto components (gearboxes)",
        cargo_value_inr=950_000,
        sensitivity=CargoSensitivity.STANDARD,
        carrier_id="carrier-value",
        eta=_now + timedelta(hours=5),
    ),
    Shipment(
        id="SHP-1008",
        origin=Location(name="Kolkata Hub", lat=22.5726, lng=88.3639),
        destination=Location(name="Ranchi Yard", lat=23.3441, lng=85.3094),
        route_waypoints=[Location(name="Durgapur", lat=23.5204, lng=87.3119)],
        cargo_description="Pharmaceutical raw material",
        cargo_value_inr=2_800_000,
        sensitivity=CargoSensitivity.HIGH_VALUE,
        carrier_id="carrier-value",
        eta=_now + timedelta(hours=16),
    ),
    Shipment(
        id="SHP-1009",
        origin=Location(name="Vadodara GIDC", lat=22.3200, lng=73.1500),
        destination=Location(name="Surat Hazira", lat=21.1167, lng=72.6500),
        route_waypoints=[],
        cargo_description="Dairy cold-chain (cultured butter)",
        cargo_value_inr=1_200_000,
        sensitivity=CargoSensitivity.COLD_CHAIN,
        carrier_id="carrier-trust",
        eta=_now + timedelta(hours=7),
    ),
    Shipment(
        id="SHP-1010",
        origin=Location(name="Hyderabad Pharma City", lat=17.3850, lng=78.4867),
        destination=Location(name="Bengaluru Whitefield", lat=12.9698, lng=77.7500),
        route_waypoints=[Location(name="Kurnool", lat=15.8281, lng=78.0373)],
        cargo_description="Industrial machinery spares",
        cargo_value_inr=600_000,
        sensitivity=CargoSensitivity.STANDARD,
        carrier_id="carrier-value",
        eta=_now + timedelta(hours=11),
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
    FleetAsset(
        id="TRK-204",
        type="truck_reefer",
        current_location=Location(name="Bhiwandi Hub", lat=19.28, lng=73.06),
        idle_since=_now - timedelta(hours=8),
        capacity_tons=14,
    ),
    FleetAsset(
        id="TRK-205",
        type="truck_dry",
        current_location=Location(name="Delhi Sanjay Gandhi Yard", lat=28.70, lng=77.15),
        idle_since=_now - timedelta(hours=12),
        capacity_tons=20,
    ),
    FleetAsset(
        id="TRK-206",
        type="truck_reefer",
        current_location=Location(name="Hyderabad Bowenpally", lat=17.45, lng=78.46),
        idle_since=_now - timedelta(hours=4),
        capacity_tons=12,
    ),
    FleetAsset(
        id="TRK-207",
        type="truck_dry",
        current_location=Location(name="Sriperumbudur Park", lat=12.97, lng=79.94),
        idle_since=_now - timedelta(hours=6),
        capacity_tons=16,
    ),
    FleetAsset(
        id="TRK-208",
        type="truck_dry",
        current_location=Location(name="Jaipur Transport Nagar", lat=26.91, lng=75.80),
        idle_since=None,
        capacity_tons=18,
    ),
    FleetAsset(
        id="TRK-209",
        type="rail_wagon",
        current_location=Location(name="Vadodara Junction", lat=22.30, lng=73.18),
        idle_since=_now - timedelta(hours=20),
        capacity_tons=40,
    ),
    FleetAsset(
        id="TRK-210",
        type="truck_reefer",
        current_location=Location(name="Kadodara Depot", lat=21.15, lng=72.96),
        idle_since=_now - timedelta(hours=3),
        capacity_tons=10,
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
    ],
    # SHP-1005 (insulin, Chennai -> Hyderabad): compliant run, one door event, no breach
    "SHP-1005": [
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now - timedelta(hours=5),
            temperature_c=3.2,
            humidity_pct=58.0,
            battery_pct=97.0,
            door_open=False,
            lat=13.0827,
            lng=80.2707,
        ),
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now - timedelta(hours=4),
            temperature_c=3.8,
            humidity_pct=59.5,
            battery_pct=94.0,
            door_open=False,
            lat=14.2000,
            lng=79.9000,
        ),
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now - timedelta(hours=3),
            temperature_c=4.4,
            humidity_pct=61.0,
            battery_pct=91.0,
            door_open=True,  # Scheduled checkpoint scan at Ongole
            lat=15.5057,
            lng=80.0499,
        ),
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now - timedelta(hours=2),
            temperature_c=5.1,
            humidity_pct=62.0,
            battery_pct=88.0,
            door_open=False,
            lat=16.2000,
            lng=79.2000,
        ),
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now - timedelta(hours=1),
            temperature_c=5.8,
            humidity_pct=63.0,
            battery_pct=85.0,
            door_open=False,
            lat=16.9000,
            lng=78.8000,
        ),
        IoTSensorLog(
            sensor_id="IOT-INSULIN-07",
            shipment_id="SHP-1005",
            timestamp=_now,
            temperature_c=4.9,
            humidity_pct=60.0,
            battery_pct=82.0,
            door_open=False,
            lat=17.3850,
            lng=78.4867,
        ),
    ],
}


def get_shipment(shipment_id: str) -> Shipment | None:
    return next((s for s in SHIPMENTS if s.id == shipment_id), None)


def get_cold_chain_logs(shipment_id: str) -> list[IoTSensorLog]:
    return COLD_CHAIN_LOGS.get(shipment_id, [])

