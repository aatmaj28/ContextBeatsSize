import bpy
import math
from bpy_extras import anim_utils
from mathutils import Vector

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Helpers ----------
def make_material(name, color, emission_strength=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Star ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
bpy.ops.object.shade_smooth()
star.data.materials.append(make_material("StarMat", (1.0, 0.75, 0.35), emission_strength=12.0))

# ---------- Orbit pivot (animated) ----------
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"

# ---------- Planet (child of pivot, offset as orbit radius) ----------
ORBIT_RADIUS = 5.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=40, ring_count=20,
                                     location=(ORBIT_RADIUS, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()
planet.data.materials.append(make_material("PlanetMat", (0.15, 0.4, 0.9), roughness=0.6))
planet.parent = pivot
planet.matrix_parent_inverse = pivot.matrix_world.inverted()

# ---------- Animation: full 360° rotation of the pivot, linear interpolation ----------
START_FRAME = 1
END_FRAME = START_FRAME + 120  # 120 frames of motion (one full loop)

pivot.rotation_mode = 'XYZ'
pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=START_FRAME)

pivot.rotation_euler = (0.0, 0.0, math.tau)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=END_FRAME)

# Set linear interpolation on all keys of the pivot's action (Blender 5.x layered API)
action = pivot.animation_data.action
slot = pivot.animation_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'
    fcurve.update()

# ---------- Scene frame range ----------
scene = bpy.context.scene
scene.frame_start = START_FRAME
scene.frame_end = END_FRAME
scene.frame_set(START_FRAME)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
star_light = bpy.context.active_object
star_light.name = "StarLight"
star_light.data.energy = 6000.0
star_light.data.color = (1.0, 0.8, 0.55)
star_light.data.shadow_soft_size = 0.5

bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "FillSun"
sun.data.energy = 1.5
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((0.0, -13.0, 7.0))

direction = Vector((0.0, 0.0, 0.0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
