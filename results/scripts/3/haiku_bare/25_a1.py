import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# --- Clear default scene contents ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)


# --- Helpers ---
def make_material(name, color, emission_strength=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_sphere(name, radius, location, material, segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=segments, ring_count=rings, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(material)
    return obj


# --- World background ---
world = bpy.data.worlds.new("SpaceWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 0.3
scene.world = world

# --- Star ---
star_mat = make_material("StarMat", (1.0, 0.75, 0.3), emission_strength=8.0, roughness=0.3)
star = make_sphere("Star", 1.5, (0.0, 0.0, 0.0), star_mat)

star_light_data = bpy.data.lights.new(name="StarLight", type='POINT')
star_light_data.energy = 5000.0
star_light_data.color = (1.0, 0.8, 0.5)
star_light_data.shadow_soft_size = 0.5
star_light = bpy.data.objects.new("StarLight", star_light_data)
bpy.context.collection.objects.link(star_light)
star_light.location = (0.0, 0.0, 0.0)

# --- Planet ---
planet_mat = make_material("PlanetMat", (0.15, 0.4, 0.9), roughness=0.6)
orbit_radius = 5.0
planet = make_sphere("Planet", 0.6, (orbit_radius, 0.0, 0.0), planet_mat, segments=48, rings=24)
planet.rotation_euler = (math.radians(15), 0.0, 0.0)

# Pivot empty at the star's position; the planet is parented to it
pivot = bpy.data.objects.new("OrbitPivot", None)
bpy.context.collection.objects.link(pivot)
pivot.location = (0.0, 0.0, 0.0)
planet.parent = pivot

# --- Animation: full 360° orbit over 120 frames, linear interpolation ---
scene.frame_start = 1
scene.frame_end = 120

# Make newly inserted keyframes use linear interpolation
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

pivot.rotation_mode = 'XYZ'
pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

pivot.rotation_euler = (0.0, 0.0, math.radians(360.0))
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=120)

scene.frame_set(1)

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam_loc = Vector((0.0, -14.0, 7.0))
cam.location = cam_loc
target = Vector((0.0, 0.0, 0.0))
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
