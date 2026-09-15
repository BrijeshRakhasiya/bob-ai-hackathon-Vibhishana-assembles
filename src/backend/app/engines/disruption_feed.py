"""
Live disruption feed connectors.

This is the piece that differentiates RouteGuard AI from a purely simulated
demo: real public sources feed the engine, not hand-typed fixtures.

- IMD/GDACS: GDACS (Global Disaster Alert and Coordination System) publishes
  a public, no-auth RSS/JSON feed of active disasters (floods, cyclones,
  earthquakes) with lat/lng and severity — genuinely live, genuinely free.
  https://www.gdacs.org/xml/rss.xml
- NHAI: NHAI does not expose a public real-time API. We treat highway
  closures as a *seeded* feed for the demo (clearly labelled as such) unless
  your team wires up a scraper for a specific state's traffic police
  advisory page. Be upfront about this in docs/architecture.md — judges
  respect honesty about what's real vs. seeded far more than an unlabelled
  fake feed.

Both connectors return the same Disruption shape so the rest of the engine
never needs to know where a disruption came from.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx

from app.models.schemas import Disruption, DisruptionSeverity, DisruptionType

GDACS_FEED_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"


async def fetch_gdacs_disruptions(country: str = "India") -> list[Disruption]:
    """
    Pull currently active disasters from GDACS's public JSON API and map
    them into our Disruption shape. Falls back to an empty list (not fake
    data) if the feed is unreachable — the caller should handle that
    gracefully, e.g. by showing "live feed unavailable" in the UI rather
    than silently substituting fixtures.
    """
    severity_map = {
        "Green": DisruptionSeverity.LOW,
        "Orange": DisruptionSeverity.MODERATE,
        "Red": DisruptionSeverity.HIGH,
    }
    disruptions: list[Disruption] = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GDACS_FEED_URL, params={"country": country})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return disruptions

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [None, None])
        if coords[0] is None:
            continue

        alert_level = props.get("alertlevel", "Green")
        disruptions.append(
            Disruption(
                id=f"gdacs-{props.get('eventid', uuid.uuid4().hex[:8])}",
                type=DisruptionType.WEATHER,
                severity=severity_map.get(alert_level, DisruptionSeverity.LOW),
                title=props.get("eventname") or props.get("eventtype", "Weather event"),
                description=props.get("htmldescription", "")[:300],
                lat=coords[1],
                lng=coords[0],
                radius_km=100.0,  # GDACS doesn't give a precise radius; conservative default
                source="GDACS",
                source_url=props.get("url", {}).get("report") if isinstance(props.get("url"), dict) else None,
                reported_at=datetime.now(timezone.utc),
            )
        )
    return disruptions


def seeded_nhai_disruptions() -> list[Disruption]:
    """
    Seeded, clearly-labelled highway closure advisories standing in for a
    live NHAI feed (NHAI has no public real-time API as of this writing).
    Document this honestly in docs/architecture.md — do not present this
    function's output as "live" in the UI or the presentation.
    """
    now = datetime.now(timezone.utc)
    return [
        Disruption(
            id="nhai-seed-001",
            type=DisruptionType.HIGHWAY_CLOSURE,
            severity=DisruptionSeverity.HIGH,
            title="NH48 partial closure near Vadodara — waterlogging",
            description="Seeded advisory standing in for NHAI's non-public real-time feed.",
            lat=22.3072,
            lng=73.1812,
            radius_km=40.0,
            source="NHAI (seeded)",
            source_url=None,
            reported_at=now,
        ),
        Disruption(
            id="port-seed-002",
            type=DisruptionType.PORT_STRIKE,
            severity=DisruptionSeverity.MODERATE,
            title="JNPT container gate congestion — berth delays",
            description="Seeded advisory standing in for the port authority's non-public feed.",
            lat=18.9490,
            lng=72.9525,
            radius_km=30.0,
            source="Port Authority (seeded)",
            source_url=None,
            reported_at=now,
        ),
        Disruption(
            id="nhai-seed-003",
            type=DisruptionType.HIGHWAY_CLOSURE,
            severity=DisruptionSeverity.MODERATE,
            title="NH44 lane maintenance near Hyderabad — speed restrictions",
            description="Seeded advisory standing in for NHAI's non-public real-time feed.",
            lat=17.3850,
            lng=78.4867,
            radius_km=35.0,
            source="NHAI (seeded)",
            source_url=None,
            reported_at=now,
        ),
    ]


async def fetch_all_disruptions() -> list[Disruption]:
    """Combine live GDACS weather data with seeded highway advisories."""
    live = await fetch_gdacs_disruptions()
    seeded = seeded_nhai_disruptions()
    return live + seeded
