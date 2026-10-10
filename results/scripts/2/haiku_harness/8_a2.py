import bpy
import bmesh
import math
import random
from math import cos, sin, pi
from mathutils import Vector, Matrix

random.seed(7)

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)

scene = bpy.context.scene
coll = scene.collection


# ---------- Helpers ----------
def make_mat(name, color, roughness=0.6, metallic=0.0,
             emit_color=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emit_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def finish(name, bm, mats):
    """Convert bmesh to a mesh object and link it to the scene collection once."""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    me.update()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def cone(bm, r1, r2, depth, segs, loc, caps=True):
    bmesh.ops.create_cone(
        bm,
        cap_ends=caps,
        cap_tris=False,
        segments=segs,
        radius1=r1,
        radius2=r2,
        depth=depth,
        matrix=Matrix.Translation(loc),
        calc_uvs=False,
    )


# ---------- Materials ----------
red_paint = make_mat("RedPaint", (0.75, 0.05, 0.04), roughness=0.45)
white_paint = make_mat("WhitePaint", (0.92, 0.92, 0.9), roughness=0.4)
metal_dark = make_mat("DarkMetal", (0.05, 0.05, 0.06), roughness=0.35, metallic=0.8)
roof_mat = make_mat("RoofRed", (0.45, 0.06, 0.05), roughness=0.5)
glass_mat = make_mat("LanternGlass", (1.0, 0.9, 0.6), roughness=0.05,
                     emit_color=(1.0, 0.85, 0.5), emit_strength=12.0)
rock_mat = make_mat("Rock", (0.24, 0.22, 0.19), roughness=0.92)
water_mat = make_mat("Water", (0.02, 0.10, 0.14), roughness=0.03)


# ---------- Island height function ----------
def island_height(x, y):
    r = math.hypot(x, y)
    base = 2.8 * max(0.0, 1.0 - r / 6.5) ** 0.7
    n = (0.45 * sin(2.1 * x + 0.7) * cos(1.7 * y)
         + 0.30 * sin(4.3 * x - 1.1) * sin(3.7 * y + 0.4)
         + 0.12 * cos(9.0 * x) * sin(8.0 * y))
    v = base + n * 0.9 - 0.8 * max(0.0, r - 7.0) / 5.0
    return max(v, -1.2)


# ---------- Water ----------
bm = bmesh.new()
half = 120.0
v0 = bm.verts.new((-half, -half, 0.0))
v1 = bm.verts.new((half, -half, 0.0))
v2 = bm.verts.new((half, half, 0.0))
v3 = bm.verts.new((-half, half, 0.0))
bm.faces.new((v0, v1, v2, v3))
water = finish("Water", bm, [water_mat])

# ---------- Rocky island ----------
bm = bmesh.new()
N = 56
span = 14.0
grid = []
for i in range(N + 1):
    row = []
    for j in range(N + 1):
        x = -span + 2 * span * i / N
        y = -span + 2 * span * j / N
        z = island_height(x, y)
        row.append(bm.verts.new((x, y, z)))
    grid.append(row)
for i in range(N):
    for j in range(N):
        bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
island = finish("Island", bm, [rock_mat])

# Boulders around the shoreline
bm = bmesh.new()
for _ in range(14):
    ang = random.uniform(0, 2 * pi)
    rad = random.uniform(6.0, 10.0)
    x, y = rad * cos(ang), rad * sin(ang)
    s = random.uniform(0.4, 1.1)
    loc = (x, y, 0.1)
    mat = Matrix.LocRotScale(
        loc,
        (random.uniform(0, pi), random.uniform(0, pi), random.uniform(0, pi)),
        (s * random.uniform(1.0, 1.6), s, s * random.uniform(0.5, 0.9)),
    )
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=mat)
boulders = finish("Boulders", bm, [rock_mat])

# ---------- Lighthouse tower ----------
z0 = island_height(0.0, 0.0)
TOWER_H = 18.0
BAND = 1.5
SEG = 28
R_BASE, R_TOP = 1.9, 1.1

bm = bmesh.new()
angles = [2 * pi * i / SEG for i in range(SEG)]
rings = []
n_bands = int(round(TOWER_H / BAND))
for k in range(n_bands + 1):
    t = k / n_bands
    z = z0 + k * BAND
    r = R_BASE + (R_TOP - R_BASE) * t
    rings.append([bm.verts.new((r * cos(a), r * sin(a), z)) for a in angles])

for k in range(n_bands):
    a_ring, b_ring = rings[k], rings[k + 1]
    for i in range(SEG):
        j = (i + 1) % SEG
        f = bm.faces.new((a_ring[i], a_ring[j], b_ring[j], b_ring[i]))
        f.material_index = k % 2  # alternating red / white stripes

bottom = bm.faces.new(list(reversed(rings[0])))
bottom.material_index = 0
top = bm.faces.new(rings[-1])
top.material_index = 1

tower = finish("Tower", bm, [red_paint, white_paint])

top_z = z0 + TOWER_H

# Gallery deck
bm = bmesh.new()
cone(bm, 2.05, 2.05, 0.18, 32, (0, 0, top_z + 0.09), caps=True)
gallery = finish("Gallery", bm, [metal_dark])

# Railing posts and top rail
bm = bmesh.new()
RAIL_R = 1.9
for i in range(36):
    a = 2 * pi * i / 36
    cone(bm, 0.035, 0.035, 1.0, 6, (RAIL_R * cos(a), RAIL_R * sin(a), top_z + 0.68))
cone(bm, RAIL_R, RAIL_R, 0.06, 36, (0, 0, top_z + 1.15), caps=False)
railing = finish("Railing", bm, [metal_dark])

# Lantern room (glowing glass)
bm = bmesh.new()
cone(bm, 0.95, 0.95, 2.2, 16, (0, 0, top_z + 1.3), caps=True)
lantern = finish("Lantern", bm, [glass_mat])

# Lantern frame
bm = bmesh.new()
for i in range(8):
    a = 2 * pi * i / 8
    cone(bm, 0.05, 0.05, 2.25, 6, (0.95 * cos(a), 0.95 * sin(a), top_z + 1.3))
frame = finish("LanternFrame", bm, [metal_dark])

# Roof dome cone
bm = bmesh.new()
cone(bm, 1.25, 0.0, 1.1, 16, (0, 0, top_z + 2.85), caps=True)
roof = finish("LanternRoof", bm, [roof_mat])

# Finial
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.12,
                           matrix=Matrix.Translation((0, 0, top_z + 3.45)))
finial = finish("Finial", bm, [metal_dark])

# Keeper's house (small hut at the base)
bm = bmesh.new()
cone(bm, 1.3, 1.3, 2.6, 8, (-4.2, 1.0, z0 + 1.3))
hut = finish("Hut", bm, [white_paint])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.5
sun_data.angle = math.radians(2.5)
sun = bpy.data.objects.new("Sun", sun_data)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-35))

# Warm lantern point light
lamp_data = bpy.data.lights.new("LanternLight", 'POINT')
lamp_data.energy = 1500.0
lamp_data.color = (1.0, 0.85, 0.6)
lamp_data.shadow_soft_size = 0.5
lamp = bpy.data.objects.new("LanternLight", lamp_data)
coll.objects.link(lamp)
lamp.location = (0, 0, top_z + 1.3)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.42, 0.62, 0.90, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
coll.objects.link(cam)
cam_loc = Vector((17.0, -25.0, 10.0))
target = Vector((0.0, 0.0, z0 + 9.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
