/* RouteGuard AI  -  Control Tower App Logic */

const API_BASE = '/api';
const DEFAULT_SHIPMENT_ID = 'SHP-1001';

// GET helper — throws on network/HTTP error so callers can fall back to mock data
async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

function inr(n) {
  return "Rs " + Number(n).toLocaleString("en-IN");
}

// Backend risk bands (must match assess_risk in risk_engine.py)
function riskBadgeClass(score) {
  if (score >= 81) return 'badge-critical';
  if (score >= 61) return 'badge-warning';
  if (score >= 31) return 'badge-blue';
  return 'badge-safe';
}

function riskBandLabel(score) {
  if (score >= 81) return 'CRITICAL';
  if (score >= 61) return 'HIGH';
  if (score >= 31) return 'MEDIUM';
  return 'LOW';
}

// Seeded Data for Fallback & Instant Preview
const mockShipments = [
  {
    id: "SHP-1001",
    origin: "Mumbai JNPT",
    destination: "Delhi Okhla",
    cargo: "Pharma cold-chain shipment (vaccines)",
    value: "Rs 6,500,000",
    riskScore: 88,
    status: "Critical Risk",
    reason: "NH-48 Waterlogging + Temp Excursion (9.4 degC)"
  },
  {
    id: "SH-219",
    origin: "Chennai",
    destination: "Bengaluru Logistics Hub",
    cargo: "Auto Components",
    value: "Rs 12,500,000",
    riskScore: 62,
    status: "Moderate Delay",
    reason: "Port Strike Traffic Spillover"
  },
  {
    id: "SH-104",
    origin: "Delhi NCR",
    destination: "Jaipur Express Center",
    cargo: "Consumer Electronics",
    value: "Rs 8,200,000",
    riskScore: 18,
    status: "On Schedule",
    reason: "Normal Transit"
  },
  {
    id: "SH-302",
    origin: "Kolkata Hub",
    destination: "Ranchi Yard",
    cargo: "Pharmaceutical Raw Material",
    value: "Rs 28,000,000",
    riskScore: 45,
    status: "Watchlist",
    reason: "Approaching GDACS Severe Rainfall Zone"
  },
  {
    id: "SHP-1009",
    origin: "Vadodara GIDC",
    destination: "Surat Hazira",
    cargo: "Dairy cold-chain (cultured butter)",
    value: "Rs 1,200,000",
    riskScore: 68,
    status: "Critical Risk",
    reason: "NH-48 Waterlogging at Vadodara origin"
  },
  {
    id: "SHP-1005",
    origin: "Chennai Port",
    destination: "Hyderabad Genome Valley",
    cargo: "Pharma cold-chain shipment (insulin)",
    value: "Rs 4,800,000",
    riskScore: 53,
    status: "Watchlist",
    reason: "NH-44 lane maintenance near Hyderabad"
  }
];

const mockDisruptions = [
  {
    id: "DIS-01",
    title: "NH-48 Monsoon Inundation",
    location: "Vapi-Valsad Stretch",
    severity: "HIGH",
    impactedShipments: 14,
    source: "NHAI Advisory Feed"
  },
  {
    id: "DIS-02",
    title: "Cyclone Advisory Level 3",
    location: "Gujarat Coastal Corridor",
    severity: "CRITICAL",
    impactedShipments: 8,
    source: "GDACS / IMD Warning"
  },
  {
    id: "DIS-03",
    title: "Port Terminal Congestion",
    location: "JNPT Container Gate 2",
    severity: "MEDIUM",
    impactedShipments: 22,
    source: "Port Authority Feed"
  }
];

const mockTelemetry = [
  { time: "10:00", temp: 4.2, status: "normal" },
  { time: "11:00", temp: 4.8, status: "normal" },
  { time: "12:00", temp: 5.1, status: "normal" },
  { time: "13:00", temp: 7.9, status: "normal" },
  { time: "14:00", temp: 9.4, status: "breach" },
  { time: "15:00", temp: 9.1, status: "breach" },
  { time: "16:00", temp: 8.6, status: "breach" },
  { time: "17:00", temp: 5.5, status: "normal" }
];

const mockBids = [
  {
    carrier: "FastFreight Express (Speed Persona)",
    price: "Rs 48,000",
    timeSaved: "4.5 Hours",
    slaScore: "98%",
    status: "RECOMMENDED",
    isWinner: true
  },
  {
    carrier: "EcoCarrier Logistics (Cost Persona)",
    price: "Rs 34,500",
    timeSaved: "2.0 Hours",
    slaScore: "91%",
    status: "RUNNER UP",
    isWinner: false
  },
  {
    carrier: "Reliant Cold Logistics (Reliability Persona)",
    price: "Rs 52,000",
    timeSaved: "3.8 Hours",
    slaScore: "99.5%",
    status: "QUALIFIED",
    isWinner: false
  }
];

const mockFleet = [
  {
    id: "TRK-201",
    type: "Refrigerated truck (12t)",
    location: "Vadodara Yard (5 km away)",
    status: "Idle - Available",
    matchScore: "96%",
    driver: "Rajesh Kumar (Active Duty)"
  },
  {
    id: "TRK-202",
    type: "Dry truck (18t)",
    location: "Ahmedabad Yard (85 km away)",
    status: "Idle - Available",
    matchScore: "88%",
    driver: "Suresh Patel (Available)"
  },
  {
    id: "TRK-203",
    type: "Dry truck (15t)",
    location: "Surat Depot (140 km away)",
    status: "Idle - Standby",
    matchScore: "82%",
    driver: "Amit Shah (Standby)"
  },
  {
    id: "TRK-204",
    type: "Refrigerated truck (14t)",
    location: "Bhiwandi Hub (35 km away)",
    status: "Idle - Available",
    matchScore: "91%",
    driver: "Vikram Yadav (Available)"
  },
  {
    id: "TRK-206",
    type: "Refrigerated truck (12t)",
    location: "Hyderabad Bowenpally (12 km away)",
    status: "Idle - Available",
    matchScore: "93%",
    driver: "Srinivas Rao (Available)"
  }
];

// Initialize Dashboard
document.addEventListener("DOMContentLoaded", () => {
  renderShipments();
  renderDisruptions();
  renderColdChainChart();
  renderBids();
  renderFleet();
});

// Tab Switcher — works from both click events and programmatic calls
function switchTab(tabId, el) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  const activeBtn = el || document.querySelector(`.tab-btn[onclick*="${tabId}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  document.getElementById(`tab-${tabId}`).classList.add('active');
}

// Render Shipments — live backend first, mock fallback when API is offline
function shipmentRowHtml(s) {
  const badgeClass = s.band ? riskBadgeClass(s.riskScore) : (s.riskScore > 75 ? "badge-critical" : s.riskScore > 40 ? "badge-warning" : "badge-safe");
  return `
    <tr>
      <td style="font-family: var(--font-code); font-weight: 600; color: var(--accent-blue);">${s.id}</td>
      <td>${s.origin} to ${s.destination}</td>
      <td>${s.cargo}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${s.value}</span></td>
      <td>
        <span class="badge ${badgeClass}">${s.riskScore} / 100${s.band ? ` &mdash; ${s.band}` : ""}</span>
      </td>
      <td>${s.status}</td>
      <td>
        <button class="btn-action" onclick="openRerouteModal('${s.id}')">Reroute & Negotiate</button>
      </td>
    </tr>
  `;
}

async function renderShipments() {
  const tbody = document.getElementById("shipments-tbody");
  try {
    const [shipments, data] = await Promise.all([
      apiGet("/shipments"),
      apiGet("/risk/assessments"),
    ]);
    const scores = Object.fromEntries((data.assessments || []).map((a) => [a.shipment_id, a]));
    const rows = shipments.map((sh) => {
      const a = scores[sh.id];
      const score = a ? a.score : 0;
      const band = a ? riskBandLabel(score) : null;
      return shipmentRowHtml({
        id: sh.id,
        origin: sh.origin.name,
        destination: sh.destination.name,
        cargo: sh.cargo_description,
        value: inr(sh.cargo_value_inr),
        riskScore: score,
        band: band,
        status: !a ? "Unknown" : band === "CRITICAL" || band === "HIGH" ? "Critical Risk" : band === "MEDIUM" ? "Watchlist" : "On Schedule",
      });
    });
    tbody.innerHTML = rows.join('');
    // Live stat counts (HIGH = score >= 61, matching backend bands)
    const high = Object.values(scores).filter((a) => a.score >= 61).length;
    document.getElementById("stat-active-count").textContent = shipments.length;
    document.getElementById("stat-risk-count").textContent = high;
  } catch (e) {
    tbody.innerHTML = mockShipments.map(shipmentRowHtml).join('');
  }
}

// Render Disruptions — live GDACS+NHAI feed first, mock fallback when offline
function disruptionCardHtml(d) {
  let badge = d.severity === 'CRITICAL' ? 'badge-critical' : d.severity === 'HIGH' ? 'badge-warning' : 'badge-blue';
  return `
    <div style="background: var(--bg-surface-elevated); padding: 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <strong style="font-size: 0.9rem;">${d.title}</strong>
        <span class="badge ${badge}">${d.severity}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
        ${d.subtitle}
      </div>
      <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 4px; font-family: var(--font-code);">
        Source: ${d.source}
      </div>
    </div>
  `;
}

async function renderDisruptions() {
  const container = document.getElementById("disruption-feed-list");
  try {
    const data = await apiGet("/risk/disruptions");
    const list = data.disruptions || [];
    if (!list.length) {
      container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-secondary);">No active disruptions — live feed reachable, nothing in range.</div>`;
      return;
    }
    container.innerHTML = list.map((x) => disruptionCardHtml({
      title: x.title,
      severity: String(x.severity).toUpperCase(),
      subtitle: `Radius ${x.radius_km} km @ ${Number(x.lat).toFixed(2)}, ${Number(x.lng).toFixed(2)}`,
      source: x.source,
    })).join('');
  } catch (e) {
    container.innerHTML = mockDisruptions.map((d) => disruptionCardHtml({
      title: d.title,
      severity: d.severity,
      subtitle: `Location: ${d.location} — ${d.impactedShipments} active shipments affected`,
      source: d.source,
    })).join('');
  }
}

// Render Cold Chain Telemetry Chart — live sensor logs first, mock fallback offline
function telemetryChartHtml(points) {
  const maxTemp = 12;
  return points.map(t => {
    let heightPercent = Math.min(100, (t.temp / maxTemp) * 100);
    return `
      <div class="chart-bar-wrap">
        <div class="bar-val" style="color: ${t.status === 'breach' ? 'var(--status-critical)' : 'var(--text-primary)'};">${t.temp} degC</div>
        <div class="chart-bar ${t.status}" style="height: ${heightPercent}%;"></div>
        <div class="bar-time">${t.time}</div>
      </div>
    `;
  }).join('');
}

function updateColdSeverityBox(report) {
  const headerBadge = document.getElementById("cold-chain-status-badge");
  const box = document.getElementById("cold-chain-report-box");
  const sev = report.severity || "NOMINAL";
  const breach = sev !== "NOMINAL" && sev !== "STABILITY_OK";
  const sevLabel = String(sev).replace(/_/g, " ");
  if (headerBadge) {
    headerBadge.className = "badge " + (breach ? "badge-critical" : "badge-safe");
    headerBadge.textContent = breach ? `${sevLabel} DETECTED` : "COMPLIANT";
  }
  const statCold = document.getElementById("stat-cold-count");
  if (statCold) statCold.textContent = breach ? "1 Excursion" : "Compliant";
  if (!box) return;
  const bg = breach ? "rgba(220, 38, 38, 0.06)" : "rgba(5, 150, 105, 0.06)";
  const border = breach ? "rgba(220, 38, 38, 0.3)" : "rgba(5, 150, 105, 0.3)";
  const badgeCls = breach ? "badge-critical" : "badge-safe";
  box.style.background = bg;
  box.style.border = `1px solid ${border}`;
  box.style.borderRadius = "var(--radius-md)";
  box.style.padding = "1.25rem";
  box.style.marginTop = "1rem";
  box.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
      <div>
        <span class="badge ${badgeCls}">${sevLabel}</span>
        <h3 style="font-size: 1.1rem; font-weight: 700; margin-top: 0.5rem; color: var(--status-critical);">
          Max ${report.max_recorded_c} deg C &nbsp;|&nbsp; Excursion ${report.total_excursion_minutes} min &nbsp;|&nbsp; Door events ${report.door_open_events}
        </h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.4rem; line-height: 1.4;">
          <strong>Standard:</strong> ${report.compliance_standard || "WHO TRS 961 / FDA 21 CFR GDP Guidelines"}<br>
          <strong>Regulatory Analysis:</strong> ${report.action_recommended}
        </p>
      </div>
      <button class="btn-action" style="background: var(--status-critical); color: #fff; white-space: nowrap;" onclick="triggerColdChainReroute()">
        Emergency Reroute
      </button>
    </div>`;
}

async function renderColdChainChart() {
  const container = document.getElementById("sensor-chart");
  try {
    const [logs, report] = await Promise.all([
      apiGet(`/cold-chain/telemetry/${encodeURIComponent(DEFAULT_SHIPMENT_ID)}`),
      apiGet(`/cold-chain/report/${encodeURIComponent(DEFAULT_SHIPMENT_ID)}`),
    ]);
    const points = logs.map((l) => {
      const out = l.temperature_c > 8.0 || l.temperature_c < 2.0;
      return {
        temp: l.temperature_c,
        status: out ? "breach" : "normal",
        time: new Date(l.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false }),
      };
    });
    container.innerHTML = telemetryChartHtml(points);
    updateColdSeverityBox(report);
  } catch (e) {
    container.innerHTML = telemetryChartHtml(mockTelemetry);
  }
}

// CrewAI carrier auction — live POST /api/negotiation/{id}, mock fallback offline
function bidCardHtml(b, chosenId, awardedId) {
  const isWinner = b.carrier_id ? b.carrier_id === (awardedId || chosenId) : b.isWinner;
  const name = b.carrier_name || b.carrier;
  const price = b.price_inr != null ? inr(b.price_inr) : b.price;
  const eta = b.eta_hours != null ? `${b.eta_hours} hrs ETA` : b.timeSaved;
  const sla = b.reliability_score != null ? `${Math.round(b.reliability_score * 100)}%` : b.slaScore;
  const key = b.carrier_id || b.carrier;
  return `
    <div class="bidder-card ${isWinner ? 'winner' : ''}" data-bid-card="${key}">
      <div>
        <div class="bidder-name">
          <span>${name}</span>
          ${isWinner ? '<span class="badge badge-safe">WINNING BID</span>' : ''}
        </div>
        <div class="bid-metrics">
          <div class="metric-item">
            <span style="font-size: 0.7rem; color: var(--text-muted);">Bid Amount</span>
            <div class="val" style="color: var(--accent-blue);">${price}</div>
          </div>
          <div class="metric-item">
            <span style="font-size: 0.7rem; color: var(--text-muted);">ETA</span>
            <div class="val" style="color: var(--status-safe);">${eta}</div>
          </div>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          Reliability: <strong>${sla}</strong>${b.rationale ? `<br><span style="font-size: 0.75rem;">${b.rationale}</span>` : ""}
        </div>
      </div>
      <button class="btn-action" style="margin-top: 1rem; width: 100%;" onclick="selectBid('${key}')" ${isWinner ? "disabled" : ""}>
        ${isWinner ? 'Contract Awarded' : 'Select Alternative'}
      </button>
    </div>
  `;
}

// Awarding a contract just re-marks the cards inline — no alert box
function selectBid(key) {
  document.querySelectorAll("[data-bid-card]").forEach((card) => {
    const win = card.getAttribute("data-bid-card") === key;
    card.classList.toggle("winner", win);
    const badge = card.querySelector(".bidder-name .badge");
    if (win && !badge) {
      card.querySelector(".bidder-name").insertAdjacentHTML("beforeend", '<span class="badge badge-safe">WINNING BID</span>');
    } else if (!win && badge) {
      badge.remove();
    }
    const btn = card.querySelector("button");
    if (btn) { btn.disabled = win; btn.textContent = win ? "Contract Awarded" : "Select Alternative"; }
  });
}

async function runNegotiation(shipmentId) {
  const container = document.getElementById("bidding-container");
  container.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-secondary);">Running carrier agent auction for ${shipmentId}…</p>`;
  try {
    const res = await fetch(`${API_BASE}/negotiation/${encodeURIComponent(shipmentId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ priority: "balanced" }),
    });
    if (!res.ok) throw new Error(`negotiation -> ${res.status}`);
    const data = await res.json();
    const neg = data.negotiation || {};
    const bids = neg.bids || [];
    const chosen = neg.chosen_carrier_id;
    container.innerHTML =
      (neg.recommendation ? `<div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;"><strong>Negotiator:</strong> ${neg.recommendation}</div>` : "") +
      bids.map((b) => bidCardHtml(b, chosen, null)).join('');
  } catch (e) {
    container.innerHTML = mockBids.map((b) => bidCardHtml(b, null, null)).join('');
  }
}

function renderBids() {
  runNegotiation(DEFAULT_SHIPMENT_ID);
}

// Render Fleet — dispatched state comes from the row's own status (set by dispatchFleetAsset)
function fleetRowHtml(f) {
  const deployed = f.status.startsWith("Deployed");
  const badge = deployed ? "badge-blue" : "badge-safe";
  return `
    <tr data-asset-row="${f.id}">
      <td style="font-family: var(--font-code); font-weight: 600;">${f.id}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${f.type}</span></td>
      <td>${f.location}</td>
      <td>${f.driver}<br><span class="badge ${badge}">${f.status}</span></td>
      <td style="font-family: var(--font-code);">${f.location.split('(')[1] ? f.location.split('(')[1].replace(')', '') : '15 km'}</td>
      <td><span class="badge badge-blue">${f.matchScore}</span></td>
      <td>
        <button class="btn-action" data-dispatch-btn="${f.id}" onclick="dispatchFleetAsset('${f.id}')" ${deployed ? "disabled" : ""}>${deployed ? "Deployed ✓" : `Redeploy to ${DEFAULT_SHIPMENT_ID}`}</button>
      </td>
    </tr>
  `;
}

function candidateRowHtml(c, shipmentId) {
  const asset = c.asset;
  const score = Math.round(c.redeployment_score * 100);
  const scoreCls = score >= 60 ? "badge-safe" : score >= 30 ? "badge-blue" : "badge-warning";
  return `
    <tr data-asset-row="${asset.id}">
      <td style="font-family: var(--font-code); font-weight: 600;">${asset.id}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${asset.type} · ${asset.capacity_tons}T</span></td>
      <td>${asset.current_location.name}</td>
      <td><span class="badge badge-safe" data-asset-status="${asset.id}">Idle ${Number(c.idle_hours).toFixed(1)} hrs</span></td>
      <td style="font-family: var(--font-code);">${c.distance_km} km</td>
      <td><span class="badge ${scoreCls}">${score} / 100</span></td>
      <td>
        <button class="btn-action" data-dispatch-btn="${asset.id}" onclick="dispatchFleetAsset('${asset.id}', '${shipmentId}')">Deploy to ${shipmentId}</button>
      </td>
    </tr>
  `;
}

async function renderFleet(shipmentId) {
  const sid = shipmentId || DEFAULT_SHIPMENT_ID;
  const tbody = document.getElementById("fleet-tbody");
  // Ranked idle candidates near the shipment destination; mock rows stay as fallback
  try {
    const [data, fleet] = await Promise.all([
      apiGet(`/fleet/redeploy/${encodeURIComponent(sid)}`),
      apiGet("/fleet").catch(() => null),
    ]);
    const candidates = data.candidates || [];
    if (!candidates.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No idle assets within 250 km of destination.</td></tr>`;
    } else {
      tbody.innerHTML = candidates.map((c) => candidateRowHtml(c, sid)).join('');
    }
    const idleCount = fleet ? fleet.filter((a) => a.idle_since != null).length : candidates.length;
    const idleBadge = document.getElementById("fleet-idle-badge");
    if (idleBadge) idleBadge.textContent = `${idleCount} Idle Assets Available`;
    const statIdle = document.getElementById("stat-idle-count");
    if (statIdle) statIdle.textContent = `${idleCount} Trucks`;
  } catch (e) {
    tbody.innerHTML = mockFleet.map(fleetRowHtml).join('');
  }
}

// Reroute Modal Logic — live corridors from GET /api/risk/reroute/{id}
async function openRerouteModal(shipmentId) {
  const modal = document.getElementById("reroute-modal");
  document.getElementById("modal-shipment-title").innerText = `Reroute Engine: ${shipmentId}`;

  const corridorList = document.getElementById("modal-corridor-list");
  corridorList.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-secondary);">Evaluating corridors…</p>`;
  modal.classList.add("active");

  try {
    const data = await apiGet(`/risk/reroute/${encodeURIComponent(shipmentId)}`);
    const options = data.reroute_options || [];
    if (!options.length) throw new Error("empty");
    corridorList.innerHTML = options.map((o) => `
      <div style="background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-md); border: 1px solid ${o.recommended ? "var(--accent-blue)" : "var(--border-color)"};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="${o.recommended ? "color: var(--accent-blue);" : ""}">${o.corridor_description}</strong>
          ${o.recommended ? '<span class="badge badge-safe">RECOMMENDED</span>' : ""}
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">
          Extra time: <strong>+${o.delta_time_hours} hrs</strong> · Extra cost: <strong>${inr(o.delta_cost_inr)}</strong> · Post-reroute risk: <strong>${o.projected_risk_after}/100</strong>
        </p>
        ${o.recommended ? `<button class="btn-action" style="margin-top: 0.75rem;" onclick="confirmReroute('${shipmentId}')">Confirm Reroute Corridor</button>` : ""}
      </div>
    `).join('');
  } catch (e) {
    corridorList.innerHTML = `
      <div style="background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--accent-blue);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: var(--accent-blue);">Corridor A: Expressway Bypass via Vadodara-Godhra</strong>
          <span class="badge badge-safe">RECOMMENDED</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">
          Bypasses NH-48 flood point. Additional distance: +42 km. Estimated ETA reduction: <strong>3.5 hours</strong>. Post-reroute Risk: <strong>14/100</strong>.
        </p>
        <button class="btn-action" style="margin-top: 0.75rem;" onclick="confirmReroute('${shipmentId}')">Confirm Reroute Corridor</button>
      </div>
    `;
  }
}

function closeModal() {
  document.getElementById("reroute-modal").classList.remove("active");
}

// Confirming a corridor jumps to the live carrier auction — no alert box
function confirmReroute(shipmentId) {
  closeModal();
  switchTab('negotiation');
  runNegotiation(shipmentId);
}

function triggerColdChainReroute() {
  openRerouteModal(DEFAULT_SHIPMENT_ID);
}

async function dispatchFleetAsset(assetId, shipmentId) {
  const sid = shipmentId || DEFAULT_SHIPMENT_ID;
  const btn = document.querySelector(`[data-dispatch-btn="${assetId}"]`);
  if (btn) { btn.disabled = true; btn.textContent = "Dispatching…"; }
  try {
    const res = await fetch(`${API_BASE}/fleet/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset_id: assetId, shipment_id: sid })
    });
    if (!res.ok) throw new Error(`Dispatch failed (${res.status})`);
    await res.json();
    // Update row inline — no alert box
    const statusEl = document.querySelector(`[data-asset-status="${assetId}"]`);
    if (statusEl) { statusEl.className = "badge badge-blue"; statusEl.textContent = `Deployed - ${sid}`; }
    const entry = mockFleet.find((f) => f.id === assetId);
    if (entry) entry.status = `Deployed - ${sid}`;
    if (btn) { btn.textContent = "Deployed ✓"; }
    // Refresh idle counts from the backend
    try {
      const fleet = await apiGet("/fleet");
      const idleCount = fleet.filter((a) => a.idle_since != null).length;
      const idleBadge = document.getElementById("fleet-idle-badge");
      if (idleBadge) idleBadge.textContent = `${idleCount} Idle Assets Available`;
      const statIdle = document.getElementById("stat-idle-count");
      if (statIdle) statIdle.textContent = `${idleCount} Trucks`;
    } catch { /* counts stay as-is offline */ }
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = "Failed — retry"; }
  }
}

// Escape raw text so model output can't inject HTML, then render Markdown
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// Minimal Markdown renderer (headings, bold, italic, code, lists, breaks)
// Covers what the copilot emits so raw `*` / `#` never show in the UI.
function renderMarkdown(md) {
  const lines = escapeHtml(md).split("\n");
  const isTableRow = (t) => /^\|.*\|\s*$/.test(t);
  const isDelimRow = (t) => /^\|[\s|:.-]+\|\s*$/.test(t) && /-{2,}/.test(t);
  const splitCells = (t) => t.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  let html = "";
  let inList = false;
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    // GitHub-style tables: header row + delimiter row + body rows
    if (isTableRow(t) && i + 1 < lines.length && isDelimRow(lines[i + 1].trim())) {
      if (inList) { html += "</ul>"; inList = false; }
      const headers = splitCells(t);
      html += "<table><thead><tr>" + headers.map((c) => `<th>${c}</th>`).join("") + "</tr></thead><tbody>";
      i += 2; // skip delimiter row
      while (i < lines.length && isTableRow(lines[i].trim())) {
        const cells = splitCells(lines[i].trim());
        html += "<tr>" + cells.map((c) => `<td>${c}</td>`).join("") + "</tr>";
        i++;
      }
      html += "</tbody></table>";
      i--; // offset outer increment
      continue;
    }
    if (/^###\s+/.test(t)) { if (inList) { html += "</ul>"; inList = false; } html += `<h4>${t.replace(/^###\s+/, "")}</h4>`; }
    else if (/^##\s+/.test(t)) { if (inList) { html += "</ul>"; inList = false; } html += `<h3>${t.replace(/^##\s+/, "")}</h3>`; }
    else if (/^#\s+/.test(t)) { if (inList) { html += "</ul>"; inList = false; } html += `<h3>${t.replace(/^#\s+/, "")}</h3>`; }
    else if (/^([-*•]\s+)/.test(t)) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${t.replace(/^([-*•]\s+)/, "")}</li>`;
    } else if (t === "") { if (inList) { html += "</ul>"; inList = false; } }
    else { if (inList) { html += "</ul>"; inList = false; } html += `<p>${t}</p>`; }
  }
  if (inList) html += "</ul>";
  return html
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function appendAssistantBubble(chatHist, badge, bodyHtml) {
  const div = document.createElement("div");
  div.className = "msg-bubble assistant";
  div.innerHTML = `<div class="grounded-badge">${badge}</div><div class="md-body"></div>`;
  div.querySelector(".md-body").innerHTML = bodyHtml;
  chatHist.appendChild(div);
  return div.querySelector(".md-body");
}

// IBM BoB Copilot Chat Logic — SSE streaming with Markdown rendering
function sendCopilotMsg() {
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  const chatHist = document.getElementById("chat-history");

  // Add User Bubble (escaped — user text is not Markdown)
  const userDiv = document.createElement("div");
  userDiv.className = "msg-bubble user";
  userDiv.textContent = query;
  chatHist.appendChild(userDiv);
  input.value = "";
  chatHist.scrollTop = chatHist.scrollHeight;

  // Brief the shipment mentioned in the question (e.g. "SHP-1005"), else the default
  const sidMatch = query.match(/SHP-\d+/i);
  const briefSid = sidMatch ? sidMatch[0].toUpperCase() : DEFAULT_SHIPMENT_ID;

  const bodyEl = appendAssistantBubble(chatHist, `IBM BoB Copilot — Live Grounded Brief (${briefSid})`, "<em>Thinking…</em>");
  let raw = "";

  const paint = () => { bodyEl.innerHTML = renderMarkdown(raw); chatHist.scrollTop = chatHist.scrollHeight; };

  // Non-streaming fallback (keeps old POST endpoint working)
  const fallbackPost = async () => {
    const res = await fetch(`${API_BASE}/copilot/brief`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shipment_id: briefSid, query: query })
    });
    if (!res.ok) throw new Error("API Offline");
    const data = await res.json();
    raw = data.brief || data.response || "";
    paint();
  };

  try {
    const url = `${API_BASE}/copilot/brief/stream?shipment_id=${encodeURIComponent(briefSid)}&query=${encodeURIComponent(query)}`;
    const es = new EventSource(url);
    es.onmessage = (ev) => {
      if (ev.data === "[DONE]") { es.close(); paint(); return; }
      try {
        const msg = JSON.parse(ev.data);
        if (msg.token) { raw += msg.token; paint(); }
        else if (msg.error) { raw += `\n\n**Stream error:** ${msg.error}`; paint(); es.close(); }
      } catch { /* ignore malformed chunk */ }
    };
    es.onerror = async () => {
      es.close();
      if (!raw) { try { await fallbackPost(); } catch (e) { showStaticFallback(chatHist); } }
      else paint();
    };
  } catch (e) {
    fallbackPost().catch(() => showStaticFallback(chatHist));
  }
  chatHist.scrollTop = chatHist.scrollHeight;
}

function showStaticFallback(chatHist) {
  const reply = `**SHP-1001 (Pharma cold-chain)**\n\n- **Risk Score:** 88/100 (Critical)\n- **Primary Disruption:** NH-48 Waterlogging near Vadodara\n- **Cold Chain:** excursion detected, quarantine review recommended\n- **Recommendation:** reroute via bypass corridor and redeploy idle reefer TRK-201.`;
  appendAssistantBubble(chatHist, "IBM BoB Copilot — Grounded Brief Engine", renderMarkdown(reply));
  chatHist.scrollTop = chatHist.scrollHeight;
}
