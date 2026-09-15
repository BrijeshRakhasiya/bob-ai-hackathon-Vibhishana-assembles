"""
Cold Chain IoT Telemetry Monitoring & Regulatory Severity Classification Engine.

Implements deterministic evaluation of cold-chain sensor logs against WHO TRS 961
and FDA 21 CFR Good Distribution Practice (GDP) standards for vaccines & biologics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.models.schemas import (
    ColdChainAnalysisReport,
    ExcursionSeverity,
    IoTSensorLog,
    Shipment,
)


def analyze_cold_chain_telemetry(
    shipment: Shipment,
    logs: Sequence[IoTSensorLog],
    min_threshold_c: float = 2.0,
    max_threshold_c: float = 8.0,
) -> ColdChainAnalysisReport:
    """
    Evaluates IoT telemetry logs for a cold-chain shipment.

    Calculates:
    - Min, max, and average temperature
    - Degree-hours out-of-range
    - Total excursion duration in minutes
    - Door open count
    - Regulatory severity classification (WHO TRS 961 / FDA GDP)
    """
    now = datetime.now(timezone.utc)
    if not logs:
        return ColdChainAnalysisReport(
            shipment_id=shipment.id,
            min_temp_threshold_c=min_threshold_c,
            max_temp_threshold_c=max_threshold_c,
            min_recorded_c=0.0,
            max_recorded_c=0.0,
            avg_recorded_c=0.0,
            degree_hours_out_of_range=0.0,
            total_excursion_minutes=0,
            door_open_events=0,
            severity=ExcursionSeverity.NOMINAL,
            action_recommended="No IoT sensor logs available yet. Monitor active telemetry.",
            computed_at=now,
        )

    temps = [l.temperature_c for l in logs]
    min_temp = min(temps)
    max_temp = max(temps)
    avg_temp = sum(temps) / len(temps)

    door_open_events = sum(1 for l in logs if l.door_open)

    # Sort logs by timestamp to calculate duration accurately
    sorted_logs = sorted(logs, key=lambda l: l.timestamp)

    degree_hours = 0.0
    excursion_minutes = 0

    for i in range(len(sorted_logs)):
        current = sorted_logs[i]
        # Calculate time delta to next log or assume 15-min interval if single point
        if i < len(sorted_logs) - 1:
            next_log = sorted_logs[i + 1]
            delta_hours = max(0.0, (next_log.timestamp - current.timestamp).total_seconds() / 3600.0)
        else:
            delta_hours = 0.25  # 15 minutes default interval

        temp = current.temperature_c
        if temp > max_threshold_c:
            excess = temp - max_threshold_c
            degree_hours += excess * delta_hours
            excursion_minutes += int(delta_hours * 60)
        elif temp < min_threshold_c:
            excess = min_threshold_c - temp
            degree_hours += excess * delta_hours
            excursion_minutes += int(delta_hours * 60)

    # Determine WHO / FDA GDP Regulatory Severity
    if excursion_minutes == 0:
        severity = ExcursionSeverity.NOMINAL
        action = "Full compliance maintained. Cargo temperature within optimal 2°C - 8°C window."
    elif excursion_minutes <= 15 and max_temp <= 10.0 and min_temp >= 1.0:
        severity = ExcursionSeverity.STABILITY_OK
        action = "Minor transient excursion within manufacturer stability budget (<15 mins). Standard delivery permitted."
    elif excursion_minutes <= 120 and max_temp <= 15.0 and min_temp >= 0.0:
        severity = ExcursionSeverity.QUARANTINE_REQUIRED
        action = "Moderate excursion detected. Automatic quarantine flag added. QA stability review & data log download required at receiving dock."
    else:
        severity = ExcursionSeverity.CARGO_SPOILED
        action = "CRITICAL THERMAL BREACH! Cargo integrity compromised (excursion > 2 hours or temp > 15°C). Reject delivery & initiate replacement dispatch."

    return ColdChainAnalysisReport(
        shipment_id=shipment.id,
        min_temp_threshold_c=min_threshold_c,
        max_temp_threshold_c=max_threshold_c,
        min_recorded_c=round(min_temp, 2),
        max_recorded_c=round(max_temp, 2),
        avg_recorded_c=round(avg_temp, 2),
        degree_hours_out_of_range=round(degree_hours, 3),
        total_excursion_minutes=excursion_minutes,
        door_open_events=door_open_events,
        severity=severity,
        action_recommended=action,
        computed_at=now,
    )
