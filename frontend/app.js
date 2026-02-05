const apiBaseInput = document.getElementById("apiBase");
const healthBtn = document.getElementById("healthBtn");
const healthStatus = document.getElementById("healthStatus");
const analyzeForm = document.getElementById("analyzeForm");
const analysisOutput = document.getElementById("analysisOutput");
const summarySection = document.getElementById("summarySection");
const riskCards = document.getElementById("riskCards");
const actionPlan = document.getElementById("actionPlan");
const summaryMeta = document.getElementById("summaryMeta");
const historyOutput = document.getElementById("historyOutput");
const refreshHistory = document.getElementById("refreshHistory");

const stringify = (obj) => JSON.stringify(obj, null, 2);

const getBaseUrl = () => apiBaseInput.value.replace(/\/+$/, "");

const setStatus = (text, ok = true) => {
  healthStatus.textContent = text;
  healthStatus.style.color = ok ? "#16a34a" : "#dc2626";
};

healthBtn.addEventListener("click", async () => {
  setStatus("Checking...");
  try {
    const res = await fetch(`${getBaseUrl()}/health`);
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

  const labReport = document.getElementById("labReport").files[0];
  const retinalImage = document.getElementById("retinalImage").files[0];

  if (!labReport) {
    analysisOutput.textContent = "Lab report is required.";
    return;
  }

  const formData = new FormData();
  formData.append("lab_report", labReport);
  if (retinalImage) {
    formData.append("retinal_image", retinalImage);
  }

  try {
    const res = await fetch(`${getBaseUrl()}/api/analyze`, {
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
    const res = await fetch(`${getBaseUrl()}/api/history?limit=5`);
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
  summaryMeta.textContent = data.retinal?.grade
    ? `Retinal grade: ${data.retinal.grade}`
    : "Retinal grade: N/A";

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
