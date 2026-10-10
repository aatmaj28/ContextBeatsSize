import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene


# ---------- Helpers ----------
def make_material(name, base_color, roughness=0.5, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def add_sphere(name, radius, location, material, segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


# ---------- Materials ----------
star_mat = make_material(
    "StarMat", base_color=(1.0, 0.75, 0.3), roughness=0.4,
    emission_color=(1.0, 0.6, 0.2), emission_strength=8.0
)
planet_mat = make_material(
    "PlanetMat", base_color=(0.15, 0.4, 0.85), roughness=0.6
)

# ---------- Star (centre of the system) ----------
star = add_sphere("Star", radius=1.5, location=(0, 0, 0), material=star_mat)

# Point light at the star so the planet is lit from the correct side
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
star_light = bpy.context.active_object
star_light.name = "StarLight"
star_light.data.energy = 3000.0
star_light.data.shadow_soft_size = 0.5

# ---------- Orbit pivot ----------
# The pivot sits at the star and rotates about Z; the planet is parented to it.
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"
pivot.rotation_mode = 'XYZ'

# ---------- Planet ----------
orbit_radius = 6.0
planet = add_sphere("Planet", radius=0.8, location=(orbit_radius, 0, 0), material=planet_mat)
planet.parent = pivot
planet.matrix_parent_inverse.identity()

# ---------- Animation: full 360° rotation over 120 frames ----------
# Keys at frame 1 (0°) and frame 121 (360°) give 120 frame intervals.
FRAME_START = 1
FRAME_END = 121

pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_START)

pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)

# Set linear interpolation on the Z rotation F-Curve (Blender 5.x layered actions)
action = pivot.animation_data.action
slot = pivot.animation_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'
    fcurve.update()

# ---------- Scene timing ----------
scene.frame_start = FRAME_START
scene.frame_end = FRAME_END
scene.frame_set(FRAME_START)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0.0, -16.0, 9.0))

# Aim the camera at the origin
direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------- World background ----------
world = bpy.data.worlds.new("SpaceWorld")  # nodes created automatically in 5.x
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.0
