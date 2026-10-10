import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------- Clear the scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_part(op, location, scale=(1, 1, 1), rotation=(0, 0, 0), material=None):
    op(location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.scale = scale
    if material is not None:
        obj.data.materials.append(material)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# ---------- Materials ----------
marble = make_material("Marble", (0.80, 0.78, 0.73), roughness=0.35)
pedestal_mat = make_material("Pedestal", (0.25, 0.23, 0.22), roughness=0.6)
floor_mat = make_material("Floor", (0.12, 0.12, 0.13), roughness=0.9)

# ---------- Statue ----------
# Pedestal (spans z 0 .. 1)
add_part(bpy.ops.mesh.primitive_cube_add, (0, 0, 0.5),
         scale=(0.9, 0.9, 0.5), material=pedestal_mat)
# Plinth cap
add_part(bpy.ops.mesh.primitive_cylinder_add, (0, 0, 1.05),
         scale=(1.0, 1.0, 0.08), material=pedestal_mat)
# Torso (ellipsoid)
add_part(bpy.ops.mesh.primitive_uv_sphere_add, (0, 0, 2.1),
         scale=(0.5, 0.33, 0.9), material=marble)
# Hips / drape base
add_part(bpy.ops.mesh.primitive_cylinder_add, (0, 0, 1.45),
         scale=(0.42, 0.3, 0.3), material=marble)
# Neck
add_part(bpy.ops.mesh.primitive_cylinder_add, (0, 0, 3.12),
         scale=(0.14, 0.14, 0.15), material=marble)
# Head
add_part(bpy.ops.mesh.primitive_uv_sphere_add, (0, 0, 3.55),
         scale=(0.3, 0.32, 0.37), material=marble)
# Arms (slightly outstretched)
for side in (-1, 1):
    add_part(bpy.ops.mesh.primitive_cylinder_add,
             (side * 0.62, 0, 2.35),
             scale=(0.11, 0.11, 0.6),
             rotation=(0, side * 0.25, 0),
             material=marble)
    # Hands
    add_part(bpy.ops.mesh.primitive_uv_sphere_add,
             (side * 0.72, 0, 1.6),
             scale=(0.1, 0.1, 0.12),
             material=marble)

# ---------- Ground ----------
add_part(bpy.ops.mesh.primitive_plane_add, (0, 0, 0),
         scale=(15, 15, 1), material=floor_mat)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.04, 0.045, 0.055, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 600.0
area_data.size = 4.0
area_obj = bpy.data.objects.new("FillArea", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (4.0, -4.0, 4.5)
look_at(area_obj, (0, 0, 1.5))

# ---------- Orbit target ----------
target = bpy.data.objects.new("OrbitTarget", None)
target.location = (0, 0, 1.9)
scene.collection.objects.link(target)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

track = cam_obj.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam_obj

# ---------- Orbit animation ----------
FRAME_START = 1
FRAME_END = 100
RADIUS = 9.0
HEIGHT = 2.6

scene.frame_start = FRAME_START
scene.frame_end = FRAME_END

for i, frame in enumerate(range(FRAME_START, FRAME_END + 1)):
    t = i / (FRAME_END - FRAME_START + 1)  # 0 .. <1, seamless loop
    angle = 2.0 * math.pi * t
    cam_obj.location = (RADIUS * math.cos(angle), RADIUS * math.sin(angle), HEIGHT)
    cam_obj.keyframe_insert(data_path="location", frame=frame)

# Linear interpolation for constant orbital speed
if cam_obj.animation_data and cam_obj.animation_data.action:
    action = cam_obj.animation_data.action
    slot = cam_obj.animation_data.action_slot
    channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
    if channelbag is not None:
        for fcurve in channelbag.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'
            fcurve.update()

scene.frame_set(FRAME_START)
