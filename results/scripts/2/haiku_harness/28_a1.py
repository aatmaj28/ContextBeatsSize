import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras import anim_utils

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


# ---------- Helpers ----------
def make_box(name, x0, x1, y0, y1, z0, z1):
    """Create a box mesh object spanning the given world-space bounds."""
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    sx, sy, sz = (x1 - x0), (y1 - y0), (z1 - z0)
    for v in bm.verts:
        v.co = Vector((cx + v.co.x * sx, cy + v.co.y * sy, cz + v.co.z * sz))
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


# ---------- Materials ----------
mat_floor = make_material("Floor", (0.35, 0.25, 0.18), 0.6)
mat_wall = make_material("Wall", (0.85, 0.83, 0.78), 0.9)
mat_frame = make_material("Frame", (0.95, 0.95, 0.93), 0.4)
mat_door = make_material("Door", (0.45, 0.22, 0.10), 0.35)
mat_knob = make_material("Knob", (0.9, 0.7, 0.2), 0.2)

# ---------- Environment geometry ----------
floor = make_box("Floor", -3, 3, -3, 2, -0.1, 0.0)
floor.data.materials.append(mat_floor)

# Back wall (behind the door, at +y)
wall = make_box("Wall", -3, 3, 0.15, 0.35, 0.0, 3.0)
wall.data.materials.append(mat_wall)

# Door frame (jambs and header) around opening x:0..0.9, z:0..2.1
DOOR_W, DOOR_H, DOOR_T = 0.9, 2.1, 0.05
frame_parts = [
    make_box("JambLeft", -0.10, 0.0, -0.06, 0.16, 0.0, 2.18),
    make_box("JambRight", DOOR_W, DOOR_W + 0.10, -0.06, 0.16, 0.0, 2.18),
    make_box("Header", -0.10, DOOR_W + 0.10, -0.06, 0.16, DOOR_H, DOOR_H + 0.08),
]
for part in frame_parts:
    part.data.materials.append(mat_frame)

# ---------- Door panel (origin at hinge on the left edge) ----------
door = make_box("Door", 0.0, DOOR_W, -DOOR_T / 2, DOOR_T / 2, 0.0, DOOR_H)
door.data.materials.append(mat_door)
door.location = (0.0, 0.0, 0.0)  # hinge pivot
door.rotation_mode = 'XYZ'

# Door knob on the far (free) edge
knob = make_box("Knob", DOOR_W - 0.12, DOOR_W - 0.06, -0.05, -0.01, DOOR_H * 0.5 - 0.03, DOOR_H * 0.5 + 0.03)
knob.data.materials.append(mat_knob)
knob.parent = door
knob.matrix_parent_inverse = door.matrix_world.inverted()

# ---------- Door animation: swing open over 40 frames ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(1)

door.rotation_euler = (0.0, 0.0, 0.0)
door.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

door.rotation_euler = (0.0, 0.0, math.radians(-100.0))
door.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

# Ease in and ease out on the rotation F-Curve (layered action API in 5.x)
ad = door.animation_data
action = ad.action
slot = ad.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
if channelbag:
    for fc in channelbag.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

# Start with the door closed
door.rotation_euler = (0.0, 0.0, 0.0)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (3, -4, 5)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 400
fill_data.size = 3.0
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-2.5, -3.5, 2.5)
fill.rotation_euler = (math.radians(65), 0, math.radians(-35))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (2.6, -3.6, 1.7)
target = Vector((0.45, 0.0, 1.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
