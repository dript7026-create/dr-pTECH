import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def argv_after_double_dash():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def load_config() -> dict:
    args = argv_after_double_dash()
    if not args:
        raise RuntimeError("Missing config path argument.")
    config_path = Path(args[0])
    return json.loads(config_path.read_text(encoding="utf-8"))


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def ensure_collection(name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def row_width_at(profile: dict, y_ratio: float) -> float:
    rows = profile["rows"]
    index = max(0, min(len(rows) - 1, int(round((1.0 - y_ratio) * (len(rows) - 1)))))
    width = rows[index]["width"]
    if width > 0:
        return float(width)
    for delta in range(1, len(rows)):
        for candidate in (index - delta, index + delta):
            if 0 <= candidate < len(rows) and rows[candidate]["width"] > 0:
                return float(rows[candidate]["width"])
    return 6.0


def create_armature(config: dict):
    rig = config["rig"]
    bones = rig["bones"]
    ys = [bone["y"] for bone in bones]
    min_y = min(ys)
    max_y = max(ys)
    height_units = 2.2
    scale = height_units / max(1.0, float(max_y - min_y))
    points = {}
    for bone in bones:
        points[bone["name"]] = Vector((float(bone["x"]) * scale * 0.95, 0.0, (float(bone["y"]) - min_y) * scale))

    bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0.0, 0.0, 0.0))
    armature_obj = bpy.context.object
    armature_obj.name = "BangoRig"
    armature = armature_obj.data
    armature.name = "BangoRigData"
    edit_bones = armature.edit_bones
    default_bone = edit_bones[0]
    edit_bones.remove(default_bone)

    for bone in bones:
        edit_bone = edit_bones.new(bone["name"])
        bone_point = points[bone["name"]]
        parent_name = bone["parent"]
        if parent_name:
            parent_point = points[parent_name]
            edit_bone.head = parent_point
            edit_bone.tail = bone_point if (bone_point - parent_point).length > 0.001 else parent_point + Vector((0.0, 0.0, 0.08))
        else:
            edit_bone.head = bone_point
            pelvis = points.get("pelvis", bone_point + Vector((0.0, 0.0, 0.12)))
            edit_bone.tail = pelvis if (pelvis - bone_point).length > 0.001 else bone_point + Vector((0.0, 0.0, 0.12))

    for bone in bones:
        parent_name = bone["parent"]
        if parent_name:
            edit_bones[bone["name"]].parent = edit_bones[parent_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    return armature_obj, points, scale, min_y, max_y


def orient_cylinder(obj, start: Vector, end: Vector) -> None:
    direction = end - start
    obj.location = (start + end) * 0.5
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())


def create_blockout_mesh(config: dict, points: dict, scale: float, min_y: float, max_y: float):
    front_profile = next(frame["profile"] for frame in config["sheet"]["frames"] if frame["label"] == "front")
    side_profile = next(frame["profile"] for frame in config["sheet"]["frames"] if frame["label"] in {"left", "right"})
    rig_bones = config["rig"]["bones"]
    created = []
    for bone in rig_bones:
        bone_name = bone["name"]
        point = points[bone_name]
        ratio = (float(bone["y"]) - min_y) / max(1.0, max_y - min_y)
        width_units = row_width_at(front_profile, ratio) * scale * 0.45
        depth_units = row_width_at(side_profile, ratio) * scale * 0.22
        radius = max(0.04, min(width_units, depth_units) * 0.18)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * 1.2, location=point)
        sphere = bpy.context.object
        sphere.name = f"joint_{bone_name}"
        sphere.scale = (max(radius * 1.5, width_units * 0.12), max(radius * 1.4, depth_units * 0.16), max(radius * 1.6, width_units * 0.11))
        created.append(sphere)
        parent_name = bone["parent"]
        if parent_name:
            start = points[parent_name]
            end = point
            if (end - start).length > 0.02:
                bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=(end - start).length)
                cylinder = bpy.context.object
                cylinder.name = f"segment_{parent_name}_{bone_name}"
                cylinder.scale = (max(radius * 1.2, width_units * 0.08), max(radius * 1.1, depth_units * 0.11), 1.0)
                orient_cylinder(cylinder, start, end)
                created.append(cylinder)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in created:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = created[0]
    bpy.ops.object.join()
    mesh_obj = bpy.context.object
    mesh_obj.name = "BangoAutoMesh"
    bpy.ops.object.modifier_add(type='REMESH')
    mesh_obj.modifiers["Remesh"].mode = 'VOXEL'
    mesh_obj.modifiers["Remesh"].voxel_size = 0.06
    bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='SUBSURF')
    mesh_obj.modifiers["Subdivision"].levels = 1
    mesh_obj.modifiers["Subdivision"].render_levels = 2
    return mesh_obj


def attach_blendnow_txtur_metadata(config: dict):
    collection = ensure_collection("BlendNow_TxTUR")
    scene = bpy.context.scene
    scene["blendnow_trial_sheet_lift"] = config["toolchain"]["trial"]["sheet_lift"]
    scene["blendnow_vip_sheet_lift"] = config["toolchain"]["vip"]["sheet_lift"]
    spec_path = Path(config["blendnow"]["import_spec"])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for node in spec.get("nodecraft", {}).get("nodes", []):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=tuple(node["position"]))
        empty = bpy.context.object
        empty.name = f"BlendNow_{node['id']}"
        empty.scale = (node["scale"], node["scale"], node["scale"])
        if empty.name not in collection.objects:
            collection.objects.link(empty)
            bpy.context.scene.collection.objects.unlink(empty)
    return spec


def assign_box_projected_sheet_material(config: dict, mesh_obj, txtur_spec: dict):
    image = bpy.data.images.load(config["sheet"].get("polished_atlas_path", config["sheet"]["atlas_path"]))
    material = bpy.data.materials.new(name="BangoSheetProjected")
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    for node in list(nodes):
        nodes.remove(node)

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (800, 0)
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    material_profile = txtur_spec.get("materials", [{"roughness": 0.68, "normal_strength": 0.32}])[0]
    bsdf.inputs['Roughness'].default_value = material_profile.get("roughness", 0.68)
    texcoord = nodes.new(type='ShaderNodeTexCoord')
    texcoord.location = (-1000, 0)
    separate_pos = nodes.new(type='ShaderNodeSeparateXYZ')
    separate_pos.location = (-760, 140)
    separate_nrm = nodes.new(type='ShaderNodeSeparateXYZ')
    separate_nrm.location = (-760, -160)
    geometry = nodes.new(type='ShaderNodeNewGeometry')
    geometry.location = (-1000, -160)

    bounds = [Vector(corner) for corner in mesh_obj.bound_box]
    min_x = min(v.x for v in bounds)
    max_x = max(v.x for v in bounds)
    min_y = min(v.y for v in bounds)
    max_y = max(v.y for v in bounds)
    min_z = min(v.z for v in bounds)
    max_z = max(v.z for v in bounds)

    def make_frame_mapping(name: str, frame_index: int, axis: str, mirror: bool):
        combine = nodes.new(type='ShaderNodeCombineXYZ')
        combine.location = (-360, 220 - frame_index * 140)
        mapping_x = nodes.new(type='ShaderNodeMapRange')
        mapping_x.location = (-560, 240 - frame_index * 140)
        mapping_y = nodes.new(type='ShaderNodeMapRange')
        mapping_y.location = (-560, 160 - frame_index * 140)
        tex = nodes.new(type='ShaderNodeTexImage')
        tex.location = (-120, 220 - frame_index * 140)
        tex.image = image
        tex.interpolation = 'Closest'
        for node in (mapping_x, mapping_y):
            node.clamp = True
        if axis == 'front':
            src_a = separate_pos.outputs['X']
            from_min_a, from_max_a = min_x, max_x
        else:
            src_a = separate_pos.outputs['Y']
            from_min_a, from_max_a = min_y, max_y
        mapping_x.inputs['From Min'].default_value = from_min_a
        mapping_x.inputs['From Max'].default_value = from_max_a
        if mirror:
            mapping_x.inputs['To Min'].default_value = (frame_index + 1) / 4.0
            mapping_x.inputs['To Max'].default_value = frame_index / 4.0
        else:
            mapping_x.inputs['To Min'].default_value = frame_index / 4.0
            mapping_x.inputs['To Max'].default_value = (frame_index + 1) / 4.0
        mapping_y.inputs['From Min'].default_value = min_z
        mapping_y.inputs['From Max'].default_value = max_z
        mapping_y.inputs['To Min'].default_value = 0.0
        mapping_y.inputs['To Max'].default_value = 1.0
        links.new(src_a, mapping_x.inputs['Value'])
        links.new(separate_pos.outputs['Z'], mapping_y.inputs['Value'])
        links.new(mapping_x.outputs['Result'], combine.inputs['X'])
        links.new(mapping_y.outputs['Result'], combine.inputs['Y'])
        links.new(combine.outputs['Vector'], tex.inputs['Vector'])
        return tex

    links.new(texcoord.outputs['Object'], separate_pos.inputs['Vector'])
    links.new(geometry.outputs['Normal'], separate_nrm.inputs['Vector'])
    front_tex = make_frame_mapping('front', 0, 'front', False)
    left_tex = make_frame_mapping('left', 1, 'side', False)
    right_tex = make_frame_mapping('right', 2, 'side', True)
    rear_tex = make_frame_mapping('rear', 3, 'front', True)

    abs_x = nodes.new(type='ShaderNodeMath')
    abs_x.operation = 'ABSOLUTE'
    abs_x.location = (-500, -260)
    abs_y = nodes.new(type='ShaderNodeMath')
    abs_y.operation = 'ABSOLUTE'
    abs_y.location = (-500, -340)
    compare_side = nodes.new(type='ShaderNodeMath')
    compare_side.operation = 'GREATER_THAN'
    compare_side.location = (-260, -280)
    front_back_compare = nodes.new(type='ShaderNodeMath')
    front_back_compare.operation = 'GREATER_THAN'
    front_back_compare.location = (-260, -380)
    mix_side = nodes.new(type='ShaderNodeMixRGB')
    mix_side.location = (120, -80)
    mix_back = nodes.new(type='ShaderNodeMixRGB')
    mix_back.location = (320, -10)
    mix_final = nodes.new(type='ShaderNodeMixRGB')
    mix_final.location = (500, 40)

    links.new(separate_nrm.outputs['X'], abs_x.inputs[0])
    links.new(separate_nrm.outputs['Y'], abs_y.inputs[0])
    links.new(abs_x.outputs[0], compare_side.inputs[0])
    links.new(abs_y.outputs[0], compare_side.inputs[1])
    links.new(separate_nrm.outputs['Y'], front_back_compare.inputs[0])
    front_back_compare.inputs[1].default_value = 0.0

    links.new(compare_side.outputs[0], mix_side.inputs['Fac'])
    links.new(left_tex.outputs['Color'], mix_side.inputs['Color1'])
    links.new(right_tex.outputs['Color'], mix_side.inputs['Color2'])
    links.new(front_back_compare.outputs[0], mix_back.inputs['Fac'])
    links.new(rear_tex.outputs['Color'], mix_back.inputs['Color1'])
    links.new(front_tex.outputs['Color'], mix_back.inputs['Color2'])
    links.new(compare_side.outputs[0], mix_final.inputs['Fac'])
    links.new(mix_back.outputs['Color'], mix_final.inputs['Color1'])
    links.new(mix_side.outputs['Color'], mix_final.inputs['Color2'])

    links.new(mix_final.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(output.inputs['Surface'], bsdf.outputs['BSDF'])

    if mesh_obj.data.materials:
        mesh_obj.data.materials[0] = material
    else:
        mesh_obj.data.materials.append(material)


def apply_pose(armature_obj, bone_values: dict[str, tuple[float, float, float]]) -> None:
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    for bone_name, rotation in bone_values.items():
        pose_bone = armature_obj.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        pose_bone.rotation_mode = 'XYZ'
        pose_bone.rotation_euler = rotation
    bpy.ops.object.mode_set(mode='OBJECT')


def key_pose(armature_obj, frame: int, bone_values: dict[str, tuple[float, float, float]], location_z: float | None = None) -> None:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    if location_z is not None:
        armature_obj.location.z = location_z
        armature_obj.keyframe_insert(data_path="location", frame=frame)
    for bone_name, rotation in bone_values.items():
        pose_bone = armature_obj.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        pose_bone.rotation_mode = 'XYZ'
        pose_bone.rotation_euler = rotation
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    bpy.ops.object.mode_set(mode='OBJECT')


def create_action(armature_obj, name: str, poses: list[tuple[int, dict[str, tuple[float, float, float]], float | None]], loop: bool = False):
    action = bpy.data.actions.new(name=name)
    armature_obj.animation_data_create()
    armature_obj.animation_data.action = action
    for frame, bone_values, location_z in poses:
        key_pose(armature_obj, frame, bone_values, location_z)
    return action


def create_test_animations(config: dict, armature_obj):
    pose_library = {
        "neutral": {"spine": (0.02, 0.0, 0.0), "head": (-0.05, 0.0, 0.0), "arm_l": (0.0, 0.0, 0.15), "arm_r": (0.0, 0.0, -0.15)},
        "stride_left": {"leg_l": (0.35, 0.0, 0.0), "leg_r": (-0.25, 0.0, 0.0), "arm_l": (-0.3, 0.0, 0.0), "arm_r": (0.3, 0.0, 0.0)},
        "stride_right": {"leg_l": (-0.25, 0.0, 0.0), "leg_r": (0.35, 0.0, 0.0), "arm_l": (0.3, 0.0, 0.0), "arm_r": (-0.3, 0.0, 0.0)},
        "block": {"arm_l": (-0.9, 0.0, 0.45), "arm_r": (-0.8, 0.0, -0.45), "spine": (0.12, 0.0, 0.0)},
        "parry": {"arm_l": (-0.65, 0.0, 0.75), "arm_r": (-0.15, 0.0, -0.2), "head": (0.1, 0.0, 0.0)},
        "hurt": {"spine": (0.35, 0.0, 0.0), "head": (0.35, 0.0, 0.0), "arm_l": (0.45, 0.0, 0.3), "arm_r": (0.45, 0.0, -0.3)},
        "heal": {"hand_l": (-0.5, 0.0, 0.2), "hand_r": (-0.3, 0.0, -0.2), "head": (-0.2, 0.0, 0.0)},
        "death": {"spine": (1.15, 0.0, 0.0), "neck": (0.45, 0.0, 0.0), "leg_l": (-0.55, 0.0, 0.0), "leg_r": (0.25, 0.0, 0.0)},
        "rest": {"spine": (-0.18, 0.0, 0.0), "head": (-0.25, 0.0, 0.0), "arm_l": (0.18, 0.0, 0.35), "arm_r": (0.18, 0.0, -0.35)},
        "attack_light": {"arm_l": (-1.1, 0.0, 0.55), "arm_r": (0.45, 0.0, -0.2), "spine": (-0.12, 0.0, 0.0)},
        "attack_heavy": {"arm_l": (-1.45, 0.0, 0.9), "arm_r": (-0.5, 0.0, -0.55), "spine": (-0.2, 0.0, 0.0)},
        "slide": {"leg_l": (0.55, 0.0, 0.0), "leg_r": (0.45, 0.0, 0.0), "spine": (0.28, 0.0, 0.0), "arm_l": (0.2, 0.0, 0.5), "arm_r": (0.1, 0.0, -0.5)},
    }
    plans = {
        "idle": [(1, pose_library["neutral"], 0.0), (16, {**pose_library["neutral"], "head": (-0.02, 0.0, 0.0)}, 0.03), (32, pose_library["neutral"], 0.0)],
        "walk": [(1, pose_library["stride_left"], 0.0), (10, pose_library["neutral"], 0.04), (20, pose_library["stride_right"], 0.0), (30, pose_library["neutral"], 0.04)],
        "sprint": [(1, pose_library["stride_left"], 0.1), (8, pose_library["stride_right"], 0.0), (16, pose_library["stride_left"], 0.1)],
        "attack_light_combo": [(1, pose_library["neutral"], 0.0), (8, pose_library["attack_light"], 0.0), (16, pose_library["neutral"], 0.0), (24, pose_library["attack_light"], 0.0), (32, pose_library["neutral"], 0.0)],
        "attack_heavy_combo": [(1, pose_library["neutral"], 0.0), (12, pose_library["attack_heavy"], 0.0), (28, pose_library["neutral"], 0.0)],
        "jump": [(1, pose_library["neutral"], 0.0), (8, {**pose_library["neutral"], "leg_l": (-0.35, 0.0, 0.0), "leg_r": (-0.35, 0.0, 0.0)}, 0.0), (16, {**pose_library["neutral"], "arm_l": (-0.45, 0.0, 0.0), "arm_r": (-0.45, 0.0, 0.0)}, 0.45), (28, pose_library["neutral"], 0.0)],
        "block_unarmed": [(1, pose_library["block"], 0.0), (24, pose_library["block"], 0.0)],
        "parry_unarmed": [(1, pose_library["neutral"], 0.0), (5, pose_library["parry"], 0.0), (14, pose_library["neutral"], 0.0)],
        "take_damage": [(1, pose_library["neutral"], 0.0), (7, pose_library["hurt"], -0.05), (18, pose_library["neutral"], 0.0)],
        "heal_honey_vial": [(1, pose_library["neutral"], 0.0), (10, pose_library["heal"], 0.0), (24, pose_library["heal"], 0.04), (32, pose_library["neutral"], 0.0)],
        "death": [(1, pose_library["hurt"], 0.0), (18, pose_library["death"], -0.15), (36, pose_library["death"], -0.18)],
        "rest_apiary": [(1, pose_library["rest"], 0.0), (24, pose_library["rest"], 0.02), (48, pose_library["rest"], 0.0)],
        "slide_from_sprint": [(1, pose_library["stride_left"], 0.0), (8, pose_library["slide"], -0.02), (18, pose_library["slide"], -0.03), (28, pose_library["neutral"], 0.0)],
    }
    actions = []
    for name in config.get("animation_plan", []):
        if name in plans:
            actions.append(create_action(armature_obj, name, plans[name], loop=name in {"idle", "walk", "sprint", "block_unarmed", "rest_apiary"}))
    return [action.name for action in actions]


def bind_mesh_to_armature(mesh_obj, armature_obj):
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.context.view_layer.objects.active = mesh_obj


def setup_render_scene(mesh_obj):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.render.film_transparent = False

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0.0, 0.0, 0.0))
    ground = bpy.context.object
    ground.name = 'GroundPlane'
    mat = bpy.data.materials.new(name='GroundMat')
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.09, 0.08, 0.075, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.92
    ground.data.materials.append(mat)

    bpy.ops.object.light_add(type='SUN', location=(2.0, -2.0, 4.0))
    sun = bpy.context.object
    sun.data.energy = 2.2
    sun.rotation_euler = (0.8, 0.1, 0.6)

    bpy.ops.object.light_add(type='AREA', location=(-2.5, -2.5, 2.2))
    fill = bpy.context.object
    fill.data.energy = 1200.0
    fill.data.size = 5.0
    fill.rotation_euler = (1.0, 0.0, -0.8)

    bpy.ops.object.camera_add(location=(0.0, -6.4, 2.1), rotation=(math.radians(82), 0.0, 0.0))
    camera = bpy.context.object
    camera.data.lens = 50
    camera.location = (0.0, -6.2, 2.0)
    direction = mesh_obj.location - camera.location
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = direction.to_track_quat('-Z', 'Z')
    bpy.context.scene.camera = camera


def export_outputs(config: dict):
    blend_path = config['outputs']['blend']
    render_path = config['outputs']['render']
    glb_path = config['outputs']['glb']
    bpy.context.scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_visible=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    blend_backup = Path(f"{blend_path}1")
    if blend_backup.exists():
        blend_backup.unlink()


def main():
    config = load_config()
    clear_scene()
    armature_obj, points, scale, min_y, max_y = create_armature(config)
    mesh_obj = create_blockout_mesh(config, points, scale, min_y, max_y)
    txtur_spec = attach_blendnow_txtur_metadata(config)
    assign_box_projected_sheet_material(config, mesh_obj, txtur_spec)
    bind_mesh_to_armature(mesh_obj, armature_obj)
    action_names = create_test_animations(config, armature_obj)
    config.setdefault("generated", {})["actions"] = action_names
    setup_render_scene(mesh_obj)
    export_outputs(config)
    print(json.dumps(config['outputs'], indent=2))


if __name__ == '__main__':
    main()