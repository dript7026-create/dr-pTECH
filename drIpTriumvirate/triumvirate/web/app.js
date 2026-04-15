/* ─── drIpTriumvirate — main application logic ─── */

(function () {
  "use strict";

  // ── Helpers ──
  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

  function post(url, body) {
    return fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  function esc(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
  }

  // ── State ──
  const feel = {
    urgency: 0.5, trust: 0.5, wonder: 0.5,
    tenderness: 0.5, grit: 0.5, clarity: 0.5, volatility: 0.5,
  };
  let lastSignals = null;
  let lastPlan = null;
  let bootTime = Date.now();

  // ══════════════════════════════════════════════
  //  DIALS — rotary knobs drawn on <canvas>
  // ══════════════════════════════════════════════

  const dials = document.querySelectorAll(".dial");

  function drawDial(canvas, value, color) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(cx, cy) - 6;
    ctx.clearRect(0, 0, w, h);

    // Track ring
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
    ctx.strokeStyle = "rgba(0, 255, 65, 0.12)";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.stroke();

    // Value arc
    const startAngle = 0.75 * Math.PI;
    const endAngle = startAngle + value * 1.5 * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = color || "#00ff41";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.stroke();

    // Glow
    ctx.shadowColor = color || "#00ff41";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(cx, cy, r, endAngle - 0.05, endAngle);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Indicator dot
    const dotX = cx + Math.cos(endAngle) * r;
    const dotY = cy + Math.sin(endAngle) * r;
    ctx.beginPath();
    ctx.arc(dotX, dotY, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();

    // Center value
    ctx.font = "bold 11px Courier New, monospace";
    ctx.fillStyle = color || "#00ff41";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(value.toFixed(2), cx, cy);
  }

  function initDials() {
    dials.forEach(function (dial) {
      const key = dial.dataset.feel;
      const canvas = dial.querySelector(".dial-canvas");
      const valEl = dial.querySelector(".dial-val");
      let dragging = false;
      let startY = 0;
      let startValue = 0;

      function update(v) {
        v = Math.max(0, Math.min(1, v));
        feel[key] = Math.round(v * 100) / 100;
        valEl.textContent = feel[key].toFixed(2);
        const colors = {
          urgency: "#ff3333", trust: "#00ff41", wonder: "#00f0ff",
          tenderness: "#ff88cc", grit: "#ffaa00", clarity: "#ffffff", volatility: "#ff00ff",
        };
        drawDial(canvas, feel[key], colors[key] || "#00ff41");
      }

      dial.addEventListener("mousedown", function (e) {
        dragging = true;
        startY = e.clientY;
        startValue = feel[key];
        e.preventDefault();
      });

      window.addEventListener("mousemove", function (e) {
        if (!dragging) return;
        const delta = (startY - e.clientY) / 120;
        update(startValue + delta);
      });

      window.addEventListener("mouseup", function () {
        if (dragging) {
          dragging = false;
          translateSignals();
        }
      });

      // Mouse wheel
      dial.addEventListener("wheel", function (e) {
        e.preventDefault();
        update(feel[key] + (e.deltaY < 0 ? 0.02 : -0.02));
        translateSignals();
      });

      update(feel[key]);
    });
  }

  // ══════════════════════════════════════════════
  //  CONTEXT SLIDERS + WEATHER + PULSE
  // ══════════════════════════════════════════════

  const ctxSliders = {
    hour: document.getElementById("ctx-hour"),
    energy: document.getElementById("ctx-energy"),
    audience: document.getElementById("ctx-audience"),
    freshness: document.getElementById("ctx-freshness"),
    noise: document.getElementById("ctx-noise"),
  };

  const ctxValues = {
    hour: document.getElementById("ctx-hour-val"),
    energy: document.getElementById("ctx-energy-val"),
    audience: document.getElementById("ctx-audience-val"),
    freshness: document.getElementById("ctx-freshness-val"),
    noise: document.getElementById("ctx-noise-val"),
  };

  Object.keys(ctxSliders).forEach(function (key) {
    const slider = ctxSliders[key];
    if (!slider) return;
    slider.addEventListener("input", function () {
      ctxValues[key].textContent = Number(slider.value).toFixed(key === "hour" ? 1 : 2);
    });
  });

  // Weather buttons
  document.querySelectorAll(".btn-weather").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".btn-weather").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
    });
  });

  // Pulse button — sends context to server, gets back feel state, updates dials
  document.getElementById("btn-pulse").addEventListener("click", async function () {
    const weather = document.querySelector(".btn-weather.active");
    const body = {
      hour: Number(ctxSliders.hour.value),
      day_energy: Number(ctxSliders.energy.value),
      audience_pulse: Number(ctxSliders.audience.value),
      content_freshness: Number(ctxSliders.freshness.value),
      platform_noise: Number(ctxSliders.noise.value),
      weather: weather ? weather.dataset.weather : "clear",
    };

    const data = await post("/api/live/context", body);
    if (data.feel) {
      Object.keys(data.feel).forEach(function (key) {
        if (key in feel) {
          feel[key] = data.feel[key];
        }
      });
      refreshDials();
      translateSignals();
    }
    if (data.uptime_seconds != null) {
      bootTime = Date.now() - data.uptime_seconds * 1000;
    }
  });

  function refreshDials() {
    dials.forEach(function (dial) {
      const key = dial.dataset.feel;
      const canvas = dial.querySelector(".dial-canvas");
      const valEl = dial.querySelector(".dial-val");
      valEl.textContent = feel[key].toFixed(2);
      const colors = {
        urgency: "#ff3333", trust: "#00ff41", wonder: "#00f0ff",
        tenderness: "#ff88cc", grit: "#ffaa00", clarity: "#ffffff", volatility: "#ff00ff",
      };
      drawDial(canvas, feel[key], colors[key] || "#00ff41");
    });
  }

  // ══════════════════════════════════════════════
  //  SIGNAL TRANSLATION
  // ══════════════════════════════════════════════

  const signalFlow = document.getElementById("signal-flow");
  const signalBars = document.getElementById("signal-bars");
  const resonanceFill = document.getElementById("resonance-fill");
  const resonanceValue = document.getElementById("resonance-value");

  async function translateSignals() {
    appendFlow("> translating feel → signals...");
    const data = await post("/api/signals/translate", feel);
    lastSignals = data.signals;

    // Flow lines
    Object.keys(data.trace || {}).forEach(function (sig) {
      const drivers = data.trace[sig];
      if (drivers.length > 0) {
        const top = drivers[0];
        appendFlow("  " + sig + " ← " + top.feel + " (" + top.contribution.toFixed(3) + ")");
      }
    });
    appendFlow("> resonance: " + (data.resonance || 0).toFixed(3), "hot");

    // Bars
    renderSignalBars(data.signals);

    // Resonance
    const res = data.resonance || 0;
    resonanceFill.style.width = (res * 100) + "%";
    resonanceValue.textContent = res.toFixed(3);

    // Update matrix rain color to dominant feel dimension
    if (window.matrixRain) {
      const feelEntries = Object.entries(feel);
      const dominant = feelEntries.reduce(function (best, cur) { return cur[1] > best[1] ? cur : best; });
      window.matrixRain.setFeelColor(dominant[0]);
    }
  }

  function appendFlow(text, cls) {
    const line = document.createElement("div");
    line.className = "flow-line" + (cls ? " " + cls : "");
    line.textContent = text;
    signalFlow.appendChild(line);
    // Keep max 40 lines
    while (signalFlow.children.length > 40) {
      signalFlow.removeChild(signalFlow.firstChild);
    }
    signalFlow.scrollTop = signalFlow.scrollHeight;
  }

  const SIGNAL_NAMES = [
    "trend_momentum", "audience_match", "proof_strength",
    "novelty_gap", "fatigue_risk", "conversion_intent", "retention_pull",
  ];

  function renderSignalBars(signals) {
    signalBars.innerHTML = "";
    SIGNAL_NAMES.forEach(function (name) {
      const val = signals[name] || 0;
      const row = document.createElement("div");
      row.className = "signal-bar-row";
      row.innerHTML =
        '<span class="bar-label">' + esc(name.replace(/_/g, " ")) + "</span>" +
        '<div class="bar-track"><div class="bar-fill" style="width:' + (val * 100) + '%"></div></div>' +
        '<span class="bar-value">' + val.toFixed(3) + "</span>";
      signalBars.appendChild(row);
    });
  }

  // ══════════════════════════════════════════════
  //  PLAN GENERATION
  // ══════════════════════════════════════════════

  const studioOutput = document.getElementById("studio-output");

  document.getElementById("btn-generate").addEventListener("click", async function () {
    studioOutput.innerHTML = '<div class="flow-line">> generating campaign plan...</div>';

    const profile = {
      brand_name: document.getElementById("p-brand").value,
      product_name: document.getElementById("p-product").value,
      audience: document.getElementById("p-audience").value,
      offer: document.getElementById("p-offer").value,
      tone: document.getElementById("p-tone").value,
      cta: document.getElementById("p-cta").value,
      landing_page: "https://example.invalid/driptech",
    };

    const data = await post("/api/plan", { feel: feel, profile: profile, render_previews: true });
    lastPlan = data;

    // Posture + score
    studioOutput.innerHTML = "";
    appendStudio("> MARKET POSTURE: " + (data.market_posture || "---").toUpperCase(), "hot");
    appendStudio("> OVERALL SCORE: " + (data.overall_score || 0).toFixed(3));

    if (data.resonance != null) {
      appendStudio("> FEEL→SIGNAL RESONANCE: " + data.resonance.toFixed(3));
    }

    // Windows
    appendStudio("\n> RECOMMENDED WINDOWS:");
    (data.recommended_windows || []).forEach(function (w, i) {
      appendStudio("  [" + (i + 1) + "] " + w.label + " @ " + w.clock + " — score " + w.score.toFixed(3) + " | " + w.format_bias);
    });

    // Drafts
    (data.drafts || []).forEach(function (draft) {
      const block = document.createElement("div");
      block.className = "draft-block";

      let html = '<div class="draft-header">' + esc(draft.slot_label) + " — " + esc(draft.hook) + "</div>";
      html += '<div class="draft-hook">' + esc(draft.creative_angle) + "</div>";

      // Preview
      if (draft.render_assets && draft.render_assets.poster_path) {
        html += '<div class="preview-row">';
        if (draft.render_assets.video_path) {
          html += '<video controls loop muted playsinline width="200" poster="' +
            esc(draft.render_assets.poster_path) + '"><source src="' +
            esc(draft.render_assets.video_path) + '" type="video/mp4"></video>';
        } else {
          html += '<img src="' + esc(draft.render_assets.poster_path) +
            '" alt="poster" width="200">';
        }
        html += "</div>";
      }

      // Script summary
      html += '<div class="draft-meta">SHORT: ' + esc((draft.short_script || []).join(" → ")) + "</div>";
      html += '<div class="draft-meta">VISUAL: ' + esc((draft.visual_direction || []).slice(0, 3).join(" | ")) + "</div>";
      html += '<div class="draft-meta">CTA: ' + esc(draft.call_to_action) + "</div>";
      html += '<div class="draft-meta">TAGS: ' + esc((draft.hashtags || []).join(" ")) + "</div>";

      block.innerHTML = html;
      studioOutput.appendChild(block);

      // Auto-create task for this draft
      autoCreateTask(draft.slot_label);
    });

    studioOutput.scrollTop = 0;
  });

  function appendStudio(text, cls) {
    const line = document.createElement("div");
    line.className = "flow-line" + (cls ? " " + cls : "");
    line.textContent = text;
    studioOutput.appendChild(line);
  }

  // ══════════════════════════════════════════════
  //  MATRIX TASK BOARD
  // ══════════════════════════════════════════════

  const taskTerminal = document.getElementById("task-terminal");
  const taskInput = document.getElementById("task-input");

  async function loadTasks() {
    const data = await fetchJson("/api/tasks/terminal");
    renderTasks(data.lines);
  }

  async function loadTasksFull() {
    const data = await fetchJson("/api/tasks");
    renderTasksFull(data.tasks || []);
  }

  function renderTasks(lines) {
    taskTerminal.innerHTML = "";
    (lines || []).forEach(function (line, i) {
      const el = document.createElement("div");
      el.className = "task-line" + (i < 3 ? " header" : "");
      el.textContent = line;
      taskTerminal.appendChild(el);
    });
  }

  function renderTasksFull(tasks) {
    taskTerminal.innerHTML = "";

    // Header
    const hdr = document.createElement("div");
    hdr.className = "task-line header";
    hdr.textContent = "STATE     PRI  ID        LABEL                           ACTIONS";
    taskTerminal.appendChild(hdr);

    const sep = document.createElement("div");
    sep.className = "task-line header";
    sep.textContent = "--------  ---  --------  ------------------------------  -------";
    taskTerminal.appendChild(sep);

    tasks.forEach(function (task) {
      const el = document.createElement("div");
      el.className = "task-line";
      el.style.display = "flex";
      el.style.alignItems = "center";

      const stateSpan = document.createElement("span");
      stateSpan.className = "state-" + task.state;
      stateSpan.textContent = task.state;
      stateSpan.style.display = "inline-block";
      stateSpan.style.width = "66px";

      const info = document.createElement("span");
      info.textContent = "  " + String(task.priority).padStart(3) + "  " +
        task.id.padEnd(8) + "  " + task.label;
      info.style.flex = "1";

      const advBtn = document.createElement("button");
      advBtn.className = "task-btn";
      advBtn.textContent = "▶ ADV";
      advBtn.addEventListener("click", function () { advanceTask(task.id); });

      const delBtn = document.createElement("button");
      delBtn.className = "task-btn del";
      delBtn.textContent = "✕";
      delBtn.addEventListener("click", function () { removeTask(task.id); });

      el.appendChild(stateSpan);
      el.appendChild(info);
      el.appendChild(advBtn);
      el.appendChild(delBtn);
      taskTerminal.appendChild(el);
    });
  }

  async function addTask(label) {
    if (!label) return;
    const priorityEl = document.getElementById("task-priority");
    const priority = priorityEl ? Number(priorityEl.value) : 5;
    await post("/api/tasks", { label: label, priority: priority });
    loadTasksFull();
    updateStats();
  }

  async function autoCreateTask(label) {
    await post("/api/tasks", { label: label.toLowerCase().replace(/\s+/g, "-"), priority: 6 });
    loadTasksFull();
    updateStats();
  }

  async function advanceTask(id) {
    await post("/api/tasks/" + encodeURIComponent(id) + "/advance", {});
    loadTasksFull();
    updateStats();
  }

  async function removeTask(id) {
    await post("/api/tasks/" + encodeURIComponent(id) + "/remove", {});
    loadTasksFull();
    updateStats();
  }

  document.getElementById("btn-add-task").addEventListener("click", function () {
    addTask(taskInput.value.trim());
    taskInput.value = "";
  });

  taskInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      addTask(taskInput.value.trim());
      taskInput.value = "";
    }
  });

  // Priority slider display
  const prioritySlider = document.getElementById("task-priority");
  const priorityVal = document.getElementById("task-priority-val");
  if (prioritySlider && priorityVal) {
    prioritySlider.addEventListener("input", function () {
      priorityVal.textContent = prioritySlider.value;
    });
  }

  // ══════════════════════════════════════════════
  //  PIPELINE STATS BAR
  // ══════════════════════════════════════════════

  const STATE_DOT_COLORS = {
    INIT: "#444", DRAFT: "#00ff41", FEEL: "#00f0ff", SIGNAL: "#00f0ff",
    RENDER: "#ffaa00", ENCODE: "#ffaa00", REVIEW: "#ff00ff", SUBMIT: "#ff00ff", LIVE: "#00ff41",
  };

  async function updateStats() {
    const data = await fetchJson("/api/stats");
    const bar = document.getElementById("stats-bar");
    if (!bar || !data.states) return;
    let html = Object.entries(data.states).map(function (entry) {
      const state = entry[0], count = entry[1];
      const c = STATE_DOT_COLORS[state] || "#666";
      const dim = count === 0 ? " style=\"opacity:0.25\"" : "";
      return "<span class=\"stat-chip\"" + dim + "><span class=\"stat-dot\" style=\"background:" + c + "\"></span>" + state + ":" + count + "</span>";
    }).join("");
    html += "<span class=\"stat-total\">TOTAL:" + data.total + "</span>";
    html += "<span class=\"stat-live\">LIVE:" + data.live_count + "</span>";
    bar.innerHTML = html;
  }

  // ══════════════════════════════════════════════
  //  TOPBAR CONTROLS
  // ══════════════════════════════════════════════

  document.getElementById("btn-matrix").addEventListener("click", function () {
    if (window.matrixRain) {
      const on = window.matrixRain.toggle();
      this.classList.toggle("active", on);
    }
  });

  document.getElementById("btn-disco").addEventListener("click", function () {
    if (window.discoBall) window.discoBall.toggle();
    this.classList.toggle("active");
  });

  document.getElementById("btn-dubstep").addEventListener("click", function () {
    if (window.dubstepEngine) {
      const on = window.dubstepEngine.toggle();
      this.classList.toggle("active", on);
    }
  });

  document.getElementById("btn-dj-next").addEventListener("click", function () {
    if (window.dubstepEngine) window.dubstepEngine.nextSet();
  });

  // ── Auto-pulse heartbeat ──
  let autoPulse = false;
  let autoPulseInterval = null;

  document.getElementById("btn-auto-pulse").addEventListener("click", function () {
    autoPulse = !autoPulse;
    this.classList.toggle("active", autoPulse);
    if (autoPulse) {
      autoPulseInterval = setInterval(async function () {
        const weather = document.querySelector(".btn-weather.active");
        const body = {
          hour:              Number(ctxSliders.hour.value),
          day_energy:        Number(ctxSliders.energy.value),
          audience_pulse:    Number(ctxSliders.audience.value),
          content_freshness: Number(ctxSliders.freshness.value),
          platform_noise:    Number(ctxSliders.noise.value),
          weather:           weather ? weather.dataset.weather : "clear",
        };
        const data = await post("/api/live/context", body);
        if (data.feel) {
          Object.keys(data.feel).forEach(function (key) {
            if (key in feel) feel[key] = data.feel[key];
          });
          refreshDials();
          translateSignals();
        }
      }, 30000);
    } else {
      clearInterval(autoPulseInterval);
    }
  });

  // ── Beat sync: matrix flash + LED pulse ──
  setTimeout(function () {
    if (window.dubstepEngine) {
      window.dubstepEngine.addBeatListener(function (type) {
        if (type === "kick") {
          if (window.matrixRain) window.matrixRain.flashBeat();
          document.querySelectorAll(".led").forEach(function (led) {
            led.classList.add("beat");
            setTimeout(function () { led.classList.remove("beat"); }, 180);
          });
        }
      });
    }
  }, 200);

  // ── Keyboard shortcuts ──
  document.addEventListener("keydown", function (e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (e.key === " " || e.key === "Spacebar") { e.preventDefault(); document.getElementById("btn-pulse").click(); }
    if (e.key === "d" || e.key === "D") document.getElementById("btn-disco").click();
    if (e.key === "m" || e.key === "M") document.getElementById("btn-matrix").click();
    if (e.key === "\\" || e.key === "|") document.getElementById("btn-dubstep").click();
    if (e.key === "g" || e.key === "G") document.getElementById("btn-generate").click();
    if (e.key === "n" || e.key === "N") { if (window.dubstepEngine) window.dubstepEngine.nextSet(); }
  });

  // ── Panel collapse on header click ──
  document.querySelectorAll(".panel-header").forEach(function (hdr) {
    hdr.addEventListener("click", function (e) {
      if (e.target.closest("button")) return;
      hdr.closest(".panel").classList.toggle("collapsed");
    });
  });

  // ── Uptime ticker ──
  function tickUptime() {
    const elapsed = Math.floor((Date.now() - bootTime) / 1000);
    const h = String(Math.floor(elapsed / 3600)).padStart(2, "0");
    const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
    const s = String(elapsed % 60).padStart(2, "0");
    const el = document.getElementById("uptime");
    if (el) el.textContent = "T+" + h + ":" + m + ":" + s;
  }
  setInterval(tickUptime, 1000);

  // ══════════════════════════════════════════════
  //  BOOT SEQUENCE
  // ══════════════════════════════════════════════

  async function boot() {
    initDials();
    await translateSignals();
    await loadTasksFull();
    await updateStats();
  }

  boot();
})();
