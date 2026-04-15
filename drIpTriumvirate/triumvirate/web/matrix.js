/* ─── Matrix Rain — canvas character fall, feel-reactive + beat-flash ─── */

(function () {
  "use strict";

  const canvas = document.getElementById("matrix-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const CHARS = "abcdefghijklmnopqrstuvwxyz0123456789@#$%^&*(){}[]|;:,.<>?/~`ドリップテック信号声波";
  const FONT_SIZE = 14;
  let columns = [];
  let w = 0, h = 0;
  let running = true;
  let beatFlash = 0;

  // Feel → color map [R, G, B]
  const FEEL_COLORS = {
    urgency:    [255, 51,  51 ],
    trust:      [0,   255, 65 ],
    wonder:     [0,   240, 255],
    tenderness: [255, 136, 204],
    grit:       [255, 170, 0  ],
    clarity:    [220, 255, 220],
    volatility: [255, 0,   255],
  };

  // Smoothly interpolated current color
  let curR = 0, curG = 255, curB = 65;
  let tgtR = 0, tgtG = 255, tgtB = 65;
  const LERP = 0.03;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    const count = Math.floor(w / FONT_SIZE);
    columns = Array.from({ length: count }, function () { return Math.random() * h / FONT_SIZE | 0; });
  }

  function draw() {
    if (!running) return;

    // Color lerp
    curR += (tgtR - curR) * LERP;
    curG += (tgtG - curG) * LERP;
    curB += (tgtB - curB) * LERP;

    // Beat brightens, slows fade so rain blazes
    const alpha = beatFlash > 0 ? 0.015 : 0.06;
    if (beatFlash > 0) beatFlash--;

    ctx.fillStyle = "rgba(5,5,5," + alpha + ")";
    ctx.fillRect(0, 0, w, h);
    ctx.font = FONT_SIZE + "px Courier New,monospace";

    const boost = beatFlash > 0 ? 1.45 : 1.0;
    const r = Math.min(255, Math.round(curR * boost));
    const g = Math.min(255, Math.round(curG * boost));
    const b = Math.min(255, Math.round(curB * boost));

    for (let i = 0; i < columns.length; i++) {
      const char = CHARS[Math.random() * CHARS.length | 0];
      const x = i * FONT_SIZE;
      const y = columns[i] * FONT_SIZE;
      const roll = Math.random();

      if (beatFlash > 9 && roll < 0.08) {
        ctx.fillStyle = "#ffffff";
      } else if (roll < 0.025) {
        ctx.fillStyle = "#ffffff";
      } else if (roll < 0.07) {
        // Accent: cooler/lighter variant of feel color
        ctx.fillStyle = "rgba(" + Math.round(r * 0.5) + "," + Math.round(g * 0.5) + "," + Math.min(255, Math.round(b * 1.4)) + ",0.85)";
      } else {
        ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
      }

      ctx.fillText(char, x, y);
      if (y > h && Math.random() > 0.975) columns[i] = 0;
      columns[i]++;
    }
  }

  resize();
  window.addEventListener("resize", resize);
  let interval = setInterval(draw, 55);

  window.matrixRain = {
    toggle: function () {
      running = !running;
      if (running) {
        interval = setInterval(draw, 55);
      } else {
        clearInterval(interval);
        ctx.clearRect(0, 0, w, h);
      }
      return running;
    },
    isRunning: function () { return running; },
    setFeelColor: function (feelKey) {
      const c = FEEL_COLORS[feelKey];
      if (c) { tgtR = c[0]; tgtG = c[1]; tgtB = c[2]; }
    },
    flashBeat: function () { beatFlash = 14; },
  };
})();
