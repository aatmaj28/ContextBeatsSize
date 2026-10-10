import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras import anim_utils


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def make_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def make_box(name, min_corner, max_corner, material, collection):
    """Create an axis-aligned box from min/max corners in local space of the object."""
    min_c = Vector(min_corner)
    max_c = Vector(max_corner)
    center = (min_c + max_c) * 0.5
    dims = max_c - min_c

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims.x
        v.co.y *= dims.y
        v.co.z *= dims.z
        v.co += center
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    mesh.materials.append(material)

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


clear_scene()
scene = bpy.context.scene
collection = scene.collection

# Materials
wall_mat = make_material("WallMat", (0.85, 0.82, 0.76), roughness=0.8)
door_mat = make_material("DoorMat", (0.35, 0.18, 0.08), roughness=0.45)
frame_mat = make_material("FrameMat", (0.9, 0.9, 0.88), roughness=0.5)
floor_mat = make_material("FloorMat", (0.25, 0.25, 0.27), roughness=0.9)

# Floor
floor = make_box("Floor", (-4.0, -3.0, -0.1), (4.0, 3.0, 0.0), floor_mat, collection)

# Wall with a door opening (opening spans x 0..0.9, z 0..2.1)
wall_left = make_box("WallLeft", (-2.5, -0.15, 0.0), (0.0, 0.15, 3.0), wall_mat, collection)
wall_right = make_box("WallRight", (0.9, -0.15, 0.0), (3.0, 0.15, 3.0), wall_mat, collection)
wall_top = make_box("WallTop", (0.0, -0.15, 2.1), (0.9, 0.15, 3.0), wall_mat, collection)

# Door frame trim (slightly proud of the wall, on the front face)
trim_t = 0.03
trim_y0 = -0.15 - trim_t
trim_y1 = -0.15 + 0.01
make_box("TrimLeft", (-0.08, trim_y0, 0.0), (0.0, trim_y1, 2.15), frame_mat, collection)
make_box("TrimRight", (0.9, trim_y0, 0.0), (0.98, trim_y1, 2.15), frame_mat, collection)
make_box("TrimTop", (-0.08, trim_y0, 2.1), (0.98, trim_y1, 2.18), frame_mat, collection)

# Door panel, origin placed exactly at the hinge edge (bottom-left corner)
door = make_box("Door", (0.0, -0.025, 0.0), (0.9, 0.025, 2.1), door_mat, collection)
door.location = (0.0, 0.0, 0.0)
collection.objects.link(door) if door.name not in collection.objects else None
door.rotation_mode = 'XYZ'
door.rotation_euler = (0.0, 0.0, 0.0)

# Door handle
handle_mat = make_material("HandleMat", (0.8, 0.7, 0.2), roughness=0.2)
handle = make_box("Handle", (0.75, 0.025, 1.0), (0.82, 0.07, 1.05), handle_mat, collection)
handle.parent = door
handle.matrix_parent_inverse = door.matrix_world.inverted()

# Animation: swing from closed (0) to open (100 degrees) over 40 frames
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(1)

door.rotation_euler.z = 0.0
door.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

door.rotation_euler.z = math.radians(100.0)
door.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

# Apply ease in / ease out to the keyframes
action = door.animation_data.action
slot = door.animation_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
    fcurve.update()

door.rotation_euler.z = 0.0

# Lighting
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(5.0)
sun = bpy.data.objects.new("Sun", sun_data)
collection.objects.link(sun)
sun.location = (3.0, -4.0, 6.0)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 300.0
fill_data.size = 3.0
fill = bpy.data.objects.new("Fill", fill_data)
collection.objects.link(fill)
fill.location = (-3.0, -4.0, 2.5)
fill.rotation_euler = (math.radians(70), 0.0, math.radians(-30))

# Camera framing the door
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam.location = (3.2, -4.6, 1.8)
target = Vector((0.4, 0.2, 1.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
