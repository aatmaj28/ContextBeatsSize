import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Scene reset ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    if light.users == 0:
        bpy.data.lights.remove(light)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1


# ---------- Helpers ----------
def make_mat(name, color, rough=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def make_wood_mat(name, dark, light, scale=6.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.45

    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (dark[0], dark[1], dark[2], 1.0)
    ramp.color_ramp.elements[1].color = (light[0], light[1], light[2], 1.0)

    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def box(name, size, loc, mat, rot=(0.0, 0.0, 0.0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = rot
    return ob


def local_to_world(base, theta, lx, ly, lz):
    c, s = math.cos(theta), math.sin(theta)
    wx = lx * c - ly * s
    wy = lx * s + ly * c
    return (base[0] + wx, base[1] + wy, lz)


# ---------- Materials ----------
wood_table = make_wood_mat("TableWood", (0.22, 0.12, 0.05), (0.52, 0.30, 0.14), scale=5.0)
wood_chair = make_wood_mat("ChairWood", (0.30, 0.17, 0.08), (0.58, 0.37, 0.20), scale=7.0)
floor_mat = make_wood_mat("FloorWood", (0.35, 0.22, 0.10), (0.62, 0.42, 0.25), scale=3.0)
wall_mat = make_mat("WallPaint", (0.85, 0.82, 0.76), rough=0.9)
ceiling_mat = make_mat("CeilingPaint", (0.93, 0.93, 0.91), rough=0.95)
fabric_mats = [
    make_mat("Fabric_A", (0.20, 0.30, 0.45), rough=0.95),
    make_mat("Fabric_B", (0.55, 0.15, 0.12), rough=0.95),
    make_mat("Fabric_C", (0.30, 0.42, 0.25), rough=0.95),
    make_mat("Fabric_D", (0.60, 0.50, 0.25), rough=0.95),
]
accent_mat = make_mat("Ceramic", (0.75, 0.70, 0.60), rough=0.3)

# ---------- Room ----------
ROOM_W = 5.0   # x extent
ROOM_D = 5.0   # y extent
ROOM_H = 2.7

box("Floor", (ROOM_W, ROOM_D, 0.05), (0, 0, -0.025), floor_mat)
box("Ceiling", (ROOM_W, ROOM_D, 0.05), (0, 0, ROOM_H + 0.025), ceiling_mat)
box("WallBack", (ROOM_W, 0.05, ROOM_H), (0, ROOM_D / 2, ROOM_H / 2), wall_mat)
box("WallLeft", (0.05, ROOM_D, ROOM_H), (-ROOM_W / 2, 0, ROOM_H / 2), wall_mat)
box("WallRight", (0.05, ROOM_D, ROOM_H), (ROOM_W / 2, 0, ROOM_H / 2), wall_mat)

# Simple baseboard trim along the back and side walls
trim_mat = make_wood_mat("TrimWood", (0.25, 0.14, 0.06), (0.45, 0.27, 0.13), scale=8.0)
box("TrimBack", (ROOM_W, 0.02, 0.12), (0, ROOM_D / 2 - 0.01, 0.06), trim_mat)
box("TrimLeft", (0.02, ROOM_D, 0.12), (-ROOM_W / 2 + 0.01, 0, 0.06), trim_mat)
box("TrimRight", (0.02, ROOM_D, 0.12), (ROOM_W / 2 - 0.01, 0, 0.06), trim_mat)

# Rug under the table
rug_mat = make_mat("Rug", (0.50, 0.22, 0.20), rough=1.0)
box("Rug", (2.4, 1.9, 0.01), (0, 0, 0.005), rug_mat)

# ---------- Table ----------
TABLE_H = 0.75
TOP_T = 0.05
LEG = 0.07
table_loc = (0.0, 0.0)
box("TableTop", (1.4, 0.8, TOP_T),
    (0, 0, TABLE_H - TOP_T / 2), wood_table)
leg_h = TABLE_H - TOP_T
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg",
            (LEG, LEG, leg_h),
            (sx * (1.4 / 2 - 0.1), sy * (0.8 / 2 - 0.1), leg_h / 2),
            wood_table)

# Decorative items on table
box("Vase", (0.10, 0.10, 0.22), (0.35, -0.1, TABLE_H + 0.11), accent_mat)
box("Bowl", (0.28, 0.20, 0.06), (-0.3, 0.1, TABLE_H + 0.03), accent_mat)

# ---------- Chairs ----------
SEAT_H = 0.46
SEAT_T = 0.04
CL = 0.04  # chair leg thickness
CHAIR_OFFSET = 0.72  # distance from table center

chair_positions = [
    (-0.42, -CHAIR_OFFSET),
    (0.42, -CHAIR_OFFSET),
    (-0.42, CHAIR_OFFSET),
    (0.42, CHAIR_OFFSET),
]

for i, (px, py) in enumerate(chair_positions):
    base = (px, py)
    # Direction from chair toward table center
    dx, dy = -px, -py
    length = math.hypot(dx, dy)
    dx, dy = dx / length, dy / length
    # Local +Y should point toward the table
    theta = math.atan2(-dx, dy)
    rot = (0.0, 0.0, theta)
    mat = fabric_mats[i % len(fabric_mats)]

    # Seat cushion/frame
    seat_loc = local_to_world(base, theta, 0, 0, SEAT_H)
    box(f"ChairSeat_{i}", (0.44, 0.44, SEAT_T), seat_loc, wood_chair, rot)

    # Four legs
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            loc = local_to_world(base, theta, lx, ly, (SEAT_H - SEAT_T) / 2)
            box(f"ChairLeg_{i}", (CL, CL, SEAT_H - SEAT_T), loc, wood_chair, rot)

    # Backrest posts and back panel (back is on the far side from the table)
    for lx in (-0.19, 0.19):
        loc = local_to_world(base, theta, lx, -0.19, (SEAT_H + 0.52) / 2 + 0.02)
        box(f"ChairPost_{i}", (CL, CL, 0.52), loc, wood_chair, rot)
    back_loc = local_to_world(base, theta, 0, -0.21, SEAT_H + 0.33)
    box(f"ChairBack_{i}", (0.42, 0.03, 0.18), back_loc, wood_chair, rot)

    # Seat cushion in fabric on top of the seat frame
    cush_loc = local_to_world(base, theta, 0, 0, SEAT_H + SEAT_T / 2 + 0.01)
    box(f"ChairCushion_{i}", (0.38, 0.38, 0.03), cush_loc, mat, rot)

# ---------- Lighting ----------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# Ceiling area light above table
area_data = bpy.data.lights.new("CeilingArea", type='AREA')
area_data.energy = 250.0
area_data.size = 1.6
area_data.size_y = 1.0
area_obj = bpy.data.objects.new("CeilingArea", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (0.0, 0.0, ROOM_H - 0.15)
area_obj.rotation_euler = (0.0, 0.0, 0.0)

# Soft sun through an imagined window direction
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 2.5
sun_data.angle = math.radians(6)
sun_obj = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(55), 0.0, math.radians(35))

# Fill light near the open front
fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 60.0
fill_data.size = 3.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (0.0, -2.4, 2.0)
fill_obj.rotation_euler = (math.radians(70), 0.0, 0.0)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 28.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((0.0, -2.35, 1.55))
target = Vector((0.0, 0.2, 0.7))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj
