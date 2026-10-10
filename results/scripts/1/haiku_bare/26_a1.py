import bpy
import math
from mathutils import Vector

# ---------- Scene timing ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 96
scene.frame_set(1)

# ---------- Clear default objects (keep scene empty-ish) ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

floor_mat = make_material("FloorMat", (0.8, 0.8, 0.8), roughness=0.9)
sphere_mat = make_material("SphereMat", (0.6, 0.15, 0.1), roughness=0.35, metallic=0.0)
pedestal_mat = make_material("PedestalMat", (0.3, 0.3, 0.35), roughness=0.6, metallic=0.2)

# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=0.6, location=(0, 0, 0.3))
pedestal = bpy.context.active_object
pedestal.name = "Pedestal"
pedestal.data.materials.append(pedestal_mat)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32,
                                     location=(0, 0, 1.6))
sphere = bpy.context.active_object
sphere.name = "Subject"
sphere.data.materials.append(sphere_mat)
bpy.ops.object.shade_smooth()

# ---------- Point light ----------
light_data = bpy.data.lights.new(name="PulseLightData", type='POINT')
light_data.color = (1.0, 0.85, 0.6)
light_data.shadow_soft_size = 0.2
light = bpy.data.objects.new("PulseLight", light_data)
bpy.context.collection.objects.link(light)
light.location = (2.5, -2.5, 3.0)

DIM_POWER = 50.0
BRIGHT_POWER = 1500.0

# Keyframes: dim at 1, bright at 25, dim at 49 (48-frame period)
light_data.energy = DIM_POWER
light_data.keyframe_insert(data_path="energy", frame=1)
light_data.energy = BRIGHT_POWER
light_data.keyframe_insert(data_path="energy", frame=25)
light_data.energy = DIM_POWER
light_data.keyframe_insert(data_path="energy", frame=49)

# Make the pulse cycle forever so frames 1-96 loop every 48 frames
def get_fcurves(datablock):
    action = datablock.animation_data.action
    if hasattr(action, "fcurves") and len(action.fcurves) > 0:
        return action.fcurves
    # Fallback for layered actions (Blender 4.4+/5.x)
    fcurves = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcurves.extend(cb.fcurves)
    return fcurves

for fc in get_fcurves(light_data):
    if fc.data_path == "energy":
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
        fc.modifiers.new(type='CYCLES')

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (5.5, -6.5, 3.8)

target = Vector((0.0, 0.0, 1.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Fill / world ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 0.5
scene.world = world
