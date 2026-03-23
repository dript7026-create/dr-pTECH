const stateEls = {
  tick: document.getElementById("tick"),
  consensus: document.getElementById("consensus"),
  knowledge: document.getElementById("knowledge"),
  reflection: document.getElementById("reflection-metric"),
  coherence: document.getElementById("coherence"),
  friction: document.getElementById("friction"),
  habitats: document.getElementById("habitats"),
  cohort: document.getElementById("cohort"),
  registry: document.getElementById("registry"),
  datasetTitle: document.getElementById("dataset-title"),
  datasetNote: document.getElementById("dataset-note"),
};

const controls = {
  steps: document.getElementById("steps"),
  curiosity: document.getElementById("curiosity"),
  equity: document.getElementById("equity"),
  challenge: document.getElementById("challenge"),
  reflection: document.getElementById("reflection"),
  stepOnce: document.getElementById("step-once"),
  toggleAuto: document.getElementById("toggle-auto"),
  reset: document.getElementById("reset"),
};

const canvas = document.getElementById("feed");
const ctx = canvas.getContext("2d");

const assetEls = {
  planetCore: document.getElementById("planet-core"),
  glyphUpper: document.getElementById("glyph-upper"),
  glyphLower: document.getElementById("glyph-lower"),
  glyphSymbols: document.getElementById("glyph-symbols"),
  streamMap: document.getElementById("stream-map"),
  nodeSheet: document.getElementById("node-sheet"),
  avatarSheet: document.getElementById("avatar-sheet"),
  signalSheet: document.getElementById("signal-sheet"),
};

let liveState = null;
let equationRegistry = null;
let datasetMeta = null;
let assetManifest = null;
let autoTimer = null;

function directivePayload() {
  return {
    curiosity_bias: Number(controls.curiosity.value),
    equity_bias: Number(controls.equity.value),
    challenge_bias: Number(controls.challenge.value),
    reflection_bias: Number(controls.reflection.value),
  };
}

function meter(value) {
  return Number(value).toFixed(3);
}

function renderStats(state) {
  stateEls.tick.textContent = state.tick;
  stateEls.consensus.textContent = meter(state.hub_consensus);
  stateEls.knowledge.textContent = meter(state.mean_knowledge);
  stateEls.reflection.textContent = meter(state.mean_reflection);
  stateEls.coherence.textContent = meter(state.mean_coherence);
  stateEls.friction.textContent = meter(state.friction);

  stateEls.habitats.innerHTML = "";
  state.habitats.forEach((habitat) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `
      <strong>${habitat.habitat_id}</strong>
      <div>stability ${meter(habitat.stability)} | nutrient ${meter(habitat.nutrient)}</div>
      <div>complexity ${meter(habitat.complexity)} | chemistry ${meter(habitat.chemistry)}</div>
      <div>biology ${meter(habitat.biology)} | physics ${meter(habitat.physics)}</div>
    `;
    stateEls.habitats.appendChild(node);
  });

  stateEls.cohort.innerHTML = "";
  state.agents.slice(0, 8).forEach((agent) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `
      <strong>${agent.agent_id}</strong>
      <div>${agent.lifecycle_stage} | ${agent.specialization}</div>
      <div>knowledge ${meter(agent.knowledge)} | trust ${meter(agent.trust)} | stress ${meter(agent.stress)}</div>
    `;
    stateEls.cohort.appendChild(node);
  });
}

function renderRegistry(registry) {
  stateEls.registry.innerHTML = "";
  registry.equations.forEach((equation) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `<strong>${equation.key}</strong><div>${equation.expression}</div><div>${equation.description}</div>`;
    stateEls.registry.appendChild(node);
  });
}

function drawFeed() {
  if (!liveState) {
    return;
  }

  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "rgba(127,255,212,0.08)");
  gradient.addColorStop(1, "rgba(233,114,76,0.04)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  const habitats = liveState.habitats;
  const agents = liveState.agents;
  const orbitY = height * 0.56;
  const baseRadius = Math.min(width, height) * 0.24;

  ctx.strokeStyle = "rgba(232,240,231,0.12)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(width / 2, orbitY, baseRadius + 24, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = "rgba(232,240,231,0.85)";
  ctx.font = "13px Consolas";
  ctx.fillText(liveState.dataset_title, 28, 28);

  habitats.forEach((habitat, index) => {
    const angle = (Math.PI * 2 * index) / habitats.length - Math.PI / 2;
    const x = width / 2 + Math.cos(angle) * baseRadius;
    const y = orbitY + Math.sin(angle) * baseRadius * 0.68;
    const intensity = 0.35 + habitat.nutrient * 0.5;

    ctx.beginPath();
    ctx.fillStyle = `rgba(127,255,212,${intensity})`;
    ctx.arc(x, y, 18 + habitat.complexity * 24, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "rgba(232,240,231,0.25)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(x, y, 30 + habitat.stability * 16, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "rgba(232,240,231,0.85)";
    ctx.font = "12px Consolas";
    ctx.fillText(habitat.habitat_id, x - 28, y + 4);
  });

  agents.forEach((agent, index) => {
    const habitatIndex = habitats.findIndex((habitat) => habitat.habitat_id === agent.habitat_id);
    const angle = (Math.PI * 2 * habitatIndex) / habitats.length - Math.PI / 2;
    const x = width / 2 + Math.cos(angle) * baseRadius + ((index % 4) - 1.5) * 18;
    const y = orbitY + Math.sin(angle) * baseRadius * 0.68 + ((index % 3) - 1) * 20;
    const size = 6 + agent.knowledge * 10;

    ctx.fillStyle = `rgba(255,209,102,${0.25 + agent.awareness * 0.55})`;
    ctx.fillRect(x - size / 2, y - size / 2, size, size);
  });

  const chartLeft = 48;
  const chartBottom = 84;
  const chartWidth = width - 96;
  const metrics = [
    ["consensus", liveState.hub_consensus, "#7fffd4"],
    ["knowledge", liveState.mean_knowledge, "#ffd166"],
    ["reflection", liveState.mean_reflection, "#f4f1de"],
    ["coherence", liveState.mean_coherence, "#e9724c"],
  ];

  metrics.forEach(([label, value, color], index) => {
    const x = chartLeft + index * (chartWidth / metrics.length) + 28;
    const barHeight = value * 120;
    ctx.fillStyle = color;
    ctx.fillRect(x, chartBottom + 120 - barHeight, 42, barHeight);
    ctx.fillStyle = "rgba(232,240,231,0.8)";
    ctx.font = "12px Consolas";
    ctx.fillText(label, x - 6, chartBottom + 142);
  });
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  return response.json();
}

async function refreshState() {
  liveState = await fetchJson("/api/state");
  renderStats(liveState);
  drawFeed();
}

async function loadRegistry() {
  equationRegistry = await fetchJson("/api/registry");
  renderRegistry(equationRegistry);
}

async function loadDataset() {
  datasetMeta = await fetchJson("/api/dataset");
  stateEls.datasetTitle.textContent = `${datasetMeta.title} (${datasetMeta.agent_count} agents / ${datasetMeta.habitat_count} habitats)`;
  stateEls.datasetNote.textContent = datasetMeta.note;
}

async function loadAssets() {
  assetManifest = await fetchJson("/api/assets");
  assetEls.planetCore.src = assetManifest.planet_core;
  assetEls.glyphUpper.src = assetManifest.glyph_upper;
  assetEls.glyphLower.src = assetManifest.glyph_lower;
  assetEls.glyphSymbols.src = assetManifest.glyph_symbols;
  assetEls.streamMap.src = assetManifest.stream_map;
  assetEls.nodeSheet.src = assetManifest.node_sheet;
  assetEls.avatarSheet.src = assetManifest.avatar_sheet;
  assetEls.signalSheet.src = assetManifest.signal_sheet;
}

async function stepSimulation() {
  liveState = await fetchJson("/api/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      steps: Number(controls.steps.value),
      directive: directivePayload(),
    }),
  });
  renderStats(liveState);
  drawFeed();
}

async function resetSimulation() {
  liveState = await fetchJson("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed: 11, agent_count: 18, habitat_count: 4 }),
  });
  renderStats(liveState);
  drawFeed();
}

controls.stepOnce.addEventListener("click", stepSimulation);
controls.reset.addEventListener("click", resetSimulation);
controls.toggleAuto.addEventListener("click", () => {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    controls.toggleAuto.textContent = "Auto run";
    return;
  }
  autoTimer = setInterval(stepSimulation, 1200);
  controls.toggleAuto.textContent = "Pause";
});

window.addEventListener("resize", drawFeed);

Promise.all([refreshState(), loadRegistry(), loadDataset(), loadAssets()]);