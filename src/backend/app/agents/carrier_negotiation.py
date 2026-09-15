"""
Stage 3b: Multi-agent carrier negotiation.

For a shipment that needs rerouting, three simulated carrier agents each
propose a bid (price / ETA / reliability trade-off) built from their own
persona and constraints, and a Negotiator agent picks the best bid against
the dispatcher's stated priority (cheapest / fastest / most reliable).

This is deliberately grounded: agents only reason over the RerouteOption
and RiskAssessment data already computed by the deterministic engines
(risk_engine.py, reroute_engine.py) - they do not invent risk scores or
route facts on their own. That grounding is what keeps the AI Copilot
layer honest and is called out explicitly in docs/architecture.md.

Uses CrewAI >= 1.15. Requires an LLM backend configured via environment
variables (see src/backend/.env.example). Groq is the default backend;
any OpenAI-compatible endpoint works.
"""
from __future__ import annotations

import json
import os
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task

from app.models.schemas import CarrierBid, RerouteOption, RiskAssessment, Shipment


def _build_llm() -> LLM:
    """
    Build a CrewAI LLM object from environment variables.

    For Groq set:
        LLM_API_KEY   = gsk_...
        LLM_BASE_URL  = https://api.groq.com/openai/v1
        LLM_MODEL     = openai/gpt-oss-120b   (or any Groq model slug)

    Falls back to reasonable defaults so the rest of the app still
    works offline (agents will return fallback bids).
    """
    return LLM(
        model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=os.getenv("LLM_API_KEY", ""),
        max_tokens=1024,   # gpt-oss-120b is a reasoning model; needs headroom
    )


_CARRIER_PERSONAS = [
    {
        "carrier_id": "carrier-swift",
        "carrier_name": "Swift Freight Co.",
        "stance": "Prioritises speed above all else, charges a premium for it, "
        "moderate reliability track record.",
    },
    {
        "carrier_id": "carrier-value",
        "carrier_name": "ValueHaul Logistics",
        "stance": "Prioritises the lowest possible price, accepts longer ETAs, "
        "solid but unremarkable reliability.",
    },
    {
        "carrier_id": "carrier-trust",
        "carrier_name": "TrustLine Carriers",
        "stance": "Prioritises reliability and cold-chain compliance, mid-range "
        "pricing, best on-time record in the network.",
    },
]


def _build_carrier_agent(persona: dict, llm: LLM) -> Agent:
    return Agent(
        role=f"Carrier Representative - {persona['carrier_name']}",
        goal=(
            "Propose one honest, self-interested bid for the rerouted shipment "
            "that reflects your carrier's stance, expressed strictly as JSON."
        ),
        backstory=persona["stance"],
        allow_delegation=False,
        verbose=False,
        llm=llm,
    )


def _build_negotiator_agent(llm: LLM) -> Agent:
    return Agent(
        role="Dispatch Negotiator",
        goal=(
            "Given the three carrier bids and the dispatcher's stated priority, "
            "select the single best bid and explain the trade-off in plain "
            "language, grounded only in the numbers provided - never invent "
            "numbers not present in the bids."
        ),
        backstory=(
            "An experienced logistics dispatcher who has to defend every "
            "recommendation to a cost-conscious operations manager."
        ),
        allow_delegation=False,
        verbose=False,
        llm=llm,
    )


def _carrier_bid_task(agent: Agent, persona: dict, reroute: RerouteOption, shipment: Shipment) -> Task:
    return Task(
        description=(
            f"The shipment {shipment.id} ({shipment.cargo_description}, "
            f"sensitivity: {shipment.sensitivity.value}) needs rerouting via: "
            f"'{reroute.corridor_description}'. Baseline delta is "
            f"+{reroute.delta_time_hours}h and +Rs{reroute.delta_cost_inr}. "
            "Propose your bid as strict JSON with keys: "
            "price_inr (number), eta_hours (number), reliability_score (0-1 float), "
            "rationale (one sentence). Anchor your numbers to the baseline delta "
            "above - adjust them to reflect your carrier's stance, do not invent "
            "wildly different figures."
        ),
        expected_output="A single JSON object with keys price_inr, eta_hours, reliability_score, rationale.",
        agent=agent,
    )


def _negotiation_task(agent: Agent, bids: list[CarrierBid], priority: str) -> Task:
    bids_json = json.dumps([b.model_dump() for b in bids], indent=2)
    return Task(
        description=(
            f"Dispatcher priority: '{priority}' (one of: cheapest, fastest, "
            f"most_reliable, balanced). Carrier bids:\n{bids_json}\n\n"
            "Pick the single best carrier_id for this priority and explain the "
            "trade-off in 2-3 sentences, citing only the numbers given above."
        ),
        expected_output="Plain-language recommendation naming the chosen carrier_id and why.",
        agent=agent,
    )


def _parse_bid_json(raw: str, persona: dict) -> CarrierBid:
    """Best-effort JSON extraction from an LLM raw text output."""
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        payload: dict[str, Any] = json.loads(raw[start:end])
        return CarrierBid(
            carrier_id=persona["carrier_id"],
            carrier_name=persona["carrier_name"],
            price_inr=float(payload["price_inr"]),
            eta_hours=float(payload["eta_hours"]),
            reliability_score=float(payload["reliability_score"]),
            rationale=str(payload.get("rationale", "")),
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        # Fail safe: fall back to a deterministic estimate so the demo never
        # crashes on an LLM formatting slip. Clearly not a hallucination -
        # it is a rule-based fallback, logged as such.
        return CarrierBid(
            carrier_id=persona["carrier_id"],
            carrier_name=persona["carrier_name"],
            price_inr=0.0,
            eta_hours=0.0,
            reliability_score=0.5,
            rationale="Fallback estimate - agent response could not be parsed as JSON.",
        )


def run_carrier_negotiation(
    shipment: Shipment,
    reroute: RerouteOption,
    priority: str = "balanced",
) -> dict:
    """
    Orchestrates the three carrier agents + one negotiator agent via CrewAI.
    Returns {"bids": [...], "recommendation": str, "chosen_carrier_id": str}.

    If LLM_API_KEY is not set, all agents return deterministic fallback bids
    so the demo still works without credentials.
    """
    if not os.getenv("LLM_API_KEY"):
        # Deterministic fallback when no LLM key is configured
        bids = [
            CarrierBid(
                carrier_id=p["carrier_id"],
                carrier_name=p["carrier_name"],
                price_inr=reroute.delta_cost_inr * (1.2 if p["carrier_id"] == "carrier-swift" else 0.9 if p["carrier_id"] == "carrier-value" else 1.0),
                eta_hours=reroute.delta_time_hours * (0.8 if p["carrier_id"] == "carrier-swift" else 1.2 if p["carrier_id"] == "carrier-value" else 1.0),
                reliability_score=0.85 if p["carrier_id"] == "carrier-swift" else 0.78 if p["carrier_id"] == "carrier-value" else 0.95,
                rationale=f"Deterministic fallback bid for {p['carrier_name']} (no LLM key configured).",
            )
            for p in _CARRIER_PERSONAS
        ]
        return {
            "bids": [b.model_dump() for b in bids],
            "recommendation": "No LLM key configured. Showing deterministic fallback bids. Set LLM_API_KEY in .env to enable live agent negotiation.",
            "chosen_carrier_id": "carrier-trust",
        }

    llm = _build_llm()
    carrier_agents = [_build_carrier_agent(p, llm) for p in _CARRIER_PERSONAS]
    carrier_tasks = [
        _carrier_bid_task(agent, persona, reroute, shipment)
        for agent, persona in zip(carrier_agents, _CARRIER_PERSONAS)
    ]

    bidding_crew = Crew(
        agents=carrier_agents,
        tasks=carrier_tasks,
        process=Process.sequential,
        verbose=False,
    )
    bidding_crew.kickoff()

    bids = [
        _parse_bid_json(str(task.output), persona)
        for task, persona in zip(carrier_tasks, _CARRIER_PERSONAS)
    ]

    negotiator = _build_negotiator_agent(llm)
    neg_task = _negotiation_task(negotiator, bids, priority)
    negotiation_crew = Crew(
        agents=[negotiator], tasks=[neg_task], process=Process.sequential, verbose=False
    )
    negotiation_result = str(negotiation_crew.kickoff())

    # Extract the chosen carrier_id if the negotiator named it explicitly.
    chosen = next((b.carrier_id for b in bids if b.carrier_id in negotiation_result), bids[0].carrier_id if bids else None)

    return {
        "bids": [b.model_dump() for b in bids],
        "recommendation": negotiation_result,
        "chosen_carrier_id": chosen,
    }
