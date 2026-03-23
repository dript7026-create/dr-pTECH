"""
Batch manifest runner for Recraft generation.

Features:
- Validates manifest entries for required fields and safe sizes
- Can run jobs concurrently through a local client or directly against Recraft API
- Dry-run mode for safety
- Optional auto-confirm to proceed without prompt
- Optional provenance ledger updates with timestamp and SHA-256 hash capture

Usage:
    python batch_run_manifest.py --manifest manifest_example.json --concurrency 4
"""
import argparse
import base64
import csv
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

from ccp_manifest import ccp_to_manifest

try:
        import requests
        HAS_REQUESTS = True
except Exception:
        HAS_REQUESTS = False

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

MIN_SIZE = 8
MAX_SIZE = 2048
API_ENDPOINT = 'https://external.api.recraft.ai/v1/images/generations'
MODELS_WITHOUT_NEGATIVE_PROMPT = {'recraftv4'}

# Palette presets available for `--enforce-palette`.
# Values can be explicit RGB lists or generator tuples: ('bits', rbits, gbits, bbits).
PALETTES = {
    'gameboy4': [(0,0,0),(85,85,85),(170,170,170),(255,255,255)],
    'grayscale8': [(i,i,i) for i in range(0,256,32)][:8],
    'nes': [
        (124,124,124),(0,0,252),(0,0,188),(68,40,188),(148,0,132),(168,0,32),(168,16,0),(136,20,0),
        (80,48,0),(0,120,0),(0,104,0),(0,88,0),(0,64,88),(0,0,0),(0,0,0),(0,0,0),
        (188,188,188),(0,120,248),(0,88,248),(104,68,252),(216,0,204),(228,0,88),(248,56,0),(228,92,16),
        (172,124,0),(0,184,0),(0,168,0),(0,168,132),(0,136,172),(0,0,0),(0,0,0),(0,0,0),
        (248,248,248),(60,188,252),(104,136,252),(152,120,248),(248,120,248),(248,88,152),(248,120,88),(252,160,68),
        (248,184,0),(184,248,24),(88,216,84),(88,248,152),(0,232,216),(120,120,120),(0,0,0),(0,0,0)
    ],
    'gba-full': ('bits',5,5,5),
    'snes-full': ('bits',5,5,5),
    'gbc-full': ('bits',5,5,5),
    'genesis-full': ('bits',3,3,3),
    'modern-pixel-vector': [
        (0,0,0),(255,255,255),(29,53,87),(69,123,157),(168,218,220),(241,250,238),(255,183,3),(255,112,67),
        (138,201,38),(34,197,94),(72,72,255),(255,72,184),(200,160,255),(255,200,160),(120,120,120),(200,200,200)
    ],
    'xbox-series': [
        (0,0,0),(255,255,255),(12,12,12),(28,28,28),(10,176,76),(18,150,90),(34,180,110),(60,200,120),
        (24,40,48),(48,72,88),(80,96,112),(16,120,200),(34,140,210),(80,160,220),(140,200,255),(200,220,240),
        (0,64,32),(48,96,32),(120,180,64),(200,240,200),(255,200,0),(240,180,24),(200,128,0),(160,96,16)
    ],
    'ps5': [
        (0,0,0),(255,255,255),(8,12,20),(16,24,36),(10,24,56),(40,56,88),(0,120,255),(16,160,255),
        (32,200,255),(120,160,255),(200,160,255),(240,200,240),(255,180,200),(200,120,160),(120,120,160),(64,88,144),
        (200,200,200),(180,180,200),(255,240,220),(220,200,160),(160,140,120),(96,64,48),(40,32,24),(16,24,48)
    ],
    'nintendo-switch': [
        (0,0,0),(255,255,255),(200,16,46),(12,81,163),(236,65,28),(0,120,255),(32,32,32),(96,96,96),
        (160,160,160),(240,240,240),(252,184,12),(248,120,88),(88,200,120),(32,160,88),(200,80,160),(120,44,88)
    ],
    'steamdeck': [
        (0,0,0),(255,255,255),(20,20,20),(48,56,64),(72,80,88),(96,104,112),(120,128,136),(152,160,168),
        (32,160,144),(24,120,200),(0,200,160),(160,200,220),(200,200,200),(200,160,120),(120,96,72),(80,64,48)
    ]
}


def validate_item(idx, item):
    errors = []
    if not isinstance(item, dict):
        return [f'item {idx}: must be an object']
    if 'prompt' not in item or not isinstance(item['prompt'], str):
        errors.append('missing or invalid "prompt"')
    if 'w' not in item or 'h' not in item:
        errors.append('missing "w" or "h"')
    else:
        try:
            w = int(item['w']); h = int(item['h'])
            if w < MIN_SIZE or h < MIN_SIZE:
                errors.append(f'size too small ({w}x{h}), min {MIN_SIZE}')
            if w > MAX_SIZE or h > MAX_SIZE:
                errors.append(f'size too large ({w}x{h}), max {MAX_SIZE}')
        except Exception:
            errors.append('w/h must be integers')
    if 'out' not in item or not isinstance(item['out'], str):
        errors.append('missing or invalid "out"')
    return errors


def resolve_output_path(manifest_path, out_value):
    output_path = Path(out_value)
    if not output_path.is_absolute():
        output_path = (manifest_path.parent / output_path).resolve()
    return output_path


def compute_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_image_metadata(file_path):
    output_path = Path(file_path)
    width = ''
    height = ''
    size_bytes = ''
    if output_path.exists():
        size_bytes = str(output_path.stat().st_size)
    if HAS_PIL and output_path.exists():
        try:
            with Image.open(output_path) as img:
                width, height = img.size
        except Exception:
            width = ''
            height = ''
    return str(width) if width != '' else '', str(height) if height != '' else '', size_bytes


def update_ledger(ledger_path, item, output_path):
    ledger = Path(ledger_path)
    rows = []
    fieldnames = []
    if ledger.exists():
        with open(ledger, 'r', newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

    required_fields = [
        'asset_family', 'manifest_entry', 'planned_output', 'source_basis',
        'external_reference_urls', 'rights_basis', 'usage_mode',
        'prompt_revision', 'status', 'notes', 'generated_at_utc', 'file_sha256',
        'image_width', 'image_height', 'file_size_bytes'
    ]
    for field in required_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    manifest_entry = item.get('name', '')
    planned_output = item.get('out', str(output_path))
    matching_row = None
    for row in rows:
        if row.get('manifest_entry') == manifest_entry or row.get('planned_output') == planned_output:
            matching_row = row
            break

    timestamp = datetime.now(timezone.utc).isoformat()
    digest = compute_sha256(output_path) if output_path.exists() else ''
    image_width, image_height, file_size_bytes = get_image_metadata(output_path)
    generation_note = f"Generated automatically via batch_run_manifest.py at {timestamp}"

    if matching_row is None:
        matching_row = {field: '' for field in fieldnames}
        matching_row['asset_family'] = manifest_entry or output_path.stem
        matching_row['manifest_entry'] = manifest_entry
        matching_row['planned_output'] = planned_output
        matching_row['source_basis'] = 'Manifest-driven Recraft generation'
        matching_row['rights_basis'] = 'User-owned Recraft account output'
        matching_row['usage_mode'] = 'Direct API generation'
        matching_row['prompt_revision'] = item.get('prompt_revision', 'auto')
        rows.append(matching_row)

    matching_row['status'] = 'generated'
    matching_row['generated_at_utc'] = timestamp
    matching_row['file_sha256'] = digest
    matching_row['image_width'] = image_width
    matching_row['image_height'] = image_height
    matching_row['file_size_bytes'] = file_size_bytes
    if not matching_row.get('notes'):
        matching_row['notes'] = generation_note
    elif generation_note not in matching_row['notes']:
        matching_row['notes'] = matching_row['notes'] + ' | ' + generation_note

    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_job_direct_api(manifest_path, item, api_key):
    if not HAS_REQUESTS:
        return 1, '', 'requests is not installed in this Python environment'

    width = int(item['w'])
    height = int(item['h'])
    payload = {
        'prompt': item['prompt'],
        'n': int(item.get('n', 1)),
        'model': item.get('model', 'recraftv4'),
        'size': f'{width}x{height}',
        'response_format': item.get('response_format', 'b64_json')
    }
    if 'style' in item:
        payload['style'] = item['style']
    if 'style_id' in item:
        payload['style_id'] = item['style_id']
    model_name = str(payload['model']).lower()
    if 'negative_prompt' in item and model_name not in MODELS_WITHOUT_NEGATIVE_PROMPT:
        payload['negative_prompt'] = item['negative_prompt']
    controls = {}
    if 'controls' in item and isinstance(item['controls'], dict):
        controls.update(item['controls'])
    if item.get('transparent_background'):
        controls['transparent_background'] = True
    if controls:
        payload['controls'] = controls

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=300)
    if response.status_code >= 400:
        return response.status_code, '', response.text[:2000]

    try:
        body = response.json()
    except Exception as exc:
        return 1, '', f'Invalid JSON response: {exc}'

    data0 = body.get('data') and body['data'][0]
    if not data0:
        return 1, '', 'No image payload returned by API'

    image_blob = data0.get('b64_json') or data0.get('image') or data0.get('url')
    if not image_blob:
        return 1, '', 'Image payload missing from API response'

    output_path = resolve_output_path(manifest_path, item['out'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(image_blob, str) and image_blob.startswith('http'):
        image_response = requests.get(image_blob, timeout=180)
        image_response.raise_for_status()
        output_path.write_bytes(image_response.content)
    else:
        output_path.write_bytes(base64.b64decode(image_blob))

    return 0, f'Saved: {output_path}', ''


def find_client():
    base = Path(__file__).parent
    bin_path = base / 'recraft_gen'
    if os.name == 'nt': bin_path = bin_path.with_suffix('.exe')
    if bin_path.exists():
        return str(bin_path), 'bin'
    # fallback to python helper
    py_helper = base.parent.parent / 'tommygoomba' / 'recraft_generate.py'
    if py_helper.exists():
        return str(py_helper), 'py'
    return None, None


def run_job_bin(binpath, item, api_key_env='RECRAFT_API_KEY'):
    prompt = item['prompt']
    w = int(item['w']); h = int(item['h'])
    out = item['out']
    cmd = [binpath, prompt, str(w), str(h), out]
    # run subprocess
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def run_job_py(py_path, item):
    prompt = item['prompt']
    w = int(item['w']); h = int(item['h'])
    out = item['out']
    cmd = [sys.executable, str(py_path), prompt, str(w), str(h), out]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def enforce_palette_on_file(path, palette_name):
    if not HAS_PIL:
        return False, 'Pillow not available'
    try:
        img = Image.open(path).convert('RGBA')
    except Exception as e:
        return False, f'open failed: {e}'
    # lookup palette spec from module-level PALETTES
    spec = PALETTES.get(palette_name)
    # If the spec is a generator tuple: ('bits', rbits, gbits, bbits)
    if isinstance(spec, tuple) and spec[0] == 'bits':
        _, rbits, gbits, bbits = spec
        colors = []
        for r in range(1 << rbits):
            rv = int(round(r * 255.0 / ((1 << rbits) - 1)))
            for g in range(1 << gbits):
                gv = int(round(g * 255.0 / ((1 << gbits) - 1)))
                for b in range(1 << bbits):
                    bv = int(round(b * 255.0 / ((1 << bbits) - 1)))
                    colors.append((rv, gv, bv))
        # build palette image sized to hold up to 256 entries per PIL palette limitation
        pal_img = Image.new('P', (16,16))
        flat = []
        # PIL palettes are max 256 entries; if colors > 256 we sample evenly
        if len(colors) > 256:
            step = len(colors) / 256.0
            for i in range(256):
                c = colors[int(i * step)]
                flat.extend(c)
        else:
            for c in colors:
                flat.extend(c)
        while len(flat) < 768:
            flat.extend((0,0,0))
        pal_img.putpalette(flat)
        try:
            q = img.convert('RGB').quantize(palette=pal_img)
            q.save(path)
            return True, 'ok'
        except Exception as e:
            return False, f'quantize failed: {e}'
    # Otherwise spec is an explicit list of RGB tuples
    if not spec or not isinstance(spec, list):
        return False, f'unknown or unsupported palette {palette_name}'
    pal = spec
    pal_img = Image.new('P', (16,16))
    flat = []
    for c in pal:
        flat.extend(c)
    while len(flat) < 768:
        flat.extend((0,0,0))
    pal_img.putpalette(flat)
    try:
        q = img.convert('RGB').quantize(palette=pal_img)
        q.save(path)
        return True, 'ok'
    except Exception as e:
        return False, f'quantize failed: {e}'


def load_manifest_items(manifest_path):
    mp = Path(manifest_path)
    if not mp.exists():
        raise FileNotFoundError(f'Manifest not found: {mp}')
    if mp.suffix.lower() == '.ccp':
        return ccp_to_manifest(mp)
    txt = mp.read_text()
    manifest = json.loads(txt)
    if not isinstance(manifest, list):
        raise ValueError('Manifest root must be an array')
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', '-m', required=True)
    p.add_argument('--concurrency', '-j', type=int, default=2)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--yes', '-y', action='store_true')
    p.add_argument('--enforce-palette', action='store_true', help='Enforce a limited palette on output images')
    p.add_argument('--palette', type=str, default='gameboy4', help='Palette preset to enforce when --enforce-palette is used')
    p.add_argument('--list-palettes', action='store_true', help='List available palette presets and exit')
    p.add_argument('--max-jobs', type=int, default=0, help='Stop after this many successful jobs (0 = no limit)')
    p.add_argument('--max-failures', type=int, default=5, help='Stop after this many failures')
    p.add_argument('--direct-api', action='store_true', help='Call Recraft API directly using RECRAFT_API_KEY instead of a local helper/client')
    p.add_argument('--ledger', type=str, help='CSV provenance ledger to update after each successful generation')
    p.add_argument('--only', action='append', default=[], help='Restrict generation to manifest entries with these names (can be passed multiple times)')
    args = p.parse_args()

    if args.list_palettes:
        for k in sorted(PALETTES.keys()):
            spec = PALETTES[k]
            if isinstance(spec, tuple) and spec[0] == 'bits':
                desc = f"generator:{spec[1]}:{spec[2]}:{spec[3]}"
            else:
                desc = f"entries={len(spec)}"
            print(f"{k}\t{desc}")
        return 0

    try:
        manifest = load_manifest_items(args.manifest)
    except Exception as e:
        print('Failed to load manifest input:', e); sys.exit(3)
    mp = Path(args.manifest)

    if args.only:
        selected = set(args.only)
        manifest = [item for item in manifest if item.get('name') in selected]
        if not manifest:
            print('No manifest entries matched --only filters'); sys.exit(7)

    problems = []
    for i,item in enumerate(manifest):
        errs = validate_item(i, item)
        if errs:
            problems.append((i, errs))
    if problems:
        print('Manifest validation failed:')
        for i,errs in problems:
            for e in errs: print(f' - entry {i}: {e}')
        sys.exit(5)

    client = None
    ctype = None
    api_key = None
    if args.direct_api:
        api_key = os.environ.get('RECRAFT_API_KEY')
        if not api_key:
            print('RECRAFT_API_KEY is not set; cannot use --direct-api'); sys.exit(6)
        if not HAS_REQUESTS:
            print('requests is not available; install it to use --direct-api'); sys.exit(6)
        print('Using direct Recraft API mode')
    else:
        client, ctype = find_client()
        if not client:
            print('No recraft client or python helper found. Build recraft_gen or add tommygoomba/recraft_generate.py'); sys.exit(6)
        print('Using client:', client, 'type=', ctype)
    print('Items to generate:', len(manifest))
    if args.dry_run:
        print('Dry-run: no jobs will be executed. Manifest validated OK.')
        sys.exit(0)
    if not args.yes:
        ans = input(f'Proceed with {len(manifest)} generations (may consume credits)? Type YES to continue: ')
        if ans.strip().upper() != 'YES': print('Aborted'); sys.exit(0)

    # run concurrently with safeguards
    results = []
    successes = 0
    failures = 0
    max_jobs = args.max_jobs
    max_failures = args.max_failures
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {}
        for item in manifest:
            if max_jobs > 0 and successes >= max_jobs:
                print('Reached max-jobs limit; skipping remaining items')
                break
            if args.direct_api:
                f = ex.submit(run_job_direct_api, mp, item, api_key)
            elif ctype == 'bin':
                f = ex.submit(run_job_bin, client, item)
            else:
                f = ex.submit(run_job_py, client, item)
            futures[f] = item
        for f in as_completed(futures):
            item = futures[f]
            rc, out, err = f.result()
            print('---')
            print('Generated ->', item.get('out'))
            print('return code:', rc)
            if out: print('stdout:', out[:1000])
            if err: print('stderr:', err[:1000])
            if rc == 0:
                # optional palette enforcement
                if args.enforce_palette:
                    ok, msg = enforce_palette_on_file(resolve_output_path(mp, item.get('out')), args.palette)
                    if not ok:
                        print(f'Palette enforcement failed for {item.get("out")}:', msg)
                if args.ledger:
                    update_ledger(args.ledger, item, resolve_output_path(mp, item.get('out')))
                successes += 1
            else:
                failures += 1
            # check failure limit
            if max_failures > 0 and failures >= max_failures:
                print('Reached max-failures limit; aborting remaining jobs')
                break
    elapsed = time.time() - start_time
    print(f'Batch run complete in {elapsed:.1f}s (successes={successes}, failures={failures})')

if __name__ == '__main__':
    sys.exit(main())
