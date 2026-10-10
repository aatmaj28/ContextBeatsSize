import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Render settings ----------
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.frame_start = 1
scene.frame_end = 96
scene.frame_set(1)

# ---------- World ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# ---------- Materials ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

mat_floor = make_material("Floor", (0.8, 0.8, 0.8), roughness=0.9)
mat_sphere = make_material("Sphere", (0.8, 0.25, 0.15), roughness=0.3)
mat_cube = make_material("Cube", (0.2, 0.4, 0.8), roughness=0.4)
mat_torus = make_material("Torus", (0.9, 0.75, 0.3), roughness=0.15, metallic=1.0)

# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1.0), segments=64, ring_count=32)
sphere = bpy.context.active_object
sphere.data.materials.append(mat_sphere)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_cube_add(size=1.4, location=(2.2, 0.8, 0.7), rotation=(0, 0, math.radians(30)))
cube = bpy.context.active_object
cube.data.materials.append(mat_cube)

bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.25,
                                 location=(-1.9, 1.2, 0.25), rotation=(math.radians(90), 0, 0))
torus = bpy.context.active_object
torus.data.materials.append(mat_torus)
bpy.ops.object.shade_smooth()

# ---------- Point light with pulsing energy ----------
light_data = bpy.data.lights.new(name="PulseLight", type='POINT')
light_data.shadow_soft_size = 0.3
light_obj = bpy.data.objects.new("PulseLight", light_data)
scene.collection.objects.link(light_obj)
light_obj.location = (0.0, -2.5, 3.0)

DIM_W = 5.0
BRIGHT_W = 1500.0

# Keyframes: dim at 1, bright at 25, dim at 49 (one 48-frame cycle)
keys = [(1, DIM_W), (25, BRIGHT_W), (49, DIM_W)]
for frame, energy in keys:
    light_data.energy = energy
    light_data.keyframe_insert(data_path="energy", frame=frame)

# Cycle the F-Curve so the pulse repeats every 48 frames across the full 96-frame range
action = light_data.animation_data.action
slot = light_data.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
fcurve = channelbag.fcurves.find("energy")
if fcurve:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
    fcurve.update()
    fcurve.modifiers.new('CYCLES')

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((7.0, -7.5, 4.5))
target = Vector((0.0, 0.0, 0.8))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj
