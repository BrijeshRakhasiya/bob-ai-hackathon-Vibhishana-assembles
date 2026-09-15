/* RouteGuard AI  -  Control Tower App Logic */

const API_BASE = 'http://localhost:8000/api';

// Seeded Data for Fallback & Instant Preview
const mockShipments = [
  {
    id: "SH-408",
    origin: "Mumbai Port",
    destination: "Ahmedabad DC",
    cargo: "Polio Vaccines (Cold Chain)",
    value: "Rs 45,000,000",
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
    id: "TRK-8821",
    type: "Refrigerated Container 32ft",
    location: "Surat Logistics Park (28 km away)",
    status: "Idle - Available",
    matchScore: "96%",
    driver: "Rajesh Kumar (Active Duty)"
  },
  {
    id: "TRK-4402",
    type: "Multi-Axle Flatbed",
    location: "Vapi Depot (14 km away)",
    status: "Idle - Available",
    matchScore: "88%",
    driver: "Suresh Patel (Available)"
  },
  {
    id: "TRK-1099",
    type: "Refrigerated Container 24ft",
    location: "Vadodara Hub (75 km away)",
    status: "Idle - Standby",
    matchScore: "82%",
    driver: "Amit Shah (Standby)"
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

// Tab Switcher
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  event.currentTarget.classList.add('active');
  document.getElementById(`tab-${tabId}`).classList.add('active');
}

// Render Shipments
function renderShipments() {
  const tbody = document.getElementById("shipments-tbody");
  tbody.innerHTML = mockShipments.map(s => {
    let badgeClass = s.riskScore > 75 ? "badge-critical" : s.riskScore > 40 ? "badge-warning" : "badge-safe";
    return `
      <tr>
        <td style="font-family: var(--font-code); font-weight: 600; color: var(--accent-blue);">${s.id}</td>
        <td>${s.origin} to ${s.destination}</td>
        <td>${s.cargo}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${s.value}</span></td>
        <td>
          <span class="badge ${badgeClass}">${s.riskScore} / 100</span>
        </td>
        <td>${s.status}</td>
        <td>
          <button class="btn-action" onclick="openRerouteModal('${s.id}')">Reroute & Negotiate</button>
        </td>
      </tr>
    `;
  }).join('');
}

// Render Disruptions
function renderDisruptions() {
  const container = document.getElementById("disruption-feed-list");
  container.innerHTML = mockDisruptions.map(d => {
    let badge = d.severity === 'CRITICAL' ? 'badge-critical' : d.severity === 'HIGH' ? 'badge-warning' : 'badge-blue';
    return `
      <div style="background: var(--bg-surface-elevated); padding: 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <strong style="font-size: 0.9rem;">${d.title}</strong>
          <span class="badge ${badge}">${d.severity}</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
          Location: ${d.location}  -  ${d.impactedShipments} active shipments affected
        </div>
        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 4px; font-family: var(--font-code);">
          Source: ${d.source}
        </div>
      </div>
    `;
  }).join('');
}

// Render Cold Chain Telemetry Chart
function renderColdChainChart() {
  const container = document.getElementById("sensor-chart");
  const maxTemp = 12;
  container.innerHTML = mockTelemetry.map(t => {
    let heightPercent = (t.temp / maxTemp) * 100;
    return `
      <div class="chart-bar-wrap">
        <div class="bar-val" style="color: ${t.status === 'breach' ? 'var(--status-critical)' : 'var(--text-primary)'};">${t.temp} degC</div>
        <div class="chart-bar ${t.status}" style="height: ${heightPercent}%;"></div>
        <div class="bar-time">${t.time}</div>
      </div>
    `;
  }).join('');
}

// Render CrewAI Bids
function renderBids() {
  const container = document.getElementById("bidding-container");
  container.innerHTML = mockBids.map(b => `
    <div class="bidder-card ${b.isWinner ? 'winner' : ''}">
      <div>
        <div class="bidder-name">
          <span>${b.carrier}</span>
          ${b.isWinner ? '<span class="badge badge-safe">WINNING BID</span>' : ''}
        </div>
        <div class="bid-metrics">
          <div class="metric-item">
            <span style="font-size: 0.7rem; color: var(--text-muted);">Bid Amount</span>
            <div class="val" style="color: var(--accent-blue);">${b.price}</div>
          </div>
          <div class="metric-item">
            <span style="font-size: 0.7rem; color: var(--text-muted);">Time Saved</span>
            <div class="val" style="color: var(--status-safe);">${b.timeSaved}</div>
          </div>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          SLA Score: <strong>${b.slaScore}</strong>
        </div>
      </div>
      <button class="btn-action" style="margin-top: 1rem; width: 100%;" onclick="awardBid('${b.carrier}')">
        ${b.isWinner ? 'Contract Awarded' : 'Select Alternative'}
      </button>
    </div>
  `).join('');
}

// Render Fleet
function renderFleet() {
  const tbody = document.getElementById("fleet-tbody");
  tbody.innerHTML = mockFleet.map(f => `
    <tr>
      <td style="font-family: var(--font-code); font-weight: 600;">${f.id}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${f.type}</span></td>
      <td>${f.location}</td>
      <td>${f.driver}<br><span class="badge badge-safe">${f.status}</span></td>
      <td style="font-family: var(--font-code);">${f.location.split('(')[1] ? f.location.split('(')[1].replace(')', '') : '15 km'}</td>
      <td><span class="badge badge-blue">${f.matchScore}</span></td>
      <td>
        <button class="btn-action" onclick="dispatchFleetAsset('${f.id}')">Redeploy to SH-408</button>
      </td>
    </tr>
  `).join('');
}

// Reroute Modal Logic
function openRerouteModal(shipmentId) {
  const modal = document.getElementById("reroute-modal");
  document.getElementById("modal-shipment-title").innerText = `Reroute Engine: ${shipmentId}`;
  
  const corridorList = document.getElementById("modal-corridor-list");
  corridorList.innerHTML = `
    <div style="background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--accent-blue);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <strong style="color: var(--accent-blue);">Corridor A: Expressway Bypass via Vadodara-Godhra</strong>
        <span class="badge badge-safe">RECOMMENDED</span>
      </div>
      <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">
        Bypasses NH-48 flood point. Additional distance: +42 km. Estimated ETA reduction: <strong>3.5 hours</strong>. Post-reroute Risk: <strong>14/100</strong>.
      </p>
      <button class="btn-action" style="margin-top: 0.75rem;" onclick="confirmReroute('Corridor A')">Confirm Reroute Corridor</button>
    </div>

    <div style="background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <strong>Corridor B: State Highway 17 Coastal Detour</strong>
        <span class="badge badge-warning">MODERATE RISK</span>
      </div>
      <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">
        Higher toll charges. Additional distance: +78 km. Post-reroute Risk: <strong>38/100</strong>.
      </p>
    </div>
  `;
  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("reroute-modal").classList.remove("active");
}

function confirmReroute(corridor) {
  alert(`Shipment SH-408 rerouted via ${corridor}. Multi-Agent auction initiated.`);
  closeModal();
  switchTab('negotiation');
}

function triggerColdChainReroute() {
  alert("Emergency Cold Chain Reroute Protocol Initiated for SH-408. Re-routing to nearest refrigerated fulfillment hub in Surat.");
  switchTab('negotiation');
}

function awardBid(carrier) {
  alert(`Contract awarded to ${carrier}. Dispatch instruction sent.`);
}

function dispatchFleetAsset(assetId) {
  alert(`Asset ${assetId} dispatched and redeployed to SH-408.`);
}

// IBM BoB Copilot Chat Logic
async function sendCopilotMsg() {
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  const chatHist = document.getElementById("chat-history");
  
  // Add User Bubble
  chatHist.innerHTML += `
    <div class="msg-bubble user">
      ${query}
    </div>
  `;
  input.value = "";
  chatHist.scrollTop = chatHist.scrollHeight;

  // Call Backend API or Fallback
  try {
    const res = await fetch(`${API_BASE}/copilot/brief`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, shipment_id: "SH-408" })
    });
    
    if (res.ok) {
      const data = await res.json();
      chatHist.innerHTML += `
        <div class="msg-bubble assistant">
          <div class="grounded-badge">IBM BoB Copilot  -  Live Grounded Brief</div>
          ${data.brief || data.response}
        </div>
      `;
    } else {
      throw new Error("API Offline");
    }
  } catch (e) {
    // Grounded Fallback Response
    let reply = `Based on computed risk data for <strong>SH-408 (Polio Vaccines)</strong>:
    <br>- <strong>Risk Score:</strong> 88/100 (Critical)
    <br>- <strong>Primary Disruption:</strong> NH-48 Waterlogging at Vapi (Delay delta: +5.2 hrs)
    <br>- <strong>Cold Chain Status:</strong> Excursion detected (9.4 degC peak, WHO Severity Class: Critical Regulatory Breach)
    <br>- <strong>Recommendation:</strong> Reroute via Corridor A (Vadodara-Godhra Bypass) and award contract to FastFreight Express (Saved time: 4.5 hrs, Cost delta: Rs 48,000).`;
    
    chatHist.innerHTML += `
      <div class="msg-bubble assistant">
        <div class="grounded-badge">IBM BoB Copilot  -  Grounded Brief Engine</div>
        ${reply}
      </div>
    `;
  }
  
  chatHist.scrollTop = chatHist.scrollHeight;
}
