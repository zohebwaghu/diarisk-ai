const apiBaseInput = document.getElementById("apiBase");
const healthBtn = document.getElementById("healthBtn");
const healthStatus = document.getElementById("healthStatus");
const analyzeForm = document.getElementById("analyzeForm");
const analysisOutput = document.getElementById("analysisOutput");
const summarySection = document.getElementById("summarySection");
const riskCards = document.getElementById("riskCards");
const actionPlan = document.getElementById("actionPlan");
const summaryMeta = document.getElementById("summaryMeta");
const labInsights = document.getElementById("labInsights");
const agentTrace = document.getElementById("agentTrace");
const riskTrend = document.getElementById("riskTrend");
const trendMeta = document.getElementById("trendMeta");
const vitalsGrid = document.getElementById("vitalsGrid");
const historyOutput = document.getElementById("historyOutput");
const refreshHistory = document.getElementById("refreshHistory");

const stringify = (obj) => JSON.stringify(obj, null, 2);

const getBaseUrl = () => apiBaseInput.value.trim().replace(/\/+$/, "");

const buildUrl = (path) => {
  const base = getBaseUrl();
  if (!base) return path;
  if (path === "/api/health") return `${base}/health`;
  return `${base}${path}`;
};

const setStatus = (text, ok = true) => {
  healthStatus.textContent = text;
  healthStatus.style.color = ok ? "#16a34a" : "#dc2626";
};

healthBtn.addEventListener("click", async () => {
  setStatus("Checking...");
  try {
    const res = await fetch(buildUrl("/api/health"));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    setStatus(`OK (${data.status})`, true);
  } catch (err) {
    setStatus(`Error: ${err.message}`, false);
  }
});

analyzeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  analysisOutput.textContent = "Running analysis...";
  summarySection.classList.add("hidden");
  riskCards.innerHTML = "";
  actionPlan.innerHTML = "";
  summaryMeta.textContent = "";
  labInsights.innerHTML = "";
  agentTrace.innerHTML = "";
  riskTrend.innerHTML = "";
  trendMeta.textContent = "—";
  vitalsGrid.innerHTML = "";

  const labReport = document.getElementById("labReport").files[0];
  const retinalImage = document.getElementById("retinalImage").files[0];
  const cognitiveNotes = document.getElementById("cognitiveNotes").value.trim();

  if (!labReport) {
    analysisOutput.textContent = "Lab report is required.";
    return;
  }

  const formData = new FormData();
  formData.append("lab_report", labReport);
  if (retinalImage) {
    formData.append("retinal_image", retinalImage);
  }
  if (cognitiveNotes) {
    formData.append("cognitive_notes", cognitiveNotes);
  }

  try {
    const res = await fetch(buildUrl("/api/analyze"), {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderSummary(data);
    analysisOutput.textContent = stringify(data);
  } catch (err) {
    analysisOutput.textContent = `Error: ${err.message}`;
  }
});

refreshHistory.addEventListener("click", async () => {
  historyOutput.textContent = "Loading history...";
  try {
    const res = await fetch(buildUrl("/api/history?limit=5"));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    historyOutput.textContent = stringify(data);
  } catch (err) {
    historyOutput.textContent = `Error: ${err.message}`;
  }
});

refreshHistory.click();

const renderSummary = (data) => {
  if (!data || !data.risk_scores) return;
  summarySection.classList.remove("hidden");
  const retinalLabel = data.retinal?.grade ? `Retinal grade: ${data.retinal.grade}` : "Retinal grade: N/A";
  const cognitiveLabel =
    data.cognitive?.score !== undefined && data.cognitive?.score !== null
      ? `Cognitive score: ${data.cognitive.score}/5`
      : "Cognitive score: N/A";
  summaryMeta.textContent = `${retinalLabel} • ${cognitiveLabel}`;

  if (data.lab_insights) {
    const highlights = (data.lab_insights.highlights || []).map((item) => `<li>${item}</li>`).join("");
    labInsights.innerHTML = `
      <div class="lab-summary">${data.lab_insights.summary || "Lab highlights"}</div>
      ${highlights ? `<ul class="lab-list">${highlights}</ul>` : ""}
    `;
  } else {
    labInsights.innerHTML = "";
  }

  const riskMap = {
    dementia: "Dementia",
    cardiovascular: "Cardiovascular",
    retinopathy: "Retinopathy",
    nephropathy: "Nephropathy",
    neuropathy: "Neuropathy",
  };

  Object.entries(riskMap).forEach(([key, label]) => {
    const risk = data.risk_scores[key];
    if (!risk) return;
    const card = document.createElement("div");
    card.className = "risk-card";
    card.innerHTML = `
      <div class="risk-title">${label}</div>
      <div class="risk-score">${Math.round(risk.score)}%</div>
      <div class="risk-level ${risk.level.toLowerCase()}">${risk.level}</div>
      <div class="risk-factors">${(risk.key_factors || []).slice(0, 2).join(" • ")}</div>
    `;
    riskCards.appendChild(card);
  });

  renderTrend(data.risk_scores);
  renderVitals(data);
  renderTrace(data.agent_trace || []);

  const recommendations = data.recommendations || [];
  if (!recommendations.length) {
    actionPlan.innerHTML = "<p>No recommendations generated.</p>";
    return;
  }

  actionPlan.innerHTML = recommendations
    .map(
      (rec) => `
        <div class="action-item">
          <div class="action-title">${rec.title}</div>
          <div class="action-impact">${rec.expected_impact}</div>
          <div class="action-rationale">${rec.rationale}</div>
        </div>
      `
    )
    .join("");
};

const renderTrend = (riskScores) => {
  const values = Object.values(riskScores || {})
    .map((risk) => risk?.score)
    .filter((value) => typeof value === "number");
  const average = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  trendMeta.textContent = `${Math.round(average)}% avg`;
  const bars = Array.from({ length: 24 }).map((_, i) => {
    const wave = Math.sin(i / 3) * 8;
    const base = average || 20;
    const value = Math.max(8, Math.min(100, base + wave + (i % 5) * 0.6));
    return value;
  });
  riskTrend.innerHTML = bars
    .map((value) => `<div class="spark-bar" style="height:${value}%;"></div>`)
    .join("");
};

const renderVitals = (data) => {
  const labs = data.labs?.values || {};
  const entries = [
    { label: "A1C", value: labs.a1c ? `${labs.a1c}%` : "—" },
    { label: "eGFR", value: labs.egfr ? `${labs.egfr}` : "—" },
    { label: "LDL", value: labs.ldl ? `${labs.ldl}` : "—" },
    {
      label: "Blood Pressure",
      value:
        labs.systolic_bp && labs.diastolic_bp ? `${labs.systolic_bp}/${labs.diastolic_bp}` : "—",
    },
    { label: "Retinal Grade", value: data.retinal?.grade || "—" },
    {
      label: "Cognitive Score",
      value: data.cognitive?.score !== undefined && data.cognitive?.score !== null ? `${data.cognitive.score}/5` : "—",
    },
  ];
  vitalsGrid.innerHTML = entries
    .map(
      (entry) => `
        <div class="vital-card">
          <div class="vital-label">${entry.label}</div>
          <div class="vital-value">${entry.value}</div>
        </div>
      `
    )
    .join("");
};

const renderTrace = (traceItems) => {
  if (!traceItems.length) {
    agentTrace.innerHTML = "<p>No agent trace available.</p>";
    return;
  }
  agentTrace.innerHTML = traceItems
    .map((item) => {
      const duration = item.duration_ms !== null && item.duration_ms !== undefined ? `${item.duration_ms} ms` : "";
      const notes = item.notes ? `<div class="trace-notes">${item.notes}</div>` : "";
      return `
        <div class="trace-item trace-${item.status}">
          <div class="trace-title">${item.agent}</div>
          <div class="trace-meta">${item.status.toUpperCase()} • ${duration}</div>
          ${notes}
        </div>
      `;
    })
    .join("");
};
