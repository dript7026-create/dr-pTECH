#!/usr/bin/env python3
"""
gply_compiler.py -- GPLY Gameplay Section Compiler
Compiles a Clip Studio Pipeline Bridge JSON manifest into a .gply binary
for use with: ccp_compiler -g gameplay.gply

Usage:
    python tools/gply_compiler.py -i clipstudio_runtime_manifest.json -o gameplay.gply
    python tools/gply_compiler.py --help

Pipeline:
    Clip Studio Paint
      -> CSP Plugin (ClipStudioPixelBrushSuite)
           -> Pipeline Bridge (ClipStudioPipelineBridge)
                -> clipstudio_runtime_manifest.json
                     -> gply_compiler.py -> gameplay.gply
                          -> ccp_compiler -g gameplay.gply -> output.ccp (v3)

JSON Schema (clipstudio_runtime_manifest.json):
{
  "entities": [           // CSP SymbolObjects
    {
      "name":              str,   // unique identifier
      "sprite":            str,   // asset path (relative to .ccp source root)
      "default_x":         int,   // initial X position (pixels)
      "default_y":         int,   // initial Y position (pixels)
      "width":             int,   // display width  (pixels)
      "height":            int,   // display height (pixels)
      "timeline_length":   int,   // animation frame count
      "visible_by_default": bool, // start visible?
      "page":              int    // which page (255 / "global" = all pages)
    }
  ],
  "hitboxes": [           // CSP HitDetection regions
    {
      "entity":    str,   // name of owning entity
      "frame":     int,   // frame_index (65535 = all frames)
      "offset_x":  int,   // X offset relative to entity position
      "offset_y":  int,   // Y offset relative to entity position
      "width":     int,
      "height":    int,
      "kind":      str    // "solid" | "trigger" | "hurtbox" | "button"
    }
  ],
  "scripts": [            // CSP VisualScripts compiled to VM bytecode
    {
      "name":         str,
      "instructions": [    // see INSTRUCTION SET below
        {"op": "OPCODE", ...}
      ]
    }
  ],
  "scenes": [             // CSP SceneSequences
    {
      "name":     str,
      "page":     int,    // page scope (255 / "global" = all pages)
      "flags":    int,    // optional, default 0
      "entities": [str],  // entity names active in this scene (contiguous range)
      "bindings": [str]   // event binding names active in this scene
    }
  ],
  "event_bindings": [     // CSP ButtonObjects / script wiring
    {
      "name":          str,   // optional unique identifier (for scene refs)
      "event":         str,   // event type: PAGE_ENTER, PAGE_EXIT, FRAME_TICK,
                              //   CLICK, HOVER_ENTER, HOVER_EXIT, COLLIDE,
                              //   TRIGGER, BUTTON_DOWN, BUTTON_UP,
                              //   SCENE_ENTER, SCENE_EXIT
      "source_entity": str,   // entity name generating event (null = any)
      "target_entity": str,   // for COLLIDE: the other entity (null = any)
      "script":        str,   // script name to execute
      "page":          int,   // page scope (255 / "global" = all pages)
      "filter_btn":    str    // for BUTTON_DOWN/UP: button name (else null)
                              //   A, B, X, Y, DPAD_UP, DPAD_DOWN, DPAD_LEFT,
                              //   DPAD_RIGHT, START, BACK, LB, RB, LSTICK, RSTICK
    }
  ],
  "variables": [          // persistent numeric variables
    {
      "name":          str,
      "initial_value": int    // default 0; stored as int32
    }
  ]
}

INSTRUCTION SET (for "scripts[].instructions"):
  Each element is a JSON object with at least "op" (opcode name, case-insensitive).
  A bare {"label": "name"} (no "op") defines a jump target label.

  No-operand instructions (just {"op": "..."}):
    NOP, POP, DUP, RET, HALT
    ENT_DESTROY, ENT_MOVE, ENT_SET_POS, ENT_GET_POS
    ENT_SET_ANIM, ENT_SET_FRAME, ENT_SHOW, ENT_HIDE
    HIT_TEST, POINT_TEST, GOTO_PAGE, GET_DPAD
    ADD, SUB, MUL, DIV, CMP_EQ, CMP_LT, CMP_GT, AND, OR, NOT

  Operand instructions:
    PUSH_INT   {"op":"PUSH_INT",   "value": 42}          -- push int32
    PUSH_FLOAT {"op":"PUSH_FLOAT", "value": 1.5}         -- push float32
    PUSH_STR   {"op":"PUSH_STR",   "value": "hello"}     -- push string_table offset
    SET_VAR    {"op":"SET_VAR",    "var":   "score"}      -- pop -> variable
    GET_VAR    {"op":"GET_VAR",    "var":   "score"}      -- push variable
    JMP        {"op":"JMP",        "label": "loop_end"}   -- unconditional jump
    JMP_IF     {"op":"JMP_IF",     "label": "done"}       -- jump if stack top != 0
    JMP_IFNOT  {"op":"JMP_IFNOT",  "label": "skip"}       -- jump if stack top == 0
    CALL       {"op":"CALL",       "script": "helper_fn"} -- call script by name
    ENT_SPAWN  {"op":"ENT_SPAWN",  "entity": "player"}    -- push instance_id
    SET_SCENE  {"op":"SET_SCENE",  "scene":  "intro"}     -- activate scene
    PLAY_ANIM  {"op":"PLAY_ANIM",  "anim":   "explosion"} -- play named anim
    GET_BUTTON {"op":"GET_BUTTON", "button": "A"}         -- push button state (bool)
    GET_AXIS   {"op":"GET_AXIS",   "axis":   "LX"}        -- push axis value (float)
    SHOW_DIALOGUE {"op":"SHOW_DIALOGUE", "text": "Hello!"}
    SHOW_POPUP    {"op":"SHOW_POPUP",    "text": "Score up!"}
    PLAY_SOUND    {"op":"PLAY_SOUND",    "sound_id": 0}

  Label definitions (no "op"):
    {"label": "loop_top"}

  Note: LT and RT controller triggers are RESERVED for page navigation
  and are not accessible from gameplay scripts.

Binary output format (.gply):
  All integers little-endian, tightly packed (no alignment padding).
  [GplyHeader 28 B]
  [GplyEntityDef * entity_def_count  -- 16 B each]
  [GplyHitboxDef * hitbox_def_count  -- 14 B each]
  [GplyScriptDef * script_count      -- 10 B each]
  [GplySceneDef  * scene_count       -- 12 B each]
  [GplyEventBinding * event_binding_count -- 10 B each]
  [GplyVariableDef  * variable_count -- 6 B each]
  [String table -- null-terminated UTF-8 strings]
  [Bytecode -- raw VM instructions]
"""

import argparse
import json
import struct
import sys

# ---------------------------------------------------------------------------
#  Constants matching ccp_gameplay.h
# ---------------------------------------------------------------------------

GPLY_MAGIC   = 0x594C5047  # "GPLY" little-endian
GPLY_VERSION = 1

OPCODES = {
    # Stack manipulation
    "NOP":           (0x00, None),
    "PUSH_INT":      (0x01, "i32"),
    "PUSH_FLOAT":    (0x02, "f32"),
    "PUSH_STR":      (0x03, "str"),
    "POP":           (0x04, None),
    "DUP":           (0x05, None),
    # Variables
    "SET_VAR":       (0x10, "var"),
    "GET_VAR":       (0x11, "var"),
    # Control flow
    "JMP":           (0x20, "lbl"),
    "JMP_IF":        (0x21, "lbl"),
    "JMP_IFNOT":     (0x22, "lbl"),
    "CALL":          (0x23, "script"),
    "RET":           (0x24, None),
    "HALT":          (0xFF, None),
    # Entity operations
    "ENT_SPAWN":     (0x30, "entity"),
    "ENT_DESTROY":   (0x31, None),
    "ENT_MOVE":      (0x32, None),
    "ENT_SET_POS":   (0x33, None),
    "ENT_GET_POS":   (0x34, None),
    "ENT_SET_ANIM":  (0x35, None),
    "ENT_SET_FRAME": (0x36, None),
    "ENT_SHOW":      (0x37, None),
    "ENT_HIDE":      (0x38, None),
    # Collision
    "HIT_TEST":      (0x40, None),
    "POINT_TEST":    (0x41, None),
    # Navigation
    "GOTO_PAGE":     (0x50, None),
    "SET_SCENE":     (0x51, "scene"),
    "PLAY_ANIM":     (0x52, "anim_str"),
    # Controller
    "GET_BUTTON":    (0x60, "btn"),
    "GET_AXIS":      (0x61, "axis"),
    "GET_DPAD":      (0x62, None),
    # UI
    "SHOW_DIALOGUE": (0x70, "ui_str"),
    "SHOW_POPUP":    (0x71, "ui_str"),
    "PLAY_SOUND":    (0x72, "sound"),
    # Math / logic
    "ADD":           (0x80, None),
    "SUB":           (0x81, None),
    "MUL":           (0x82, None),
    "DIV":           (0x83, None),
    "CMP_EQ":        (0x84, None),
    "CMP_LT":        (0x85, None),
    "CMP_GT":        (0x86, None),
    "AND":           (0x87, None),
    "OR":            (0x88, None),
    "NOT":           (0x89, None),
}

EVENT_TYPES = {
    "PAGE_ENTER":  0,
    "PAGE_EXIT":   1,
    "FRAME_TICK":  2,
    "CLICK":       3,
    "HOVER_ENTER": 4,
    "HOVER_EXIT":  5,
    "COLLIDE":     6,
    "TRIGGER":     7,
    "BUTTON_DOWN": 8,
    "BUTTON_UP":   9,
    "SCENE_ENTER": 10,
    "SCENE_EXIT":  11,
}

HITBOX_KINDS = {
    "solid":   0,
    "trigger": 1,
    "hurtbox": 2,
    "button":  3,
}

BUTTON_IDS = {
    "A":          0,
    "B":          1,
    "X":          2,
    "Y":          3,
    "DPAD_UP":    4,
    "DPAD_DOWN":  5,
    "DPAD_LEFT":  6,
    "DPAD_RIGHT": 7,
    "START":      8,
    "BACK":       9,
    "LB":         10,
    "RB":         11,
    "LSTICK":     12,
    "RSTICK":     13,
}

AXIS_IDS = {
    "LX": 0,
    "LY": 1,
    "RX": 2,
    "RY": 3,
}

PAGE_GLOBAL = 0xFF

# ---------------------------------------------------------------------------
#  String table
# ---------------------------------------------------------------------------

class StringTable:
    """Interning string table; emits null-terminated UTF-8 byte stream."""

    def __init__(self):
        self._buf = bytearray()
        self._cache = {}           # str -> uint16 offset

    def intern(self, s: str) -> int:
        s = str(s)
        if s in self._cache:
            return self._cache[s]
        off = len(self._buf)
        if off > 0xFFFF:
            raise OverflowError(f"String table exceeds 65535 bytes at entry '{s}'")
        self._cache[s] = off
        self._buf.extend(s.encode("utf-8"))
        self._buf.append(0)
        return off

    def data(self) -> bytes:
        return bytes(self._buf)

    def size(self) -> int:
        return len(self._buf)


# ---------------------------------------------------------------------------
#  Bytecode assembler  (single script, two-pass label resolution)
# ---------------------------------------------------------------------------

def _assemble_script(
    instructions: list,
    strtab: StringTable,
    entity_index: dict,   # name -> id
    script_index: dict,   # name -> id  (forward refs ok after all scripts listed)
    scene_index: dict,    # name -> id
    var_index: dict,      # name -> id
    script_name: str,
) -> bytes:
    """
    Assemble one script's instruction list into raw bytecode.
    Jumps use 32-bit signed offsets relative to PC immediately after the
    operand (matching the VM's JMP implementation).
    """
    buf = bytearray()
    labels = {}          # label_name -> byte offset in buf
    patch_sites = []     # (buf_offset_of_operand, label_name)

    for idx, instr in enumerate(instructions):
        # Label definition -- no "op" key
        if "label" in instr and "op" not in instr:
            lname = instr["label"]
            if lname in labels:
                _error(f"Script '{script_name}': duplicate label '{lname}'")
            labels[lname] = len(buf)
            continue

        op_name = instr.get("op", "").upper()
        if not op_name:
            _error(f"Script '{script_name}': instruction {idx} has no 'op' key")
        if op_name not in OPCODES:
            _error(f"Script '{script_name}': unknown opcode '{op_name}'")

        opcode, operand_kind = OPCODES[op_name]
        buf.append(opcode)

        if operand_kind is None:
            pass

        elif operand_kind == "i32":
            val = instr.get("value")
            if val is None:
                _error(f"Script '{script_name}': {op_name} requires 'value'")
            buf.extend(struct.pack("<i", int(val)))

        elif operand_kind == "f32":
            val = instr.get("value")
            if val is None:
                _error(f"Script '{script_name}': {op_name} requires 'value'")
            buf.extend(struct.pack("<f", float(val)))

        elif operand_kind == "str":
            val = instr.get("value")
            if val is None:
                _error(f"Script '{script_name}': {op_name} requires 'value'")
            off = strtab.intern(str(val))
            buf.extend(struct.pack("<H", off))

        elif operand_kind == "var":
            vname = instr.get("var")
            if vname is None:
                _error(f"Script '{script_name}': {op_name} requires 'var'")
            if vname not in var_index:
                _error(f"Script '{script_name}': undefined variable '{vname}'")
            buf.extend(struct.pack("<H", var_index[vname]))

        elif operand_kind == "lbl":
            lname = instr.get("label")
            if lname is None:
                _error(f"Script '{script_name}': {op_name} requires 'label'")
            patch_sites.append((len(buf), lname))
            buf.extend(b"\x00\x00\x00\x00")  # placeholder int32

        elif operand_kind == "script":
            sname = instr.get("script")
            if sname is None:
                _error(f"Script '{script_name}': CALL requires 'script'")
            if sname not in script_index:
                _error(f"Script '{script_name}': CALL references unknown script '{sname}'")
            buf.extend(struct.pack("<H", script_index[sname]))

        elif operand_kind == "entity":
            ename = instr.get("entity")
            if ename is None:
                _error(f"Script '{script_name}': {op_name} requires 'entity'")
            if ename not in entity_index:
                _error(f"Script '{script_name}': undefined entity '{ename}'")
            buf.extend(struct.pack("<H", entity_index[ename]))

        elif operand_kind == "scene":
            scname = instr.get("scene")
            if scname is None:
                _error(f"Script '{script_name}': SET_SCENE requires 'scene'")
            if scname not in scene_index:
                _error(f"Script '{script_name}': undefined scene '{scname}'")
            buf.extend(struct.pack("<H", scene_index[scname]))

        elif operand_kind == "anim_str":
            aname = instr.get("anim")
            if aname is None:
                _error(f"Script '{script_name}': PLAY_ANIM requires 'anim'")
            off = strtab.intern(aname)
            buf.extend(struct.pack("<H", off))

        elif operand_kind == "ui_str":
            text = instr.get("text")
            if text is None:
                _error(f"Script '{script_name}': {op_name} requires 'text'")
            off = strtab.intern(text)
            buf.extend(struct.pack("<H", off))

        elif operand_kind == "btn":
            bname = instr.get("button", "").upper()
            if bname not in BUTTON_IDS:
                _error(
                    f"Script '{script_name}': GET_BUTTON unknown button '{bname}'. "
                    f"Valid: {sorted(BUTTON_IDS)}"
                )
            buf.append(BUTTON_IDS[bname])

        elif operand_kind == "axis":
            aname = instr.get("axis", "").upper()
            if aname not in AXIS_IDS:
                _error(
                    f"Script '{script_name}': GET_AXIS unknown axis '{aname}'. "
                    f"Valid: {sorted(AXIS_IDS)}"
                )
            buf.append(AXIS_IDS[aname])

        elif operand_kind == "sound":
            sid = instr.get("sound_id")
            if sid is None:
                _error(f"Script '{script_name}': PLAY_SOUND requires 'sound_id'")
            buf.extend(struct.pack("<H", int(sid)))

    # Patch jump targets
    for (site, lname) in patch_sites:
        if lname not in labels:
            _error(f"Script '{script_name}': undefined label '{lname}'")
        # PC after operand = site + 4
        relative = labels[lname] - (site + 4)
        struct.pack_into("<i", buf, site, relative)

    return bytes(buf)


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _error(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _resolve_page(page_val) -> int:
    """Accept an integer or the string "global" for PAGE_GLOBAL (0xFF)."""
    if page_val is None or str(page_val).lower() in ("global", "all"):
        return PAGE_GLOBAL
    val = int(page_val)
    if not (0 <= val <= 255):
        _error(f"page value {val} out of range 0-255 (use 255 / 'global' for all pages)")
    return val


def _resolve_entity(entity_index: dict, name, context: str) -> int:
    """Look up entity by name; return 0xFFFF for null/missing."""
    if not name:
        return 0xFFFF
    if name not in entity_index:
        _error(f"{context}: undefined entity '{name}'")
    return entity_index[name]


# ---------------------------------------------------------------------------
#  Main compilation
# ---------------------------------------------------------------------------

def compile_gply(manifest: dict) -> bytes:
    strtab = StringTable()

    # ------------------------------------------------------------------
    # 1.  Index names -> IDs upfront so scripts can cross-reference.
    # ------------------------------------------------------------------
    raw_entities       = manifest.get("entities",       [])
    raw_hitboxes       = manifest.get("hitboxes",       [])
    raw_scripts        = manifest.get("scripts",        [])
    raw_scenes         = manifest.get("scenes",         [])
    raw_event_bindings = manifest.get("event_bindings", [])
    raw_variables      = manifest.get("variables",      [])

    entity_index = {e["name"]: i for i, e in enumerate(raw_entities)}
    script_index = {s["name"]: i for i, s in enumerate(raw_scripts)}
    scene_index  = {sc["name"]: i for i, sc in enumerate(raw_scenes)}
    var_index    = {v["name"]: i for i, v in enumerate(raw_variables)}

    # Named event bindings (optional)
    binding_index = {
        b["name"]: i
        for i, b in enumerate(raw_event_bindings)
        if b.get("name")
    }

    # ------------------------------------------------------------------
    # 2.  Entity definitions (GplyEntityDef, 16 bytes each)
    # ------------------------------------------------------------------
    #   <HHhhHHHBB>
    entity_data = bytearray()
    for ent in raw_entities:
        name_off   = strtab.intern(ent["name"])
        sprite_off = strtab.intern(ent.get("sprite", ""))
        dx = int(ent.get("default_x", 0))
        dy = int(ent.get("default_y", 0))
        w  = int(ent.get("width",  0))
        h  = int(ent.get("height", 0))
        tl = int(ent.get("timeline_length", 1))
        vis = 1 if ent.get("visible_by_default", True) else 0
        page = _resolve_page(ent.get("page"))
        entity_data.extend(struct.pack("<HHhhHHHBB",
            name_off, sprite_off, dx, dy, w, h, tl, vis, page))

    # ------------------------------------------------------------------
    # 3.  Hitbox definitions (GplyHitboxDef, 14 bytes each)
    # ------------------------------------------------------------------
    #   <HHhhHHBB>
    hitbox_data = bytearray()
    for hb in raw_hitboxes:
        ent_name = hb.get("entity", "")
        if ent_name not in entity_index:
            _error(f"Hitbox references undefined entity '{ent_name}'")
        eid   = entity_index[ent_name]
        frame = int(hb.get("frame", 0xFFFF))
        ox    = int(hb.get("offset_x", 0))
        oy    = int(hb.get("offset_y", 0))
        w     = int(hb.get("width",  0))
        h     = int(hb.get("height", 0))
        kind_str = str(hb.get("kind", "solid")).lower()
        if kind_str not in HITBOX_KINDS:
            _error(
                f"Hitbox on '{ent_name}': unknown kind '{kind_str}'. "
                f"Use: solid, trigger, hurtbox, button"
            )
        kind = HITBOX_KINDS[kind_str]
        hitbox_data.extend(struct.pack("<HHhhHHBB",
            eid, frame, ox, oy, w, h, kind, 0))

    # ------------------------------------------------------------------
    # 4.  Bytecode assembly (scripts first, then write ScriptDef table)
    # ------------------------------------------------------------------
    bytecode_chunks = []   # [bytes, ...]  one per script
    bytecode_offset = 0

    script_defs_data = bytearray()  # GplyScriptDef, 10 bytes each
    for script in raw_scripts:
        instrs = script.get("instructions", [])
        bc = _assemble_script(
            instrs, strtab,
            entity_index, script_index, scene_index, var_index,
            script["name"],
        )
        name_off = strtab.intern(script["name"])
        script_defs_data.extend(struct.pack("<HII",
            name_off, bytecode_offset, len(bc)))
        bytecode_chunks.append(bc)
        bytecode_offset += len(bc)

    bytecode_data = b"".join(bytecode_chunks)

    # ------------------------------------------------------------------
    # 5.  Scene definitions (GplySceneDef, 12 bytes each)
    # ------------------------------------------------------------------
    #   <HHHHHBB>
    scene_data = bytearray()
    for sc in raw_scenes:
        name_off = strtab.intern(sc["name"])
        page     = _resolve_page(sc.get("page"))
        flags    = int(sc.get("flags", 0))

        # Resolve entity range
        sc_entities = sc.get("entities", [])
        if sc_entities:
            first_ent_name = sc_entities[0]
            if first_ent_name not in entity_index:
                _error(f"Scene '{sc['name']}': undefined entity '{first_ent_name}'")
            first_ent = entity_index[first_ent_name]
        else:
            first_ent = 0
        ent_count = len(sc_entities)

        # Resolve binding range
        sc_bindings = sc.get("bindings", [])
        if sc_bindings:
            first_bnd_name = sc_bindings[0]
            if first_bnd_name not in binding_index:
                _error(
                    f"Scene '{sc['name']}': event binding '{first_bnd_name}' has no "
                    f"'name' field or is not defined"
                )
            first_bnd = binding_index[first_bnd_name]
        else:
            first_bnd = 0
        bnd_count = len(sc_bindings)

        scene_data.extend(struct.pack("<HHHHHBB",
            name_off, first_ent, ent_count, first_bnd, bnd_count, page, flags))

    # ------------------------------------------------------------------
    # 6.  Event bindings (GplyEventBinding, 10 bytes each)
    # ------------------------------------------------------------------
    #   <BBHHHBx>  -- final byte is padding
    binding_data = bytearray()
    for eb in raw_event_bindings:
        evt_str = str(eb.get("event", "")).upper()
        if evt_str not in EVENT_TYPES:
            _error(
                f"Event binding: unknown event '{evt_str}'. "
                f"Valid: {sorted(EVENT_TYPES)}"
            )
        evt_type = EVENT_TYPES[evt_str]

        # filter_btn: relevant for BUTTON_DOWN / BUTTON_UP
        fb_str = eb.get("filter_btn")
        if fb_str:
            fb_str = str(fb_str).upper()
            if fb_str not in BUTTON_IDS:
                _error(
                    f"Event binding: unknown filter_btn '{fb_str}'. "
                    f"Valid: {sorted(BUTTON_IDS)}"
                )
            filter_btn = BUTTON_IDS[fb_str]
        else:
            filter_btn = 0xFF

        src  = _resolve_entity(entity_index, eb.get("source_entity"), "Event binding")
        tgt  = _resolve_entity(entity_index, eb.get("target_entity"), "Event binding")

        sname = eb.get("script", "")
        if sname not in script_index:
            _error(f"Event binding: references undefined script '{sname}'")
        sid = script_index[sname]

        page  = _resolve_page(eb.get("page"))
        binding_data.extend(struct.pack("<BBHHHBx",
            evt_type, filter_btn, src, tgt, sid, page))

    # ------------------------------------------------------------------
    # 7.  Variable definitions (GplyVariableDef, 6 bytes each)
    # ------------------------------------------------------------------
    #   <Hi>
    var_data = bytearray()
    for v in raw_variables:
        name_off = strtab.intern(v["name"])
        init_val = int(v.get("initial_value", 0))
        var_data.extend(struct.pack("<Hi", name_off, init_val))

    # ------------------------------------------------------------------
    # 8.  String table is now fully built (entities/hitboxes/scripts/etc.
    #     all called intern() above).
    # ------------------------------------------------------------------
    strtab_bytes = strtab.data()

    # ------------------------------------------------------------------
    # 9.  Validate counts fit in uint16
    # ------------------------------------------------------------------
    def _check_count(n, label):
        if n > 0xFFFF:
            _error(f"Too many {label} ({n}); maximum 65535")

    _check_count(len(raw_entities),       "entities")
    _check_count(len(raw_hitboxes),       "hitboxes")
    _check_count(len(raw_scripts),        "scripts")
    _check_count(len(raw_scenes),         "scenes")
    _check_count(len(raw_event_bindings), "event_bindings")
    _check_count(len(raw_variables),      "variables")

    # ------------------------------------------------------------------
    # 10. Assemble GplyHeader (28 bytes)
    # ------------------------------------------------------------------
    #   <IIHHHHHHII>
    header = struct.pack(
        "<IIHHHHHHII",
        GPLY_MAGIC,
        GPLY_VERSION,
        len(raw_entities),
        len(raw_hitboxes),
        len(raw_scripts),
        len(raw_scenes),
        len(raw_event_bindings),
        len(raw_variables),
        len(strtab_bytes),
        len(bytecode_data),
    )

    # ------------------------------------------------------------------
    # 11. Concatenate final binary
    # ------------------------------------------------------------------
    return (
        header
        + bytes(entity_data)
        + bytes(hitbox_data)
        + bytes(script_defs_data)
        + bytes(scene_data)
        + bytes(binding_data)
        + bytes(var_data)
        + strtab_bytes
        + bytecode_data
    )


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="GPLY Gameplay Section Compiler -- converts a "
                    "Clip Studio Pipeline Bridge JSON manifest into a "
                    ".gply binary for use with ccp_compiler -g.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n"
               "  python tools/gply_compiler.py "
               "-i clipstudio_runtime_manifest.json -o gameplay.gply\n"
               "  ccp_compiler -o book.ccp -m manifest.json "
               "-z source.zip -g gameplay.gply",
    )
    parser.add_argument(
        "-i", "--input", metavar="MANIFEST.JSON", required=True,
        help="Path to clipstudio_runtime_manifest.json",
    )
    parser.add_argument(
        "-o", "--output", metavar="OUTPUT.GPLY", required=True,
        help="Path to write .gply binary",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Print section sizes and counts",
    )
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        _error(f"Input file not found: {args.input}")
    except json.JSONDecodeError as e:
        _error(f"JSON parse error in '{args.input}': {e}")

    gply_bytes = compile_gply(manifest)

    try:
        with open(args.output, "wb") as f:
            f.write(gply_bytes)
    except OSError as e:
        _error(f"Cannot write '{args.output}': {e}")

    if args.verbose:
        m = manifest
        print(f"Compiled GPLY section -> {args.output}")
        print(f"  Total size:    {len(gply_bytes)} bytes")
        print(f"  Entities:      {len(m.get('entities', []))}")
        print(f"  Hitboxes:      {len(m.get('hitboxes', []))}")
        print(f"  Scripts:       {len(m.get('scripts', []))}")
        print(f"  Scenes:        {len(m.get('scenes', []))}")
        print(f"  Event bindings:{len(m.get('event_bindings', []))}")
        print(f"  Variables:     {len(m.get('variables', []))}")
    else:
        print(f"Compiled {args.input} -> {args.output} ({len(gply_bytes)} bytes)")


if __name__ == "__main__":
    main()
