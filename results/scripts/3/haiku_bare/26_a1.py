import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default scene contents
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Timeline: 96 frames total, light loops every 48 frames
scene.frame_start = 1
scene.frame_end = 96
scene.frame_set(1)

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor_mat = bpy.data.materials.new("FloorMat")
floor_mat.use_nodes = True
fbsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
fbsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
fbsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(floor_mat)

# Subject: a glossy sphere and a couple of blocks
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1.0), segments=64, ring_count=32)
sphere = bpy.context.active_object
sphere.name = "Subject"
sphere_mat = bpy.data.materials.new("SubjectMat")
sphere_mat.use_nodes = True
sbsdf = sphere_mat.node_tree.nodes.get("Principled BSDF")
sbsdf.inputs["Base Color"].default_value = (0.9, 0.4, 0.15, 1.0)
sbsdf.inputs["Metallic"].default_value = 0.0
sbsdf.inputs["Roughness"].default_value = 0.25
sphere.data.materials.append(sphere_mat)
bpy.ops.object.shade_smooth()

for i, (loc, scale) in enumerate([((2.8, 1.2, 0.6), (0.6, 0.6, 0.6)),
                                  ((-2.6, -1.4, 0.9), (0.9, 0.9, 0.9))]):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    block = bpy.context.active_object
    block.name = f"Block_{i}"
    block.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bmat = bpy.data.materials.new(f"BlockMat_{i}")
    bmat.use_nodes = True
    bb = bmat.node_tree.nodes.get("Principled BSDF")
    bb.inputs["Base Color"].default_value = (0.2, 0.5, 0.9, 1.0)
    bb.inputs["Roughness"].default_value = 0.5
    block.data.materials.append(bmat)

# Pulsing point light
bpy.ops.object.light_add(type='POINT', location=(0, -3.0, 3.5))
light = bpy.context.active_object
light.name = "PulseLight"
light.data.shadow_soft_size = 0.4
light.data.color = (1.0, 0.85, 0.7)

DIM = 50.0
BRIGHT = 2000.0

# Keyframes: dim at 1 & 49, bright at 25 & 73 -> period 48 frames
keys = {1: DIM, 25: BRIGHT, 49: DIM, 73: BRIGHT}
for f, e in keys.items():
    light.data.energy = e
    light.data.keyframe_insert(data_path="energy", frame=f)

# Smooth interpolation and cyclic extrapolation for a seamless loop
def get_fcurves(action):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    result = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                result.extend(cb.fcurves)
    return result

action = light.data.animation_data.action
for fc in get_fcurves(action):
    if fc.data_path == "energy":
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.modifiers.new(type='CYCLES')

# Camera framing the subject
bpy.ops.object.camera_add(location=(6.0, -7.5, 4.5))
cam = bpy.context.active_object
cam.name = "Camera"
target = Vector((0.0, 0.0, 1.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
scene.camera = cam

# Soft ambient world lighting
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wbg = world.node_tree.nodes.get("Background")
wbg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
wbg.inputs["Strength"].default_value = 0.5

scene.frame_set(1)
