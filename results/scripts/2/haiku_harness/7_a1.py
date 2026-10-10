import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def link_obj(obj):
    scene.collection.objects.link(obj)
    return obj

def make_box(name, size, loc, mat, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    link_obj(obj)
    obj.location = loc
    if parent is not None:
        obj.parent = parent
    return obj

def make_cylinder(name, radius, depth, loc, mat, segments=24, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    link_obj(obj)
    obj.location = loc
    if parent is not None:
        obj.parent = parent
    return obj

# ---------- Materials ----------
mat_wall = make_mat("Wall_Plaster", (0.86, 0.82, 0.74), 0.9)
mat_ceiling = make_mat("Ceiling_White", (0.93, 0.93, 0.92), 0.95)
mat_floor = make_mat("Floor_Wood", (0.42, 0.26, 0.14), 0.45)
mat_rug = make_mat("Rug_Fabric", (0.55, 0.16, 0.14), 0.95)
mat_table = make_mat("Table_Wood", (0.52, 0.33, 0.18), 0.38)
mat_chair = make_mat("Chair_Wood", (0.36, 0.22, 0.12), 0.42)
mat_seat = make_mat("Chair_Seat", (0.62, 0.45, 0.28), 0.7)
mat_vase = make_mat("Vase_Ceramic", (0.20, 0.45, 0.55), 0.25)

# ---------- Room ----------
ROOM_W, ROOM_D, ROOM_H = 6.0, 5.0, 2.8

make_box("Floor", (ROOM_W, ROOM_D, 0.1), (0, 0, -0.05), mat_floor)
make_box("Ceiling", (ROOM_W, ROOM_D, 0.1), (0, 0, ROOM_H + 0.05), mat_ceiling)
make_box("Wall_Back", (ROOM_W, 0.1, ROOM_H), (0, ROOM_D / 2 + 0.05, ROOM_H / 2), mat_wall)
make_box("Wall_Left", (0.1, ROOM_D, ROOM_H), (-ROOM_W / 2 - 0.05, 0, ROOM_H / 2), mat_wall)
make_box("Wall_Right", (0.1, ROOM_D, ROOM_H), (ROOM_W / 2 + 0.05, 0, ROOM_H / 2), mat_wall)

# Rug under the table
make_box("Rug", (2.8, 2.0, 0.012), (0, 0, 0.006), mat_rug)

# ---------- Table ----------
TABLE_TOP_Z = 0.75
table_root = bpy.data.objects.new("Table", None)
link_obj(table_root)
table_root.location = (0, 0, 0)

make_box("Table_Top", (1.6, 1.0, 0.05), (0, 0, TABLE_TOP_Z), mat_table, parent=table_root)
leg_h = TABLE_TOP_Z - 0.025
for sx in (-1, 1):
    for sy in (-1, 1):
        make_box(f"Table_Leg_{sx}_{sy}", (0.06, 0.06, leg_h),
                 (sx * 0.7, sy * 0.4, leg_h / 2), mat_table, parent=table_root)

# Vase on the table
make_cylinder("Vase", 0.07, 0.24, (0.25, 0.1, TABLE_TOP_Z + 0.025 + 0.12),
              mat_vase, parent=table_root)

# ---------- Chairs ----------
def make_chair(name, pos, rot_z):
    root = bpy.data.objects.new(name, None)
    link_obj(root)
    root.location = (pos[0], pos[1], 0)
    root.rotation_euler = (0, 0, rot_z)

    seat_z = 0.45
    make_box(name + "_Seat", (0.45, 0.45, 0.05), (0, 0, seat_z), mat_seat, parent=root)
    make_box(name + "_Back", (0.45, 0.05, 0.45), (0, -0.2, 0.7), mat_chair, parent=root)
    leg_len = seat_z - 0.025
    for lx in (-1, 1):
        for ly in (-1, 1):
            make_box(f"{name}_Leg_{lx}_{ly}", (0.04, 0.04, leg_len),
                     (lx * 0.19, ly * 0.19, leg_len / 2), mat_chair, parent=root)
    return root

make_chair("Chair_South", (0.0, -0.85), 0.0)
make_chair("Chair_North", (0.0, 0.85), math.pi)
make_chair("Chair_West", (-1.2, 0.0), -math.pi / 2)
make_chair("Chair_East", (1.2, 0.0), math.pi / 2)

# ---------- Lighting ----------
ceiling_light_data = bpy.data.lights.new("Ceiling_Light", 'AREA')
ceiling_light_data.energy = 350.0
ceiling_light_data.size = 1.8
ceiling_light = bpy.data.objects.new("Ceiling_Light", ceiling_light_data)
link_obj(ceiling_light)
ceiling_light.location = (0, 0, ROOM_H - 0.15)

fill_data = bpy.data.lights.new("Fill_Light", 'POINT')
fill_data.energy = 120.0
fill_data.shadow_soft_size = 0.5
fill = bpy.data.objects.new("Fill_Light", fill_data)
link_obj(fill)
fill.location = (-2.2, -1.8, 2.2)

# World ambient
world = bpy.data.worlds.new("Room_World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.52, 0.55, 1.0)
bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Room_Camera")
cam_data.lens = 28.0
cam = bpy.data.objects.new("Room_Camera", cam_data)
link_obj(cam)
cam.location = Vector((-2.4, -3.6, 1.9))
target = Vector((0.0, 0.0, 0.7))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1
