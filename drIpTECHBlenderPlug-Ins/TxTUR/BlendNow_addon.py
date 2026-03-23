bl_info = {
    "name": "BlendNow VIP Pipeline",
    "author": "drIpTECH",
    "version": (0, 9),
    "blender": (5, 0, 0),
    "description": "VIP wrapper around TxTUR + readAIpolish + Blender automation",
    "category": "Import-Export",
}

import bpy
import os
import subprocess
import sys


class BLENDNOW_OT_pipeline(bpy.types.Operator):
    bl_idname = "blendnow.run_pipeline"
    bl_label = "Run BlendNow Pipeline"

    image_path: bpy.props.StringProperty(name="Image Path", subtype='FILE_PATH')
    out_blend: bpy.props.StringProperty(name="Output .blend", subtype='FILE_PATH')
    run_readaipolish: bpy.props.BoolProperty(name="Run readAIpolish", default=True)

    def execute(self, context):
        image_path = self.image_path
        out_path = self.out_blend or bpy.data.filepath or os.path.join(os.getcwd(), "blendnow_output.blend")
        if not image_path or not os.path.exists(image_path):
            self.report({'ERROR'}, f"Image not found: {image_path}")
            return {'CANCELLED'}

        if self.run_readaipolish:
            cli_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "readAIpolish", "readAIpolish_cli.py"))
            if os.path.exists(cli_path):
                subprocess.run([bpy.app.binary_path_python, cli_path, image_path], check=False)

        bpy.ops.wm.save_as_mainfile(filepath=out_path)
        self.report({'INFO'}, f"BlendNow saved {out_path}")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(BLENDNOW_OT_pipeline.bl_idname)


def register():
    bpy.utils.register_class(BLENDNOW_OT_pipeline)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    bpy.utils.unregister_class(BLENDNOW_OT_pipeline)


if __name__ == "__main__":
    register()