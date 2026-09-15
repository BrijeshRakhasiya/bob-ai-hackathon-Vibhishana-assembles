"""
Stage 3: Reroute simulation.

Given an at-risk shipment, generate a small set of plausible alternative
corridors with an explicit time/cost delta and a projected post-reroute
risk score. This stays deterministic/rule-based (no LLM) so every number
shown to the dispatcher is reproducible.
"""
from __future__ import annotations

from app.models.schemas import Disruption, RerouteOption, RiskAssessment, Shipment

# A tiny static corridor knowledge base for the demo — in a production system
# this would come from a routing/mapping API. Kept explicit and inspectable.
_ALT_CORRIDORS = [
    {
        "label": "Bypass via NH48 alternate carriageway",
        "delta_time_hours": 3.5,
        "delta_cost_inr": 2200,
        "risk_reduction_pct": 0.55,
    },
    {
        "label": "Rail transshipment for the blocked leg",
        "delta_time_hours": 9.0,
        "delta_cost_inr": 6800,
        "risk_reduction_pct": 0.80,
    },
    {
        "label": "Regional detour via secondary state highway",
        "delta_time_hours": 5.0,
        "delta_cost_inr": 3100,
        "risk_reduction_pct": 0.65,
    },
]


def simulate_reroutes(
    shipment: Shipment, assessment: RiskAssessment
) -> list[RerouteOption]:
    """Generate a small set of alternative corridors for an at-risk shipment."""
    options: list[RerouteOption] = []
    for corridor in _ALT_CORRIDORS:
        projected = max(0, int(assessment.score * (1 - corridor["risk_reduction_pct"])))
        options.append(
            RerouteOption(
                shipment_id=shipment.id,
                corridor_description=corridor["label"],
                delta_time_hours=corridor["delta_time_hours"],
                delta_cost_inr=corridor["delta_cost_inr"],
                projected_risk_after=projected,
            )
        )

    # Rank: prefer the option with the best risk reduction per hour of delay.
    options.sort(
        key=lambda o: (assessment.score - o.projected_risk_after) / max(o.delta_time_hours, 0.1),
        reverse=True,
    )
    if options:
        options[0].recommended = True
    return options
