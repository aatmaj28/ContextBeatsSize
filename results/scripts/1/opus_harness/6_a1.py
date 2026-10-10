import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.4, spec=0.5, coat=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        try:
            bsdf.inputs["Coat Weight"].default_value = coat
        except Exception:
            pass
    return m

mat_light_sq = make_mat("LightSquare", (0.85, 0.72, 0.52), 0.35, coat=0.3)
mat_dark_sq = make_mat("DarkSquare", (0.28, 0.14, 0.06), 0.35, coat=0.3)
mat_frame = make_mat("Frame", (0.15, 0.07, 0.03), 0.3, coat=0.5)
mat_white = make_mat("WhitePieces", (0.92, 0.88, 0.78), 0.25, coat=0.4)
mat_black = make_mat("BlackPieces", (0.03, 0.03, 0.035), 0.2, coat=0.6)
mat_table = make_mat("Table", (0.12, 0.13, 0.15), 0.7)

# ---------- Primitive helpers ----------
def finish(obj, mat, smooth=False):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def cyl(r, depth, loc, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=depth, location=loc)
    return finish(bpy.context.active_object, mat)

def cone(r1, r2, depth, loc, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=r2, depth=depth, location=loc)
    return finish(bpy.context.active_object, mat)

def sphere(r, loc, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    return finish(o, mat, True)

def torus(R, r, loc, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc,
                                     major_segments=40, minor_segments=12)
    return finish(bpy.context.active_object, mat, True)

def box(loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return finish(o, mat)

# ---------- Board ----------
for f in range(8):
    for r in range(8):
        mat = mat_dark_sq if (f + r) % 2 == 0 else mat_light_sq
        box((f - 3.5, r - 3.5, -0.02), (1, 1, 0.04), mat)

box((0, 0, -0.2), (9.0, 9.0, 0.36), mat_frame)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.38))
finish(bpy.context.active_object, mat_table)

# ---------- Pieces ----------
def square_pos(sq):
    f = ord(sq[0]) - 97
    r = int(sq[1]) - 1
    return f - 3.5, r - 3.5

def base(x, y, mat, s=1.0):
    cyl(0.36 * s, 0.08, (x, y, 0.04), mat)
    torus(0.29 * s, 0.05 * s, (x, y, 0.1), mat)

def pawn(x, y, mat, side):
    base(x, y, mat, 0.85)
    cone(0.22, 0.09, 0.4, (x, y, 0.32), mat)
    torus(0.12, 0.03, (x, y, 0.52), mat)
    sphere(0.15, (x, y, 0.66), mat)

def rook(x, y, mat, side):
    base(x, y, mat)
    cone(0.27, 0.2, 0.55, (x, y, 0.38), mat)
    cyl(0.26, 0.18, (x, y, 0.74), mat)
    for i in range(5):
        a = i * 2 * math.pi / 5
        box((x + 0.19 * math.cos(a), y + 0.19 * math.sin(a), 0.88),
            (0.11, 0.11, 0.12), mat, rot=(0, 0, a))

def knight(x, y, mat, side):
    base(x, y, mat)
    cone(0.27, 0.18, 0.35, (x, y, 0.28), mat)
    d = 1 if side == "w" else -1
    box((x, y, 0.6), (0.24, 0.3, 0.5), mat, rot=(math.radians(-15 * d), 0, 0))
    box((x, y + 0.17 * d, 0.76), (0.2, 0.42, 0.2), mat, rot=(math.radians(25 * d), 0, 0))
    cone(0.06, 0.0, 0.16, (x + 0.07, y - 0.02 * d, 0.92), mat)
    cone(0.06, 0.0, 0.16, (x - 0.07, y - 0.02 * d, 0.92), mat)

def bishop(x, y, mat, side):
    base(x, y, mat)
    cone(0.25, 0.1, 0.6, (x, y, 0.4), mat)
    torus(0.13, 0.035, (x, y, 0.72), mat)
    sphere(0.16, (x, y, 0.9), mat, scale=(1, 1, 1.35))
    sphere(0.05, (x, y, 1.15), mat)

def queen(x, y, mat, side):
    base(x, y, mat, 1.05)
    cone(0.28, 0.11, 0.85, (x, y, 0.52), mat)
    torus(0.15, 0.04, (x, y, 0.95), mat)
    cone(0.12, 0.24, 0.25, (x, y, 1.1), mat)
    for i in range(8):
        a = i * 2 * math.pi / 8
        sphere(0.04, (x + 0.22 * math.cos(a), y + 0.22 * math.sin(a), 1.25), mat)
    sphere(0.08, (x, y, 1.26), mat)

def king(x, y, mat, side):
    base(x, y, mat, 1.05)
    cone(0.28, 0.12, 0.95, (x, y, 0.57), mat)
    torus(0.16, 0.04, (x, y, 1.05), mat)
    cone(0.13, 0.22, 0.22, (x, y, 1.18), mat)
    cyl(0.22, 0.05, (x, y, 1.31), mat)
    box((x, y, 1.48), (0.07, 0.07, 0.3), mat)
    box((x, y, 1.5), (0.22, 0.07, 0.07), mat)

builders = {"P": pawn, "R": rook, "N": knight, "B": bishop, "Q": queen, "K": king}

position = [
    # White
    ("w", "K", "g1"), ("w", "R", "f1"), ("w", "R", "a1"), ("w", "Q", "e2"),
    ("w", "B", "c4"), ("w", "N", "f3"),
    ("w", "P", "a2"), ("w", "P", "b2"), ("w", "P", "c3"), ("w", "P", "d4"),
    ("w", "P", "f2"), ("w", "P", "g2"), ("w", "P", "h3"),
    # Black
    ("b", "K", "g8"), ("b", "R", "f8"), ("b", "R", "a8"), ("b", "Q", "d7"),
    ("b", "B", "e6"), ("b", "N", "c6"),
    ("b", "P", "a6"), ("b", "P", "b7"), ("b", "P", "d5"),
    ("b", "P", "f7"), ("b", "P", "g7"), ("b", "P", "h6"),
]

for side, kind, sq in position:
    x, y = square_pos(sq)
    builders[kind](x, y, mat_white if side == "w" else mat_black, side)

# Captured pieces beside the board
pawn(5.2, -2.0, mat_black, "b")
knight(5.3, -3.0, mat_black, "b")
pawn(-5.2, 2.5, mat_white, "w")

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.angle = math.radians(5)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-6, -4, 7))
area = bpy.context.active_object
area.data.energy = 1500
area.data.size = 6
area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.light_add(type='AREA', location=(4, 8, 5))
rim = bpy.context.active_object
rim.data.energy = 600
rim.data.size = 4
rim.rotation_euler = (Vector((0, 0, 0)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.055, 0.07, 1)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(7.5, -10.5, 8.5))
cam = bpy.context.active_object
target = Vector((0, 0, 0.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 42
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (target - cam.location).length
cam.data.dof.aperture_fstop = 4.0
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass
scene.frame_start = 1
scene.frame_end = 1
