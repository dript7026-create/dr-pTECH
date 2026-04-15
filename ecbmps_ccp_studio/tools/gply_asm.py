"""gply_asm.py - GPLY Bytecode Assembler for CCP Studio
==========================================================
Converts a text-based .gplya source file into a binary .gply file
suitable for embedding in a CCP v3 container via `ccp_compiler -g`.

Usage:
    python gply_asm.py input.gplya [-o output.gply]

Source Format Overview
----------------------

    ; comment (rest of line ignored)

    .entity <name>
        sprite  "path/to/asset.png"
        pos     <x> <y>
        size    <width> <height>
        timeline <frame_count>
        visible  <0|1>
        page     <num|all>          ; all => 0xFF

    .hitbox <name>
        entity  <entity_name>
        frame   <num|all>           ; all => 0xFFFF
        offset  <ox> <oy>
        size    <width> <height>
        kind    <solid|trigger|hurtbox|button>

    .variable <name>
        initial <int_value>

    .script <name>
        <opcode> [operand ...]      ; see Opcodes section below
        ...

    .scene <name>
        entities <start_entity> <count>   ; or omit for 0 entities
        bindings <start_binding> <count>  ; or omit for 0 bindings
        page     <num|all>
        flags    <hex_or_decimal>

    .binding
        event   <event_name>
        button  <btn_name|none>
        source  <entity_name|any>
        target  <entity_name|any>
        script  <script_name>
        page    <num|all>

Opcodes
-------
    nop
    push_int   <int32>
    push_float <float32>
    push_str   <"string literal">
    pop
    dup
    set_var  <var_name>
    get_var  <var_name>
    jmp      <label>
    jmp_if   <label>
    jmp_ifnot <label>
    call     <script_name>
    ret
    halt
    ent_spawn    <entity_name>
    ent_destroy
    ent_move
    ent_set_pos
    ent_get_pos
    ent_set_anim
    ent_set_frame
    ent_show
    ent_hide
    hit_test
    point_test
    goto_page
    set_scene    <scene_name>
    play_anim    <"anim_name">
    get_button   <btn_name>
    get_axis     <axis_name>
    get_dpad
    show_dialogue <"text">
    show_popup    <"text">
    play_sound   <sound_id>
    add
    sub
    mul
    div
    cmp_eq
    cmp_lt
    cmp_gt
    and
    or
    not
    label <name>                    ; defines a jump target (not emitted)

Event names:
    page_enter page_exit frame_tick click
    hover_enter hover_exit collide trigger
    button_down button_up scene_enter scene_exit

Button names (for binding.button and get_button):
    a b x y dpad_up dpad_down dpad_left dpad_right
    start back lb rb lstick rstick none

Axis names (for get_axis):
    lx ly rx ry

Hitbox kind:
    solid  trigger  hurtbox  button
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from io import BytesIO
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Constants mirroring ccp_gameplay.h
# ---------------------------------------------------------------------------

GPLY_MAGIC = 0x594C5047  # "GPLY" little-endian
GPLY_VERSION = 1

# Opcodes
OPCODES: dict[str, int] = {
    "nop": 0x00,
    "push_int": 0x01,
    "push_float": 0x02,
    "push_str": 0x03,
    "pop": 0x04,
    "dup": 0x05,
    "set_var": 0x10,
    "get_var": 0x11,
    "jmp": 0x20,
    "jmp_if": 0x21,
    "jmp_ifnot": 0x22,
    "call": 0x23,
    "ret": 0x24,
    "halt": 0xFF,
    "ent_spawn": 0x30,
    "ent_destroy": 0x31,
    "ent_move": 0x32,
    "ent_set_pos": 0x33,
    "ent_get_pos": 0x34,
    "ent_set_anim": 0x35,
    "ent_set_frame": 0x36,
    "ent_show": 0x37,
    "ent_hide": 0x38,
    "hit_test": 0x40,
    "point_test": 0x41,
    "goto_page": 0x50,
    "set_scene": 0x51,
    "play_anim": 0x52,
    "get_button": 0x60,
    "get_axis": 0x61,
    "get_dpad": 0x62,
    "show_dialogue": 0x70,
    "show_popup": 0x71,
    "play_sound": 0x72,
    "add": 0x80,
    "sub": 0x81,
    "mul": 0x82,
    "div": 0x83,
    "cmp_eq": 0x84,
    "cmp_lt": 0x85,
    "cmp_gt": 0x86,
    "and": 0x87,
    "or": 0x88,
    "not": 0x89,
}

EVENT_NAMES: dict[str, int] = {
    "page_enter": 0,
    "page_exit": 1,
    "frame_tick": 2,
    "click": 3,
    "hover_enter": 4,
    "hover_exit": 5,
    "collide": 6,
    "trigger": 7,
    "button_down": 8,
    "button_up": 9,
    "scene_enter": 10,
    "scene_exit": 11,
}

BUTTON_IDS: dict[str, int] = {
    "a": 0,
    "b": 1,
    "x": 2,
    "y": 3,
    "dpad_up": 4,
    "dpad_down": 5,
    "dpad_left": 6,
    "dpad_right": 7,
    "start": 8,
    "back": 9,
    "lb": 10,
    "rb": 11,
    "lstick": 12,
    "rstick": 13,
    "none": 0xFF,
}

AXIS_IDS: dict[str, int] = {
    "lx": 0,
    "ly": 1,
    "rx": 2,
    "ry": 3,
}

HITBOX_KINDS: dict[str, int] = {
    "solid": 0,
    "trigger": 1,
    "hurtbox": 2,
    "button": 3,
}


# ---------------------------------------------------------------------------
# Intermediate representation
# ---------------------------------------------------------------------------


class EntityEntry(NamedTuple):
    name: str
    sprite: str
    x: int
    y: int
    width: int
    height: int
    timeline: int
    visible: int
    page: int  # 0xFF = any page


class HitboxEntry(NamedTuple):
    name: str
    entity_name: str
    frame: int  # 0xFFFF = all frames
    ox: int
    oy: int
    width: int
    height: int
    kind: int


class VariableEntry(NamedTuple):
    name: str
    initial: int


class SceneEntry(NamedTuple):
    name: str
    first_entity: int
    entity_count: int
    first_binding: int
    binding_count: int
    page: int
    flags: int


class BindingEntry(NamedTuple):
    event_type: int
    filter_btn: int
    source_entity_name: str  # "" = any
    target_entity_name: str  # "" = any
    script_name: str
    page: int


# Instruction = (opcode, raw_operand_bytes) or ('label', name) or ('jmp*', target_label)
Instruction = tuple


class ScriptEntry:
    def __init__(self, name: str) -> None:
        self.name = name
        self.instructions: list[Instruction] = []


# ---------------------------------------------------------------------------
# String table
# ---------------------------------------------------------------------------


class StringTable:
    def __init__(self) -> None:
        self._table: dict[str, int] = {}
        self._data = bytearray()

    def intern(self, s: str) -> int:
        if s in self._table:
            return self._table[s]
        offset = len(self._data)
        self._table[s] = offset
        self._data += s.encode("utf-8") + b"\x00"
        return offset

    def bytes(self) -> bytes:
        return bytes(self._data)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _parse_int(tok: str) -> int:
    tok = tok.strip()
    if tok.startswith("0x") or tok.startswith("0X"):
        return int(tok, 16)
    return int(tok)


def _parse_page(tok: str) -> int:
    if tok == "all":
        return 0xFF
    return _parse_int(tok)


def _parse_frame(tok: str) -> int:
    if tok == "all":
        return 0xFFFF
    return _parse_int(tok)


def _unquote(tok: str, lineno: int) -> str:
    tok = tok.strip()
    if not (tok.startswith('"') and tok.endswith('"') and len(tok) >= 2):
        raise AssemblerError(f"line {lineno}: expected quoted string, got: {tok!r}")
    return tok[1:-1]


class AssemblerError(Exception):
    pass


def _split_first_token(line: str) -> tuple[str, str]:
    """Split 'opcode rest...' respecting quoted strings for rest."""
    stripped = line.strip()
    if not stripped:
        return "", ""
    parts = stripped.split(None, 1)
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    return first, rest


def _tokenize_rest(rest: str) -> list[str]:
    """Split rest of line into tokens; handles one quoted string."""
    rest = rest.strip()
    if not rest:
        return []
    if '"' in rest:
        # Find quoted portion and return as single token with surrounding tokens
        tokens: list[str] = []
        i = 0
        while i < len(rest):
            if rest[i] == '"':
                j = rest.index('"', i + 1)
                tokens.append(rest[i : j + 1])
                i = j + 1
            elif rest[i].isspace():
                i += 1
            else:
                j = i
                while j < len(rest) and not rest[j].isspace() and rest[j] != '"':
                    j += 1
                tokens.append(rest[i:j])
                i = j
        return tokens
    return rest.split()


def parse(
    src: str,
) -> tuple[
    list[EntityEntry],
    list[HitboxEntry],
    list[VariableEntry],
    list[ScriptEntry],
    list[SceneEntry],
    list[BindingEntry],
]:
    entities: list[EntityEntry] = []
    hitboxes: list[HitboxEntry] = []
    variables: list[VariableEntry] = []
    scripts: list[ScriptEntry] = []
    scenes: list[SceneEntry] = []
    bindings: list[BindingEntry] = []

    lines = src.splitlines()
    i = 0

    def next_content_line(i: int) -> tuple[int, int, str]:
        """Return (next_i, lineno, stripped_line) skipping blank/comment lines."""
        while i < len(lines):
            raw = lines[i]
            stripped = raw.split(";", 1)[0].strip()
            if stripped:
                return i + 1, i + 1, stripped
            i += 1
        return i, -1, ""

    def peek_is_property(i: int) -> tuple[bool, int, str]:
        """Peek ahead: is next non-blank line a property (not a directive)?"""
        j = i
        while j < len(lines):
            raw = lines[j]
            stripped = raw.split(";", 1)[0].strip()
            if stripped:
                return (not stripped.startswith(".")), j, stripped
            j += 1
        return False, j, ""

    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.split(";", 1)[0].strip()
        if not stripped:
            continue
        lineno = i

        if not stripped.startswith("."):
            raise AssemblerError(
                f"line {lineno}: unexpected content outside a section: {stripped!r}"
            )

        directive, rest = _split_first_token(stripped)

        # ----------------------------------------------------------------
        if directive == ".entity":
            name = rest.strip()
            if not name:
                raise AssemblerError(f"line {lineno}: .entity requires a name")
            props: dict[str, str] = {}
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                key, val = _split_first_token(peek_line)
                props[key] = val
            sprite = _unquote(props.get("sprite", '""'), lineno)
            px, py = (int(v) for v in props.get("pos", "0 0").split())
            sw, sh = (int(v) for v in props.get("size", "16 16").split())
            timeline = int(props.get("timeline", "1"))
            visible = int(props.get("visible", "1"))
            page = _parse_page(props.get("page", "all"))
            entities.append(
                EntityEntry(name, sprite, px, py, sw, sh, timeline, visible, page)
            )

        # ----------------------------------------------------------------
        elif directive == ".hitbox":
            name = rest.strip()
            if not name:
                raise AssemblerError(f"line {lineno}: .hitbox requires a name")
            props = {}
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                key, val = _split_first_token(peek_line)
                props[key] = val
            entity_name = props.get("entity", "")
            frame = _parse_frame(props.get("frame", "all"))
            ox, oy = (int(v) for v in props.get("offset", "0 0").split())
            hw, hh = (int(v) for v in props.get("size", "16 16").split())
            kind_s = props.get("kind", "solid")
            kind = HITBOX_KINDS.get(kind_s)
            if kind is None:
                raise AssemblerError(f"line {lineno}: unknown hitbox kind {kind_s!r}")
            hitboxes.append(HitboxEntry(name, entity_name, frame, ox, oy, hw, hh, kind))

        # ----------------------------------------------------------------
        elif directive == ".variable":
            name = rest.strip()
            if not name:
                raise AssemblerError(f"line {lineno}: .variable requires a name")
            props = {}
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                key, val = _split_first_token(peek_line)
                props[key] = val
            initial = _parse_int(props.get("initial", "0"))
            variables.append(VariableEntry(name, initial))

        # ----------------------------------------------------------------
        elif directive == ".script":
            name = rest.strip()
            if not name:
                raise AssemblerError(f"line {lineno}: .script requires a name")
            script = ScriptEntry(name)
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                op, op_rest = _split_first_token(peek_line)
                op_tokens = _tokenize_rest(op_rest)
                script.instructions.append((op, op_tokens, peek_i + 1))  # store lineno
            scripts.append(script)

        # ----------------------------------------------------------------
        elif directive == ".scene":
            name = rest.strip()
            if not name:
                raise AssemblerError(f"line {lineno}: .scene requires a name")
            props = {}
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                key, val = _split_first_token(peek_line)
                props[key] = val
            fe, ec = (0, 0)
            if "entities" in props:
                ent_parts = props["entities"].split()
                fe = _parse_int(ent_parts[0]) if ent_parts else 0
                ec = _parse_int(ent_parts[1]) if len(ent_parts) > 1 else 0
            fb, bc = (0, 0)
            if "bindings" in props:
                bnd_parts = props["bindings"].split()
                fb = _parse_int(bnd_parts[0]) if bnd_parts else 0
                bc = _parse_int(bnd_parts[1]) if len(bnd_parts) > 1 else 0
            page = _parse_page(props.get("page", "all"))
            flags = _parse_int(props.get("flags", "0"))
            scenes.append(SceneEntry(name, fe, ec, fb, bc, page, flags))

        # ----------------------------------------------------------------
        elif directive == ".binding":
            # .binding has no name on the directive line;
            # identity tracked by insertion order
            props = {}
            while True:
                is_prop, peek_i, peek_line = peek_is_property(i)
                if not is_prop:
                    break
                i = peek_i + 1
                key, val = _split_first_token(peek_line)
                props[key] = val
            evt_s = props.get("event", "page_enter")
            evt = EVENT_NAMES.get(evt_s)
            if evt is None:
                raise AssemblerError(f"line {lineno}: unknown event {evt_s!r}")
            btn_s = props.get("button", "none")
            btn = BUTTON_IDS.get(btn_s)
            if btn is None:
                raise AssemblerError(f"line {lineno}: unknown button {btn_s!r}")
            src = props.get("source", "any")
            tgt = props.get("target", "any")
            scr_name = props.get("script", "")
            page = _parse_page(props.get("page", "all"))
            bindings.append(
                BindingEntry(
                    evt,
                    btn,
                    "" if src == "any" else src,
                    "" if tgt == "any" else tgt,
                    scr_name,
                    page,
                )
            )

        else:
            raise AssemblerError(f"line {lineno}: unknown directive {directive!r}")

    return entities, hitboxes, variables, scripts, scenes, bindings


# ---------------------------------------------------------------------------
# Bytecode assembler for a single script
# ---------------------------------------------------------------------------


def _assemble_script(
    script: ScriptEntry,
    strtab: StringTable,
    entity_index: dict[str, int],
    scene_index: dict[str, int],
    script_index: dict[str, int],
    var_index: dict[str, int],
) -> bytes:
    """Two-pass bytecode assembler for one ScriptEntry."""

    # Pass 1: emit bytes, record label positions and patch sites
    buf = BytesIO()
    label_pos: dict[str, int] = {}
    patch_sites: list[tuple[int, str]] = []  # (buf_offset, label_name)

    for inst in script.instructions:
        op_name, tokens, lineno = inst

        if op_name == "label":
            if not tokens:
                raise AssemblerError(f"line {lineno}: label requires a name")
            label_pos[tokens[0]] = buf.tell()
            continue

        opcode = OPCODES.get(op_name)
        if opcode is None:
            raise AssemblerError(f"line {lineno}: unknown opcode {op_name!r}")

        buf.write(bytes([opcode]))

        if op_name == "push_int":
            v = _parse_int(tokens[0]) if tokens else 0
            buf.write(struct.pack("<i", v))

        elif op_name == "push_float":
            v = float(tokens[0]) if tokens else 0.0
            buf.write(struct.pack("<f", v))

        elif op_name == "push_str":
            if not tokens:
                raise AssemblerError(f"line {lineno}: push_str requires a string")
            s = _unquote(tokens[0], lineno)
            off = strtab.intern(s)
            buf.write(struct.pack("<H", off))

        elif op_name == "set_var":
            nm = tokens[0] if tokens else ""
            vi = var_index.get(nm)
            if vi is None:
                raise AssemblerError(f"line {lineno}: unknown variable {nm!r}")
            buf.write(struct.pack("<H", vi))

        elif op_name == "get_var":
            nm = tokens[0] if tokens else ""
            vi = var_index.get(nm)
            if vi is None:
                raise AssemblerError(f"line {lineno}: unknown variable {nm!r}")
            buf.write(struct.pack("<H", vi))

        elif op_name in ("jmp", "jmp_if", "jmp_ifnot"):
            lbl = tokens[0] if tokens else ""
            patch_offset = buf.tell()
            patch_sites.append((patch_offset, lbl))
            buf.write(struct.pack("<i", 0))  # placeholder

        elif op_name == "call":
            nm = tokens[0] if tokens else ""
            si = script_index.get(nm)
            if si is None:
                raise AssemblerError(f"line {lineno}: unknown script {nm!r}")
            buf.write(struct.pack("<H", si))

        elif op_name == "ent_spawn":
            nm = tokens[0] if tokens else ""
            ei = entity_index.get(nm)
            if ei is None:
                raise AssemblerError(f"line {lineno}: unknown entity {nm!r}")
            buf.write(struct.pack("<H", ei))

        elif op_name == "set_scene":
            nm = tokens[0] if tokens else ""
            sci = scene_index.get(nm)
            if sci is None:
                raise AssemblerError(f"line {lineno}: unknown scene {nm!r}")
            buf.write(struct.pack("<H", sci))

        elif op_name == "play_anim":
            if not tokens:
                raise AssemblerError(f"line {lineno}: play_anim requires a string")
            s = _unquote(tokens[0], lineno)
            off = strtab.intern(s)
            buf.write(struct.pack("<H", off))

        elif op_name == "get_button":
            nm = tokens[0].lower() if tokens else "none"
            bi = BUTTON_IDS.get(nm)
            if bi is None:
                raise AssemblerError(f"line {lineno}: unknown button {nm!r}")
            buf.write(bytes([bi]))

        elif op_name == "get_axis":
            nm = tokens[0].lower() if tokens else "lx"
            ai = AXIS_IDS.get(nm)
            if ai is None:
                raise AssemblerError(f"line {lineno}: unknown axis {nm!r}")
            buf.write(bytes([ai]))

        elif op_name in ("show_dialogue", "show_popup"):
            if not tokens:
                raise AssemblerError(f"line {lineno}: {op_name} requires a string")
            s = _unquote(tokens[0], lineno)
            off = strtab.intern(s)
            buf.write(struct.pack("<H", off))

        elif op_name == "play_sound":
            sid = _parse_int(tokens[0]) if tokens else 0
            buf.write(struct.pack("<H", sid))

        elif op_name == "goto_page":
            # no operand — page number comes from the stack at runtime
            pass

        # no operand opcodes: nop, pop, dup, ret, halt,
        # ent_destroy, ent_move, ent_set_pos, ent_get_pos,
        # ent_set_anim, ent_set_frame, ent_show, ent_hide,
        # hit_test, point_test, get_dpad,
        # add, sub, mul, div, cmp_eq, cmp_lt, cmp_gt, and, or, not

    raw = bytearray(buf.getvalue())

    # Pass 2: patch jump targets
    for patch_offset, label_name in patch_sites:
        target = label_pos.get(label_name)
        if target is None:
            raise AssemblerError(
                f"undefined label {label_name!r} in script {script.name!r}"
            )
        # jump offset is relative to PC *after* the 4-byte operand
        pc_after = patch_offset + 4
        rel = target - pc_after
        struct.pack_into("<i", raw, patch_offset, rel)

    return bytes(raw)


# ---------------------------------------------------------------------------
# Binary emitter
# ---------------------------------------------------------------------------


def assemble(src: str) -> bytes:
    entities, hitboxes, variables, scripts, scenes, bindings = parse(src)

    strtab = StringTable()

    # intern all names
    entity_index: dict[str, int] = {}
    for idx, e in enumerate(entities):
        entity_index[e.name] = idx
        strtab.intern(e.name)
        strtab.intern(e.sprite)

    script_index: dict[str, int] = {}
    for idx, s in enumerate(scripts):
        script_index[s.name] = idx
        strtab.intern(s.name)

    scene_index: dict[str, int] = {}
    for idx, sc in enumerate(scenes):
        scene_index[sc.name] = idx
        strtab.intern(sc.name)

    var_index: dict[str, int] = {}
    for idx, v in enumerate(variables):
        var_index[v.name] = idx
        strtab.intern(v.name)

    for hb in hitboxes:
        strtab.intern(hb.name)

    # Assemble all scripts first (bytecode offset accumulates)
    bytecode_buf = BytesIO()
    script_offsets: list[tuple[int, int]] = []  # (offset, length)
    for s in scripts:
        off = bytecode_buf.tell()
        bc = _assemble_script(
            s, strtab, entity_index, scene_index, script_index, var_index
        )
        bytecode_buf.write(bc)
        script_offsets.append((off, len(bc)))

    bytecode_bytes = bytecode_buf.getvalue()
    strtab_bytes = strtab.bytes()

    # Resolve entity names in bindings
    def resolve_entity(name: str) -> int:
        if name == "":
            return 0xFFFF
        i = entity_index.get(name)
        if i is None:
            raise AssemblerError(f"binding references unknown entity {name!r}")
        return i

    def resolve_script(name: str) -> int:
        i = script_index.get(name)
        if i is None:
            raise AssemblerError(f"binding references unknown script {name!r}")
        return i

    # Build binary sections
    entity_section = bytearray()
    for e in entities:
        name_off = strtab._table[e.name]
        sprite_off = strtab._table[e.sprite]
        entity_section += struct.pack(
            "<HHhhhHHBB",
            name_off,
            sprite_off,
            e.x,
            e.y,
            e.width,
            e.height,
            e.timeline,
            e.visible & 1,
            e.page & 0xFF,
        )  # 16 bytes: HH hh hh HH B B = 2+2+2+2+2+2+2+1+1 = 16 ✓

    hitbox_section = bytearray()
    for hb in hitboxes:
        eid = entity_index.get(hb.entity_name, 0xFFFF)
        hitbox_section += struct.pack(
            "<HHhhhHHBB",
            eid,
            hb.frame,
            hb.ox,
            hb.oy,
            hb.width,
            hb.height,
            0,  # width hi — actually layout is: entity_def_id, frame, ox, oy, w, h, kind, pad
            hb.kind,
            0,  # kind, padding
        )
        # Correction - use exact GplyHitboxDef layout (14 bytes):
        # uint16 entity_def_id, uint16 frame_index,
        # int16 offset_x, int16 offset_y,
        # uint16 width, uint16 height,
        # uint8 kind, uint8 padding
        # = 2+2+2+2+2+2+1+1 = 14

    # Rebuild hitbox section with correct struct
    hitbox_section = bytearray()
    for hb in hitboxes:
        eid = entity_index.get(hb.entity_name, 0xFFFF)
        hitbox_section += struct.pack(
            "<HHhhHHBB", eid, hb.frame, hb.ox, hb.oy, hb.width, hb.height, hb.kind, 0
        )  # 2+2+2+2+2+2+1+1 = 14 bytes ✓

    script_section = bytearray()
    for idx, s in enumerate(scripts):
        off, length = script_offsets[idx]
        name_off = strtab._table[s.name]
        script_section += struct.pack("<HII", name_off, off, length)
        # 2+4+4 = 10 bytes ✓

    scene_section = bytearray()
    for sc in scenes:
        name_off = strtab._table[sc.name]
        scene_section += struct.pack(
            "<HHHHHBB",
            name_off,
            sc.first_entity,
            sc.entity_count,
            sc.first_binding,
            sc.binding_count,
            sc.page & 0xFF,
            sc.flags & 0xFF,
        )  # 2+2+2+2+2+1+1 = 12 bytes ✓

    binding_section = bytearray()
    for b in bindings:
        src_eid = resolve_entity(b.source_entity_name)
        tgt_eid = resolve_entity(b.target_entity_name)
        scr_id = resolve_script(b.script_name)
        binding_section += struct.pack(
            "<BBHHHBB",
            b.event_type & 0xFF,
            b.filter_btn & 0xFF,
            src_eid,
            tgt_eid,
            scr_id,
            b.page & 0xFF,
            0,  # padding
        )  # 1+1+2+2+2+1+1 = 10 bytes ✓

    variable_section = bytearray()
    for v in variables:
        name_off = strtab._table[v.name]
        variable_section += struct.pack("<Hi", name_off, v.initial)
        # 2+4 = 6 bytes ✓

    # GplyHeader (28 bytes)
    header = struct.pack(
        "<IIHHHHHHI I",
        GPLY_MAGIC,
        GPLY_VERSION,
        len(entities) & 0xFFFF,
        len(hitboxes) & 0xFFFF,
        len(scripts) & 0xFFFF,
        len(scenes) & 0xFFFF,
        len(bindings) & 0xFFFF,
        len(variables) & 0xFFFF,
        len(strtab_bytes),
        len(bytecode_bytes),
    )
    # struct format: I I H H H H H H I I = 4+4+2+2+2+2+2+2+4+4 = 28 bytes
    # but "< IIHHHHHHI I" has a space — let's rebuild cleanly:
    header = struct.pack(
        "<IIHHHHHHI",
        GPLY_MAGIC,
        GPLY_VERSION,
        len(entities) & 0xFFFF,
        len(hitboxes) & 0xFFFF,
        len(scripts) & 0xFFFF,
        len(scenes) & 0xFFFF,
        len(bindings) & 0xFFFF,
        len(variables) & 0xFFFF,
        len(strtab_bytes),
    )
    header += struct.pack("<I", len(bytecode_bytes))
    # total: 4+4+2+2+2+2+2+2+4+4 = 28 bytes ✓

    return (
        header
        + bytes(entity_section)
        + bytes(hitbox_section)
        + bytes(script_section)
        + bytes(scene_section)
        + bytes(binding_section)
        + bytes(variable_section)
        + strtab_bytes
        + bytecode_bytes
    )


# ---------------------------------------------------------------------------
# Disassembler (–-disasm flag): read a .gply file and print a human-readable
# summary (not round-trip source, but useful for verification).
# ---------------------------------------------------------------------------


def disassemble(data: bytes) -> str:
    out: list[str] = []
    off = 0

    if len(data) < 28:
        return "ERROR: file too small for GplyHeader"

    magic, version, n_ent, n_hit, n_scr, n_scn, n_bnd, n_var, strtab_size = (
        struct.unpack_from("<IIHHHHHHI", data, 0)
    )
    (bc_size,) = struct.unpack_from("<I", data, 24)
    off = 28

    if magic != GPLY_MAGIC:
        return f"ERROR: bad magic 0x{magic:08X}"

    out.append(f"; GPLY v{version}")
    out.append(
        f"; entities={n_ent} hitboxes={n_hit} scripts={n_scr} scenes={n_scn} bindings={n_bnd} vars={n_var}"
    )
    out.append(f"; strtab={strtab_size}B  bytecode={bc_size}B")

    # Sections
    ent_off = off
    off += n_ent * 16
    hit_off = off
    off += n_hit * 14
    scr_off = off
    off += n_scr * 10
    scn_off = off
    off += n_scn * 12
    bnd_off = off
    off += n_bnd * 10
    var_off = off
    off += n_var * 6
    str_off = off
    off += strtab_size
    bc_off = off

    def get_str(offset: int) -> str:
        if str_off + offset >= len(data):
            return f"<str@{offset}>"
        end = data.index(b"\x00", str_off + offset)
        return data[str_off + offset : end].decode("utf-8", errors="replace")

    out.append("")
    for i in range(n_ent):
        o = ent_off + i * 16
        name_o, spr_o, x, y, w, h, tl, vis, page = struct.unpack_from(
            "<HHhhhHHBB", data, o
        )
        out.append(f".entity {get_str(name_o)}")
        out.append(
            f'    sprite "{get_str(spr_o)}"  pos {x} {y}  size {w} {h}  timeline {tl}  visible {vis}  page {"all" if page == 0xFF else page}'
        )

    out.append("")
    HITBOX_KIND_NAMES = {0: "solid", 1: "trigger", 2: "hurtbox", 3: "button"}
    for i in range(n_hit):
        o = hit_off + i * 14
        eid, frame, ox, oy, hw, hh, kind, _ = struct.unpack_from("<HHhhHHBB", data, o)
        out.append(
            f".hitbox  entity_id={eid}  frame={'all' if frame == 0xFFFF else frame}  offset={ox},{oy}  size={hw},{hh}  kind={HITBOX_KIND_NAMES.get(kind, kind)}"
        )

    out.append("")
    for i in range(n_var):
        o = var_off + i * 6
        name_o, init = struct.unpack_from("<Hi", data, o)
        out.append(f".variable {get_str(name_o)}  initial={init}")

    out.append("")
    INV_OPCODES = {v: k for k, v in OPCODES.items()}
    for i in range(n_scr):
        o = scr_off + i * 10
        name_o, bc_offset, bc_len = struct.unpack_from("<HII", data, o)
        out.append(f".script {get_str(name_o)}  ; bytecode @{bc_offset} len={bc_len}")
        pc = bc_off + bc_offset
        end = pc + bc_len
        while pc < end:
            opcode = data[pc]
            pc += 1
            op_name = INV_OPCODES.get(opcode, f"0x{opcode:02X}")
            operand = ""
            if opcode == 0x01:
                (v,) = struct.unpack_from("<i", data, pc)
                pc += 4
                operand = str(v)
            elif opcode == 0x02:
                (v,) = struct.unpack_from("<f", data, pc)
                pc += 4
                operand = str(v)
            elif opcode in (0x03, 0x52, 0x70, 0x71):
                (o2,) = struct.unpack_from("<H", data, pc)
                pc += 2
                operand = f'"{get_str(o2)}"'
            elif opcode in (0x10, 0x11):
                (vid,) = struct.unpack_from("<H", data, pc)
                pc += 2
                operand = f"var[{vid}]"
            elif opcode in (0x20, 0x21, 0x22):
                (rel,) = struct.unpack_from("<i", data, pc)
                pc += 4
                operand = f"+{rel}"
            elif opcode in (0x23, 0x51):
                (sid,) = struct.unpack_from("<H", data, pc)
                pc += 2
                operand = f"id={sid}"
            elif opcode == 0x30:
                (eid,) = struct.unpack_from("<H", data, pc)
                pc += 2
                operand = f"def={eid}"
            elif opcode in (0x60,):
                operand = f"btn={data[pc]}"
                pc += 1
            elif opcode == 0x61:
                operand = f"axis={data[pc]}"
                pc += 1
            elif opcode == 0x72:
                (sid,) = struct.unpack_from("<H", data, pc)
                pc += 2
                operand = f"snd={sid}"
            out.append(f"    {op_name}  {operand}".rstrip())

    out.append("")
    EVT_NAMES = {v: k for k, v in EVENT_NAMES.items()}
    BTN_NAMES = {v: k for k, v in BUTTON_IDS.items()}
    for i in range(n_bnd):
        o = bnd_off + i * 10
        evt, btn, src_e, tgt_e, scr_id, page, _ = struct.unpack_from(
            "<BBHHHBB", data, o
        )
        out.append(
            f".binding  event={EVT_NAMES.get(evt, evt)}  button={BTN_NAMES.get(btn, '?')}  "
            f"source={'any' if src_e == 0xFFFF else src_e}  target={'any' if tgt_e == 0xFFFF else tgt_e}  "
            f"script={scr_id}  page={'all' if page == 0xFF else page}"
        )

    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GPLY Bytecode Assembler / Disassembler for CCP Studio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input", help="Input file (.gplya to assemble, .gply to disassemble)"
    )
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--disasm",
        action="store_true",
        help="Disassemble a .gply binary instead of assembling",
    )
    args = parser.parse_args()

    if args.disasm:
        with open(args.input, "rb") as fh:
            data = fh.read()
        print(disassemble(data))
        return

    with open(args.input, "r", encoding="utf-8") as fh:
        src = fh.read()

    try:
        binary = assemble(src)
    except AssemblerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    out_path = args.output
    if not out_path:
        base = os.path.splitext(args.input)[0]
        out_path = base + ".gply"

    with open(out_path, "wb") as fh:
        fh.write(binary)

    print(f"Assembled {len(binary)} bytes -> {out_path}")


if __name__ == "__main__":
    main()
