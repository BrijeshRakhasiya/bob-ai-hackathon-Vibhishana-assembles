# Solution Overview

## Core mechanism

RouteGuard AI is built as a **five-stage pipeline**, deliberately separating deterministic, auditable logic from the AI/LLM layer:

```
Live disruption feed + shipment/fleet data
            │
            ▼
1. Impact correlation   — which shipments intersect which disruptions (geometry, not ML)
            │
            ▼
2. Risk scoring          — deterministic 0-100 score, every point traces to a named factor
            │
            ▼
3. Reroute simulation     4. Fleet matching
            │                       │
            └───────────┬───────────┘
                         ▼
        3b. Multi-agent carrier negotiation (CrewAI)
                         │
                         ▼
        5. AI copilot — explains the above, grounded strictly
           in the facts already computed (never invents numbers)
```

## What makes it different from a naive alternative

A naive "AI-powered logistics assistant" would hand raw shipment and disruption data to an LLM and ask it to "figure out the risk and recommend a route." We deliberately avoided that pattern for three reasons:

1. **Auditability.** A dispatcher (or an FDA-style auditor, or a judge) needs to be able to ask "why is this shipment rated 75/100?" and get a factor-by-factor answer, not "the AI said so." Our risk engine returns a list of named `RiskFactor` objects with exact point contributions.
2. **Reliability.** LLMs are excellent at synthesis and language, unreliable at consistent arithmetic across many examples. We use deterministic Python for the scoring and routing math, and only use the LLM for what LLMs are actually good at: negotiation reasoning and natural-language explanation.
3. **Trust.** The copilot layer's system prompt explicitly forbids inventing any number that isn't already present in the JSON payload it's given. This is the single design decision we'd point to first if asked "how do you know Bob isn't hallucinating your risk scores?"

## Key design decisions

- **Live data over simulated data where a real feed exists.** GDACS (weather/disaster alerts) is public and free — we use it directly rather than faking weather data. NHAI highway closures have no public real-time API, so we use clearly-labelled seeded data instead of pretending it's live. This honesty is itself a design decision worth stating explicitly, since overclaiming live data is a known way submissions lose credibility with judges.
- **Multi-agent negotiation, not a single chatbot.** Three CrewAI carrier agents with distinct personas (speed-focused, cost-focused, reliability-focused) each independently propose a bid; a fourth negotiator agent selects the best one against the dispatcher's stated priority. This demonstrates genuinely load-bearing agentic AI use, not a single wrapped LLM call.
- **Domestic road freight scope, not global ocean shipping.** We scoped to Indian domestic freight specifically — different disruption types (highway closures, monsoon flooding) and different data sources (GDACS, NHAI-style advisories) than a generic global port/vessel version of this problem.

## What the user experience looks like

A dispatcher opens the RouteGuard dashboard and sees:

1. A ranked list of active shipments by risk score (highest first), each with a plain-language reason.
2. For any at-risk shipment, a click reveals the reroute options with cost/time deltas.
3. A "Negotiate" button triggers the carrier agent bidding, returning three bids and a recommended choice.
4. A "Fleet Match" view shows nearby idle assets that could be redeployed.
5. A "Brief me" button generates a natural-language summary of the whole situation, grounded in the numbers already shown on screen.
