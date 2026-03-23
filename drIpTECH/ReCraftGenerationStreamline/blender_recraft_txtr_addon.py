bl_info = {
    "name": "Recraft TxTUR Bridge",
    "author": "drIpTECH",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "description": "Import generated textures and run a TxTUR placeholder pipeline (readAIpolish integration point)",
    "category": "Import-Export",
}

import bpy
import os

class RCRAFT_OT_import_and_model(bpy.types.Operator):
    bl_idname = "recraft.import_and_model"
    bl_label = "Import image and run TxTUR"

    image_path: bpy.props.StringProperty(name="Image Path", subtype='FILE_PATH')
    out_blend: bpy.props.StringProperty(name="Output .blend", subtype='FILE_PATH')
    run_auto_model: bpy.props.BoolProperty(name="Run Auto-Model (readAIpolish)", default=True)

    def execute(self, context):
        img_path = self.image_path
        out_path = self.out_blend or bpy.data.filepath or os.path.join(os.getcwd(), 'recraft_out.blend')
        if not os.path.exists(img_path):
            self.report({'ERROR'}, f"Image not found: {img_path}")
            return {'CANCELLED'}

        # Clear scene
        bpy.ops.wm.read_factory_settings(use_empty=True)

        # Load image
        img = bpy.data.images.load(img_path)

        # Create material with image texture
        mat = bpy.data.materials.new(name='RecraftMat')
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex = nodes.new(type='ShaderNodeTexImage')
        tex.image = img
        bsdf = nodes.get('Principled BSDF')
        if bsdf is None:
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

        # Create a plane and assign material
        bpy.ops.mesh.primitive_plane_add(size=2)
        ob = bpy.context.active_object
        if ob.data.materials:
            ob.data.materials[0] = mat
        else:
            ob.data.materials.append(mat)

        # Try to call readAIpolish/TxTUR integration if requested and available
        if self.run_auto_model:
            try:
                import importlib
                ra = importlib.import_module('readAIpolish')
                if hasattr(ra, 'auto_model'):
                    try:
                        ra.auto_model(img_path, context={'bpy': bpy})
                    except Exception as e:
                        print('readAIpolish.auto_model failed:', e)
                else:
                    print('readAIpolish module found but no auto_model() entrypoint; skipping')
            except Exception:
                # Try calling an external CLI `readAIpolish` if available on PATH
                try:
                    import subprocess
                    subprocess.run(['readAIpolish', img_path], check=False)
                    print('Invoked external readAIpolish CLI (if present)')
                except Exception:
                    print('readAIpolish not available; skipping auto-model step')

        # Save .blend
        bpy.ops.wm.save_mainfile(filepath=out_path)
        self.report({'INFO'}, f"Saved {out_path}")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(RCRAFT_OT_import_and_model.bl_idname)

def register():
    bpy.utils.register_class(RCRAFT_OT_import_and_model)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_class(RCRAFT_OT_import_and_model)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)

if __name__ == '__main__':
    register()
