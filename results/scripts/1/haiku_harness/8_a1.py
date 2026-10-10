import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Scene reset ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_mat(name, color, roughness=0.5, metallic=0.0,
             emission=None, emission_strength=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if transmission > 0:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def obj_from_bm(name, bm, mat):
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    return link(obj)


def frustum(name, r0, r1, z0, z1, mat, seg=40):
    """Truncated cone (r1 == 0 gives a cone with apex)."""
    bm = bmesh.new()
    angles = [2 * math.pi * i / seg for i in range(seg)]
    bot = [bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), z0)) for a in angles]
    bm.faces.new(bot)
    if r1 > 1e-6:
        top = [bm.verts.new((r1 * math.cos(a), r1 * math.sin(a), z1)) for a in angles]
        bm.faces.new(top)
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
    else:
        apex = bm.verts.new((0.0, 0.0, z1))
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((bot[i], bot[j], apex))
    return obj_from_bm(name, bm, mat)


def box(name, center, size, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    cx, cy, cz = center
    for v in bm.verts:
        v.co = Vector((v.co.x * sx + cx, v.co.y * sy + cy, v.co.z * sz + cz))
    return obj_from_bm(name, bm, mat)


# ---------- Materials ----------
mat_red = make_mat("LH_Red", (0.70, 0.04, 0.03), roughness=0.55)
mat_white = make_mat("LH_White", (0.90, 0.90, 0.87), roughness=0.45)
mat_metal = make_mat("LH_DarkMetal", (0.05, 0.05, 0.06), roughness=0.35, metallic=0.9)
mat_roof = make_mat("LH_Roof", (0.12, 0.05, 0.04), roughness=0.6)
mat_glass = make_mat("LH_Lamp", (1.0, 0.95, 0.8), roughness=0.1,
                     emission=(1.0, 0.92, 0.7), emission_strength=25.0)
mat_rock = make_mat("LH_Rock", (0.28, 0.26, 0.23), roughness=0.92)
mat_water = make_mat("LH_Water", (0.02, 0.09, 0.12), roughness=0.06)
mat_house = make_mat("LH_House", (0.85, 0.84, 0.80), roughness=0.5)

# ---------- World / sky ----------
world = bpy.data.worlds.new("LH_Sky")
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.42, 0.60, 0.85, 1.0)
bg.inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world

# ---------- Island (flattened, jittered icosphere) ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
for v in bm.verts:
    x, y, z = v.co
    f = 1.0 + random.uniform(-0.09, 0.09)
    v.co = Vector((x * 9.0 * f, y * 8.0 * f, z * 2.0 - 1.5 + random.uniform(-0.05, 0.05)))
island = obj_from_bm("Island", bm, mat_rock)

# ---------- Scattered boulders ----------
for i in range(9):
    ang = random.uniform(0, 2 * math.pi)
    dist = random.uniform(7.0, 10.5)
    px, py = dist * math.cos(ang) * 0.95, dist * math.sin(ang) * 0.8
    rad = random.uniform(0.25, 0.7)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad)
    for v in bm.verts:
        v.co = Vector((v.co.x * random.uniform(0.8, 1.2),
                       v.co.y * random.uniform(0.8, 1.2),
                       v.co.z * random.uniform(0.5, 0.8)) + Vector((px, py, 0.0)))
    obj_from_bm(f"Boulder_{i}", bm, mat_rock)

# ---------- Water ----------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * 90.0, v.co.y * 90.0, -0.05))
water = obj_from_bm("Water", bm, mat_water)

# ---------- Lighthouse tower (striped bands) ----------
TOWER_BOT = 0.3
TOWER_TOP = 14.0
R_BOT = 2.0
R_TOP = 1.35


def tower_r(z):
    t = (z - TOWER_BOT) / (TOWER_TOP - TOWER_BOT)
    return R_BOT + (R_TOP - R_BOT) * t


bands = 10
for i in range(bands):
    z0 = TOWER_BOT + (TOWER_TOP - TOWER_BOT) * i / bands
    z1 = TOWER_BOT + (TOWER_TOP - TOWER_BOT) * (i + 1) / bands
    mat = mat_red if i % 2 == 0 else mat_white
    frustum(f"Tower_Band_{i}", tower_r(z0), tower_r(z1), z0, z1, mat, seg=48)

# Gallery deck and railing
frustum("Gallery", 1.95, 1.95, TOWER_TOP, TOWER_TOP + 0.3, mat_metal, seg=48)
frustum("Gallery_Rail", 1.9, 1.9, TOWER_TOP + 0.3, TOWER_TOP + 0.9, mat_metal, seg=48)

# Lantern room (glass) and top cap
frustum("Lantern_Glass", 1.25, 1.25, TOWER_TOP + 0.3, 16.6, mat_glass, seg=40)
frustum("Lantern_Frame", 1.35, 1.35, 16.6, 16.9, mat_metal, seg=40)

# Roof
frustum("Roof", 1.6, 0.0, 16.9, 18.4, mat_roof, seg=40)

# Finial
frustum("Finial", 0.12, 0.12, 18.4, 18.9, mat_metal, seg=12)

# Keeper's house beside the tower
box("Keeper_House", (-4.6, -1.2, 1.2), (3.2, 2.6, 2.6), mat_house)
box("Keeper_Roof", (-4.6, -1.2, 2.95), (3.6, 3.0, 0.4), mat_roof)

# ---------- Lights ----------
lamp_data = bpy.data.lights.new("LampLight", 'POINT')
lamp_data.energy = 6000.0
lamp_data.color = (1.0, 0.9, 0.7)
lamp_data.shadow_soft_size = 0.5
lamp_obj = bpy.data.objects.new("LampLight", lamp_data)
lamp_obj.location = (0.0, 0.0, 15.6)
link(lamp_obj)

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.color = (1.0, 0.96, 0.9)
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = (math.radians(52), math.radians(8), math.radians(35))
link(sun_obj)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("LH_Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("LH_Camera", cam_data)
cam_loc = Vector((15.0, -24.0, 6.5))
target = Vector((0.0, 0.0, 8.0))
cam_obj.location = cam_loc
cam_obj.rotation_euler = (target - cam_loc).to_track_quat('-Z', 'Y').to_euler()
link(cam_obj)
bpy.context.scene.camera = cam_obj
