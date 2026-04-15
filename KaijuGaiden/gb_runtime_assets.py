import os
import re
from PIL import Image, ImageDraw, ImageEnhance


GB_HEADER_SPECS = {
    'player_idle': ('spr_rei_generated.h', 'spr_rei_idle_data', (2, 3), 'player'),
    'player_run': ('spr_rei_generated.h', 'spr_rei_run_data', (2, 3), 'player'),
    'player_attack': ('spr_rei_generated.h', 'spr_rei_attack_data', (2, 3), 'player'),
    'boss_p1': ('spr_boss_generated.h', 'spr_boss_p1_data', (4, 2), 'boss'),
    'boss_p2': ('spr_boss_generated.h', 'spr_boss_p2_data', (4, 2), 'boss'),
    'boss_p3': ('spr_boss_generated.h', 'spr_boss_p3_data', (4, 2), 'boss'),
    'minion_base': ('spr_minion_generated.h', 'spr_minion_data', (2, 2), 'minion'),
    'fx_hit': ('spr_fx_generated.h', 'spr_fx_hit_data', (2, 1), 'fx_hit'),
    'fx_nano': ('spr_fx_generated.h', 'spr_fx_nano_data', (2, 1), 'fx_nano'),
    'cinematic_player': ('spr_cinematic_generated.h', 'spr_cinematic_a', (4, 3), 'player'),
    'cinematic_boss': ('spr_cinematic_generated.h', 'spr_cinematic_b', (4, 3), 'boss'),
}


ROLE_PALETTES = {
    'player': ((0, 0, 0, 0), (18, 30, 43, 255), (74, 147, 176, 255), (233, 244, 250, 255)),
    'boss': ((0, 0, 0, 0), (45, 12, 18, 255), (131, 54, 52, 255), (235, 183, 142, 255)),
    'minion': ((0, 0, 0, 0), (34, 26, 18, 255), (155, 110, 63, 255), (241, 212, 165, 255)),
    'fx_hit': ((0, 0, 0, 0), (72, 24, 10, 255), (230, 120, 35, 255), (255, 232, 142, 255)),
    'fx_nano': ((0, 0, 0, 0), (25, 18, 56, 255), (111, 88, 220, 255), (210, 248, 255, 255)),
}


VISUAL_SEED_PROFILES = {
    'cathedral_spire': {
        'palette_shift': (18, 12, 4),
        'horn_bias': 2,
        'tracery_bias': 3,
        'arch_bias': 3,
        'spine_bias': 2,
        'window_bias': 2,
        'crown_bias': 3,
        'fang_bias': 0,
        'flare_bias': 1,
    },
    'gargoyle_cloister': {
        'palette_shift': (-8, 6, 14),
        'horn_bias': 3,
        'tracery_bias': 2,
        'arch_bias': 2,
        'spine_bias': 3,
        'window_bias': 1,
        'crown_bias': 1,
        'fang_bias': 3,
        'flare_bias': 0,
    },
    'rose_transept': {
        'palette_shift': (14, -4, -6),
        'horn_bias': 1,
        'tracery_bias': 4,
        'arch_bias': 4,
        'spine_bias': 1,
        'window_bias': 3,
        'crown_bias': 1,
        'fang_bias': 0,
        'flare_bias': 4,
    },
}


def _header_text(header_root, file_name):
    path = os.path.join(header_root, file_name)
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as handle:
        return handle.read()


def _parse_symbol_tiles(text, symbol_name):
    pattern = re.compile(rf"static const uint8_t\s+{re.escape(symbol_name)}\[(\d+)\]\[16\]\s*=\s*\{{(.*?)\n\}};", re.S)
    match = pattern.search(text)
    if not match:
        return []
    values = [int(token, 16) for token in re.findall(r'0x[0-9A-Fa-f]+', match.group(2))]
    tiles = []
    for index in range(0, len(values), 16):
        tile = values[index:index + 16]
        if len(tile) == 16:
            tiles.append(tile)
    return tiles


def _decode_tile(tile_bytes, palette):
    image = Image.new('RGBA', (8, 8), palette[0])
    pixels = image.load()
    for row in range(8):
        low_byte = tile_bytes[row * 2]
        high_byte = tile_bytes[(row * 2) + 1]
        for column in range(8):
            shift = 7 - column
            color_index = ((low_byte >> shift) & 1) | (((high_byte >> shift) & 1) << 1)
            pixels[column, row] = palette[color_index]
    return image


def _compose_sprite(tiles, grid, palette):
    columns, rows = grid
    sprite = Image.new('RGBA', (columns * 8, rows * 8), (0, 0, 0, 0))
    for tile_index, tile_bytes in enumerate(tiles):
        tile_image = _decode_tile(tile_bytes, palette)
        x_offset = (tile_index % columns) * 8
        y_offset = (tile_index // columns) * 8
        sprite.alpha_composite(tile_image, (x_offset, y_offset))
    return sprite


def load_gb_base_assets(header_root):
    base_assets = {}
    for key, (file_name, symbol_name, grid, role_name) in GB_HEADER_SPECS.items():
        text = _header_text(header_root, file_name)
        if not text:
            continue
        tiles = _parse_symbol_tiles(text, symbol_name)
        if not tiles:
            continue
        base_assets[key] = {
            'image': _compose_sprite(tiles, grid, ROLE_PALETTES[role_name]),
            'role': role_name,
        }
    return base_assets


def _bbox_or_full(image):
    alpha = image.getchannel('A')
    return alpha.getbbox() or (0, 0, image.width, image.height)


def _accent_for_role(role_name, context):
    boost_active = bool(context.get('boost_active', False))
    beat_perfect = bool(context.get('beat_perfect', False))
    if role_name == 'player':
        return (248, 214, 116, 255) if beat_perfect else (141, 232, 251, 255)
    if role_name == 'boss':
        return (223, 132, 93, 255) if boost_active else (182, 233, 171, 255)
    if role_name == 'minion':
        return (242, 175, 87, 255)
    if role_name == 'fx_nano':
        return (215, 255, 255, 255)
    return (255, 224, 149, 255)


def _stable_seed(*parts):
    total = 0
    for part in parts:
        text = str(part)
        for char in text:
            total = ((total * 131) + ord(char)) & 0xFFFFFFFF
    return total


def _select_visual_profile(context):
    profile_id = context.get('visual_profile', 'cathedral_spire')
    return VISUAL_SEED_PROFILES.get(profile_id, VISUAL_SEED_PROFILES['cathedral_spire'])


def _shift_palette(image, shift):
    shifted = image.copy()
    pixels = shifted.load()
    for y_pos in range(shifted.height):
        for x_pos in range(shifted.width):
            red, green, blue, alpha = pixels[x_pos, y_pos]
            if alpha == 0:
                continue
            pixels[x_pos, y_pos] = (
                max(0, min(255, red + shift[0])),
                max(0, min(255, green + shift[1])),
                max(0, min(255, blue + shift[2])),
                alpha,
            )
    return shifted


def _darken_for_conditions(image, metrics, context):
    brightness = float(metrics.get('brightness', 0.5))
    confidence = float(metrics.get('confidence', 0.0))
    hp_ratio = float(context.get('hp_ratio', 1.0))
    contrast = 1.12 + (confidence * 0.14)
    shade = 0.95 + max(0.0, brightness - 0.45) * 0.18
    shade -= (1.0 - hp_ratio) * 0.10
    shaded = ImageEnhance.Contrast(image).enhance(contrast)
    return ImageEnhance.Brightness(shaded).enhance(max(0.72, shade))


def _draw_horns(draw, bbox, accent, strength):
    if strength <= 0:
        return
    left, top, right, _ = bbox
    horn_height = max(2, strength)
    draw.line((left + 3, top + 2, left + 1, top - horn_height), fill=accent, width=1)
    draw.line((right - 4, top + 2, right - 2, top - horn_height), fill=accent, width=1)
    if strength > 2:
        draw.point((left + 2, top - horn_height), fill=accent)
        draw.point((right - 3, top - horn_height), fill=accent)


def _draw_feathers(draw, bbox, accent, density, seed):
    if density <= 0:
        return
    left, top, right, _ = bbox
    for index in range(density):
        x_pos = left + 1 + ((index * 3 + seed) % max(2, right - left - 2))
        draw.line((x_pos, top + 4, x_pos - 1, top + 1), fill=accent, width=1)


def _draw_scales(draw, image, bbox, accent, density, seed):
    if density <= 0:
        return
    pixels = image.load()
    left, top, right, bottom = bbox
    for y_pos in range(top + 4, bottom - 1, 3):
        for x_pos in range(left + 1, right - 1, 3):
            if ((x_pos + y_pos + seed) % max(2, 5 - density)) != 0:
                continue
            if pixels[x_pos, y_pos][3] == 0:
                continue
            draw.point((x_pos, y_pos), fill=accent)


def _draw_blisters(draw, image, bbox, accent, count, seed):
    if count <= 0:
        return
    pixels = image.load()
    left, top, right, bottom = bbox
    width = max(1, right - left - 2)
    height = max(1, bottom - top - 2)
    for index in range(count):
        x_pos = left + 1 + ((seed * 5 + index * 7) % width)
        y_pos = top + 2 + ((seed * 3 + index * 5) % height)
        if pixels[x_pos, y_pos][3] == 0:
            continue
        draw.point((x_pos, y_pos), fill=accent)
        draw.point((min(right - 1, x_pos + 1), y_pos), fill=(255, 244, 213, 255))


def _draw_spines(draw, bbox, accent, count, seed):
    if count <= 0:
        return
    left, top, right, bottom = bbox
    for index in range(count):
        x_pos = left + 1 + ((seed + index * 5) % max(2, right - left - 2))
        draw.line((x_pos, top + 1, x_pos + 1, max(top - 4, top - 1 - (index % 3))), fill=accent, width=1)
        draw.line((x_pos, bottom - 2, x_pos - 1, min(bottom + 3, bottom + 1 + (index % 2))), fill=accent, width=1)


def _draw_arches(draw, bbox, accent, count, seed):
    if count <= 0:
        return
    left, top, right, bottom = bbox
    width = max(6, right - left)
    base_y = min(bottom - 2, top + max(5, (bottom - top) // 2))
    for index in range(count):
        x_pos = left + 2 + ((index * 5 + seed) % max(4, width - 6))
        draw.line((x_pos, base_y, x_pos + 2, base_y - 3), fill=accent)
        draw.line((x_pos + 4, base_y, x_pos + 2, base_y - 3), fill=accent)
        draw.line((x_pos, base_y, x_pos + 4, base_y), fill=accent)


def _draw_tracery(draw, image, bbox, accent, density, seed):
    if density <= 0:
        return
    pixels = image.load()
    left, top, right, bottom = bbox
    for row in range(top + 3, bottom - 2, 4):
        for col in range(left + 2, right - 2, 4):
            if ((row + col + seed) % max(2, 6 - density)) != 0:
                continue
            if pixels[col, row][3] == 0:
                continue
            draw.line((col - 1, row, col + 1, row), fill=accent)
            draw.line((col, row - 1, col, row + 1), fill=accent)


def _draw_rose_window(draw, bbox, accent, strength):
    if strength <= 0:
        return
    left, top, right, bottom = bbox
    center_x = (left + right) // 2
    center_y = top + max(3, (bottom - top) // 3)
    draw.point((center_x, center_y), fill=accent)
    draw.line((center_x - 2, center_y, center_x + 2, center_y), fill=accent)
    draw.line((center_x, center_y - 2, center_x, center_y + 2), fill=accent)


def _draw_keystone_crown(draw, bbox, accent, strength):
    if strength <= 0:
        return
    left, top, right, _ = bbox
    center_x = (left + right) // 2
    for index in range(max(1, strength)):
        offset = (index - (strength // 2)) * 2
        draw.line((center_x + offset, top + 1, center_x + offset, top - 2 - (index % 2)), fill=accent)
    draw.line((center_x - 3, top + 2, center_x + 3, top + 2), fill=accent)


def _draw_fang_fringe(draw, bbox, accent, count, seed):
    if count <= 0:
        return
    left, _, right, bottom = bbox
    width = max(6, right - left - 4)
    for index in range(count):
        x_pos = left + 2 + ((index * 4 + seed) % width)
        draw.line((x_pos, bottom - 2, x_pos + 1, bottom + 1 + (index % 2)), fill=accent)
        draw.line((x_pos + 2, bottom - 2, x_pos + 1, bottom + 1 + (index % 2)), fill=accent)


def _draw_rose_flare(draw, bbox, accent, strength):
    if strength <= 0:
        return
    left, top, right, bottom = bbox
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    radius = max(2, min(4, strength))
    draw.line((center_x - radius, center_y, center_x + radius, center_y), fill=accent)
    draw.line((center_x, center_y - radius, center_x, center_y + radius), fill=accent)
    draw.line((center_x - radius + 1, center_y - radius + 1, center_x + radius - 1, center_y + radius - 1), fill=accent)
    draw.line((center_x - radius + 1, center_y + radius - 1, center_x + radius - 1, center_y - radius + 1), fill=accent)


def _apply_runtime_mutation(image, role_name, metrics, context, variant_seed):
    seed_profile = _select_visual_profile(context)
    profile_seed = _stable_seed(context.get('playthrough_seed', 0), context.get('visual_profile', 'cathedral_spire'), role_name, variant_seed)
    mutated = _shift_palette(_darken_for_conditions(image, metrics, context), seed_profile['palette_shift'])
    bbox = _bbox_or_full(mutated)
    draw = ImageDraw.Draw(mutated)
    accent = _accent_for_role(role_name, context)
    proximity = float(metrics.get('proximity', 0.35))
    eye_open = float(metrics.get('eye_open', 0.5))
    dilation = float(metrics.get('dilation', 0.5))
    edge_density = float(metrics.get('edge_density', 0.0))
    confidence = float(metrics.get('confidence', 0.0))
    aggression = float(context.get('aggression', 0.0))
    defense = float(context.get('defense', 0.0))
    movement_energy = float(context.get('movement_energy', 0.0))
    input_pressure = int(context.get('input_pressure', 0))
    horn_strength = int(round(proximity * 3.0)) + seed_profile['horn_bias'] + (1 if role_name == 'boss' else 0)
    feather_density = int(round(eye_open * 3.0)) + (1 if role_name == 'player' and context.get('beat_perfect') else 0)
    scale_density = int(round((proximity + edge_density + confidence + aggression) * 2.0))
    blister_count = int(round(dilation * 4.0)) + (1 if role_name == 'boss' and context.get('phase', 1) >= 3 else 0)
    spine_count = seed_profile['spine_bias'] + int(round(movement_energy * 3.0)) + (1 if role_name == 'boss' else 0)
    arch_count = seed_profile['arch_bias'] + int(round(defense * 2.0))
    tracery_density = seed_profile['tracery_bias'] + int(round((confidence + aggression) * 2.0))
    rose_strength = seed_profile['window_bias'] + (1 if context.get('beat_perfect') else 0)
    crown_strength = seed_profile.get('crown_bias', 0) + int(round(confidence * 2.0))
    fang_count = seed_profile.get('fang_bias', 0) + int(round(aggression * 2.0))
    flare_strength = seed_profile.get('flare_bias', 0) + int(round((movement_energy + input_pressure * 0.08) * 2.0))
    if role_name in ('player', 'boss'):
        _draw_horns(draw, bbox, accent, horn_strength)
        _draw_feathers(draw, bbox, accent, feather_density, variant_seed)
        _draw_keystone_crown(draw, bbox, accent, crown_strength)
    if role_name in ('player', 'boss', 'minion'):
        _draw_scales(draw, mutated, bbox, accent, scale_density, profile_seed)
        _draw_blisters(draw, mutated, bbox, accent, blister_count, profile_seed)
        _draw_spines(draw, bbox, accent, spine_count, profile_seed)
        _draw_arches(draw, bbox, accent, arch_count, profile_seed)
        _draw_tracery(draw, mutated, bbox, accent, tracery_density, profile_seed)
        _draw_fang_fringe(draw, bbox, accent, fang_count if role_name != 'minion' else max(0, fang_count - 1), profile_seed)
        if role_name != 'minion' or input_pressure > 1:
            _draw_rose_window(draw, bbox, accent, rose_strength)
            _draw_rose_flare(draw, bbox, accent, flare_strength)
    if context.get('boost_active'):
        left, top, right, bottom = bbox
        draw.rectangle((left, bottom - 2, right - 1, bottom - 1), fill=accent)
    if role_name == 'player' and context.get('facing') == 'left':
        mutated = mutated.transpose(Image.FLIP_LEFT_RIGHT)
    return mutated


def build_runtime_bundle(base_assets, metrics, context):
    if not base_assets:
        return {}
    bundle = {}
    for key, entry in base_assets.items():
        bundle[key] = _apply_runtime_mutation(entry['image'].copy(), entry['role'], metrics, context, context.get('variant_seed', 0))
    minion_base = base_assets.get('minion_base', {}).get('image')
    if minion_base is not None:
        for variant in range(3):
            minion_context = dict(context)
            minion_context['variant_seed'] = context.get('variant_seed', 0) + variant + 1
            bundle[f'minion{variant + 1}'] = _apply_runtime_mutation(minion_base.copy(), 'minion', metrics, minion_context, minion_context['variant_seed'])
    if 'fx_hit' in bundle:
        bundle['attackfx1'] = bundle['fx_hit']
        bundle['attackfx2'] = _apply_runtime_mutation(base_assets['fx_hit']['image'].copy(), 'fx_hit', metrics, dict(context, variant_seed=context.get('variant_seed', 0) + 4), context.get('variant_seed', 0) + 4)
        bundle['blodfx'] = bundle['attackfx2']
    if 'fx_nano' in bundle:
        bundle['nanocell1'] = bundle['fx_nano']
        bundle['nanocell2'] = _apply_runtime_mutation(base_assets['fx_nano']['image'].copy(), 'fx_nano', metrics, dict(context, variant_seed=context.get('variant_seed', 0) + 5), context.get('variant_seed', 0) + 5)
    return bundle