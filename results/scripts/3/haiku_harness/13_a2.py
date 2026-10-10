import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    if m.users == 0:
        bpy.data.meshes.remove(m)

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------
TAU = 2.0 * math.pi
R = 1.0
r = 0.38
PLATE_TOP = 0.14
Z0 = PLATE_TOP + r + 0.02

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def set_input(bsdf, name, value):
    if bsdf is None:
        return
    try:
        bsdf.inputs[name].default_value = value
    except KeyError:
        pass

def make_mat(name, color, rough, coat=0.0, sss=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (color[0], color[1], color[2], 1.0))
    set_input(bsdf, "Roughness", rough)
    set_input(bsdf, "Coat Weight", coat)
    set_input(bsdf, "Subsurface Weight", sss)
    set_input(bsdf, "Specular IOR Level", spec)
    return mat

dough_mat = make_mat("Donut_Dough", (0.80, 0.52, 0.28), 0.60, sss=0.05)
frosting_mat = make_mat("Donut_PinkFrosting", (1.0, 0.42, 0.62), 0.16, coat=0.35)
plate_mat = make_mat("Plate_White", (0.95, 0.95, 0.95), 0.12, coat=0.1)
floor_mat = make_mat("Floor", (0.55, 0.50, 0.46), 0.85)

SPRINKLE_COLORS = [
    (1.00, 0.15, 0.20),
    (0.20, 0.50, 1.00),
    (1.00, 0.85, 0.10),
    (0.20, 0.90, 0.35),
    (0.70, 0.30, 1.00),
    (1.00, 1.00, 1.00),
]
sprinkle_mats = [make_mat(f"Sprinkle_{i}", c, 0.30, coat=0.2)
                 for i, c in enumerate(SPRINKLE_COLORS)]

# ---------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------
def base_pt(u, v):
    cu, su = math.cos(u), math.sin(u)
    cv, sv = math.cos(v), math.sin(v)
    n = Vector((cv * cu, cv * su, sv))
    p = Vector(((R + r * cv) * cu, (R + r * cv) * su, r * sv))
    return p, n

def frost_pt(u, v):
    p, n = base_pt(u, v)
    nz = n.z
    f = min(max((nz + 0.25) / 1.1, 0.0), 1.0)
    f = f * f * (3.0 - 2.0 * f)
    wave = 0.010 * math.sin(7.0 * u + 2.0 * math.sin(3.0 * v)) \
         + 0.006 * math.sin(13.0 * u + 5.0 * v)
    thick = 0.02 + 0.075 * f + wave * (0.3 + f)
    q = p + n * thick
    outer = max(0.0, math.cos(v)) ** 2
    lower = min(1.0, max(0.0, 0.4 - nz) * 2.0)
    drip_wave = max(0.0, math.sin(6.0 * u + 1.0)) ** 3
    q.z -= 0.09 * drip_wave * outer * lower
    return q, n

def build_torus_bm(fn, nu=96, nv=48):
    bm = bmesh.new()
    grid = []
    for i in range(nu):
        u = TAU * i / nu
        row = []
        for j in range(nv):
            v = TAU * j / nv
            p, _ = fn(u, v)
            row.append(bm.verts.new(p))
        grid.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(nu):
        for j in range(nv):
            a = grid[i][j]
            b = grid[(i + 1) % nu][j]
            c = grid[(i + 1) % nu][(j + 1) % nv]
            d = grid[i][(j + 1) % nv]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm

def add_cylinder(bm, mtx, length, rad, seg=8):
    h = length * 0.5
    bottom, top = [], []
    for k in range(seg):
        a = TAU * k / seg
        x = rad * math.cos(a)
        y = rad * math.sin(a)
        bottom.append(bm.verts.new(mtx @ Vector((x, y, -h))))
        top.append(bm.verts.new(mtx @ Vector((x, y, h))))
    for k in range(seg):
        k2 = (k + 1) % seg
        try:
            bm.faces.new((bottom[k], bottom[k2], top[k2], top[k]))
        except ValueError:
            pass
    try:
        bm.faces.new(bottom[::-1])
        bm.faces.new(top)
    except ValueError:
        pass

def make_obj(name, bm, mat=None, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if mat is not None:
        me.materials.append(mat)
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------
# Plate and floor
# ---------------------------------------------------------------
plate_bm = bmesh.new()
add_cylinder(plate_bm, Matrix.Translation((0.0, 0.0, PLATE_TOP - 0.02)),
             0.04, 1.9, seg=64)
plate = make_obj("Plate", plate_bm, plate_mat, smooth=True)

floor_bm = bmesh.new()
fs = 6.0
fz = -0.01
fv = [floor_bm.verts.new(Vector(p)) for p in
      [(-fs, -fs, fz), (fs, -fs, fz), (fs, fs, fz), (-fs, fs, fz)]]
floor_bm.faces.new(fv)
floor = make_obj("Floor", floor_bm, floor_mat, smooth=False)

# ---------------------------------------------------------------
# Donut dough and frosting
# ---------------------------------------------------------------
dough_bm = build_torus_bm(base_pt)
dough = make_obj("Donut_Dough", dough_bm, dough_mat)
dough.location = (0.0, 0.0, Z0)

frost_bm = build_torus_bm(frost_pt)
frosting = make_obj("Donut_Frosting", frost_bm, frosting_mat)
frosting.location = (0.0, 0.0, Z0)

# ---------------------------------------------------------------
# Sprinkles (one mesh per color)
# ---------------------------------------------------------------
sprinkle_bms = [bmesh.new() for _ in SPRINKLE_COLORS]
placed = []
count = 0
tries = 0
TARGET = 130
while count < TARGET and tries < 8000:
    tries += 1
    u = random.uniform(0.0, TAU)
    v = random.uniform(0.0, TAU)
    _, n_base = base_pt(u, v)
    if n_base.z < 0.5:
        continue
    surf, n = frost_pt(u, v)
    pos = surf + n * 0.004

    if any((pos - q).length < 0.13 for q in placed):
        continue

    rv = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    t = n.cross(rv)
    if t.length < 1e-6:
        continue
    t.normalize()
    y = n.cross(t).normalized()
    x = y.cross(t).normalized()
    M = Matrix((x, y, t)).transposed().to_4x4()
    world_pos = pos + Vector((0.0, 0.0, Z0))
    mtx = Matrix.Translation(world_pos) @ M

    L = random.uniform(0.07, 0.10)
    rad = 0.011
    idx = random.randrange(len(SPRINKLE_COLORS))
    add_cylinder(sprinkle_bms[idx], mtx, L, rad, seg=8)

    placed.append(pos)
    count += 1

for i, sbm in enumerate(sprinkle_bms):
    if len(sbm.faces) == 0:
        sbm.free()
        continue
    make_obj(f"Sprinkles_{i}", sbm, sprinkle_mats[i], smooth=False)

# ---------------------------------------------------------------
# World
# ---------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
set_input(bg, "Color", (0.92, 0.92, 0.95, 1.0))
set_input(bg, "Strength", 0.6)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(4.0)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (4.0, -3.0, 6.0)
look_at(sun, (0.0, 0.0, 0.5))

area_data = bpy.data.lights.new("KeyArea", 'AREA')
area_data.energy = 400.0
area_data.size = 3.0
area = bpy.data.objects.new("KeyArea", area_data)
scene.collection.objects.link(area)
area.location = (-3.0, -3.5, 3.5)
look_at(area, (0.0, 0.0, 0.5))

rim_data = bpy.data.lights.new("Rim", 'AREA')
rim_data.energy = 150.0
rim_data.size = 2.0
rim = bpy.data.objects.new("Rim", rim_data)
scene.collection.objects.link(rim)
rim.location = (3.0, 3.5, 2.5)
look_at(rim, (0.0, 0.0, 0.5))

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (3.2, -4.4, 2.6)
look_at(cam, (0.0, 0.0, 0.45))
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
