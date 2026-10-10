import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_wood_material(name, dark, light, scale=6.0, roughness=0.55):
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def make_box(name, dims, loc, mat, rot_z=0.0):
    dx, dy, dz = dims
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dx
        v.co.y *= dy
        v.co.z *= dz
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    obj.location = Vector(loc)
    obj.rotation_euler = (0.0, 0.0, rot_z)
    obj.data.materials.append(mat)
    return obj


def make_cylinder(name, radius, depth, loc, mat, segments=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    obj.location = Vector(loc)
    obj.data.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    return obj


def make_sphere(name, radius, loc, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=radius)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    obj.location = Vector(loc)
    obj.data.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    return obj


def rot2d(x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (x * c - y * s, x * s + y * c)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
floor_mat = make_wood_material("FloorWood", (0.20, 0.11, 0.05), (0.42, 0.25, 0.12), scale=4.0, roughness=0.5)
table_mat = make_wood_material("TableWood", (0.35, 0.18, 0.08), (0.62, 0.38, 0.20), scale=7.0, roughness=0.45)
chair_mat = make_wood_material("ChairWood", (0.30, 0.16, 0.07), (0.55, 0.33, 0.17), scale=9.0, roughness=0.5)
seat_mat = make_material("SeatFabric", (0.12, 0.35, 0.38), roughness=0.95)
wall_mat = make_material("WallPaint", (0.86, 0.84, 0.78), roughness=0.9)
ceiling_mat = make_material("CeilingPaint", (0.92, 0.92, 0.90), roughness=0.95)
vase_mat = make_material("Ceramic", (0.75, 0.80, 0.85), roughness=0.15)
apple_mat = make_material("Apple", (0.65, 0.05, 0.04), roughness=0.3)
pear_mat = make_material("Pear", (0.70, 0.65, 0.15), roughness=0.35)

# ---------------------------------------------------------------------------
# Room shell (room spans -2..2 on X and Y, height 2.8)
# ---------------------------------------------------------------------------
ROOM_H = 2.8
HALF = 2.0
T = 0.1

make_box("Floor", (4.2, 4.2, 0.1), (0, 0, -0.05), floor_mat)
make_box("Ceiling", (4.2, 4.2, 0.1), (0, 0, ROOM_H + 0.05), ceiling_mat)
make_box("Wall_Back", (4.2, T, ROOM_H), (0, -HALF - T / 2, ROOM_H / 2), wall_mat)
make_box("Wall_Front", (4.2, T, ROOM_H), (0, HALF + T / 2, ROOM_H / 2), wall_mat)
make_box("Wall_Left", (T, 4.2, ROOM_H), (-HALF - T / 2, 0, ROOM_H / 2), wall_mat)
make_box("Wall_Right", (T, 4.2, ROOM_H), (HALF + T / 2, 0, ROOM_H / 2), wall_mat)

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------
TABLE_Z = 0.0
make_box("Table_Top", (1.3, 0.8, 0.05), (0, 0, 0.725), table_mat)
for i, (lx, ly) in enumerate([(-0.6, -0.33), (0.6, -0.33), (-0.6, 0.33), (0.6, 0.33)]):
    make_box(f"Table_Leg_{i}", (0.06, 0.06, 0.70), (lx, ly, 0.35), table_mat)

# Table centerpiece
make_cylinder("Vase", 0.06, 0.28, (0.25, 0.0, 0.75 + 0.14), vase_mat)
make_sphere("Apple_1", 0.05, (-0.2, -0.1, 0.80), apple_mat)
make_sphere("Apple_2", 0.05, (-0.12, 0.12, 0.80), apple_mat)
make_sphere("Pear_1", 0.055, (-0.35, 0.05, 0.81), pear_mat)

# ---------------------------------------------------------------------------
# Chairs (built in local space with the backrest on -Y, then rotated)
# ---------------------------------------------------------------------------
def make_chair(idx, cx, cy, ang):
    prefix = f"Chair_{idx}"

    def part(name, dims, lx, ly, lz, mat):
        wx, wy = rot2d(lx, ly, ang)
        return make_box(f"{prefix}_{name}", dims, (cx + wx, cy + wy, lz), mat, rot_z=ang)

    # Seat
    part("Seat", (0.45, 0.45, 0.05), 0.0, 0.0, 0.45, seat_mat)
    # Four legs
    for j, (lx, ly) in enumerate([(-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)]):
        part(f"Leg_{j}", (0.04, 0.04, 0.425), lx, ly, 0.2125, chair_mat)
    # Two back posts continuing up from rear legs
    for j, lx in enumerate([-0.18, 0.18]):
        part(f"BackPost_{j}", (0.04, 0.04, 0.45), lx, -0.2, 0.7, chair_mat)
    # Backrest panel
    part("Backrest", (0.36, 0.03, 0.22), 0.0, -0.2, 0.78, chair_mat)


# Two chairs on each long side of the table
make_chair(0, -0.4, -0.9, 0.0)
make_chair(1, 0.4, -0.9, 0.0)
make_chair(2, -0.4, 0.9, math.pi)
make_chair(3, 0.4, 0.9, math.pi)

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
ceiling_light_data = bpy.data.lights.new("CeilingLight", type='AREA')
ceiling_light_data.energy = 350.0
ceiling_light_data.size = 1.6
ceiling_light_data.color = (1.0, 0.95, 0.88)
ceiling_light = bpy.data.objects.new("CeilingLight", ceiling_light_data)
collection.objects.link(ceiling_light)
ceiling_light.location = (0.0, 0.0, ROOM_H - 0.15)
ceiling_light.rotation_euler = (0.0, 0.0, 0.0)  # faces down (-Z)

fill_data = bpy.data.lights.new("FillLight", type='POINT')
fill_data.energy = 60.0
fill_data.color = (0.9, 0.93, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
collection.objects.link(fill)
fill.location = (-1.4, 1.4, 1.9)

# Soft world ambient
world = bpy.data.worlds.new("RoomWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.25, 0.25, 0.27, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("RoomCamera")
cam_data.lens = 24.0
cam_data.sensor_width = 36.0
cam = bpy.data.objects.new("RoomCamera", cam_data)
collection.objects.link(cam)

cam_loc = Vector((1.75, -1.75, 1.55))
target = Vector((0.0, 0.0, 0.8))
direction = (target - cam_loc).normalized()
cam.location = cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------------------------------------------------------------------------
# Render settings (no rendering performed here)
# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
