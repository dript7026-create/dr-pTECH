/* ─── Disco Ball + Procedural Dubstep Engine + Beat-Sync Projections ─── */

(function () {
  "use strict";

  // ── Track name generator ──
  const PREFIXES = [
    "Midnight", "Neon", "Vapor", "Shadow", "Cyber", "Quantum", "Echo",
    "Plasma", "Gravity", "Orbital", "Sub-Zero", "Fractal", "Prism",
    "Obsidian", "Phantom", "Crystal", "Thunder", "Vortex", "Pulse",
    "Acid", "Hyper", "Turbo", "Glitch", "Flux", "Synth",
  ];
  const SUFFIXES = [
    "Wobble", "Drop", "Circuit", "Signal", "Protocol", "Frequency",
    "Bassline", "Override", "Sequence", "Flux", "Voltage", "Machine",
    "Reactor", "Decibel", "Waveform", "Tremor", "Sync", "Grid",
    "Surge", "Blaster", "Static", "Drive",
  ];

  function genTrackName() {
    const p = PREFIXES[Math.random() * PREFIXES.length | 0];
    const s = SUFFIXES[Math.random() * SUFFIXES.length | 0];
    return p + " " + s;
  }

  // ── Beat listeners ──
  const beatListeners = [];
  function fireBeat(type) {
    beatListeners.forEach(function (fn) { try { fn(type); } catch (e) {} });
  }

  // ── Dubstep Sequencer ──
  let audioCtx = null;
  let masterGain = null;
  let analyser = null;
  let freqData = null;
  let playing = false;
  let currentTrack = "---";
  let stepTimer = null;
  let pattern = [];
  let step = 0;
  const BPM = 140;
  const STEPS = 16;
  const STEP_TIME = 60 / BPM / 4;

  function initAudio() {
    if (audioCtx) return;
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    masterGain = audioCtx.createGain();
    masterGain.gain.value = 0.35;

    // Real FFT analyser wired before destination
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 128;
    analyser.smoothingTimeConstant = 0.75;
    freqData = new Uint8Array(analyser.frequencyBinCount);

    masterGain.connect(analyser);
    analyser.connect(audioCtx.destination);
  }

  function genPattern() {
    pattern = [];
    for (let i = 0; i < STEPS; i++) {
      pattern.push({
        kick:   i % 4 === 0 || (i % 8 === 6 && Math.random() > 0.4),
        snare:  i % 8 === 4 || (i === 14 && Math.random() > 0.3),
        hat:    Math.random() > 0.35,
        wobble: i % 2 === 0 || Math.random() > 0.6,
        sub:    i % 4 === 0,
      });
    }
    currentTrack = genTrackName();
    step = 0;
  }

  function playKick(time) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(150, time);
    osc.frequency.exponentialRampToValueAtTime(30, time + 0.12);
    gain.gain.setValueAtTime(0.8, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.2);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(time);
    osc.stop(time + 0.2);
  }

  function playSnare(time) {
    const bufferSize = audioCtx.sampleRate * 0.08;
    const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
    }
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    const filter = audioCtx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.value = 3000 + Math.random() * 2000;
    filter.Q.value = 1.2;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.5, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    source.start(time);
  }

  function playHat(time) {
    const bufferSize = audioCtx.sampleRate * 0.04;
    const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize) * 0.5;
    }
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    const filter = audioCtx.createBiquadFilter();
    filter.type = "highpass";
    filter.frequency.value = 8000;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.25, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.04);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    source.start(time);
  }

  function playWobble(time) {
    const osc = audioCtx.createOscillator();
    const filter = audioCtx.createBiquadFilter();
    const lfo = audioCtx.createOscillator();
    const lfoGain = audioCtx.createGain();
    const gain = audioCtx.createGain();
    osc.type = Math.random() > 0.5 ? "sawtooth" : "square";
    osc.frequency.value = 55 + Math.random() * 30;
    filter.type = "lowpass";
    filter.frequency.value = 400;
    filter.Q.value = 8 + Math.random() * 12;
    lfo.type = "sine";
    lfo.frequency.value = 2 + Math.random() * 6;
    lfoGain.gain.value = 800 + Math.random() * 1200;
    gain.gain.setValueAtTime(0.3, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + STEP_TIME * 1.8);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);
    osc.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    osc.start(time);
    lfo.start(time);
    osc.stop(time + STEP_TIME * 2);
    lfo.stop(time + STEP_TIME * 2);
  }

  function playSub(time) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.value = 35 + Math.random() * 15;
    gain.gain.setValueAtTime(0.4, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + STEP_TIME * 3);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(time);
    osc.stop(time + STEP_TIME * 3.5);
  }

  function scheduleStep() {
    if (!playing || !audioCtx) return;
    const time = audioCtx.currentTime + 0.05;
    const s = pattern[step % STEPS];
    if (s.kick)   { playKick(time);   fireBeat("kick");  }
    if (s.snare)  { playSnare(time);  fireBeat("snare"); }
    if (s.hat)    { playHat(time); }
    if (s.wobble) { playWobble(time); }
    if (s.sub)    { playSub(time); }
    step++;
    if (step >= STEPS * 4) {
      genPattern();
      updateUI();
    }
  }

  function start() {
    initAudio();
    if (audioCtx.state === "suspended") audioCtx.resume();
    genPattern();
    playing = true;
    stepTimer = setInterval(scheduleStep, STEP_TIME * 1000);
    updateUI();
  }

  function stop() {
    playing = false;
    if (stepTimer) clearInterval(stepTimer);
    stepTimer = null;
    currentTrack = "---";
    updateUI();
  }

  function nextSet() {
    if (playing) {
      genPattern();
      updateUI();
    }
  }

  function updateUI() {
    const trackEl = document.getElementById("dj-track");
    if (trackEl) trackEl.textContent = currentTrack;
  }

  // ── Real FFT waveform visualizer ──
  function initViz() {
    const vizCanvas = document.getElementById("dj-viz");
    if (!vizCanvas) return;
    const vctx = vizCanvas.getContext("2d");
    const vw = vizCanvas.width;
    const vh = vizCanvas.height;

    function drawViz() {
      vctx.fillStyle = "rgba(0,0,0,0.3)";
      vctx.fillRect(0, 0, vw, vh);

      if (!playing || !analyser) {
        requestAnimationFrame(drawViz);
        return;
      }

      analyser.getByteFrequencyData(freqData);
      const barCount = freqData.length;
      const barWidth = vw / barCount - 0.5;

      for (let i = 0; i < barCount; i++) {
        const barHeight = (freqData[i] / 255) * vh;
        const hue = 120 + (i / barCount) * 200; // green → cyan → magenta
        vctx.fillStyle = "hsl(" + hue + ",100%,60%)";
        vctx.fillRect(i * (barWidth + 0.5), vh - barHeight, barWidth, barHeight);
      }

      requestAnimationFrame(drawViz);
    }

    drawViz();
  }

  // ── Disco floor light projections ──
  let discoOn = false;
  let projCanvas = null;
  let projCtx = null;
  const projSpots = [];
  let projFrameRunning = false;
  let projAngle = 0;

  function initProjections() {
    if (projCanvas) return;
    projCanvas = document.createElement("canvas");
    projCanvas.style.cssText = [
      "position:fixed", "inset:0", "z-index:3",
      "pointer-events:none", "opacity:0.5", "mix-blend-mode:screen",
    ].join(";") + ";";
    document.body.appendChild(projCanvas);
    projCtx = projCanvas.getContext("2d");
    resizeProj();
    window.addEventListener("resize", resizeProj);

    // Seed light spots with random personalities
    for (let i = 0; i < 14; i++) {
      projSpots.push({
        speed:    0.25 + Math.random() * 0.75,
        phase:    Math.random() * Math.PI * 2,
        r:        50 + Math.random() * 90,
        hue:      Math.random() * 360,
        intensity: 0,
        xBias:    (Math.random() - 0.5) * 1.6,
        yBias:    (Math.random() - 0.5) * 1.2,
      });
    }
  }

  function resizeProj() {
    if (!projCanvas) return;
    projCanvas.width  = window.innerWidth;
    projCanvas.height = window.innerHeight;
  }

  function drawProjections() {
    if (!projFrameRunning) return;
    projCtx.clearRect(0, 0, projCanvas.width, projCanvas.height);

    if (!discoOn) {
      requestAnimationFrame(drawProjections);
      return;
    }

    projAngle += 0.008;
    const cw = projCanvas.width;
    const ch = projCanvas.height;

    projSpots.forEach(function (spot) {
      const px = cw * 0.5 + Math.cos(projAngle * spot.speed + spot.phase) * (cw * 0.38) * spot.xBias + cw * 0.5 * (spot.xBias > 0 ? 0.1 : -0.1);
      const py = ch * 0.5 + Math.sin(projAngle * spot.speed * 0.65 + spot.phase) * (ch * 0.32) * spot.yBias + ch * 0.15;

      // Decay intensity between beats
      spot.intensity = Math.max(0, spot.intensity - 0.04);

      const baseAlpha = 0.08 + spot.intensity * 0.55;
      const h = (spot.hue + projAngle * 40) % 360;
      const grd = projCtx.createRadialGradient(px, py, 0, px, py, spot.r + spot.intensity * 30);
      grd.addColorStop(0, "hsla(" + h + ",100%,75%," + baseAlpha + ")");
      grd.addColorStop(0.5, "hsla(" + h + ",90%,55%," + (baseAlpha * 0.4) + ")");
      grd.addColorStop(1, "hsla(" + h + ",80%,40%,0)");
      projCtx.fillStyle = grd;
      projCtx.beginPath();
      projCtx.arc(px, py, spot.r + spot.intensity * 30, 0, Math.PI * 2);
      projCtx.fill();
    });

    requestAnimationFrame(drawProjections);
  }

  // Beat → light flash
  function onBeat(type) {
    if (!discoOn) return;
    if (type === "kick") {
      // Slam 4 random spots to full brightness and re-hue them
      const shuffled = projSpots.slice().sort(function () { return 0.5 - Math.random(); });
      shuffled.slice(0, 4).forEach(function (s) {
        s.intensity = 1.0;
        s.hue = Math.random() * 360;
      });
    } else if (type === "snare") {
      projSpots.forEach(function (s) { s.intensity = Math.max(s.intensity, 0.45); });
    }
  }

  beatListeners.push(onBeat);

  function toggleDisco() {
    discoOn = !discoOn;
    const container = document.getElementById("disco-container");
    if (container) container.classList.toggle("hidden", !discoOn);

    if (discoOn) {
      initProjections();
      if (!projFrameRunning) {
        projFrameRunning = true;
        drawProjections();
      }
    } else {
      if (projCtx) projCtx.clearRect(0, 0, projCanvas.width, projCanvas.height);
    }
  }

  // ── Expose API ──
  window.dubstepEngine = {
    toggle: function () { if (playing) stop(); else start(); return playing; },
    isPlaying: function () { return playing; },
    nextSet: nextSet,
    currentTrack: function () { return currentTrack; },
    addBeatListener: function (fn) { beatListeners.push(fn); },
  };

  window.discoBall = {
    toggle: toggleDisco,
    isOn: function () { return discoOn; },
  };

  initViz();
})();

  // ── Track name generator ──
  const PREFIXES = [
    "Midnight", "Neon", "Vapor", "Shadow", "Cyber", "Quantum", "Echo",
    "Plasma", "Gravity", "Orbital", "Sub-Zero", "Fractal", "Prism",
    "Obsidian", "Phantom", "Crystal", "Thunder", "Vortex", "Pulse",
  ];
  const SUFFIXES = [
    "Wobble", "Drop", "Circuit", "Signal", "Protocol", "Frequency",
    "Bassline", "Override", "Sequence", "Flux", "Voltage", "Machine",
    "Reactor", "Decibel", "Waveform", "Tremor", "Sync", "Grid",
  ];

  function genTrackName() {
    const p = PREFIXES[Math.random() * PREFIXES.length | 0];
    const s = SUFFIXES[Math.random() * SUFFIXES.length | 0];
    return p + " " + s;
  }

  // ── Dubstep Sequencer ──
  let audioCtx = null;
  let masterGain = null;
  let playing = false;
  let currentTrack = "---";
  let stepTimer = null;
  let pattern = [];
  let step = 0;
  const BPM = 140;
  const STEPS = 16;
  const STEP_TIME = 60 / BPM / 4; // 16th notes

  function initAudio() {
    if (audioCtx) return;
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    masterGain = audioCtx.createGain();
    masterGain.gain.value = 0.35;
    masterGain.connect(audioCtx.destination);
  }

  function genPattern() {
    pattern = [];
    for (let i = 0; i < STEPS; i++) {
      pattern.push({
        kick: i % 4 === 0 || (i % 8 === 6 && Math.random() > 0.4),
        snare: i % 8 === 4 || (i === 14 && Math.random() > 0.3),
        hat: Math.random() > 0.35,
        wobble: i % 2 === 0 || Math.random() > 0.6,
        sub: i % 4 === 0,
      });
    }
    currentTrack = genTrackName();
    step = 0;
  }

  function playKick(time) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(150, time);
    osc.frequency.exponentialRampToValueAtTime(30, time + 0.12);
    gain.gain.setValueAtTime(0.8, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.2);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(time);
    osc.stop(time + 0.2);
  }

  function playSnare(time) {
    // Noise burst through bandpass
    const bufferSize = audioCtx.sampleRate * 0.08;
    const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
    }
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    const filter = audioCtx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.value = 3000 + Math.random() * 2000;
    filter.Q.value = 1.2;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.5, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    source.start(time);
  }

  function playHat(time) {
    const bufferSize = audioCtx.sampleRate * 0.04;
    const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize) * 0.5;
    }
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    const filter = audioCtx.createBiquadFilter();
    filter.type = "highpass";
    filter.frequency.value = 8000;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.25, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.04);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    source.start(time);
  }

  function playWobble(time) {
    const osc = audioCtx.createOscillator();
    const filter = audioCtx.createBiquadFilter();
    const lfo = audioCtx.createOscillator();
    const lfoGain = audioCtx.createGain();
    const gain = audioCtx.createGain();

    osc.type = Math.random() > 0.5 ? "sawtooth" : "square";
    osc.frequency.value = 55 + Math.random() * 30;

    filter.type = "lowpass";
    filter.frequency.value = 400;
    filter.Q.value = 8 + Math.random() * 12;

    lfo.type = "sine";
    lfo.frequency.value = 2 + Math.random() * 6; // wobble rate
    lfoGain.gain.value = 800 + Math.random() * 1200;

    gain.gain.setValueAtTime(0.3, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + STEP_TIME * 1.8);

    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);
    osc.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);

    osc.start(time);
    lfo.start(time);
    osc.stop(time + STEP_TIME * 2);
    lfo.stop(time + STEP_TIME * 2);
  }

  function playSub(time) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.value = 35 + Math.random() * 15;
    gain.gain.setValueAtTime(0.4, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + STEP_TIME * 3);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(time);
    osc.stop(time + STEP_TIME * 3.5);
  }

  function scheduleStep() {
    if (!playing || !audioCtx) return;
    const time = audioCtx.currentTime + 0.05;
    const s = pattern[step % STEPS];
    if (s.kick) playKick(time);
    if (s.snare) playSnare(time);
    if (s.hat) playHat(time);
    if (s.wobble) playWobble(time);
    if (s.sub) playSub(time);

    step++;
    // Generate new pattern every 4 bars
    if (step >= STEPS * 4) {
      genPattern();
      updateUI();
    }
  }

  function start() {
    initAudio();
    if (audioCtx.state === "suspended") audioCtx.resume();
    genPattern();
    playing = true;
    stepTimer = setInterval(scheduleStep, STEP_TIME * 1000);
    updateUI();
  }

  function stop() {
    playing = false;
    if (stepTimer) clearInterval(stepTimer);
    stepTimer = null;
    currentTrack = "---";
    updateUI();
  }

  function nextSet() {
    if (playing) {
      genPattern();
      updateUI();
    }
  }

  function updateUI() {
    const trackEl = document.getElementById("dj-track");
    if (trackEl) trackEl.textContent = currentTrack;
  }

  // ── Waveform visualizer ──
  function initViz() {
    const vizCanvas = document.getElementById("dj-viz");
    if (!vizCanvas) return;
    const vctx = vizCanvas.getContext("2d");
    const vw = vizCanvas.width;
    const vh = vizCanvas.height;

    function drawViz() {
      vctx.fillStyle = "rgba(0, 0, 0, 0.3)";
      vctx.fillRect(0, 0, vw, vh);

      if (!playing) {
        requestAnimationFrame(drawViz);
        return;
      }

      const barCount = 32;
      const barWidth = vw / barCount - 1;

      for (let i = 0; i < barCount; i++) {
        const barHeight = (Math.random() * 0.6 + 0.1) * vh;
        const hue = 120 + (i / barCount) * 180; // green → cyan → magenta
        vctx.fillStyle = "hsl(" + hue + ", 100%, 60%)";
        vctx.fillRect(i * (barWidth + 1), vh - barHeight, barWidth, barHeight);
      }

      requestAnimationFrame(drawViz);
    }

    drawViz();
  }

  // ── Disco toggle ──
  function toggleDisco() {
    const container = document.getElementById("disco-container");
    if (container) container.classList.toggle("hidden");
  }

  // ── Expose API ──
  window.dubstepEngine = {
    toggle() {
      if (playing) stop(); else start();
      return playing;
    },
    isPlaying() { return playing; },
    nextSet: nextSet,
    currentTrack() { return currentTrack; },
  };

  window.discoBall = {
    toggle: toggleDisco,
  };

  initViz();
})();
