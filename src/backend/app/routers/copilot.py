"""
Copilot layer — takes the outputs of the deterministic engines (risk,
reroute, fleet) and turns them into a plain-language brief for a dispatcher.

Grounding rule: the prompt sent to the LLM contains ONLY the already-computed
facts (risk score + factors, reroute deltas, fleet candidates). The system
prompt explicitly forbids inventing numbers not present in that payload.
This is the single most important design decision in the whole project —
call it out in docs/architecture.md and in the presentation, since judges
score "IBM Bob Integration" on whether Bob/watsonx is load-bearing and
trustworthy, not just chatty.
"""
from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.engines.disruption_feed import fetch_all_disruptions
from app.engines.fleet_engine import find_redeployment_candidates
from app.engines.reroute_engine import simulate_reroutes
from app.engines.risk_engine import assess_risk, find_affected_shipments
from app.models import demo_data

router = APIRouter()

_SYSTEM_PROMPT = """You are the RouteGuard AI dispatch copilot.
You will be given a JSON payload of already-computed facts: a shipment's
risk assessment, its reroute options, and fleet redeployment candidates.

Rules:
1. Explain the situation in plain, dispatcher-friendly language.
2. Cite ONLY numbers present in the payload. Never invent a price, ETA,
   distance, or risk score that is not in the JSON you were given.
3. If the payload is missing a piece of information, say so explicitly
   rather than filling it in.
4. End with one clear recommended action.
5. Format your answer in clean Markdown: short headings, bullet lists,
   and **bold** for key numbers (risk score, price, ETA, distance).
"""


class BriefRequest(BaseModel):
    shipment_id: str
    query: str | None = None


def _call_llm(system_prompt: str, user_payload: dict) -> str:
    """
    Thin LLM call wrapper using Groq's OpenAI-compatible endpoint.

    Configure in .env:
        LLM_BASE_URL = https://api.groq.com/openai/v1
        LLM_API_KEY  = gsk_...
        LLM_MODEL    = openai/gpt-oss-120b

    Returns a stub string if the key is not set, so deterministic
    endpoints (/api/risk/*, /api/fleet/*) still work without credentials.
    """
    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key:
        return (
            "[No LLM_API_KEY configured - this is a stub response. "
            "Set LLM_API_KEY in src/backend/.env to enable the copilot. "
            f"Computed facts were: {json.dumps(user_payload)[:500]}]"
        )

    try:
        from openai import OpenAI
    except ImportError:
        return (
            "[openai package not installed - run: uv pip install openai. "
            f"Computed facts were: {json.dumps(user_payload)[:500]}]"
        )

    client = OpenAI(
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        temperature=0.2,
        max_tokens=1024,   # gpt-oss-120b is a reasoning model; needs headroom
    )
    return response.choices[0].message.content or ""


async def _grounding_payload(shipment) -> dict:
    """Build the deterministic facts payload the LLM is grounded on."""
    disruptions = await fetch_all_disruptions()
    affected = find_affected_shipments([shipment], disruptions)
    hits = affected.get(shipment.id, [])
    assessment = assess_risk(shipment, hits)
    reroutes = simulate_reroutes(shipment, assessment)
    fleet_candidates = find_redeployment_candidates(demo_data.FLEET, shipment.destination)

    return {
        "shipment": shipment.model_dump(mode="json"),
        "risk_assessment": assessment.model_dump(mode="json"),
        "reroute_options": [r.model_dump(mode="json") for r in reroutes],
        "fleet_redeployment_candidates": [
            {
                "asset_id": c["asset"].id,
                "distance_km": c["distance_km"],
                "idle_hours": c["idle_hours"],
            }
            for c in fleet_candidates
        ],
    }


def _sse_token_stream(system_prompt: str, user_payload: dict):
    """Yield SSE `data:` chunks of the brief as the LLM streams tokens."""
    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key:
        stub = (
            "[No LLM_API_KEY configured - this is a stub response. "
            "Set LLM_API_KEY in src/backend/.env to enable the copilot. "
            f"Computed facts were: {json.dumps(user_payload)[:500]}]"
        )
        yield f"data: {json.dumps({'token': stub})}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        from openai import OpenAI
    except ImportError:
        yield f"data: {json.dumps({'error': 'openai package not installed - run: uv pip install openai'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=api_key,
        )
        stream = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=0.2,
            max_tokens=1024,   # gpt-oss-120b is a reasoning model; needs headroom
            stream=True,
        )
        for chunk in stream:
            delta = None
            if chunk.choices:
                delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'token': delta})}\n\n"
    except Exception as exc:  # network / auth / quota — surface to UI, don't hang
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/brief")
async def generate_brief(req: BriefRequest):
    """Grounded natural-language dispatcher brief for one shipment (non-streaming)."""
    shipment = demo_data.get_shipment(req.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    payload = await _grounding_payload(shipment)
    brief_text = _call_llm(_SYSTEM_PROMPT, payload)
    return {"shipment_id": req.shipment_id, "brief": brief_text, "grounding_facts": payload}


@router.get("/brief/stream")
async def stream_brief(
    shipment_id: str = Query(...),
    query: str | None = Query(default=None),
):
    """SSE stream of the grounded brief. Events: `{"token": "..."}` then `[DONE]`."""
    shipment = demo_data.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    payload = await _grounding_payload(shipment)
    if query:
        payload = {**payload, "dispatcher_question": query}
    return StreamingResponse(
        _sse_token_stream(_SYSTEM_PROMPT, payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
