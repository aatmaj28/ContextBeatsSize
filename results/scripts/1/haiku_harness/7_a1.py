import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler

random.seed(7)

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
collection = scene.collection


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def make_mat(name, color, roughness=0.6):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def make_wood_mat(name, dark, light, scale, roughness=0.45):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Distortion"].default_value = 0.6

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (dark[0], dark[1], dark[2], 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (light[0], light[1], light[2], 1.0)

    nt.links.new(ramp.inputs["Fac"], noise.outputs["Fac"])
    nt.links.new(bsdf.inputs["Base Color"], ramp.outputs["Color"])
    return mat


def make_box(name, center, dims, mat, rot_z=0.0):
    """Axis-aligned box in world space, optionally rotated around Z."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    bm.normal_update()

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = False

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = Vector(center)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    return obj


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
floor_mat = make_wood_mat("FloorWood", (0.18, 0.11, 0.06), (0.36, 0.22, 0.12), 3.0, 0.5)
wall_mat = make_mat("WallPaint", (0.82, 0.78, 0.70), 0.9)
ceiling_mat = make_mat("CeilingPaint", (0.92, 0.92, 0.9), 0.95)
table_mat = make_wood_mat("TableWood", (0.28, 0.14, 0.06), (0.55, 0.32, 0.16), 4.0, 0.4)
chair_wood_mat = make_wood_mat("ChairWood", (0.22, 0.12, 0.05), (0.42, 0.25, 0.12), 5.0, 0.45)
seat_mat = make_mat("SeatFabric", (0.12, 0.25, 0.32), 0.85)

# ---------------------------------------------------------------
# Room (6 x 6 x 3 m, open front for the camera)
# ---------------------------------------------------------------
make_box("Floor", (0, 0, -0.05), (6.0, 6.0, 0.1), floor_mat)
make_box("Ceiling", (0, 0, 3.05), (6.0, 6.0, 0.1), ceiling_mat)
make_box("BackWall", (0, 3.05, 1.5), (6.0, 0.1, 3.0), wall_mat)
make_box("LeftWall", (-3.05, 0, 1.5), (0.1, 6.0, 3.0), wall_mat)
make_box("RightWall", (3.05, 0, 1.5), (0.1, 6.0, 3.0), wall_mat)

# ---------------------------------------------------------------
# Table
# ---------------------------------------------------------------
TABLE_TOP_Z = 0.75
TOP_T = 0.05
table_parts = []
table_parts.append(make_box("TableTop", (0, 0, TABLE_TOP_Z), (1.4, 0.9, TOP_T), table_mat))
leg_h = TABLE_TOP_Z - TOP_T / 2
for sx in (-1, 1):
    for sy in (-1, 1):
        table_parts.append(make_box(
            "TableLeg",
            (sx * 0.62, sy * 0.36, leg_h / 2),
            (0.07, 0.07, leg_h),
            table_mat,
        ))

# ---------------------------------------------------------------
# Chairs
# ---------------------------------------------------------------
SEAT_H = 0.45
SEAT_T = 0.05
SEAT_SIZE = 0.45


def make_chair(name, base, angle):
    """Chair built in local space (facing +Y, backrest at -Y), then rotated and moved."""
    def place(local):
        p = Vector(local).to_2d()
        rotated = Vector(local).copy()
        rotated.rotate(Euler((0.0, 0.0, angle)))
        return Vector((base[0] + rotated.x, base[1] + rotated.y, rotated.z))

    parts = []
    # Seat
    parts.append(make_box(name + "_Seat", place((0, 0, SEAT_H)),
                          (SEAT_SIZE, SEAT_SIZE, SEAT_T), seat_mat, angle))
    # Legs
    leg_len = SEAT_H - SEAT_T / 2
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            parts.append(make_box(name + "_Leg", place((lx, ly, leg_len / 2)),
                                  (0.04, 0.04, leg_len), chair_wood_mat, angle))
    # Backrest posts (extend upward from rear legs)
    back_h = 0.45
    for lx in (-0.19, 0.19):
        parts.append(make_box(name + "_Post", place((lx, -0.19, SEAT_H + back_h / 2)),
                              (0.04, 0.04, back_h), chair_wood_mat, angle))
    # Backrest panel
    parts.append(make_box(name + "_Back", place((0, -0.19, SEAT_H + 0.30)),
                          (0.42, 0.03, 0.14), chair_wood_mat, angle))
    return parts


chair_positions = [
    ("ChairFront", (0.0, -0.78), 0.0),
    ("ChairBack", (0.0, 0.78), math.pi),
    ("ChairLeft", (-1.02, 0.0), -math.pi / 2),
    ("ChairRight", (1.02, 0.0), math.pi / 2),
]
for cname, cbase, cang in chair_positions:
    make_chair(cname, cbase, cang)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
key_data = bpy.data.lights.new("KeyArea", 'AREA')
key_data.energy = 350.0
key_data.size = 2.0
key_data.color = (1.0, 0.92, 0.82)
key_obj = bpy.data.objects.new("KeyArea", key_data)
collection.objects.link(key_obj)
key_obj.location = Vector((0.0, 0.0, 2.85))
key_obj.rotation_euler = Euler((0.0, 0.0, 0.0))

fill_data = bpy.data.lights.new("FillPoint", 'POINT')
fill_data.energy = 60.0
fill_data.color = (0.8, 0.9, 1.0)
fill_data.shadow_soft_size = 0.5
fill_obj = bpy.data.objects.new("FillPoint", fill_data)
collection.objects.link(fill_obj)
fill_obj.location = Vector((-1.8, -2.0, 2.4))

# World ambience
world = bpy.data.worlds.new("RoomWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 28.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
collection.objects.link(cam_obj)

cam_loc = Vector((2.3, -2.6, 1.75))
look_at = Vector((0.0, 0.1, 0.7))
cam_obj.location = cam_loc
direction = look_at - cam_loc
cam_obj.rotation_mode = 'QUATERNION'
cam_obj.rotation_quaternion = direction.to_track_quat('-Z', 'Y')

scene.camera = cam_obj
