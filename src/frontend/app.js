/* RouteGuard AI - Control Tower App Logic
 * All data is fetched from the live FastAPI backend.
 * Backend must be running at http://localhost:8000
 * Start with: uvicorn app.main:app --reload --port 8000
 */

const API_BASE = 'http://localhost:8000/api';

/* ─────────────────────────────────────────────
   BOOT: load all tabs on page ready
───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  loadControlTower();
  loadColdChain();
  loadFleet();
  // Negotiation and Copilot tabs are loaded on demand (user-triggered)
});

/* ─────────────────────────────────────────────
   TAB SWITCHER
───────────────────────────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  event.currentTarget.classList.add('active');
  document.getElementById(`tab-${tabId}`).classList.add('active');
}

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */
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

function setLoading(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted);">${message}</td></tr>`;
}

function setLoadingDiv(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted);">${message}</div>`;
}

/* ─────────────────────────────────────────────
   TAB 1: CONTROL TOWER
   APIs used:
     GET /api/risk/assessments   -> risk scores for all shipments
     GET /api/risk/disruptions   -> live GDACS disruption feed
───────────────────────────────────────────── */
async function loadControlTower() {
  setLoading('shipments-tbody', 'Loading shipments from backend...');
  setLoadingDiv('disruption-feed-list', 'Fetching live disruption feed...');

  // Load risk assessments and disruptions in parallel
  const [assessData, disruptData] = await Promise.all([
    fetch(`${API_BASE}/risk/assessments`).then(r => r.json()).catch(() => null),
    fetch(`${API_BASE}/risk/disruptions`).then(r => r.json()).catch(() => null),
  ]);

  // ── Shipments table ──
  const tbody = document.getElementById('shipments-tbody');
  if (!assessData || !assessData.assessments) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--status-critical);padding:1rem;">
      Backend offline - start uvicorn at port 8000</td></tr>`;
  } else {
    const assessments = assessData.assessments;

    // Update top stat boxes
    document.getElementById('stat-active-count').textContent = assessments.length;
    const highRisk = assessments.filter(a => a.score >= 61).length;
    document.getElementById('stat-risk-count').textContent = highRisk;

    tbody.innerHTML = assessments.map(a => {
      const badge = riskBadgeClass(a.score);
      const label = riskBandLabel(a.score);
      // Build a human-readable factor summary
      const factorSummary = a.factors
        .filter(f => f.contribution > 0)
        .map(f => f.explanation)
        .join(' | ') || 'No active disruptions';

      return `
        <tr>
          <td style="font-family:var(--font-code);font-weight:600;color:var(--accent-blue);">
            ${a.shipment_id}
          </td>
          <td>${factorSummary.substring(0, 60)}...</td>
          <td>
            <span style="font-size:0.75rem;color:var(--text-muted);">
              Computed ${new Date(a.computed_at).toLocaleTimeString()}
            </span>
          </td>
          <td>
            <span class="badge ${badge}">${a.score} / 100 &mdash; ${label}</span>
          </td>
          <td>${label}</td>
          <td>
            <button class="btn-action" onclick="openRerouteModal('${a.shipment_id}')">
              Reroute &amp; Negotiate
            </button>
          </td>
        </tr>`;
    }).join('');
  }

  // ── Disruption feed panel ──
  const feedEl = document.getElementById('disruption-feed-list');
  if (!disruptData || !disruptData.disruptions) {
    feedEl.innerHTML = `<div style="color:var(--text-muted);font-size:0.85rem;">
      GDACS feed unavailable (backend offline or no network)</div>`;
  } else {
    const disruptions = disruptData.disruptions;
    document.getElementById('stat-risk-count').textContent =
      disruptData.count !== undefined ? disruptData.count : disruptions.length;

    if (disruptions.length === 0) {
      feedEl.innerHTML = `<div style="color:var(--status-safe);font-size:0.85rem;padding:1rem;">
        No active disruptions detected on GDACS feed.</div>`;
    } else {
      feedEl.innerHTML = disruptions.slice(0, 5).map(d => {
        const badge = d.severity === 'critical' ? 'badge-critical'
                    : d.severity === 'high'     ? 'badge-warning'
                    : 'badge-blue';
        return `
          <div style="background:var(--bg-surface-elevated);padding:0.9rem;
                      border-radius:var(--radius-sm);border:1px solid var(--border-color);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <strong style="font-size:0.9rem;">${d.title}</strong>
              <span class="badge ${badge}">${d.severity.toUpperCase()}</span>
            </div>
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
              ${d.description ? d.description.substring(0, 80) : 'Radius: ' + d.radius_km + ' km'}
            </div>
            <div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px;
                        font-family:var(--font-code);">
              Source: ${d.source || 'GDACS'} &nbsp;|&nbsp;
              Lat: ${d.lat.toFixed(2)}, Lng: ${d.lng.toFixed(2)}
            </div>
          </div>`;
      }).join('');
    }
  }
}

/* ─────────────────────────────────────────────
   TAB 2: COLD CHAIN IoT
   APIs used:
     GET /api/cold-chain/telemetry/{id}   -> raw IoT sensor logs
     GET /api/cold-chain/report/{id}      -> analysis report + severity
   Default shipment: SHP-1001 (vaccine cold chain)
───────────────────────────────────────────── */
async function loadColdChain(shipmentId) {
  const sid = shipmentId || 'SHP-1001';

  const [logs, report] = await Promise.all([
    fetch(`${API_BASE}/cold-chain/telemetry/${sid}`).then(r => r.json()).catch(() => null),
    fetch(`${API_BASE}/cold-chain/report/${sid}`).then(r => r.json()).catch(() => null),
  ]);

  // ── Sensor bar chart ──
  const chartEl = document.getElementById('sensor-chart');
  if (!logs || !Array.isArray(logs) || logs.length === 0) {
    chartEl.innerHTML = `<div style="color:var(--text-muted);padding:1rem;">
      No IoT telemetry available for ${sid}.</div>`;
  } else {
    const maxTemp = Math.max(...logs.map(l => l.temperature_c), 12);
    chartEl.innerHTML = logs.map(l => {
      const isBreach = l.temperature_c > 8.0 || l.temperature_c < 2.0;
      const heightPct = Math.round((l.temperature_c / maxTemp) * 100);
      const timeLabel = new Date(l.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
      return `
        <div class="chart-bar-wrap">
          <div class="bar-val" style="color:${isBreach ? 'var(--status-critical)' : 'var(--text-primary)'};">
            ${l.temperature_c.toFixed(1)} degC
          </div>
          <div class="chart-bar ${isBreach ? 'breach' : 'normal'}" style="height:${heightPct}%;"></div>
          <div class="bar-time">${timeLabel}</div>
        </div>`;
    }).join('');
  }

  // ── Report / severity box ──
  if (report && report.severity) {
    const badge = document.getElementById('cold-chain-status-badge');
    const isCritical = report.severity === 'CARGO_SPOILED' || report.severity === 'QUARANTINE_REQUIRED';

    if (badge) {
      badge.textContent = isCritical
        ? `${report.severity.replace(/_/g, ' ')} DETECTED`
        : 'NOMINAL - COMPLIANT';
      badge.className = isCritical ? 'badge badge-critical' : 'badge badge-safe';
    }

    // Inject the live regulatory analysis below the chart
    const reportBox = document.getElementById('cold-chain-report-box');
    if (reportBox) {
      const color = isCritical ? 'rgba(239,68,68,0.08)' : 'rgba(34,197,94,0.08)';
      const border = isCritical ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)';
      reportBox.style.background = color;
      reportBox.style.border = `1px solid ${border}`;
      reportBox.style.borderRadius = 'var(--radius-md)';
      reportBox.style.padding = '1.25rem';
      reportBox.style.marginTop = '1rem';

      reportBox.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <span class="badge ${isCritical ? 'badge-critical' : 'badge-safe'}">
              ${report.severity.replace(/_/g, ' ')}
            </span>
            <h3 style="font-size:1.1rem;font-weight:700;margin-top:0.5rem;
                       color:${isCritical ? '#f87171' : '#4ade80'};">
              Max Temp: ${report.max_recorded_c} degC &nbsp;|&nbsp;
              Excursion: ${report.total_excursion_minutes} min &nbsp;|&nbsp;
              Degree-hours OOR: ${report.degree_hours_out_of_range}
            </h3>
            <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.4rem;line-height:1.4;">
              <strong>Standard:</strong> ${report.compliance_standard}<br>
              <strong>Action:</strong> ${report.action_recommended}
            </p>
          </div>
          <button class="btn-action"
                  style="background:var(--status-critical);color:#fff;"
                  onclick="triggerColdChainReroute()">
            Emergency Reroute
          </button>
        </div>`;
    }
  }
}

/* ─────────────────────────────────────────────
   TAB 3: MULTI-AGENT CARRIER AUCTION
   API used:
     POST /api/negotiation/{shipment_id}
     Body: { "priority": "balanced" }
   Called when user clicks "Run Auction" or when
   reroute modal confirms a corridor.
───────────────────────────────────────────── */
async function runNegotiation(shipmentId, priority) {
  const sid = shipmentId || 'SHP-1001';
  const pri = priority || 'balanced';
  const container = document.getElementById('bidding-container');

  container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted);">
    Running CrewAI multi-agent auction for ${sid}... (may take 10-20 seconds)</div>`;

  try {
    const res = await fetch(`${API_BASE}/negotiation/${sid}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ priority: pri }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const bids = data.negotiation.bids || [];
    const recommendation = data.negotiation.recommendation || '';
    const chosenId = data.negotiation.chosen_carrier_id || '';

    if (bids.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);padding:1rem;">
        No bids returned from agents.</div>`;
      return;
    }

    container.innerHTML = bids.map(b => {
      const isWinner = b.carrier_id === chosenId;
      return `
        <div class="bidder-card ${isWinner ? 'winner' : ''}">
          <div>
            <div class="bidder-name">
              <span>${b.carrier_name}</span>
              ${isWinner ? '<span class="badge badge-safe">WINNING BID</span>' : ''}
            </div>
            <div class="bid-metrics">
              <div class="metric-item">
                <span style="font-size:0.7rem;color:var(--text-muted);">Bid Amount</span>
                <div class="val" style="color:var(--accent-blue);">
                  Rs ${b.price_inr.toLocaleString('en-IN')}
                </div>
              </div>
              <div class="metric-item">
                <span style="font-size:0.7rem;color:var(--text-muted);">ETA (hrs)</span>
                <div class="val" style="color:var(--status-safe);">
                  +${b.eta_hours.toFixed(1)} hrs
                </div>
              </div>
              <div class="metric-item">
                <span style="font-size:0.7rem;color:var(--text-muted);">Reliability</span>
                <div class="val">${(b.reliability_score * 100).toFixed(0)}%</div>
              </div>
            </div>
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.5rem;">
              ${b.rationale}
            </div>
          </div>
          <button class="btn-action" style="margin-top:1rem;width:100%;"
                  onclick="awardBid('${b.carrier_id}','${b.carrier_name}')">
            ${isWinner ? 'Contract Awarded' : 'Select Alternative'}
          </button>
        </div>`;
    }).join('');

    // Show negotiator recommendation below bids
    if (recommendation) {
      container.innerHTML += `
        <div style="grid-column:1/-1;background:var(--bg-surface-elevated);
                    border:1px solid var(--accent-blue);border-radius:var(--radius-md);
                    padding:1rem;margin-top:0.5rem;">
          <div style="font-size:0.75rem;font-weight:700;color:var(--accent-blue);
                      text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
            IBM BoB Negotiator Agent Recommendation
          </div>
          <div style="font-size:0.875rem;color:var(--text-primary);line-height:1.6;">
            ${recommendation}
          </div>
        </div>`;
    }
  } catch (err) {
    container.innerHTML = `<div style="color:var(--status-critical);padding:1rem;">
      Negotiation API error: ${err.message}<br>
      <small>Ensure backend is running and LLM_API_KEY is set in .env</small></div>`;
  }
}

/* ─────────────────────────────────────────────
   TAB 4: FLEET ASSET REDEPLOYMENT
   APIs used:
     GET /api/fleet/redeploy/{shipment_id}  -> ranked idle candidates
     GET /api/fleet/utilisation             -> utilisation %
───────────────────────────────────────────── */
async function loadFleet(shipmentId) {
  const sid = shipmentId || 'SHP-1001';
  const tbody = document.getElementById('fleet-tbody');
  if (tbody) setLoading('fleet-tbody', 'Loading fleet candidates...');

  const [candidateData, utilData] = await Promise.all([
    fetch(`${API_BASE}/fleet/redeploy/${sid}`).then(r => r.json()).catch(() => null),
    fetch(`${API_BASE}/fleet/utilisation`).then(r => r.json()).catch(() => null),
  ]);

  // Update idle fleet stat box
  if (candidateData && candidateData.candidates) {
    document.getElementById('stat-idle-count').textContent =
      `${candidateData.candidates.length} Available`;
  }

  if (utilData && utilData.utilisation_pct !== undefined) {
    // Update utilisation display if element exists
    const utilEl = document.getElementById('stat-utilisation');
    if (utilEl) utilEl.textContent = `${utilData.utilisation_pct}%`;
  }

  if (!candidateData || !candidateData.candidates) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--status-critical);padding:1rem;">
      Fleet API unavailable</td></tr>`;
    return;
  }

  const candidates = candidateData.candidates;

  if (candidates.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;
      color:var(--text-muted);padding:2rem;">
      No idle assets within 250 km of destination.</td></tr>`;
    return;
  }

  tbody.innerHTML = candidates.map((c, i) => {
    const asset = c.asset;
    const score = (c.redeployment_score * 100).toFixed(0);
    const scoreClass = score >= 60 ? 'badge-safe' : score >= 30 ? 'badge-blue' : 'badge-warning';
    const idleSince = asset.idle_since
      ? `Idle ${c.idle_hours.toFixed(1)} hrs`
      : 'Active';
    return `
      <tr>
        <td style="font-family:var(--font-code);font-weight:600;">
          ${asset.id}<br>
          <span style="font-size:0.75rem;color:var(--text-muted);">${asset.type}</span>
        </td>
        <td>${asset.current_location.name}</td>
        <td>
          <span class="badge badge-safe">${idleSince}</span><br>
          <span style="font-size:0.75rem;color:var(--text-muted);">
            ${asset.capacity_tons}T capacity
          </span>
        </td>
        <td style="font-family:var(--font-code);">${c.distance_km} km</td>
        <td><span class="badge ${scoreClass}">${score} / 100</span></td>
        <td>
          <button class="btn-action"
                  onclick="dispatchFleetAsset('${asset.id}','${sid}')">
            Deploy to ${sid}
          </button>
        </td>
      </tr>`;
  }).join('');
}

/* ─────────────────────────────────────────────
   REROUTE MODAL
   API used:
     GET /api/risk/reroute/{shipment_id}
───────────────────────────────────────────── */
async function openRerouteModal(shipmentId) {
  const modal = document.getElementById('reroute-modal');
  document.getElementById('modal-shipment-title').textContent =
    `Reroute Analysis: ${shipmentId}`;
  modal.classList.add('active');

  const corridorList = document.getElementById('modal-corridor-list');
  corridorList.innerHTML = `<div style="text-align:center;padding:1.5rem;
    color:var(--text-muted);">Computing corridor alternatives...</div>`;

  try {
    const res = await fetch(`${API_BASE}/risk/reroute/${shipmentId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const options = data.reroute_options || [];
    const originalScore = data.assessment ? data.assessment.score : '?';

    if (options.length === 0) {
      corridorList.innerHTML = `<div style="color:var(--text-muted);">
        No reroute options available.</div>`;
      return;
    }

    corridorList.innerHTML = options.map((opt, i) => {
      const isRec = opt.recommended;
      const borderColor = isRec ? 'var(--accent-blue)' : 'var(--border-color)';
      const riskDelta = originalScore - opt.projected_risk_after;
      return `
        <div style="background:var(--bg-surface-elevated);padding:1rem;
                    border-radius:var(--radius-md);border:1px solid ${borderColor};">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong style="color:${isRec ? 'var(--accent-blue)' : 'var(--text-primary)'};">
              Corridor ${String.fromCharCode(65 + i)}: ${opt.corridor_description}
            </strong>
            ${isRec ? '<span class="badge badge-safe">RECOMMENDED</span>' : ''}
          </div>
          <div style="font-size:0.85rem;color:var(--text-secondary);
                      margin-top:0.5rem;display:grid;
                      grid-template-columns:repeat(3,1fr);gap:0.5rem;">
            <div>
              <div style="font-size:0.7rem;color:var(--text-muted);">Time Delta</div>
              <strong>+${opt.delta_time_hours} hrs</strong>
            </div>
            <div>
              <div style="font-size:0.7rem;color:var(--text-muted);">Cost Delta</div>
              <strong>+Rs ${opt.delta_cost_inr.toLocaleString('en-IN')}</strong>
            </div>
            <div>
              <div style="font-size:0.7rem;color:var(--text-muted);">Risk After</div>
              <strong style="color:var(--status-safe);">
                ${opt.projected_risk_after}/100
                (${riskDelta > 0 ? '-' + riskDelta : '0'} pts)
              </strong>
            </div>
          </div>
          ${isRec ? `
          <button class="btn-action" style="margin-top:0.75rem;"
                  onclick="confirmReroute('${shipmentId}', '${opt.corridor_description}')">
            Confirm &amp; Start Carrier Auction
          </button>` : ''}
        </div>`;
    }).join('');
  } catch (err) {
    corridorList.innerHTML = `<div style="color:var(--status-critical);">
      Reroute engine error: ${err.message}</div>`;
  }
}

function closeModal() {
  document.getElementById('reroute-modal').classList.remove('active');
}

function confirmReroute(shipmentId, corridor) {
  closeModal();
  // Switch to negotiation tab and run the auction
  document.querySelectorAll('.tab-btn').forEach((btn, i) => {
    if (btn.textContent.trim().includes('Carrier')) btn.click();
  });
  // Find and click the negotiation tab button
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes('negotiation')) {
      btn.click();
    }
  });
  runNegotiation(shipmentId, 'balanced');
}

function triggerColdChainReroute() {
  // Switch to negotiation tab and run the auction for SHP-1001
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes('negotiation')) {
      btn.click();
    }
  });
  runNegotiation('SHP-1001', 'most_reliable');
}

function awardBid(carrierId, carrierName) {
  alert(`Contract awarded to ${carrierName}. Dispatch instruction sent via system.`);
}

function dispatchFleetAsset(assetId, shipmentId) {
  alert(`Asset ${assetId} dispatched and redeployed to ${shipmentId}.`);
}

/* ─────────────────────────────────────────────
   TAB 5: IBM BoB DISPATCHER COPILOT
   API used:
     POST /api/copilot/brief
     Body: { "shipment_id": "SHP-1001" }
   Extracts shipment_id from user message if present,
   otherwise defaults to SHP-1001.
───────────────────────────────────────────── */
async function sendCopilotMsg() {
  const input = document.getElementById('chat-input');
  const query = input.value.trim();
  if (!query) return;

  const chatHist = document.getElementById('chat-history');

  // Render user bubble
  chatHist.innerHTML += `
    <div class="msg-bubble user">${query}</div>`;
  input.value = '';
  chatHist.scrollTop = chatHist.scrollHeight;

  // Show typing indicator
  const typingId = `typing-${Date.now()}`;
  chatHist.innerHTML += `
    <div class="msg-bubble assistant" id="${typingId}">
      <div class="grounded-badge">IBM BoB Copilot - Thinking...</div>
      Querying risk engine and cold chain monitor...
    </div>`;
  chatHist.scrollTop = chatHist.scrollHeight;

  // Extract shipment ID from query if mentioned (e.g. "SHP-1001" or "SHP-1003")
  const sidMatch = query.match(/SHP-\d+/i);
  const shipmentId = sidMatch ? sidMatch[0].toUpperCase() : 'SHP-1001';

  try {
    const res = await fetch(`${API_BASE}/copilot/brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shipment_id: shipmentId }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Remove typing indicator
    document.getElementById(typingId)?.remove();

    // Format grounding facts as a collapsible summary
    const facts = data.grounding_facts;
    const riskScore = facts?.risk_assessment?.score ?? '?';
    const riskBand  = facts?.risk_assessment?.band  ?? '?';
    const rerouteCount = facts?.reroute_options?.length ?? 0;
    const fleetCount   = facts?.fleet_redeployment_candidates?.length ?? 0;

    chatHist.innerHTML += `
      <div class="msg-bubble assistant">
        <div class="grounded-badge">
          IBM BoB Copilot - Grounded Response &nbsp;|&nbsp;
          Facts: Risk ${riskScore}/100 (${riskBand}),
          ${rerouteCount} reroute options,
          ${fleetCount} idle fleet assets
        </div>
        <div style="margin-top:0.5rem;line-height:1.7;">
          ${(data.brief || '').replace(/\n/g, '<br>')}
        </div>
      </div>`;
  } catch (err) {
    document.getElementById(typingId)?.remove();

    // Grounded offline fallback — never invents numbers
    chatHist.innerHTML += `
      <div class="msg-bubble assistant">
        <div class="grounded-badge">IBM BoB Copilot - Offline Stub</div>
        <div style="margin-top:0.5rem;line-height:1.7;color:var(--text-secondary);">
          Backend is offline (${err.message}). Start the server with:<br>
          <code style="font-size:0.8rem;">
            cd src/backend &amp;&amp;
            .venv\\Scripts\\uvicorn.exe app.main:app --reload --port 8000
          </code>
        </div>
      </div>`;
  }

  chatHist.scrollTop = chatHist.scrollHeight;
}
