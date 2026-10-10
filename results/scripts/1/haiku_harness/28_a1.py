import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---- Clear the scene -------------------------------------------------------
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---- Helpers ---------------------------------------------------------------
def make_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)  # node tree is created automatically
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_box_geometry(verts, faces, mn, mx):
    """Append an axis-aligned box (min/max corners) to verts/faces lists."""
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    base = len(verts)
    verts.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    faces.extend([tuple(base + i for i in q) for q in quads])


def make_object(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = False
    return obj


# ---- Materials -------------------------------------------------------------
mat_floor = make_material("FloorMat", (0.35, 0.33, 0.30), 0.8)
mat_wall = make_material("WallMat", (0.85, 0.82, 0.76), 0.9)
mat_door = make_material("DoorMat", (0.42, 0.22, 0.10), 0.45)
mat_handle = make_material("HandleMat", (0.85, 0.7, 0.25), 0.2)

# ---- Floor and wall (static) -----------------------------------------------
# Opening: x in [-0.5, 0.5], z in [0, 2.1]; wall thickness y in [-0.1, 0.1]
wall_verts, wall_faces = [], []
add_box_geometry(wall_verts, wall_faces, (-3.0, -0.1, 0.0), (-0.5, 0.1, 3.0))   # left
add_box_geometry(wall_verts, wall_faces, (0.5, -0.1, 0.0), (3.0, 0.1, 3.0))     # right
add_box_geometry(wall_verts, wall_faces, (-0.5, -0.1, 2.1), (0.5, 0.1, 3.0))    # above door
make_object("Wall", wall_verts, wall_faces, mat_wall)

floor_verts, floor_faces = [], []
add_box_geometry(floor_verts, floor_faces, (-3.0, -2.5, -0.1), (3.0, 2.0, 0.0))
make_object("Floor", floor_verts, floor_faces, mat_floor)

# ---- Door (pivot at hinge, which sits at the object origin) ----------------
# Door panel lies in local X from 0 to 1.0 (hinge at x=0), Z from 0 to 2.1.
HINGE_POS = Vector((-0.5, 0.0, 0.0))
door_verts, door_faces = [], []
add_box_geometry(door_verts, door_faces, (0.0, -0.025, 0.0), (1.0, 0.025, 2.1))
# Lever handle on the camera-facing side (-Y), near the free edge
add_box_geometry(door_verts, door_faces, (0.80, -0.06, 0.98), (0.97, -0.025, 1.02))
add_box_geometry(door_verts, door_faces, (0.80, -0.08, 0.98), (0.85, -0.06, 1.02))

door = make_object("Door", door_verts, door_faces, mat_door)
door.data.materials.append(mat_handle)  # handle faces use the brass material
for poly in door.data.polygons[-12:]:
    poly.material_index = 1
door.location = HINGE_POS
door.rotation_mode = 'XYZ'
door.rotation_euler = (0.0, 0.0, 0.0)

# ---- Animation: swing open over 40 frames, ease in and out ------------------
scene.frame_start = 1
scene.frame_end = 40

door.rotation_euler = (0.0, 0.0, 0.0)
door.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

door.rotation_euler = (0.0, 0.0, math.radians(-100.0))
door.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

action = door.animation_data.action
slot = door.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
    fcurve.update()

scene.frame_set(1)

# ---- Lighting ---------------------------------------------------------------
sun_data = bpy.data.lights.new("SunLight", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("SunLight", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(30))

area_data = bpy.data.lights.new("AreaLight", type='AREA')
area_data.energy = 400.0
area_data.size = 3.0
area = bpy.data.objects.new("AreaLight", area_data)
scene.collection.objects.link(area)
area.location = (1.5, -3.0, 3.0)
area.rotation_euler = (math.radians(60), 0.0, math.radians(20))

# ---- World --------------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---- Camera -------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam_pos = Vector((2.2, -4.2, 1.5))
target = Vector((-0.1, 0.0, 1.1))
cam.location = cam_pos
direction = target - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
