bl_info = {
    "name": "DripCraft AI Pipeline",
    "author": "drIpTECH",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "description": "Integrates Recraft -> DripCraft CLI -> readAIpolish pipeline inside Blender",
    "category": "Import-Export",
}

import bpy
import os
import subprocess
import json

class DRIPCRAFT_OT_pipeline(bpy.types.Operator):
    bl_idname = "dripcraft.run_pipeline"
    bl_label = "Run DripCraft Pipeline"

    image_path: bpy.props.StringProperty(name="Image Path", subtype='FILE_PATH')
    out_blend: bpy.props.StringProperty(name="Output .blend", subtype='FILE_PATH')
    run_recraft: bpy.props.BoolProperty(name="Run Recraft Manifest", default=False)
    run_dripcraft_cli: bpy.props.BoolProperty(name="Run DripCraft CLI", default=True)
    run_readAIpolish: bpy.props.BoolProperty(name="Run readAIpolish Auto-Model", default=True)

    def execute(self, context):
        img_path = self.image_path
        out_path = self.out_blend or bpy.data.filepath or os.path.join(os.getcwd(), 'dripcraft_out.blend')
        if self.run_recraft:
            # Attempt to run run_pipeline.py from the ReCraftGenerationStreamline folder
            base = os.path.dirname(__file__)
            runner = os.path.join(base, '..', 'ReCraftGenerationStreamline', 'run_pipeline.py')
            runner = os.path.normpath(runner)
            if os.path.exists(runner):
                try:
                    p = subprocess.run([bpy.app.binary_path_python, runner], check=False)
                    print('Recraft runner exit code:', p.returncode)
                except Exception as e:
                    self.report({'WARNING'}, f'Recraft runner failed: {e}')
            else:
                self.report({'INFO'}, 'Recraft runner not found; skipping')

        # If image not provided, try to pick a default generated asset
        if not img_path or not os.path.exists(img_path):
            # look for assets/tommy_sprite.png near the run_pipeline script
            base = os.path.dirname(__file__)
            alt = os.path.normpath(os.path.join(base, '..', 'ReCraftGenerationStreamline', 'assets', 'tommy_sprite.png'))
            if os.path.exists(alt): img_path = alt
            else: self.report({'ERROR'}, f'Image not found: {img_path}'); return {'CANCELLED'}

        # Optionally run the DripCraft C CLI to generate artifacts
        base = os.path.dirname(__file__)
        drip_cli = os.path.join(base, 'DripCraft.exe' if os.name=='nt' else 'DripCraft')
        drip_cli = os.path.normpath(drip_cli)
        work_dir = os.path.join(os.path.dirname(img_path), 'dripcraft_out')
        os.makedirs(work_dir, exist_ok=True)

        if self.run_dripcraft_cli:
            if os.path.exists(drip_cli):
                try:
                    p = subprocess.run([drip_cli, 'model', img_path, work_dir], check=False, capture_output=True, text=True)
                    print('DripCraft output:', p.stdout)
                except Exception as e:
                    self.report({'WARNING'}, f'DripCraft CLI failed: {e}')
            else:
                self.report({'INFO'}, f'DripCraft executable not found at {drip_cli}; skipping CLI step')

        # Attempt to call readAIpolish.auto_model if installed
        if self.run_readAIpolish:
            try:
                ra = __import__('readAIpolish')
                if hasattr(ra, 'auto_model'):
                    try:
                        ra.auto_model(img_path, context={'bpy': bpy, 'work_dir': work_dir})
                        print('readAIpolish.auto_model ran successfully')
                    except Exception as e:
                        print('readAIpolish.auto_model error:', e)
                else:
                    print('readAIpolish module present but auto_model not found')
            except Exception:
                # fallback: try external CLI
                try:
                    subprocess.run(['readAIpolish', img_path, work_dir], check=False)
                    print('Invoked external readAIpolish CLI')
                except Exception:
                    print('readAIpolish not available; skipping')

        # Import the generated texture into Blender and create a plane
        try:
            img = bpy.data.images.load(img_path)
        except Exception:
            self.report({'ERROR'}, f'Failed to load image {img_path}'); return {'CANCELLED'}

        mat = bpy.data.materials.new(name='DripCraftMat')
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex = nodes.new(type='ShaderNodeTexImage')
        tex.image = img
        bsdf = nodes.get('Principled BSDF')
        if bsdf is None:
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

        bpy.ops.mesh.primitive_plane_add(size=2)
        ob = bpy.context.active_object
        if ob.data.materials:
            ob.data.materials[0] = mat
        else:
            ob.data.materials.append(mat)

        bpy.ops.wm.save_mainfile(filepath=out_path)
        self.report({'INFO'}, f"Saved pipeline output to {out_path}")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(DRIPCRAFT_OT_pipeline.bl_idname)


def register():
    bpy.utils.register_class(DRIPCRAFT_OT_pipeline)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    try:
        bpy.utils.unregister_class(DRIPCRAFT_OT_pipeline)
        bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    except Exception:
        pass

if __name__ == '__main__':
    register()
