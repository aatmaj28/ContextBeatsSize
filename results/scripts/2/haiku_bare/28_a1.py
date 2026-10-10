import bpy
import bmesh
import math
from mathutils import Vector


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def make_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*color, 1.0)
    return mat


def make_box(name, center, dims, mat, mesh_offset=(0.0, 0.0, 0.0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * dims[0] + mesh_offset[0]
        v.co.y = v.co.y * dims[1] + mesh_offset[1]
        v.co.z = v.co.z * dims[2] + mesh_offset[2]
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = center
    obj.data.materials.append(mat)
    return obj


clear_scene()
scene = bpy.context.scene

# Materials
wall_mat = make_material("Wall", (0.85, 0.82, 0.76), 0.9)
floor_mat = make_material("Floor", (0.35, 0.25, 0.18), 0.6)
frame_mat = make_material("Frame", (0.92, 0.92, 0.9), 0.4)
door_mat = make_material("Door", (0.45, 0.22, 0.10), 0.35)
room_mat = make_material("RoomWall", (0.6, 0.7, 0.8), 0.9)

# Static environment
make_box("Floor", (0.0, 0.0, -0.05), (5.0, 5.0, 0.1), floor_mat)
make_box("FrontWallLeft", (-1.6, 0.0, 1.5), (1.8, 0.15, 3.0), wall_mat)
make_box("FrontWallRight", (1.6, 0.0, 1.5), (1.8, 0.15, 3.0), wall_mat)
make_box("FrontWallTop", (0.0, 0.0, 2.5), (1.4, 0.15, 1.0), wall_mat)
make_box("BackWall", (0.0, 1.2, 1.5), (5.0, 0.15, 3.0), room_mat)

# Door frame (jambs and lintel)
make_box("JambLeft", (-0.5, 0.0, 1.1), (0.1, 0.2, 2.2), frame_mat)
make_box("JambRight", (0.5, 0.0, 1.1), (0.1, 0.2, 2.2), frame_mat)
make_box("Lintel", (0.0, 0.0, 2.15), (1.1, 0.2, 0.1), frame_mat)

# Door panel, origin placed at the hinge edge
door = make_box(
    "Door",
    center=(-0.45, 0.0, 0.0),
    dims=(0.9, 0.05, 2.1),
    mat=door_mat,
    mesh_offset=(0.45, 0.0, 1.05),
)

# Door handle
handle = make_box(
    "Handle",
    center=(-0.45 + 0.78, -0.05, 1.0),
    dims=(0.04, 0.06, 0.04),
    mat=frame_mat,
)
handle.parent = door
handle.matrix_parent_inverse = door.matrix_world.inverted()

# Animation: swing open over 40 frames
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(1)

door.rotation_euler = (0.0, 0.0, 0.0)
door.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

door.rotation_euler = (0.0, 0.0, math.radians(-100.0))
door.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

# Ease in and out on the keyframes
if door.animation_data and door.animation_data.action:
    for fc in door.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
        fc.update()

# Lighting
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (3.0, -4.0, 6.0)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))

area_data = bpy.data.lights.new(name="Fill", type='AREA')
area_data.energy = 400.0
area_data.size = 3.0
fill = bpy.data.objects.new("Fill", area_data)
scene.collection.objects.link(fill)
fill.location = (0.0, -3.0, 3.0)
fill.rotation_euler = (math.radians(60), 0.0, 0.0)

# Camera framing the doorway
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((1.8, -4.2, 1.6))
target = Vector((0.0, 0.0, 1.05))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
