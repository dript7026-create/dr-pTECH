bl_info = {
    "name": "TxTUR C Bridge",
    "blender": (2, 80, 0),
    "category": "Texture",
}

import bpy
import os
import ctypes
import sys
from bpy.props import IntProperty, FloatProperty
import bmesh
from mathutils import Vector
import math
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

# Library name - adjust if you compile to a different filename.
_lib_name = 'blenderTxTUR.dll' if os.name == 'nt' else 'libblenderTxTUR.so'
_lib = None

# Try load from same folder as this script, then system path
try:
    _lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), _lib_name))
except Exception:
    try:
        _lib = ctypes.CDLL(_lib_name)
    except Exception:
        _lib = None


def lib_ok():
    return _lib is not None


# --- ctypes prototypes (if available) ---
if _lib:
    try:
        _lib.txtur_start.restype = ctypes.c_int
        _lib.txtur_stop.restype = None
        _lib.txtur_get_brush_count.restype = ctypes.c_int
        _lib.txtur_get_brush_name.restype = ctypes.c_char_p
        _lib.txtur_apply_texture_simple.argtypes = [ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        _lib.txtur_apply_texture_simple.restype = ctypes.c_int

        _lib.txtur_get_mapping_count.restype = ctypes.c_int
        _lib.txtur_get_mapping_name.restype = ctypes.c_char_p
        _lib.txtur_apply_mapping_simple.argtypes = [ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        _lib.txtur_apply_mapping_simple.restype = ctypes.c_int

        _lib.txtur_node_add.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        _lib.txtur_node_add.restype = ctypes.c_int
        _lib.txtur_node_link.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float]
        _lib.txtur_node_link.restype = ctypes.c_int

        _lib.txtur_set_mode_simple.argtypes = [ctypes.c_int]
        _lib.txtur_set_mode_simple.restype = ctypes.c_int
        _lib.txtur_sample_displacement.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
        _lib.txtur_sample_displacement.restype = ctypes.c_float
    except Exception:
        pass


# Draw handler state
_txtur_draw_handler = None
_txtur_draw_data = {
    'pos': (0, 0),
    'radius': 64,
    'color': (1.0, 0.2, 0.2, 0.6),
}


def _txtur_draw_brush():
    cx, cy = _txtur_draw_data.get('pos', (0, 0))
    r = float(_txtur_draw_data.get('radius', 32))
    color = _txtur_draw_data.get('color', (1.0, 0.2, 0.2, 0.6))
    fill_color = (color[0], color[1], color[2], 0.12)
    outline_color = (color[0], color[1], color[2], 0.9)

    segments = 64
    verts = []
    for i in range(segments + 1):
        a = (i / segments) * (2.0 * math.pi)
        verts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

    # Draw filled circle as triangle fan (triangles list)
    tri_verts = []
    for i in range(segments):
        tri_verts.append((cx, cy))
        tri_verts.append(verts[i])
        tri_verts.append(verts[i + 1])
    if tri_verts:
        batch = batch_for_shader(shader, 'TRIS', {"pos": tri_verts})
        shader.bind()
        shader.uniform_float('color', fill_color)
        batch.draw(shader)

    # Outline
    batch_outline = batch_for_shader(shader, 'LINE_LOOP', {"pos": verts[:-1]})
    shader.bind()
    shader.uniform_float('color', outline_color)
    batch_outline.draw(shader)

    # Crosshair lines
    line_verts = [
        (cx - r, cy), (cx + r, cy),
        (cx, cy - r), (cx, cy + r)
    ]
    batch_lines = batch_for_shader(shader, 'LINES', {"pos": line_verts})
    shader.bind()
    shader.uniform_float('color', outline_color)
    batch_lines.draw(shader)


class TXTUR_OT_init(bpy.types.Operator):
    bl_idname = "txtur.init"
    bl_label = "Initialize TxTUR"

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        try:
            _lib.txtur_get_info.restype = ctypes.c_char_p
            info = _lib.txtur_get_info()
            if info:
                self.report({'INFO'}, info.decode('utf-8'))
        except Exception:
            pass
        return {'FINISHED'}


class TXTUR_PT_panel(bpy.types.Panel):
    bl_label = "TxTUR Bridge"
    bl_idname = "TXTUR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TxTUR'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('txtur.init')
        row = layout.row()
        if lib_ok():
            row.label(text='TxTUR library loaded')
        else:
            row.label(text='TxTUR library NOT loaded')
        row = layout.row()
        row.operator('txtur.generate_image')

        # Brush controls
        scn = context.scene
        row = layout.row()
        row.prop(scn, 'txtur_brush_index', text='Brush')
        row = layout.row()
        row.prop(scn, 'txtur_brush_intensity', text='Intensity')
        row = layout.row()
        row.operator('txtur.apply_brush')

        # Mapping controls
        row = layout.row()
        row.prop(scn, 'txtur_mapping_index', text='Mapping')
        row = layout.row()
        row.prop(scn, 'txtur_mapping_depth', text='Depth')
        row = layout.row()
        row.operator('txtur.apply_mapping')

        # NodeCraft controls
        row = layout.row()
        row.operator('txtur.node_add')
        row = layout.row()
        row.operator('txtur.node_link')
        
        row = layout.row()
        row.operator('txtur.modal_sculpt')
        row = layout.row()
        row.label(text='Modal sculpt: drag LMB in viewport')

            row = layout.row()
            row.operator('txtur.enter_brush_mode')
            row = layout.row()
            row.prop(scn, 'txtur_brush_size', text='Size')
            row.operator('txtur.stamp_at_cursor')


class TXTUR_OT_apply_brush(bpy.types.Operator):
    bl_idname = 'txtur.apply_brush'
    bl_label = 'Apply Brush'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        scn = context.scene
        brush = int(scn.txtur_brush_index)
        intensity = float(scn.txtur_brush_intensity)
        # use 3D cursor as target position
        loc = context.scene.cursor.location
        res = _lib.txtur_apply_texture_simple(brush, loc.x, loc.y, loc.z, ctypes.c_float(intensity))
        if res != 0:
            self.report({'ERROR'}, 'Brush apply failed')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Applied brush {brush}')
        return {'FINISHED'}


    class TXTUR_OT_modal_sculpt(bpy.types.Operator):
        bl_idname = 'txtur.modal_sculpt'
        bl_label = 'TxTUR Sculpt (Modal)'
        bl_options = {'REGISTER', 'UNDO'}

        def invoke(self, context, event):
            if not lib_ok():
                self.report({'ERROR'}, 'TxTUR library not loaded')
                return {'CANCELLED'}
            obj = context.object
            if not obj or obj.type != 'MESH':
                self.report({'ERROR'}, 'Select a mesh object first')
                return {'CANCELLED'}
            self.obj = obj
            self._mouse_down = False
            self._mouse_x = 0
            self._mouse_y = 0
            global _txtur_draw_handler
            if _txtur_draw_handler is None:
                _txtur_draw_handler = bpy.types.SpaceView3D.draw_handler_add(_txtur_draw_brush, (), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        def modal(self, context, event):
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self._mouse_down = True
                # start undo push for stroke
                try:
                    bpy.ops.ed.undo_push(message='TxTUR Sculpt Stroke')
                except Exception:
                    pass
                return {'RUNNING_MODAL'}
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._mouse_down = False
                return {'RUNNING_MODAL'}
            if event.type == 'MOUSEMOVE' and self._mouse_down:
                # update mouse for preview
                try:
                    self._mouse_x = event.mouse_region_x
                    self._mouse_y = event.mouse_region_y
                    _txtur_draw_data['pos'] = (self._mouse_x, self._mouse_y)
                    _txtur_draw_data['radius'] = int(context.scene.txtur_brush_size)
                except Exception:
                    pass
                # determine 3D location under mouse
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        region = None
                        for r in area.regions:
                            if r.type == 'WINDOW':
                                region = r
                                break
                        rv3d = area.spaces.active.region_3d
                        if not region or not rv3d:
                            continue
                        coord = (event.mouse_region_x, event.mouse_region_y)
                        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                        deps = context.evaluated_depsgraph_get()
                        hit, loc, norm, index, ob, matrix = context.scene.ray_cast(deps, origin, direction)
                        if hit and ob == self.obj:
                            self.apply_sculpt_at(context, loc, norm)
                            return {'RUNNING_MODAL'}
                return {'RUNNING_MODAL'}
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                # remove draw handler
                global _txtur_draw_handler
                if _txtur_draw_handler is not None:
                    bpy.types.SpaceView3D.draw_handler_remove(_txtur_draw_handler, 'WINDOW')
                    _txtur_draw_handler = None
                return {'CANCELLED'}
            return {'PASS_THROUGH'}

        def apply_sculpt_at(self, context, loc_world, normal_world):
            scene = context.scene
            radius = max(0.001, scene.txtur_brush_size * 0.01)
            strength = scene.txtur_brush_intensity
            falloff_power = getattr(scene, 'txtur_falloff_power', 2.0)

            obj = self.obj
            mesh = obj.data

            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()
            bm.normal_update()

            # transform world loc to object local
            loc_local = obj.matrix_world.inverted() @ Vector(loc_world)

            for v in bm.verts:
                dist = (v.co - loc_local).length
                if dist > radius:
                    continue
                # smooth falloff (power-based)
                t = 1.0 - (dist / radius)
                if t < 0.0:
                    continue
                falloff = t ** falloff_power
                # sample displacement from C lib using world coords
                s = 0.0
                try:
                    s = float(_lib.txtur_sample_displacement(ctypes.c_float(loc_world.x), ctypes.c_float(loc_world.y), ctypes.c_float(loc_world.z)))
                except Exception:
                    s = 0.0
                delta = s * strength * falloff * 0.1
                # apply along vertex normal (local)
                n = v.normal
                v.co = v.co + (n * delta)

            bm.to_mesh(mesh)
            mesh.update()
            bm.free()
            return


class TXTUR_OT_enter_brush_mode(bpy.types.Operator):
    bl_idname = 'txtur.enter_brush_mode'
    bl_label = 'Enter TxTUR Brush Mode'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, 'Select a mesh object first')
            return {'CANCELLED'}

        # Ensure an image exists and assign it to the object material for painting
        img_name = 'TxTUR_PaintTex'
        width, height = 1024, 1024
        if img_name in bpy.data.images:
            img = bpy.data.images[img_name]
        else:
            # create buffer using C if available
            img = bpy.data.images.new(img_name, width=width, height=height, alpha=True)
            try:
                size = width * height * 4
                BufType = ctypes.c_ubyte * size
                buf = BufType()
                if _lib and hasattr(_lib, 'txtur_fill_test_image'):
                    _lib.txtur_fill_test_image(ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)), width, height)
                    pixels = [v / 255.0 for v in buf]
                    img.pixels = pixels
                    img.update()
            except Exception:
                pass

        # switch to Texture Paint mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        bpy.ops.paint.texture_paint_toggle()

        # Set brush properties
        ts = context.tool_settings
        ip = ts.image_paint
        if ip is not None:
            b = ip.brush
            if b is None:
                b = bpy.data.brushes.new('TxTUR_Brush', mode='IMAGE')
                ip.brush = b
            b.size = int(context.scene.txtur_brush_size)
            b.strength = context.scene.txtur_brush_intensity

        self.report({'INFO'}, 'Entered Texture Paint (TxTUR)')
        return {'FINISHED'}


class TXTUR_OT_stamp_at_cursor(bpy.types.Operator):
    bl_idname = 'txtur.stamp_at_cursor'
    bl_label = 'Stamp Brush at Cursor'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}

        # find a 3D View area to project
        area = None
        region = None
        rv3d = None
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                for r in a.regions:
                    if r.type == 'WINDOW':
                        region = r
                        break
                rv3d = a.spaces.active.region_3d
                break

        if not area or not region or not rv3d:
            self.report({'ERROR'}, 'No 3D View found')
            return {'CANCELLED'}

        coord_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, context.scene.cursor.location)
        if not coord_2d:
            self.report({'ERROR'}, 'Cursor not in view')
            return {'CANCELLED'}

        mx, my = int(coord_2d.x), int(coord_2d.y)

        # perform an image paint stroke at the mouse position
        stroke = [{
            'name': '',
            'mouse': (mx, my),
            'pressure': 1.0,
            'size': int(context.scene.txtur_brush_size),
            'pen_flip': False,
            'is_start': True
        }]

        try:
            # switch context to the found area for operator
            override = context.copy()
            override['area'] = area
            override['region'] = region
            bpy.ops.paint.image_paint(override, stroke=stroke)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        self.report({'INFO'}, 'Stamped brush at cursor')
        return {'FINISHED'}


class TXTUR_OT_apply_mapping(bpy.types.Operator):
    bl_idname = 'txtur.apply_mapping'
    bl_label = 'Apply Mapping'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        scn = context.scene
        mapping = int(scn.txtur_mapping_index)
        depth = float(scn.txtur_mapping_depth)
        loc = context.scene.cursor.location
        res = _lib.txtur_apply_mapping_simple(mapping, loc.x, loc.y, loc.z, ctypes.c_float(depth))
        if res != 0:
            self.report({'ERROR'}, 'Mapping apply failed')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Applied mapping {mapping}')
        return {'FINISHED'}


class TXTUR_OT_node_add(bpy.types.Operator):
    bl_idname = 'txtur.node_add'
    bl_label = 'NodeCraft: Add Node'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        loc = context.scene.cursor.location
        nid = _lib.txtur_node_add(loc.x, loc.y, loc.z, ctypes.c_float(1.0))
        if nid < 0:
            self.report({'ERROR'}, 'Node add failed')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Node added id={nid}')
        return {'FINISHED'}


class TXTUR_OT_node_link(bpy.types.Operator):
    bl_idname = 'txtur.node_link'
    bl_label = 'NodeCraft: Link Last Two'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        # This operator links the last two nodes (simple helper)
        # NOTE: This requires the C-side to manage node indices; we attempt a best-effort link
        # Ask C to add two nodes quickly if none exist is not implemented; user can add nodes first.
        # For simplicity, here we use indices 0 and 1.
        res = _lib.txtur_node_link(0, 1, 0, ctypes.c_float(0.1))
        if res < 0:
            self.report({'ERROR'}, 'Node link failed')
            return {'CANCELLED'}
        self.report({'INFO'}, f'Linked nodes 0 and 1 (link id={res})')
        return {'FINISHED'}


class TXTUR_OT_generate_image(bpy.types.Operator):
    bl_idname = 'txtur.generate_image'
    bl_label = 'Generate Test Image (TxTUR)'

    def execute(self, context):
        if not lib_ok():
            self.report({'ERROR'}, 'TxTUR library not loaded')
            return {'CANCELLED'}
        try:
            width = 256
            height = 256
            size = width * height * 4
            BufType = ctypes.c_ubyte * size
            buf = BufType()

            # configure function prototype
            try:
                _lib.txtur_fill_test_image.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.c_int]
                _lib.txtur_fill_test_image.restype = ctypes.c_int
            except Exception:
                pass

            res = _lib.txtur_fill_test_image(ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)), width, height)
            if not res:
                self.report({'ERROR'}, 'txtur_fill_test_image failed')
                return {'CANCELLED'}

            # Create a new image in Blender and assign pixels (expects floats 0..1)
            img_name = 'TxTUR_Test'
            if img_name in bpy.data.images:
                img = bpy.data.images[img_name]
                if img.size[0] != width or img.size[1] != height:
                    bpy.data.images.remove(img)
                    img = bpy.data.images.new(img_name, width=width, height=height, alpha=True)
            else:
                img = bpy.data.images.new(img_name, width=width, height=height, alpha=True)

            # Convert buffer to float pixels
            pixels = [v / 255.0 for v in buf]
            img.pixels = pixels
            img.update()

            # Show image in first Image Editor found
            for area in bpy.context.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    area.spaces.active.image = img
                    break

            self.report({'INFO'}, f'Generated image "{img.name}"')
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}


def register():
    bpy.utils.register_class(TXTUR_OT_init)
    bpy.utils.register_class(TXTUR_PT_panel)
    bpy.utils.register_class(TXTUR_OT_generate_image)
    bpy.utils.register_class(TXTUR_OT_apply_brush)
    bpy.utils.register_class(TXTUR_OT_apply_mapping)
    bpy.utils.register_class(TXTUR_OT_node_add)
    bpy.utils.register_class(TXTUR_OT_node_link)
    bpy.utils.register_class(TXTUR_OT_modal_sculpt)

    bpy.types.Scene.txtur_brush_index = IntProperty(name='TxTUR Brush', default=0, min=0, max=11)
    bpy.types.Scene.txtur_brush_intensity = FloatProperty(name='TxTUR Intensity', default=0.5, min=0.0, max=1.0)
    bpy.types.Scene.txtur_brush_size = IntProperty(name='TxTUR Size', default=64, min=1, max=4096)
    bpy.types.Scene.txtur_falloff_power = FloatProperty(name='TxTUR Falloff Power', default=2.0, min=0.1, max=8.0)
    bpy.types.Scene.txtur_mapping_index = IntProperty(name='TxTUR Mapping', default=0, min=0, max=31)
    bpy.types.Scene.txtur_mapping_depth = FloatProperty(name='TxTUR Depth', default=0.5, min=0.0, max=1.0)


def unregister():
    bpy.utils.unregister_class(TXTUR_PT_panel)
    bpy.utils.unregister_class(TXTUR_OT_init)
    bpy.utils.unregister_class(TXTUR_OT_generate_image)
    bpy.utils.unregister_class(TXTUR_OT_apply_brush)
    bpy.utils.unregister_class(TXTUR_OT_apply_mapping)
    bpy.utils.unregister_class(TXTUR_OT_node_add)
    bpy.utils.unregister_class(TXTUR_OT_node_link)

    del bpy.types.Scene.txtur_brush_index
    del bpy.types.Scene.txtur_brush_intensity
    del bpy.types.Scene.txtur_brush_size
    del bpy.types.Scene.txtur_falloff_power
    del bpy.types.Scene.txtur_mapping_index
    del bpy.types.Scene.txtur_mapping_depth
    bpy.utils.unregister_class(TXTUR_OT_modal_sculpt)


if __name__ == '__main__':
    register()
