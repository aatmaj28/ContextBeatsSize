import bpy
import math
from mathutils import Vector

# ---------- Helpers ----------

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                  bpy.data.cameras, bpy.data.actions):
        for item in list(block):
            if item.users == 0:
                block.remove(item)

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

def get_fcurves(action):
    """Works with both legacy actions and Blender 5.x layered/slotted actions."""
    try:
        return list(action.fcurves)
    except AttributeError:
        fcs = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs.extend(cb.fcurves)
        return fcs

def set_linear(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in get_fcurves(obj.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.extrapolation = 'LINEAR'

# ---------- Setup ----------

clear_scene()
scene = bpy.context.scene

# Make new keyframes default to linear as well
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 121  # 120 intervals of motion, seamless loop (frame 1 == frame 121 pose)

# ---------- Star ----------

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, segments=48, ring_count=24, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
star.data.materials.append(make_material("StarMat", (1.0, 0.75, 0.3), emission_strength=25.0, roughness=0.3))
bpy.ops.object.shade_smooth()

star_light = bpy.data.lights.new(name="StarLight", type='POINT')
star_light.energy = 6000.0
star_light.color = (1.0, 0.85, 0.6)
star_light.shadow_soft_size = 0.5
star_light_obj = bpy.data.objects.new("StarLight", star_light)
bpy.context.collection.objects.link(star_light_obj)
star_light_obj.location = (0, 0, 0)

# ---------- Orbit pivot ----------

pivot = bpy.data.objects.new("OrbitPivot", None)
pivot.empty_display_type = 'PLAIN_AXES'
pivot.empty_display_size = 0.5
bpy.context.collection.objects.link(pivot)
pivot.location = (0, 0, 0)
pivot.rotation_euler = (0, 0, 0)

# ---------- Planet ----------

orbit_radius = 6.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, segments=40, ring_count=20,
                                     location=(orbit_radius, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
planet.data.materials.append(make_material("PlanetMat", (0.15, 0.4, 0.85), roughness=0.6))
bpy.ops.object.shade_smooth()
planet.parent = pivot

# Small moon for visual interest (also orbits the planet region via the same pivot only)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, segments=24, ring_count=12,
                                     location=(orbit_radius + 1.0, 0, 0))
moon = bpy.context.active_object
moon.name = "Moon"
moon.data.materials.append(make_material("MoonMat", (0.7, 0.7, 0.72), roughness=0.9))
bpy.ops.object.shade_smooth()
moon.parent = planet

# ---------- Keyframes: full circle, constant speed ----------

pivot.rotation_mode = 'XYZ'
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

set_linear(pivot)

# Moon spins on its own axis at constant speed, linear too
moon.rotation_mode = 'XYZ'
moon.rotation_euler = (0, 0, 0)
moon.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
moon.rotation_euler = (0, 0, 2 * math.pi * 4)
moon.keyframe_insert(data_path="rotation_euler", index=2, frame=121)
set_linear(moon)

# ---------- Camera ----------

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)

cam_loc = Vector((0.0, -15.0, 9.0))
cam_obj.location = cam_loc
target = Vector((0.0, 0.0, 0.0))
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Fill light (soft world-like ambience via area light) ----------

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 300.0
fill_data.size = 10.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = (-8, -8, 10)
fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-45))

# ---------- World background ----------

world = bpy.data.worlds.new("SpaceWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.012, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world
