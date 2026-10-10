import bpy
import math
from mathutils import Vector

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------- Helper functions ----------
def make_principled(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

def make_emission(name, color, strength=20.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1.0)
    emit.inputs["Strength"].default_value = strength
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat

# ---------- Star ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
star.data.materials.append(make_emission("StarMat", (1.0, 0.85, 0.4), strength=15.0))
bpy.ops.object.shade_smooth()

star_light = bpy.data.lights.new(name="StarLight", type='POINT')
star_light.energy = 6000
star_light.color = (1.0, 0.9, 0.7)
star_light_obj = bpy.data.objects.new("StarLight", star_light)
bpy.context.collection.objects.link(star_light_obj)
star_light_obj.location = (0, 0, 0)

# ---------- Orbit pivot (empty at star position) ----------
pivot = bpy.data.objects.new("OrbitPivot", None)
pivot.empty_display_type = 'PLAIN_AXES'
pivot.empty_display_size = 0.5
bpy.context.collection.objects.link(pivot)
pivot.location = (0, 0, 0)

# ---------- Planet (child of pivot, offset gives orbit radius) ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, segments=48, ring_count=24, location=(6.0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
planet.data.materials.append(make_principled("PlanetMat", (0.15, 0.4, 0.9), roughness=0.6))
bpy.ops.object.shade_smooth()
planet.parent = pivot

# Faint orbit ring for visual reference (not animated)
bpy.ops.mesh.primitive_torus_add(major_radius=6.0, minor_radius=0.02,
                                 major_segments=128, minor_segments=8,
                                 location=(0, 0, 0))
ring = bpy.context.active_object
ring.name = "OrbitRing"
ring.data.materials.append(make_emission("RingMat", (0.6, 0.6, 0.7), strength=1.0))

# ---------- Animation: constant-speed circular orbit ----------
# Rotating the pivot about Z with LINEAR interpolation gives constant angular speed.
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# Make newly inserted keyframes use linear interpolation
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

pivot.rotation_mode = 'XYZ'
scene.frame_set(1)
pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", frame=1)

scene.frame_set(120)
pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", frame=120)

# Enforce linear interpolation explicitly on the F-curves when accessible
try:
    action = pivot.animation_data.action
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except Exception:
    pass

scene.frame_set(1)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0.0, -20.0, 11.0)

target = Vector((0.0, 0.0, 0.0))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Background and ambient fill ----------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 0.3

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 300
fill_data.size = 10
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-8, -10, 12)
fill.rotation_euler = (math.radians(55), 0, math.radians(-45))
