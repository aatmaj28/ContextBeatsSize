import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.4, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    return m

m_light_sq = make_mat("LightSquare", (0.82, 0.68, 0.48), 0.35, coat=0.3)
m_dark_sq = make_mat("DarkSquare", (0.25, 0.13, 0.06), 0.35, coat=0.3)
m_frame = make_mat("Frame", (0.12, 0.06, 0.03), 0.3, coat=0.5)
m_white = make_mat("WhitePiece", (0.92, 0.88, 0.78), 0.25, coat=0.6)
m_black = make_mat("BlackPiece", (0.04, 0.04, 0.045), 0.2, coat=0.8)
m_table = make_mat("Table", (0.3, 0.32, 0.35), 0.8)

def assign(obj, mat):
    obj.data.materials.append(mat)

# ---------- Board ----------
for f in range(8):
    for r in range(8):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(f - 3.5, r - 3.5, -0.05))
        sq = bpy.context.active_object
        sq.scale = (1, 1, 0.1)
        assign(sq, m_light_sq if (f + r) % 2 else m_dark_sq)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.08))
frame = bpy.context.active_object
frame.scale = (9.0, 9.0, 0.16)
assign(frame, m_frame)
bev = frame.modifiers.new("Bevel", "BEVEL")
bev.width = 0.05
bev.segments = 3

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.16))
assign(bpy.context.active_object, m_table)

# ---------- Primitive helpers ----------
def cone(x, y, z, r1, r2, depth, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=r2, depth=depth,
                                    location=(x, y, z + depth / 2), rotation=rot)
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    assign(o, mat)
    return o

def sphere(x, y, z, r, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=(x, y, z))
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.shade_smooth()
    assign(o, mat)
    return o

def box(x, y, z, sx, sy, sz, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z), rotation=rot)
    o = bpy.context.active_object
    o.scale = (sx, sy, sz)
    assign(o, mat)
    return o

def base(x, y, m, r=0.36):
    cone(x, y, 0, r, r * 0.92, 0.08, m)
    cone(x, y, 0.08, r * 0.92, r * 0.7, 0.06, m)

# ---------- Pieces ----------
def pawn(x, y, m, side):
    base(x, y, m, 0.3)
    cone(x, y, 0.14, 0.2, 0.08, 0.35, m)
    cone(x, y, 0.47, 0.14, 0.14, 0.03, m)
    sphere(x, y, 0.6, 0.12, m)

def rook(x, y, m, side):
    base(x, y, m)
    cone(x, y, 0.14, 0.26, 0.2, 0.45, m)
    cone(x, y, 0.59, 0.25, 0.25, 0.17, m)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        box(x + 0.17 * math.cos(a), y + 0.17 * math.sin(a), 0.8, 0.1, 0.1, 0.1, m)

def knight(x, y, m, side):
    base(x, y, m)
    cone(x, y, 0.14, 0.26, 0.18, 0.25, m)
    d = side  # facing direction along y
    box(x, y + 0.02 * d, 0.55, 0.18, 0.22, 0.38, m, rot=(math.radians(-15 * d), 0, 0))
    box(x, y + 0.14 * d, 0.72, 0.17, 0.36, 0.17, m, rot=(math.radians(25 * d), 0, 0))
    box(x, y - 0.06 * d, 0.82, 0.06, 0.06, 0.12, m)

def bishop(x, y, m, side):
    base(x, y, m)
    cone(x, y, 0.14, 0.22, 0.09, 0.55, m)
    cone(x, y, 0.66, 0.16, 0.16, 0.03, m)
    sphere(x, y, 0.84, 0.13, m, scale=(1, 1, 1.4))
    sphere(x, y, 1.03, 0.04, m)

def queen(x, y, m, side):
    base(x, y, m, 0.4)
    cone(x, y, 0.14, 0.27, 0.1, 0.75, m)
    cone(x, y, 0.86, 0.19, 0.19, 0.04, m)
    cone(x, y, 0.9, 0.12, 0.2, 0.15, m)
    sphere(x, y, 1.1, 0.07, m)

def king(x, y, m, side):
    base(x, y, m, 0.4)
    cone(x, y, 0.14, 0.28, 0.11, 0.85, m)
    cone(x, y, 0.96, 0.2, 0.2, 0.04, m)
    cone(x, y, 1.0, 0.13, 0.19, 0.14, m)
    box(x, y, 1.27, 0.06, 0.06, 0.26, m)
    box(x, y, 1.3, 0.18, 0.06, 0.06, m)

def sqpos(s):
    return ord(s[0]) - ord('a') - 3.5, int(s[1]) - 1 - 3.5

white = {"g1": king, "f1": rook, "a1": rook, "e2": queen, "f3": knight, "c4": bishop,
         "e4": pawn, "d3": pawn, "f2": pawn, "g2": pawn, "h2": pawn, "a2": pawn, "b3": pawn}
black = {"g8": king, "f8": rook, "a8": rook, "e7": queen, "c6": knight, "g4": bishop,
         "e5": pawn, "d6": pawn, "f7": pawn, "g7": pawn, "h6": pawn, "a7": pawn, "b7": pawn}

for s, fn in white.items():
    x, y = sqpos(s)
    fn(x, y, m_white, 1)
for s, fn in black.items():
    x, y = sqpos(s)
    fn(x, y, m_black, -1)

# Captured pieces beside the board
cx = 5.2
pawn(cx, -2.0, m_black, -1)
knight(cx, -1.0, m_black, -1)
pawn(-cx, 2.0, m_white, 1)
bishop(-cx, 1.0, m_white, 1)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(35))
sun.data.angle = math.radians(5)

bpy.ops.object.light_add(type='AREA', location=(-6, -4, 7))
area = bpy.context.active_object
area.data.energy = 800
area.data.size = 5
area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(7.5, -10.5, 8.0))
cam = bpy.context.active_object
target = Vector((0, 0.3, 0.3))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 40
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (target - cam.location).length
cam.data.dof.aperture_fstop = 4.0
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
