import bpy
import bmesh
import math
import mathutils
from bpy_extras import anim_utils

# ---------- Clear any existing objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.frame_current = 1


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, emission_strength=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_sphere(name, radius, material, segments=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj


# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.005, 0.006, 0.012, 1.0)
    bg_node.inputs[1].default_value = 1.0

# ---------- Materials ----------
star_mat = make_material("StarMat", (1.0, 0.75, 0.35), roughness=0.4, emission_strength=12.0)
planet_mat = make_material("PlanetMat", (0.15, 0.45, 0.9), roughness=0.6)

# ---------- Star ----------
star = make_sphere("Star", 1.8, star_mat)
scene.collection.objects.link(star)

star_light = bpy.data.lights.new("StarLight", type='POINT')
star_light.energy = 4000.0
star_light.shadow_soft_size = 0.5
star_light_obj = bpy.data.objects.new("StarLight", star_light)
scene.collection.objects.link(star_light_obj)
star_light_obj.location = (0.0, 0.0, 0.0)

# ---------- Orbit pivot and planet ----------
ORBIT_RADIUS = 6.0
pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)
pivot.location = (0.0, 0.0, 0.0)
pivot.empty_display_size = 1.0

planet = make_sphere("Planet", 0.9, planet_mat)
scene.collection.objects.link(planet)
planet.parent = pivot
planet.location = (ORBIT_RADIUS, 0.0, 0.0)

# ---------- Animate full revolution with linear interpolation ----------
pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=120)

action = pivot.animation_data.action
slot = pivot.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    fcurve.extrapolation = 'LINEAR'
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

cam_location = mathutils.Vector((0.0, -22.0, 12.0))
cam_obj.location = cam_location
target = mathutils.Vector((0.0, 0.0, 0.0))
direction = target - cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj
