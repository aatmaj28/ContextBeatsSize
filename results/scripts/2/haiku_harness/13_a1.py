import bpy
import bmesh
import math
import random
import colorsys
from mathutils import Vector, Matrix

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, coat=0.0, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if coat > 0 and "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat
            if "Coat Roughness" in bsdf.inputs:
                bsdf.inputs["Coat Roughness"].default_value = 0.05
    return mat


def bm_to_object(bm, name, material):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ---------- Materials ----------
dough_mat = make_material("Dough", (0.72, 0.43, 0.18), roughness=0.45)
frosting_mat = make_material("PinkFrosting", (0.95, 0.42, 0.62), roughness=0.18, coat=0.6)
plate_mat = make_material("WhitePlate", (0.92, 0.92, 0.92), roughness=0.12, coat=0.3)

sprinkle_colors = [
    (0.10, 0.55, 0.95),  # blue
    (0.98, 0.85, 0.15),  # yellow
    (0.20, 0.80, 0.35),  # green
    (0.55, 0.20, 0.90),  # purple
    (0.98, 0.98, 0.98),  # white
]
sprinkle_mats = [make_material(f"Sprinkle{i}", c, roughness=0.3, coat=0.4)
                 for i, c in enumerate(sprinkle_colors)]

# ---------- Donut geometry ----------
R = 1.0      # major radius
r = 0.40     # minor radius
NU = 96      # around the ring
NV = 40      # around the tube
PLATE_TOP = 0.14
DONUT_Z = PLATE_TOP + r
DONUT_LOC = Vector((0.0, 0.0, DONUT_Z))


def tube_normal(u, v):
    return Vector((math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v)))


def tube_point(u, v, rad):
    center = Vector((R * math.cos(u), R * math.sin(u), 0.0))
    return center + tube_normal(u, v) * rad


# Dough
bm = bmesh.new()
dv = [[None] * NV for _ in range(NU)]
for i in range(NU):
    u = 2 * math.pi * i / NU
    for j in range(NV):
        v = 2 * math.pi * j / NV
        dv[i][j] = bm.verts.new(tube_point(u, v, r))
for i in range(NU):
    for j in range(NV):
        bm.faces.new((dv[i][j], dv[(i + 1) % NU][j],
                      dv[(i + 1) % NU][(j + 1) % NV], dv[i][(j + 1) % NV]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
donut = bm_to_object(bm, "Donut", dough_mat)
donut.location = DONUT_LOC

# Frosting radius and drip-like coverage boundary
FROST_R = r * 1.04 + 0.01


def frost_cut(u):
    return -0.25 + 0.12 * math.sin(7 * u) + 0.05 * math.sin(13 * u)


bm = bmesh.new()
fv = [[None] * NV for _ in range(NU)]
for i in range(NU):
    u = 2 * math.pi * i / NU
    for j in range(NV):
        v = 2 * math.pi * j / NV
        fv[i][j] = bm.verts.new(tube_point(u, v, FROST_R))
for i in range(NU):
    uc = 2 * math.pi * (i + 0.5) / NU
    for j in range(NV):
        vc = 2 * math.pi * (j + 0.5) / NV
        if math.sin(vc) > frost_cut(uc):
            try:
                bm.faces.new((fv[i][j], fv[(i + 1) % NU][j],
                              fv[(i + 1) % NU][(j + 1) % NV], fv[i][(j + 1) % NV]))
            except ValueError:
                pass
bm.verts.ensure_lookup_table()
loose = [v for v in bm.verts if not v.link_faces]
if loose:
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
frosting = bm_to_object(bm, "Frosting", frosting_mat)
frosting.location = DONUT_LOC

# ---------- Sprinkles ----------
SPRINKLE_R = 0.018
SPRINKLE_LEN = 0.12
buckets = [bmesh.new() for _ in sprinkle_colors]
placed = 0
attempts = 0
TARGET = 90
while placed < TARGET and attempts < 5000:
    attempts += 1
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(-math.pi, math.pi)
    if math.sin(v) < frost_cut(u) + 0.12:
        continue
    N = tube_normal(u, v)
    P = tube_point(u, v, FROST_R - 0.004)
    rnd = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1)))
    T = rnd - N * rnd.dot(N)
    if T.length < 1e-6:
        continue
    T.normalize()
    z_axis = T
    y_axis = N.copy()
    x_axis = y_axis.cross(z_axis).normalized()
    rot = Matrix.Identity(3)
    rot.col[0] = x_axis
    rot.col[1] = y_axis
    rot.col[2] = z_axis
    M = rot.to_4x4()
    M.translation = P
    k = random.randrange(len(sprinkle_colors))
    bmesh.ops.create_cone(buckets[k], cap_ends=True, cap_tris=False, segments=8,
                          radius1=SPRINKLE_R, radius2=SPRINKLE_R,
                          depth=SPRINKLE_LEN, matrix=M, calc_uvs=False)
    placed += 1

for idx, bm_s in enumerate(buckets):
    if len(bm_s.verts) == 0:
        bm_s.free()
        continue
    obj = bm_to_object(bm_s, f"Sprinkles{idx}", sprinkle_mats[idx])
    obj.parent = donut

# ---------- Plate ----------
bm = bmesh.new()
profile = [
    (1.85, 0.00),
    (2.00, 0.03),
    (2.05, 0.07),
    (2.00, 0.11),
    (1.85, 0.13),
    (1.30, PLATE_TOP),
]
PN = 96
rings = []
for rad, z in profile:
    ring = []
    for k in range(PN):
        a = 2 * math.pi * k / PN
        ring.append(bm.verts.new((rad * math.cos(a), rad * math.sin(a), z)))
    rings.append(ring)
bot_c = bm.verts.new((0.0, 0.0, 0.0))
top_c = bm.verts.new((0.0, 0.0, PLATE_TOP))
for k in range(PN):
    bm.faces.new((bot_c, rings[0][(k + 1) % PN], rings[0][k]))
for ri in range(len(rings) - 1):
    a_ring, b_ring = rings[ri], rings[ri + 1]
    for k in range(PN):
        k2 = (k + 1) % PN
        bm.faces.new((a_ring[k], a_ring[k2], b_ring[k2], b_ring[k]))
for k in range(PN):
    bm.faces.new((top_c, rings[-1][k], rings[-1][(k + 1) % PN]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
plate = bm_to_object(bm, "Plate", plate_mat)

# ---------- Lighting ----------
def add_area_light(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = Vector(loc)
    aim(lo, (0, 0, 0.3))
    return lo


add_area_light("KeyLight", (3.5, -3.5, 5.0), 900, 4.0)
add_area_light("FillLight", (-4.0, -2.5, 3.0), 250, 5.0, (0.9, 0.95, 1.0))
add_area_light("RimLight", (-1.5, 4.5, 3.5), 500, 3.0, (1.0, 0.97, 0.9))

# World background
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.85, 0.87, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((0.0, -6.4, 4.4))
aim(cam, (0.0, 0.0, 0.25))
bpy.context.scene.camera = cam
