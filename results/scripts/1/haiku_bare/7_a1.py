import bpy
import math
from mathutils import Vector

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection

# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def make_box(name, loc, size, mat, rot_z=0.0):
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    verts = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5),
    ]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    obj.rotation_euler = (0.0, 0.0, rot_z)
    collection.objects.link(obj)
    return obj

def local_to_world(cx, cy, theta, lx, ly):
    c, s = math.cos(theta), math.sin(theta)
    return (cx + lx * c - ly * s, cy + lx * s + ly * c)

# ---------- Materials ----------
mat_floor = make_mat("Floor_Oak", (0.45, 0.28, 0.14), 0.45)
mat_wall = make_mat("Wall_Plaster", (0.82, 0.78, 0.70), 0.9)
mat_ceiling = make_mat("Ceiling_White", (0.9, 0.9, 0.88), 0.95)
mat_table = make_mat("Table_Wood", (0.52, 0.32, 0.17), 0.35)
mat_chair = make_mat("Chair_Wood", (0.38, 0.22, 0.11), 0.4)
mat_seat = make_mat("Chair_Seat", (0.25, 0.30, 0.45), 0.8)

# ---------- Room ----------
ROOM_HALF = 2.0
WALL_H = 2.7
WALL_T = 0.12

make_box("Floor", (0, 0, -0.05), (4.2 + WALL_T, 4.2 + WALL_T, 0.1), mat_floor)
make_box("Ceiling", (0, 0, WALL_H + 0.05), (4.2 + WALL_T, 4.2 + WALL_T, 0.1), mat_ceiling)

wall_c = ROOM_HALF + WALL_T / 2
make_box("Wall_Back", (0, wall_c, WALL_H / 2), (4.2 + WALL_T, WALL_T, WALL_H), mat_wall)
make_box("Wall_Front", (0, -wall_c, WALL_H / 2), (4.2 + WALL_T, WALL_T, WALL_H), mat_wall)
make_box("Wall_Left", (-wall_c, 0, WALL_H / 2), (WALL_T, 4.2, WALL_H), mat_wall)
make_box("Wall_Right", (wall_c, 0, WALL_H / 2), (WALL_T, 4.2, WALL_H), mat_wall)

# ---------- Table ----------
TABLE_TOP_Z = 0.76
make_box("Table_Top", (0, 0, TABLE_TOP_Z), (1.2, 0.8, 0.04), mat_table)
leg_h = 0.72
for sx in (-1, 1):
    for sy in (-1, 1):
        make_box(
            f"Table_Leg_{sx}_{sy}",
            (sx * 0.52, sy * 0.32, leg_h / 2),
            (0.07, 0.07, leg_h),
            mat_table,
        )

# ---------- Chairs ----------
def make_chair(name, cx, cy, theta):
    # Local frame: sitter faces +Y, backrest on -Y side
    seat_z = 0.45
    # Seat
    sx, sy = local_to_world(cx, cy, theta, 0, 0)
    make_box(f"{name}_Seat", (sx, sy, seat_z), (0.44, 0.44, 0.04), mat_seat, theta)
    # Legs
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            px, py = local_to_world(cx, cy, theta, lx, ly)
            make_box(f"{name}_Leg", (px, py, seat_z / 2), (0.04, 0.04, seat_z), mat_chair, theta)
    # Backrest posts (rear legs extended) and panel
    for lx in (-0.19, 0.19):
        px, py = local_to_world(cx, cy, theta, lx, -0.19)
        make_box(f"{name}_BackPost", (px, py, (seat_z + 0.45) / 2 + 0.02), (0.04, 0.04, 0.45 + 0.04), mat_chair, theta)
    bx, by = local_to_world(cx, cy, theta, 0, -0.205)
    make_box(f"{name}_BackPanel", (bx, by, 0.72), (0.40, 0.03, 0.24), mat_chair, theta)

CHAIR_D = 0.92
make_chair("Chair_South", 0.0, -CHAIR_D, 0.0)
make_chair("Chair_North", 0.0, CHAIR_D, math.pi)
make_chair("Chair_West", -CHAIR_D, 0.0, -math.pi / 2)
make_chair("Chair_East", CHAIR_D, 0.0, math.pi / 2)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lighting ----------
ceiling_light_data = bpy.data.lights.new("Ceiling_Light", type='AREA')
ceiling_light_data.shape = 'RECTANGLE'
ceiling_light_data.size = 1.4
ceiling_light_data.size_y = 1.4
ceiling_light_data.energy = 350.0
ceiling_light_data.color = (1.0, 0.92, 0.82)
ceiling_light = bpy.data.objects.new("Ceiling_Light", ceiling_light_data)
ceiling_light.location = (0.0, 0.0, WALL_H - 0.15)
collection.objects.link(ceiling_light)

fill_data = bpy.data.lights.new("Fill_Light", type='POINT')
fill_data.energy = 60.0
fill_data.color = (0.85, 0.9, 1.0)
fill = bpy.data.objects.new("Fill_Light", fill_data)
fill.location = (-1.4, 1.4, 1.8)
collection.objects.link(fill)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 30.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam.location = Vector((1.75, -1.75, 1.5))
target = Vector((0.0, 0.0, 0.8))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
