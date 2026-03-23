/* ccp_gameplay_vm.c — CCP Gameplay bytecode VM interpreter
 *
 * Stack-based VM that executes compiled CSP visual scripting bytecode
 * for in-page interactivity in .ccp files. Handles entity lifecycle,
 * collision detection, controller input, scene state, and event dispatch.
 */

#include "ccp_gameplay.h"
#include <stdio.h>
#include <stdlib.h>

/* ------------------------------------------------------------------ */
/*  Stack helpers                                                     */
/* ------------------------------------------------------------------ */
static void vm_push(GplyVM *vm, GplyValue v) {
    if (vm->sp < GPLY_MAX_STACK)
        vm->stack[vm->sp++] = v;
}

static GplyValue vm_pop(GplyVM *vm) {
    if (vm->sp > 0)
        return vm->stack[--vm->sp];
    GplyValue z;
    z.i = 0;
    return z;
}

/* ------------------------------------------------------------------ */
/*  String table                                                      */
/* ------------------------------------------------------------------ */
const char *gply_vm_string(const GplyVM *vm, uint16_t offset) {
    if (!vm->string_table || offset >= vm->header->string_table_size)
        return "";
    return vm->string_table + offset;
}

/* ------------------------------------------------------------------ */
/*  Bytecode readers (advance PC)                                     */
/* ------------------------------------------------------------------ */
static uint8_t bc_read_u8(const GplyVM *vm, uint32_t *pc) {
    uint8_t v = vm->bytecode[*pc];
    (*pc)++;
    return v;
}

static uint16_t bc_read_u16(const GplyVM *vm, uint32_t *pc) {
    uint16_t v;
    memcpy(&v, vm->bytecode + *pc, 2);
    *pc += 2;
    return v;
}

static int32_t bc_read_i32(const GplyVM *vm, uint32_t *pc) {
    int32_t v;
    memcpy(&v, vm->bytecode + *pc, 4);
    *pc += 4;
    return v;
}

static float bc_read_f32(const GplyVM *vm, uint32_t *pc) {
    float v;
    memcpy(&v, vm->bytecode + *pc, 4);
    *pc += 4;
    return v;
}

/* ------------------------------------------------------------------ */
/*  Initialization                                                    */
/* ------------------------------------------------------------------ */
int gply_vm_init(GplyVM *vm, const void *data, uint32_t size) {
    memset(vm, 0, sizeof(*vm));
    vm->pending_page = -1;

    if (size < sizeof(GplyHeader))
        return 0;

    const GplyHeader *h = (const GplyHeader *)data;
    if (h->magic != GPLY_MAGIC || h->version != GPLY_VERSION)
        return 0;

    vm->header = h;
    const uint8_t *p = (const uint8_t *)data + sizeof(GplyHeader);

    vm->entity_defs    = (const GplyEntityDef *)p;
    p += h->entity_def_count * sizeof(GplyEntityDef);

    vm->hitbox_defs    = (const GplyHitboxDef *)p;
    p += h->hitbox_def_count * sizeof(GplyHitboxDef);

    vm->script_defs    = (const GplyScriptDef *)p;
    p += h->script_count * sizeof(GplyScriptDef);

    vm->scene_defs     = (const GplySceneDef *)p;
    p += h->scene_count * sizeof(GplySceneDef);

    vm->event_bindings = (const GplyEventBinding *)p;
    p += h->event_binding_count * sizeof(GplyEventBinding);

    vm->variable_defs  = (const GplyVariableDef *)p;
    p += h->variable_count * sizeof(GplyVariableDef);

    vm->string_table   = (const char *)p;
    p += h->string_table_size;

    vm->bytecode       = p;

    /* Validate total size */
    uint32_t expected = (uint32_t)(p + h->bytecode_size - (const uint8_t *)data);
    if (expected > size)
        return 0;

    /* Initialize variables to their defaults */
    for (int i = 0; i < h->variable_count && i < GPLY_MAX_VARIABLES; i++)
        vm->variables[i].i = vm->variable_defs[i].initial_value;

    vm->current_page = 0;
    vm->current_scene = 0;
    vm->running = 1;
    return 1;
}

/* ------------------------------------------------------------------ */
/*  Reset runtime state                                               */
/* ------------------------------------------------------------------ */
void gply_vm_reset(GplyVM *vm) {
    vm->instance_count = 0;
    vm->sp = 0;
    vm->csp = 0;
    vm->pc = 0;
    vm->pending_page = -1;
    if (vm->header) {
        for (int i = 0; i < vm->header->variable_count && i < GPLY_MAX_VARIABLES; i++)
            vm->variables[i].i = vm->variable_defs[i].initial_value;
    }
}

/* ------------------------------------------------------------------ */
/*  Entity instance management                                        */
/* ------------------------------------------------------------------ */
static int spawn_entity(GplyVM *vm, uint16_t def_id) {
    if (def_id >= vm->header->entity_def_count) return -1;
    if (vm->instance_count >= GPLY_MAX_INSTANCES) return -1;

    int id = vm->instance_count++;
    GplyEntityInstance *inst = &vm->instances[id];
    const GplyEntityDef *def = &vm->entity_defs[def_id];

    inst->def_id        = def_id;
    inst->active        = 1;
    inst->x             = (float)def->default_x;
    inst->y             = (float)def->default_y;
    inst->current_frame = 0;
    inst->visible       = def->visible_by_default;
    inst->anim_playing  = 0;
    inst->anim_speed    = 1;
    return id;
}

/* ------------------------------------------------------------------ */
/*  Hit testing                                                       */
/* ------------------------------------------------------------------ */
int gply_hit_test_instances(const GplyVM *vm, int ia, int ib) {
    if (ia < 0 || ia >= vm->instance_count) return 0;
    if (ib < 0 || ib >= vm->instance_count) return 0;
    const GplyEntityInstance *a = &vm->instances[ia];
    const GplyEntityInstance *b = &vm->instances[ib];
    if (!a->active || !b->active) return 0;

    for (int i = 0; i < vm->header->hitbox_def_count; i++) {
        if (vm->hitbox_defs[i].entity_def_id != a->def_id) continue;
        const GplyHitboxDef *ha = &vm->hitbox_defs[i];
        if (ha->frame_index != 0xFFFF && ha->frame_index != (uint16_t)a->current_frame)
            continue;

        for (int j = 0; j < vm->header->hitbox_def_count; j++) {
            if (vm->hitbox_defs[j].entity_def_id != b->def_id) continue;
            const GplyHitboxDef *hb = &vm->hitbox_defs[j];
            if (hb->frame_index != 0xFFFF && hb->frame_index != (uint16_t)b->current_frame)
                continue;

            /* AABB overlap */
            float ax1 = a->x + ha->offset_x;
            float ay1 = a->y + ha->offset_y;
            float ax2 = ax1 + ha->width;
            float ay2 = ay1 + ha->height;
            float bx1 = b->x + hb->offset_x;
            float by1 = b->y + hb->offset_y;
            float bx2 = bx1 + hb->width;
            float by2 = by1 + hb->height;

            if (ax1 < bx2 && ax2 > bx1 && ay1 < by2 && ay2 > by1)
                return 1;
        }
    }
    return 0;
}

int gply_hit_test_point(const GplyVM *vm, int inst_id, float px, float py) {
    if (inst_id < 0 || inst_id >= vm->instance_count) return 0;
    const GplyEntityInstance *inst = &vm->instances[inst_id];
    if (!inst->active) return 0;

    for (int i = 0; i < vm->header->hitbox_def_count; i++) {
        if (vm->hitbox_defs[i].entity_def_id != inst->def_id) continue;
        const GplyHitboxDef *h = &vm->hitbox_defs[i];
        if (h->frame_index != 0xFFFF && h->frame_index != (uint16_t)inst->current_frame)
            continue;

        float hx = inst->x + h->offset_x;
        float hy = inst->y + h->offset_y;
        if (px >= hx && px < hx + h->width && py >= hy && py < hy + h->height)
            return 1;
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Variable access                                                   */
/* ------------------------------------------------------------------ */
int gply_vm_get_var(const GplyVM *vm, uint16_t id) {
    if (id >= GPLY_MAX_VARIABLES) return 0;
    return vm->variables[id].i;
}

void gply_vm_set_var(GplyVM *vm, uint16_t id, int value) {
    if (id < GPLY_MAX_VARIABLES)
        vm->variables[id].i = value;
}

/* ------------------------------------------------------------------ */
/*  Bytecode interpreter                                              */
/* ------------------------------------------------------------------ */
void gply_vm_exec_script(GplyVM *vm, uint16_t script_id) {
    if (!vm->header || script_id >= vm->header->script_count) return;

    const GplyScriptDef *sd = &vm->script_defs[script_id];
    vm->pc  = sd->bytecode_offset;
    vm->sp  = 0;
    vm->csp = 0;

    int max_iter = 100000;  /* safety bound */

    while (vm->pc < vm->header->bytecode_size && vm->running && max_iter-- > 0) {
        uint8_t op = bc_read_u8(vm, &vm->pc);
        GplyValue a, b, r;

        switch (op) {
        case OP_NOP: break;

        case OP_PUSH_INT:
            r.i = bc_read_i32(vm, &vm->pc);
            vm_push(vm, r);
            break;
        case OP_PUSH_FLOAT:
            r.f = bc_read_f32(vm, &vm->pc);
            vm_push(vm, r);
            break;
        case OP_PUSH_STR:
            r.str_offset = bc_read_u16(vm, &vm->pc);
            vm_push(vm, r);
            break;
        case OP_POP:
            vm_pop(vm);
            break;
        case OP_DUP:
            if (vm->sp > 0) vm_push(vm, vm->stack[vm->sp - 1]);
            break;

        case OP_SET_VAR: {
            uint16_t id = bc_read_u16(vm, &vm->pc);
            a = vm_pop(vm);
            if (id < GPLY_MAX_VARIABLES) vm->variables[id] = a;
            break;
        }
        case OP_GET_VAR: {
            uint16_t id = bc_read_u16(vm, &vm->pc);
            r.i = (id < GPLY_MAX_VARIABLES) ? vm->variables[id].i : 0;
            vm_push(vm, r);
            break;
        }

        case OP_JMP: {
            int32_t off = bc_read_i32(vm, &vm->pc);
            vm->pc = (uint32_t)((int32_t)vm->pc + off);
            break;
        }
        case OP_JMP_IF: {
            int32_t off = bc_read_i32(vm, &vm->pc);
            a = vm_pop(vm);
            if (a.i) vm->pc = (uint32_t)((int32_t)vm->pc + off);
            break;
        }
        case OP_JMP_IFNOT: {
            int32_t off = bc_read_i32(vm, &vm->pc);
            a = vm_pop(vm);
            if (!a.i) vm->pc = (uint32_t)((int32_t)vm->pc + off);
            break;
        }
        case OP_CALL: {
            uint16_t sid = bc_read_u16(vm, &vm->pc);
            if (vm->csp < GPLY_MAX_CALL_DEPTH && sid < vm->header->script_count) {
                vm->call_stack[vm->csp++] = vm->pc;
                vm->pc = vm->script_defs[sid].bytecode_offset;
            }
            break;
        }
        case OP_RET:
            if (vm->csp > 0)
                vm->pc = vm->call_stack[--vm->csp];
            else
                return;
            break;
        case OP_HALT:
            return;

        /* Entity operations */
        case OP_ENT_SPAWN: {
            uint16_t def_id = bc_read_u16(vm, &vm->pc);
            r.i = spawn_entity(vm, def_id);
            vm_push(vm, r);
            break;
        }
        case OP_ENT_DESTROY:
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count)
                vm->instances[a.i].active = 0;
            break;
        case OP_ENT_MOVE: {
            GplyValue dy = vm_pop(vm), dx = vm_pop(vm);
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count) {
                vm->instances[a.i].x += dx.f;
                vm->instances[a.i].y += dy.f;
            }
            break;
        }
        case OP_ENT_SET_POS: {
            GplyValue ny = vm_pop(vm), nx = vm_pop(vm);
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count) {
                vm->instances[a.i].x = nx.f;
                vm->instances[a.i].y = ny.f;
            }
            break;
        }
        case OP_ENT_GET_POS:
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count) {
                r.f = vm->instances[a.i].x; vm_push(vm, r);
                r.f = vm->instances[a.i].y; vm_push(vm, r);
            } else {
                r.f = 0; vm_push(vm, r); vm_push(vm, r);
            }
            break;
        case OP_ENT_SET_ANIM:
            b = vm_pop(vm); a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count) {
                vm->instances[a.i].anim_playing = 1;
                vm->instances[a.i].current_frame = 0;
            }
            break;
        case OP_ENT_SET_FRAME:
            b = vm_pop(vm); a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count)
                vm->instances[a.i].current_frame = b.i;
            break;
        case OP_ENT_SHOW:
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count)
                vm->instances[a.i].visible = 1;
            break;
        case OP_ENT_HIDE:
            a = vm_pop(vm);
            if (a.i >= 0 && a.i < vm->instance_count)
                vm->instances[a.i].visible = 0;
            break;

        /* Collision */
        case OP_HIT_TEST:
            b = vm_pop(vm); a = vm_pop(vm);
            r.i = gply_hit_test_instances(vm, a.i, b.i);
            vm_push(vm, r);
            break;
        case OP_POINT_TEST: {
            GplyValue py = vm_pop(vm), px = vm_pop(vm);
            a = vm_pop(vm);
            r.i = gply_hit_test_point(vm, a.i, px.f, py.f);
            vm_push(vm, r);
            break;
        }

        /* Page/scene */
        case OP_GOTO_PAGE:
            a = vm_pop(vm);
            vm->pending_page = a.i;
            break;
        case OP_SET_SCENE:
            vm->current_scene = bc_read_u16(vm, &vm->pc);
            break;
        case OP_PLAY_ANIM:
            bc_read_u16(vm, &vm->pc);  /* consume operand; animation playback TBD */
            break;

        /* Input */
        case OP_GET_BUTTON: {
            uint8_t btn = bc_read_u8(vm, &vm->pc);
            r.i = (btn < GPLY_BTN_COUNT) ? vm->buttons[btn] : 0;
            vm_push(vm, r);
            break;
        }
        case OP_GET_AXIS: {
            uint8_t axis = bc_read_u8(vm, &vm->pc);
            r.f = (axis < GPLY_AXIS_COUNT) ? vm->axes[axis] : 0.0f;
            vm_push(vm, r);
            break;
        }
        case OP_GET_DPAD:
            r.i = 0;
            if (vm->buttons[GPLY_BTN_DPAD_UP])    r.i |= 1;
            if (vm->buttons[GPLY_BTN_DPAD_DOWN])  r.i |= 2;
            if (vm->buttons[GPLY_BTN_DPAD_LEFT])  r.i |= 4;
            if (vm->buttons[GPLY_BTN_DPAD_RIGHT]) r.i |= 8;
            vm_push(vm, r);
            break;

        /* UI actions (viewer handles these externally; VM signals them) */
        case OP_SHOW_DIALOGUE:
            bc_read_u16(vm, &vm->pc);
            break;
        case OP_SHOW_POPUP:
            bc_read_u16(vm, &vm->pc);
            break;
        case OP_PLAY_SOUND:
            bc_read_u16(vm, &vm->pc);
            break;

        /* Math */
        case OP_ADD: b = vm_pop(vm); a = vm_pop(vm); r.i = a.i + b.i; vm_push(vm, r); break;
        case OP_SUB: b = vm_pop(vm); a = vm_pop(vm); r.i = a.i - b.i; vm_push(vm, r); break;
        case OP_MUL: b = vm_pop(vm); a = vm_pop(vm); r.i = a.i * b.i; vm_push(vm, r); break;
        case OP_DIV:
            b = vm_pop(vm); a = vm_pop(vm);
            r.i = (b.i != 0) ? a.i / b.i : 0;
            vm_push(vm, r);
            break;
        case OP_CMP_EQ: b = vm_pop(vm); a = vm_pop(vm); r.i = (a.i == b.i); vm_push(vm, r); break;
        case OP_CMP_LT: b = vm_pop(vm); a = vm_pop(vm); r.i = (a.i <  b.i); vm_push(vm, r); break;
        case OP_CMP_GT: b = vm_pop(vm); a = vm_pop(vm); r.i = (a.i >  b.i); vm_push(vm, r); break;
        case OP_AND:    b = vm_pop(vm); a = vm_pop(vm); r.i = (a.i && b.i); vm_push(vm, r); break;
        case OP_OR:     b = vm_pop(vm); a = vm_pop(vm); r.i = (a.i || b.i); vm_push(vm, r); break;
        case OP_NOT:    a = vm_pop(vm); r.i = !a.i; vm_push(vm, r); break;

        default:
            return;  /* unknown opcode = halt */
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Event dispatch                                                    */
/* ------------------------------------------------------------------ */
void gply_vm_fire_event(GplyVM *vm, int event_type, uint16_t source, uint16_t target) {
    if (!vm->header) return;

    for (int i = 0; i < vm->header->event_binding_count; i++) {
        const GplyEventBinding *eb = &vm->event_bindings[i];

        if (eb->event_type != (uint8_t)event_type) continue;
        if (eb->page != 0xFF && eb->page != (uint8_t)vm->current_page) continue;
        if (eb->source_entity != 0xFFFF && eb->source_entity != source) continue;

        if (event_type == GPLY_EVT_COLLIDE &&
            eb->target_entity != 0xFFFF && eb->target_entity != target)
            continue;

        if ((event_type == GPLY_EVT_BUTTON_DOWN || event_type == GPLY_EVT_BUTTON_UP) &&
            eb->filter_btn != 0xFF && eb->filter_btn != (uint8_t)source)
            continue;

        gply_vm_exec_script(vm, eb->script_id);
    }
}

/* ------------------------------------------------------------------ */
/*  Tick (per-frame update)                                           */
/* ------------------------------------------------------------------ */
void gply_vm_tick(GplyVM *vm) {
    if (!vm->header || !vm->running) return;

    /* Advance animations */
    for (int i = 0; i < vm->instance_count; i++) {
        GplyEntityInstance *inst = &vm->instances[i];
        if (!inst->active || !inst->anim_playing) continue;
        const GplyEntityDef *def = &vm->entity_defs[inst->def_id];
        inst->current_frame += inst->anim_speed;
        if (inst->current_frame >= def->timeline_length)
            inst->current_frame = 0;
    }

    /* Collision detection between all active instances */
    for (int i = 0; i < vm->instance_count; i++) {
        if (!vm->instances[i].active) continue;
        for (int j = i + 1; j < vm->instance_count; j++) {
            if (!vm->instances[j].active) continue;
            if (gply_hit_test_instances(vm, i, j)) {
                gply_vm_fire_event(vm, GPLY_EVT_COLLIDE, (uint16_t)i, (uint16_t)j);
                gply_vm_fire_event(vm, GPLY_EVT_COLLIDE, (uint16_t)j, (uint16_t)i);
            }
        }
    }

    /* Button edge detection */
    for (int b = 0; b < GPLY_BTN_COUNT; b++) {
        if (vm->buttons[b] && !vm->buttons_prev[b])
            gply_vm_fire_event(vm, GPLY_EVT_BUTTON_DOWN, (uint16_t)b, 0);
        if (!vm->buttons[b] && vm->buttons_prev[b])
            gply_vm_fire_event(vm, GPLY_EVT_BUTTON_UP, (uint16_t)b, 0);
        vm->buttons_prev[b] = vm->buttons[b];
    }

    /* Fire per-frame tick event */
    gply_vm_fire_event(vm, GPLY_EVT_FRAME_TICK, 0xFFFF, 0);
}

/* ------------------------------------------------------------------ */
/*  Page management                                                   */
/* ------------------------------------------------------------------ */
void gply_vm_set_page(GplyVM *vm, int page) {
    if (!vm->header) return;
    int old_page = vm->current_page;
    if (old_page == page) return;

    /* Fire exit event for old page */
    gply_vm_fire_event(vm, GPLY_EVT_PAGE_EXIT, 0xFFFF, 0);

    /* Clear instances and switch page */
    vm->instance_count = 0;
    vm->current_page = page;

    /* Auto-spawn entities for this page */
    for (int i = 0; i < vm->header->entity_def_count; i++) {
        if (vm->entity_defs[i].page == (uint8_t)page || vm->entity_defs[i].page == 0xFF)
            spawn_entity(vm, (uint16_t)i);
    }

    /* Fire enter event for new page */
    gply_vm_fire_event(vm, GPLY_EVT_PAGE_ENTER, 0xFFFF, 0);
}
