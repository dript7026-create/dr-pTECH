const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
const packageUrlInput = document.getElementById('packageUrl');
const statusEl = document.getElementById('status');
const metaEl = document.getElementById('meta');
const loadBtn = document.getElementById('loadBtn');
const nextMapBtn = document.getElementById('nextMapBtn');

const state = {
  manifest: null,
  anchors: new Map(),
  images: new Map(),
  currentMap: 0,
  playerX: 640,
  playerY: 620,
  velocityX: 0,
  combo: 0,
  playerHealth: 100,
  playerStamina: 100,
  enemyHealth: 100,
  attackFlash: 0,
  ritualFlash: 0,
  attackTimer: 0,
  beatTimer: 0,
  bpm: 100,
  animTime: 0,
  deck: [-1, -1, -1],
  keys: new Set(),
  loadedUrl: ''
};

function setStatus(text) {
  statusEl.textContent = text;
}

function getQueryPackage() {
  const url = new URL(window.location.href);
  return url.searchParams.get('src');
}

function anchorKey(asset, anchor) {
  return `${asset}:${anchor}`;
}

function getAnchor(asset, anchor) {
  return state.anchors.get(anchorKey(asset, anchor)) ?? { x: 0.5, y: 0.5 };
}

function parseAnchorCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const anchors = new Map();
  for (const line of lines.slice(1)) {
    const [name, anchorName, x, y] = line.split(',');
    if (!name || !anchorName) continue;
    anchors.set(anchorKey(name, anchorName), { x: Number(x), y: Number(y) });
  }
  return anchors;
}

async function blobToImage(blob) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(blob);
  });
}

async function loadFarim(url) {
  setStatus(`Loading ${url} ...`);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} while fetching package`);
  }

  const zipBuffer = await response.arrayBuffer();
  const zip = await JSZip.loadAsync(zipBuffer);
  const manifestText = await zip.file('farim_manifest.json').async('string');
  const manifest = JSON.parse(manifestText);
  if (manifest.format !== 'farim') {
    throw new Error('Package format is not farim');
  }

  const anchorText = await zip.file('runtime_anchors.csv').async('string');
  const anchors = parseAnchorCsv(anchorText);
  const images = new Map();
  for (const asset of manifest.assets) {
    const file = zip.file(asset.archive_path);
    if (!file) continue;
    const blob = await file.async('blob');
    const image = await blobToImage(blob);
    images.set(asset.name, image);
  }

  state.manifest = manifest;
  state.anchors = anchors;
  state.images = images;
  state.currentMap = 0;
  state.loadedUrl = url;
  metaEl.textContent = JSON.stringify({
    format: manifest.format,
    format_version: manifest.format_version,
    assets: manifest.assets.length,
    runtime_note: manifest.runtime_note
  }, null, 2);
  setStatus(`Loaded ${manifest.assets.length} assets from ${url}`);
}

function drawImageNamed(name, x, y, w, h, alpha = 1) {
  const img = state.images.get(name);
  if (!img) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(img, x, y, w, h);
  ctx.restore();
}

function drawBar(x, y, w, h, value, color) {
  ctx.fillStyle = 'rgba(10, 12, 16, 0.82)';
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = color;
  ctx.fillRect(x, y, Math.max(0, Math.min(1, value)) * w, h);
}

function placeByAnchor(worldX, worldY, width, height, anchor) {
  return {
    x: worldX - anchor.x * width,
    y: worldY - anchor.y * height,
    width,
    height
  };
}

function drawPlayerRig() {
  const sway = Math.sin(state.animTime * 3.4);
  const stride = Math.sin(state.animTime * 7.0);

  drawImageNamed('misha_torso', state.playerX - 88, state.playerY - 276, 176, 220);

  const neck = getAnchor('misha_head', 'neck_pivot');
  const headRect = placeByAnchor(state.playerX, state.playerY - 180, 150, 150, neck);
  drawImageNamed('misha_head', headRect.x, headRect.y, headRect.width, headRect.height);

  drawImageNamed('misha_arm_segment', state.playerX - 122, state.playerY - 220 + sway * 8, 132, 132);
  drawImageNamed('misha_forearm_hand_segment', state.playerX - 146, state.playerY - 180 + sway * 8, 132, 132);
  drawImageNamed('misha_arm_segment', state.playerX + 4, state.playerY - 210 - sway * 7, 132, 132);
  drawImageNamed('misha_forearm_hand_segment', state.playerX + 26, state.playerY - 170 - sway * 6, 132, 132);

  drawImageNamed('misha_leg_segment', state.playerX - 76, state.playerY - 88 + stride * 6, 138, 138);
  drawImageNamed('misha_shin_foot_segment', state.playerX - 92, state.playerY - 10 + stride * 8, 138, 138);
  drawImageNamed('misha_leg_segment', state.playerX - 4, state.playerY - 86 - stride * 6, 138, 138);
  drawImageNamed('misha_shin_foot_segment', state.playerX + 18, state.playerY - 8 - stride * 7, 138, 138);
}

function drawScene() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const bgNames = [
    'wild_orchard_backdrop',
    'wild_marsh_backdrop',
    'wild_mire_backdrop',
    'hub_city_segment_a',
    'hub_city_segment_b',
    'hub_city_segment_c'
  ];
  const bg = bgNames[state.currentMap] ?? bgNames[0];
  drawImageNamed(bg, 0, 0, canvas.width, canvas.height);

  ctx.fillStyle = '#22160f';
  ctx.fillRect(0, canvas.height - 92, canvas.width, 92);

  if (state.attackFlash > 0) {
    ctx.fillStyle = `rgba(255,220,120,${Math.min(0.6, state.attackFlash * 2.2)})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  if (state.ritualFlash > 0) {
    ctx.fillStyle = `rgba(120,220,255,${Math.min(0.55, state.ritualFlash * 1.8)})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  drawPlayerRig();

  if (state.currentMap < 3) {
    drawImageNamed('leshy_core', canvas.width - 360, canvas.height - 360, 230, 230);
    if (state.enemyHealth > 0 && state.attackTimer > 0) {
      drawImageNamed('ritual_ring_fx', canvas.width - 340, canvas.height - 380, 180, 180, 0.75);
    }
  } else {
    drawImageNamed('domovoi_vendor', 80, canvas.height - 300, 150, 150);
  }

  drawImageNamed('hud_rhythm_frame', 0, 0, canvas.width, 160);
  drawImageNamed('media_deck_panel', 18, canvas.height - 204, 380, 180);

  for (let i = 0; i < 3; i += 1) {
    ctx.fillStyle = state.deck[i] === -1 ? 'rgba(24,24,24,0.9)' : 'rgba(184,104,144,0.95)';
    ctx.fillRect(58 + i * 98, canvas.height - 138, 64, 64);
  }

  drawBar(36, 26, 260, 18, state.playerHealth / 100, '#ba3448');
  drawBar(36, 52, 260, 12, state.playerStamina / 100, '#4cc684');
  if (state.currentMap < 3) {
    drawBar(canvas.width - 296, 26, 260, 16, state.enemyHealth / 100, '#947436');
  }

  ctx.fillStyle = '#edf3fb';
  ctx.font = '16px Consolas';
  ctx.fillText(`Map ${state.currentMap + 1}/6`, 36, 92);
  ctx.fillText(`Combo ${state.combo}`, 36, 116);
  ctx.fillText(`Beat ${state.bpm} BPM`, 36, 138);
}

function tryAttack() {
  if (state.playerStamina < 10 || state.attackTimer > 0) return;
  state.attackTimer = 0.24;
  state.attackFlash = 0.18;
  state.playerStamina = Math.max(0, state.playerStamina - 10);
  if (state.currentMap < 3 && Math.abs((canvas.width - 250) - state.playerX) < 220) {
    state.enemyHealth = Math.max(0, state.enemyHealth - 14);
    state.combo += 1;
  } else {
    state.combo = 0;
  }
}

function tryRitual() {
  if (state.deck.some((value) => value === -1)) return;
  state.ritualFlash = 0.4;
  if (state.deck[0] === 1 && state.deck[1] === 2 && state.deck[2] === 3) {
    state.playerHealth = Math.min(100, state.playerHealth + 20);
  } else {
    state.enemyHealth = Math.max(0, state.enemyHealth - 12);
  }
  state.deck = [-1, -1, -1];
}

function update(dt) {
  state.animTime += dt;
  state.beatTimer += dt;
  const secondsPerBeat = 60 / state.bpm;
  if (state.beatTimer >= secondsPerBeat) state.beatTimer -= secondsPerBeat;

  state.playerStamina = Math.min(100, state.playerStamina + dt * 18);
  state.attackTimer = Math.max(0, state.attackTimer - dt);
  state.attackFlash = Math.max(0, state.attackFlash - dt);
  state.ritualFlash = Math.max(0, state.ritualFlash - dt);

  state.velocityX = 0;
  if (state.keys.has('a') || state.keys.has('arrowleft')) state.velocityX = -300;
  if (state.keys.has('d') || state.keys.has('arrowright')) state.velocityX = 300;
  state.playerX += state.velocityX * dt;
  if (state.playerX < 60) {
    state.playerX = canvas.width - 100;
    state.currentMap = (state.currentMap + 5) % 6;
  }
  if (state.playerX > canvas.width - 60) {
    state.playerX = 100;
    state.currentMap = (state.currentMap + 1) % 6;
  }

  if (state.currentMap < 3 && state.enemyHealth <= 0) {
    state.enemyHealth = 100;
  }
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  update(dt);
  drawScene();
  requestAnimationFrame(frame);
}

window.addEventListener('keydown', (event) => {
  state.keys.add(event.key.toLowerCase());
  if (event.key === 'j' || event.key === 'J') tryAttack();
  if (event.key === 'k' || event.key === 'K') tryRitual();
  if (event.key === 'm' || event.key === 'M') state.currentMap = (state.currentMap + 1) % 6;
  if (event.key === '1') state.deck[0] = state.deck[0] === -1 ? 1 : -1;
  if (event.key === '2') state.deck[1] = state.deck[1] === -1 ? 2 : -1;
  if (event.key === '3') state.deck[2] = state.deck[2] === -1 ? 3 : -1;
});
window.addEventListener('keyup', (event) => {
  state.keys.delete(event.key.toLowerCase());
});

loadBtn.addEventListener('click', async () => {
  try {
    await loadFarim(packageUrlInput.value.trim());
  } catch (error) {
    setStatus(error.message);
  }
});

nextMapBtn.addEventListener('click', () => {
  state.currentMap = (state.currentMap + 1) % 6;
});

const initialPackage = getQueryPackage() ?? packageUrlInput.value;
packageUrlInput.value = initialPackage;
loadFarim(initialPackage).catch((error) => {
  setStatus(error.message);
});
requestAnimationFrame(frame);
