import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Quaternion

random.seed(7)

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

collection = bpy.context.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0,
                  coat=0.0, sss=0.0, sss_color=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    for key, val in (("Coat Weight", coat), ("Subsurface Weight", sss)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val
    if sss > 0 and sss_color and "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.5, 0.3, 0.15)
    if sss > 0 and sss_color and "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = (
            sss_color[0], sss_color[1], sss_color[2], 1.0)
    return mat


def link_mesh_from_bm(name, bm, material, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(material)
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    return obj


def ring_point(R, a, b, zc, u, v, wob=1.0):
    """Point on a tube-ring (ellipse cross-section) plus its outward normal."""
    cu, su = math.cos(u), math.sin(u)
    cv, sv = math.cos(v), math.sin(v)
    rr = R + a * cv * wob
    pos = Vector((rr * cu, rr * su, zc + b * sv * wob))
    # ellipse normal in (radial, z) plane
    nr, nz = cv / a, sv / b
    ln = math.hypot(nr, nz)
    nr, nz = nr / ln, nz / ln
    normal = Vector((nr * cu, nr * su, nz))
    return pos, normal


def build_ring(name, R, a, b, zc, nu, nv, material, jitter=0.0):
    bm = bmesh.new()
    grid = []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        row = []
        for j in range(nv):
            v = 2 * math.pi * j / nv
            wob = 1.0 + jitter * math.sin(5 * u + 1.3) * math.cos(3 * v)
            pos, _ = ring_point(R, a, b, zc, u, v, wob)
            row.append(bm.verts.new(pos))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            v00 = grid[i][j]
            v10 = grid[(i + 1) % nu][j]
            v11 = grid[(i + 1) % nu][(j + 1) % nv]
            v01 = grid[i][(j + 1) % nv]
            bm.faces.new([v00, v10, v11, v01])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return link_mesh_from_bm(name, bm, material)


# ---------- Materials ----------
plate_mat = make_material("PlateWhite", (0.92, 0.92, 0.90), roughness=0.18, coat=0.3)
dough_mat = make_material("DoughBaked", (0.72, 0.42, 0.18), roughness=0.55,
                          sss=0.15, sss_color=(0.9, 0.5, 0.2))
frost_mat = make_material("PinkGlaze", (0.95, 0.42, 0.62), roughness=0.08, coat=1.0)

sprinkle_colors = [
    (0.95, 0.10, 0.12),  # red
    (0.10, 0.45, 0.95),  # blue
    (0.98, 0.85, 0.12),  # yellow
    (0.20, 0.85, 0.30),  # green
    (0.55, 0.15, 0.90),  # purple
    (0.98, 0.98, 0.98),  # white
]
sprinkle_mats = [
    make_material(f"Sprinkle_{i}", c, roughness=0.3, coat=0.2)
    for i, c in enumerate(sprinkle_colors)
]

# ---------- Plate ----------
PLATE_R = 2.4
PLATE_T = 0.14
bm = bmesh.new()
bmesh.ops.create_cone(
    bm, cap_ends=True, cap_tris=False, segments=96,
    radius1=PLATE_R, radius2=PLATE_R, depth=PLATE_T,
    matrix=Matrix.Translation((0, 0, -PLATE_T / 2)))
plate = link_mesh_from_bm("Plate", bm, plate_mat)
bev = plate.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.05
bev.segments = 4
bev.limit_method = 'ANGLE'
sub = plate.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1
sub.render_levels = 2

# ---------- Donut dough ----------
DONUT_R = 1.0
DOUGH_A = 0.38
DOUGH_B = 0.38
DONUT_Z = 0.40
build_ring("DonutDough", DONUT_R, DOUGH_A, DOUGH_B, DONUT_Z, 96, 40, dough_mat)

# ---------- Pink frosting ----------
FROST_A = 0.43
FROST_B = 0.30
FROST_ZC = DONUT_Z + 0.14
build_ring("PinkFrosting", DONUT_R, FROST_A, FROST_B, FROST_ZC, 128, 40,
           frost_mat, jitter=0.04)

# ---------- Sprinkles ----------
SPRINKLE_R = 0.028
SPRINKLE_L = 0.12
N_SPRINKLES = 160

groups = [bmesh.new() for _ in sprinkle_mats]
for _ in range(N_SPRINKLES):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(0.35, 1.95)
    pos, normal = ring_point(DONUT_R, FROST_A, FROST_B, FROST_ZC, u, v)
    pos = pos + normal * 0.005

    align = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    spin = Matrix.Rotation(random.uniform(0, math.pi), 4, 'Z')
    tilt = Matrix.Rotation(random.uniform(-0.25, 0.25), 4, 'X')
    M = Matrix.Translation(pos) @ align @ spin @ tilt

    gi = random.randrange(len(groups))
    bmesh.ops.create_cone(
        groups[gi], cap_ends=True, cap_tris=False, segments=10,
        radius1=SPRINKLE_R, radius2=SPRINKLE_R, depth=SPRINKLE_L, matrix=M)

for i, gbm in enumerate(groups):
    if len(gbm.faces) == 0:
        gbm.free()
        continue
    link_mesh_from_bm(f"Sprinkles_{i}", gbm, sprinkle_mats[i], smooth=False)

# ---------- World ----------
world = bpy.data.worlds.new("StudioWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
bg.inputs["Strength"].default_value = 0.6
bpy.context.scene.world = world

# ---------- Lights ----------
key_data = bpy.data.lights.new("KeyLight", 'AREA')
key_data.energy = 900
key_data.size = 4.0
key_data.color = (1.0, 0.97, 0.93)
key = bpy.data.objects.new("KeyLight", key_data)
collection.objects.link(key)
key.location = (3.5, -3.0, 5.0)
key.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 250
fill_data.size = 5.0
fill_data.color = (0.85, 0.92, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
collection.objects.link(fill)
fill.location = (-4.5, -2.0, 2.5)
fill.rotation_euler = (math.radians(70), 0, math.radians(-60))

rim_data = bpy.data.lights.new("RimLight", 'SPOT')
rim_data.energy = 1500
rim_data.spot_size = math.radians(60)
rim_data.color = (1.0, 0.9, 0.85)
rim = bpy.data.objects.new("RimLight", rim_data)
collection.objects.link(rim)
rim.location = (-2.5, 4.0, 3.5)
target_r = Vector((0, 0, 0.4)) - rim.location
rim.rotation_euler = target_r.to_track_quat('-Z', 'Y').to_euler()

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 58
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 6.0
cam_data.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam_loc = Vector((3.8, -4.6, 3.6))
cam.location = cam_loc
look_target = Vector((0.0, 0.0, 0.35))
direction = look_target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Timeline ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
