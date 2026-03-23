"""
Recraft.ai asset generator helper (placeholder template).

Usage:
  - Set environment variable `RECRAFT_API_KEY` to your Recraft.ai API key.
  - Run: `python recraft_generate.py --dry-run` to see planned prompts.
  - Run: `python recraft_generate.py` to perform generation (will prompt before spending credits).

Notes:
  - This script uses a generic HTTP API call structure and must be configured
    to match Recraft.ai's actual REST API. Edit `API_ENDPOINT` and request
    payload keys if Recraft provides different parameters.
  - The script attempts to detect billing/credit errors and will stop and
    report them so you can decide how to proceed.
"""
import os
import sys
import time
import json
import base64
from pathlib import Path

try:
    import requests
except Exception:
    print('requests is required. Install with: pip install requests')
    raise

API_ENDPOINT = 'https://external.api.recraft.ai/v1/images/generations'
API_KEY_ENV = 'RECRAFT_API_KEY'
OUT_DIR = Path(__file__).parent / 'assets'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Asset specification: name, width, height, prompt (base)
ASSETS = [
    ('tommy_sprite', 16, 16, '16x16 pixel art sprite of a small chibi character, clear silhouette, expressive head, simple limbs, Game Boy 4-shade palette'),
    ('enemy_sprite', 16, 16, '16x16 pixel art sprite of a hostile goomba-like enemy, readable silhouette, Game Boy 4-shade palette'),
    ('hud_tommy', 24, 24, '24x24 pixel art portrait of character head, simplified, Game Boy 4-shade palette'),
    ('bg_day', 160, 144, '160x144 pixel art background with sky and ground, simple tiles, limited palette compatible with Game Boy 4 shades'),
    ('tile_grass', 8, 8, '8x8 pixel tile: grass, clear tileable edges, 4-shade palette'),
    ('tile_block', 8, 8, '8x8 pixel tile: stone block, clear tileable edges, 4-shade palette')
]

def check_api_key():
    key = os.environ.get(API_KEY_ENV)
    if not key:
        print(f'ERROR: Environment variable {API_KEY_ENV} not set. Obtain your Recraft.ai API key and set it before running.')
        return None
    return key

def generate_image(api_key, prompt, w, h, seed=None, steps=20):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    # Recraft expects fields like 'prompt', 'n', 'model', 'size', and 'response_format'
    # Some API models restrict extremely small sizes (e.g., 8x8,16x16).
    # Request a safe larger generation size and downscale locally to target size.
    gen_size = '256x256'
    payload = {
        'prompt': prompt,
        'n': 1,
        'model': 'recraftv4',
        'size': gen_size,
        'response_format': 'b64_json',
        'controls': { 'colors': [{'rgb':[0,0,0]}, {'rgb':[85,85,85]}, {'rgb':[170,170,170]}, {'rgb':[255,255,255]}] }
    }
    if seed is not None: payload['seed'] = seed

    resp = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=120)
    if resp.status_code == 402:
        raise RuntimeError('Payment required / credits exhausted (HTTP 402).')
    if resp.status_code == 401:
        raise RuntimeError('Unauthorized — API key invalid (HTTP 401).')
    if resp.status_code >= 400:
        # try to show error details
        try:
            j = resp.json()
            raise RuntimeError(f'API error {resp.status_code}: {j.get("error") or j}')
        except Exception:
            raise RuntimeError(f'API error {resp.status_code}: {resp.text[:200]}')

    # Expecting a JSON response with base64 PNG in `image` or a direct binary stream.
    j = resp.json()
    # Expect response.data[0].b64_json or response.data[0].image
    data0 = j.get('data') and j['data'][0]
    if not data0:
        raise RuntimeError('No image data in response: ' + str(j)[:200])
    img_b64 = data0.get('b64_json') or data0.get('image') or data0.get('url')
    if not img_b64:
        raise RuntimeError('API response missing image data: ' + str(j)[:200])
    # if it's a URL, fetch it
    if isinstance(img_b64, str) and img_b64.startswith('http'):
        r2 = requests.get(img_b64, timeout=60)
        return r2.content
    img_bytes = base64.b64decode(img_b64)
    return img_bytes

def save_image(bytestr, outpath):
    with open(outpath, 'wb') as f:
        f.write(bytestr)

def main(dry_run=False, seeds=None, auto_confirm=False):
    print('Provider: Recraft.ai (user must supply API key via environment variable)')
    api_key = check_api_key()
    if not api_key:
        print('Set API key and re-run. Aborting.')
        return 2

    print('Planned assets:')
    for name,w,h,prompt in ASSETS:
        print(f' - {name}: {w}x{h}')
    if dry_run:
        print('\nDry run mode — no API calls will be made.')
        return 0

    # Confirm spending
    if not auto_confirm:
        confirm = input('\nThis will call Recraft.ai and may consume credits. Type YES to proceed: ')
        if confirm.strip().upper() != 'YES':
            print('Aborted by user.')
            return 1

    for idx,(name,w,h,prompt) in enumerate(ASSETS):
        seed = seeds[idx] if seeds and idx < len(seeds) else None
        print(f'Generating {name} ({w}x{h})...')
        try:
            data = generate_image(api_key, prompt, w, h, seed=seed)
        except RuntimeError as e:
            print('Generation error:', e)
            print('Stopping to avoid further spending. Fix the issue and retry.')
            return 3
        # If generated at larger size, downscale to requested size
        from PIL import Image
        from io import BytesIO
        img = Image.open(BytesIO(data)).convert('RGBA')
        img_small = img.resize((w,h), resample=Image.NEAREST)
        outpath = OUT_DIR / f'{name}.png'
        img_small.save(outpath)
        print('Saved:', outpath)
        time.sleep(1)

    print('\nAll assets generated into', OUT_DIR)
    print('Next: run `python convert_assets.py assets/*.png > tiles.c` to produce tiles.c for GBDK.')
    return 0

if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    auto = '--yes' in sys.argv or '-y' in sys.argv
    sys.exit(main(dry_run=dry, auto_confirm=auto))
