import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------- Clear the default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


# ---------- Materials ----------
mat_ground = make_mat("Grass", (0.18, 0.42, 0.14), roughness=0.9)
mat_tower = make_mat("Tower", (0.85, 0.85, 0.82), roughness=0.45)
mat_nacelle = make_mat("Nacelle", (0.75, 0.2, 0.15), roughness=0.4)
mat_hub = make_mat("Hub", (0.9, 0.9, 0.9), roughness=0.3, metallic=0.4)
mat_blade = make_mat("Blade", (0.95, 0.95, 0.97), roughness=0.35)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = assign(bpy.context.active_object, mat_ground)
ground.name = "Ground"

# ---------- Tower ----------
bpy.ops.mesh.primitive_cone_add(
    vertices=16, radius1=0.6, radius2=0.25, depth=8.5,
    location=(0, 0, 4.25))
tower = assign(bpy.context.active_object, mat_tower)
tower.name = "Tower"

# ---------- Nacelle ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.2, 8.8))
nacelle = assign(bpy.context.active_object, mat_nacelle)
nacelle.name = "Nacelle"
nacelle.scale = (0.55, 1.6, 0.55)

# ---------- Rotor pivot (spins around Y axis) ----------
HUB_POS = (0.0, -1.0, 9.0)

bpy.ops.object.empty_add(type='PLAIN_AXES', location=HUB_POS)
pivot = bpy.context.active_object
pivot.name = "RotorPivot"
pivot.rotation_mode = 'XYZ'

# Hub cylinder (axis along Y)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.35, depth=0.5, location=HUB_POS,
    rotation=(math.radians(90), 0, 0))
hub = assign(bpy.context.active_object, mat_hub)
hub.name = "Hub"
hub.parent = pivot

# ---------- Blades (3 blades, 120 degrees apart) ----------
BLADE_CENTER_DIST = 1.3
for i in range(3):
    theta = 2.0 * math.pi * i / 3.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    blade = assign(bpy.context.active_object, mat_blade)
    blade.name = f"Blade_{i}"
    blade.scale = (0.12, 0.04, 1.0)   # long along local Z (length 2.0)
    # Position in the XZ plane around the hub, oriented radially
    blade.location = (
        math.sin(theta) * BLADE_CENTER_DIST,
        0.0,
        math.cos(theta) * BLADE_CENTER_DIST,
    )
    blade.rotation_euler = (0.0, theta, 0.0)
    blade.parent = pivot

# ---------- Constant-speed animation over 120 frames ----------
scene.frame_start = 1
scene.frame_end = 120

pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=1, frame=1)

pivot.rotation_euler = (0.0, 4.0 * math.pi, 0.0)   # two full revolutions
pivot.keyframe_insert(data_path="rotation_euler", index=1, frame=120)

# Linear interpolation for constant angular speed (Blender 5.x layered actions)
anim_data = pivot.animation_data
if anim_data and anim_data.action:
    channelbag = anim_utils.action_get_channelbag_for_slot(
        anim_data.action, anim_data.action_slot)
    if channelbag:
        for fc in channelbag.fcurves:
            fc.extrapolation = 'LINEAR'
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.75, 0.95, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(-30))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 300.0
fill_data.size = 6.0
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (-6.0, -8.0, 8.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (9.0, -20.0, 6.0)

target = Vector((0.0, 0.0, 5.0))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
