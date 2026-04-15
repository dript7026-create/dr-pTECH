const form = document.getElementById("planner-form");
const signalGrid = document.getElementById("signal-grid");
const windowList = document.getElementById("window-list");
const draftList = document.getElementById("draft-list");
const marketPosture = document.getElementById("market-posture");
const overallScore = document.getElementById("overall-score");
const resetButton = document.getElementById("reset-defaults");

let defaults = null;

function sliderRow(name, value) {
  const label = document.createElement("label");
  label.className = "slider-card";
  label.innerHTML = `
    <div class="slider-head">
      <span>${name.replaceAll("_", " ")}</span>
      <strong id="${name}_value">${Number(value).toFixed(2)}</strong>
    </div>
    <input id="${name}" name="${name}" type="range" min="0" max="1" step="0.01" value="${value}">
  `;

  const input = label.querySelector("input");
  const valueNode = label.querySelector("strong");
  input.addEventListener("input", () => {
    valueNode.textContent = Number(input.value).toFixed(2);
  });
  return label;
}

function fillProfile(profile) {
  Object.entries(profile).forEach(([key, value]) => {
    const field = document.getElementById(key);
    if (field) {
      field.value = value;
    }
  });
}

function fillSignals(signals) {
  signalGrid.innerHTML = "";
  Object.entries(signals).forEach(([key, value]) => {
    signalGrid.appendChild(sliderRow(key, value));
  });
}

function collectProfile() {
  return {
    brand_name: document.getElementById("brand_name").value,
    product_name: document.getElementById("product_name").value,
    audience: document.getElementById("audience").value,
    offer: document.getElementById("offer").value,
    tone: document.getElementById("tone").value,
    cta: document.getElementById("cta").value,
    landing_page: document.getElementById("landing_page").value,
  };
}

function collectSignals() {
  const signals = {};
  signalGrid.querySelectorAll("input[type='range']").forEach((input) => {
    signals[input.name] = Number(input.value);
  });
  return signals;
}

function renderWindows(windows) {
  windowList.innerHTML = "";
  windows.forEach((window, index) => {
    const node = document.createElement("article");
    node.className = "window-card";
    node.innerHTML = `
      <div class="window-rank">${index + 1}</div>
      <div>
        <div class="window-header">
          <strong>${window.label}</strong>
          <span>${window.clock}</span>
        </div>
        <div class="window-meta">score ${window.score.toFixed(3)} | ${window.format_bias}</div>
        <p>${window.rationale}</p>
      </div>
    `;
    windowList.appendChild(node);
  });
}

function renderList(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function renderDrafts(drafts) {
  draftList.innerHTML = "";
  drafts.forEach((draft) => {
    const previewBlock = draft.render_assets && draft.render_assets.poster_path
      ? `
        <section class="preview-panel">
          <h3>Rendered preview</h3>
          <div class="preview-meta">${draft.render_assets.mode}</div>
          ${draft.render_assets.video_path
            ? `<video controls loop muted playsinline preload="metadata" poster="${draft.render_assets.poster_path}">
                 <source src="${draft.render_assets.video_path}" type="video/mp4">
               </video>`
            : `<img src="${draft.render_assets.poster_path}" alt="Rendered poster preview for ${draft.slot_label}">`}
        </section>
      `
      : "";
    const node = document.createElement("article");
    node.className = "draft-card";
    node.innerHTML = `
      <div class="draft-topline">
        <span>${draft.slot_label}</span>
        <strong>${draft.hook}</strong>
      </div>
      <p class="angle">${draft.creative_angle}</p>
      ${previewBlock}
      <div class="draft-grid">
        <section>
          <h3>Short script</h3>
          ${renderList(draft.short_script)}
        </section>
        <section>
          <h3>Long script</h3>
          ${renderList(draft.long_script)}
        </section>
        <section>
          <h3>Visual direction</h3>
          ${renderList(draft.visual_direction)}
        </section>
        <section>
          <h3>Shot plan</h3>
          ${renderList(draft.shot_plan)}
        </section>
        <section>
          <h3>Asset checklist</h3>
          ${renderList(draft.asset_checklist)}
        </section>
        <section>
          <h3>Caption</h3>
          <p>${draft.caption}</p>
          <div class="tags">${draft.hashtags.map((tag) => `<span>${tag}</span>`).join("")}</div>
          <p class="cta-line">CTA: ${draft.call_to_action}</p>
        </section>
      </div>
    `;
    draftList.appendChild(node);
  });
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  return response.json();
}

async function loadDefaults() {
  defaults = await fetchJson("/api/defaults");
  fillProfile(defaults.profile);
  fillSignals(defaults.signals);
}

async function generatePlan() {
  const payload = {
    profile: collectProfile(),
    signals: collectSignals(),
    render_previews: true,
  };
  const plan = await fetchJson("/api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  marketPosture.textContent = plan.market_posture;
  overallScore.textContent = plan.overall_score.toFixed(3);
  renderWindows(plan.recommended_windows);
  renderDrafts(plan.drafts);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await generatePlan();
});

resetButton.addEventListener("click", async () => {
  await loadDefaults();
  await generatePlan();
});

Promise.all([loadDefaults(), fetchJson("/api/catalog")]).then(generatePlan);