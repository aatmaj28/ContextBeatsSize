import bpy, math, random
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

m_light = mat("LightSq", (0.85, 0.75, 0.55), 0.35)
m_dark = mat("DarkSq", (0.25, 0.13, 0.06), 0.35)
m_frame = mat("Frame", (0.12, 0.06, 0.03), 0.3)
m_white = mat("WhitePiece", (0.92, 0.9, 0.85), 0.25)
m_black = mat("BlackPiece", (0.03, 0.03, 0.03), 0.2)
m_table = mat("Table", (0.35, 0.22, 0.12), 0.6)

S = 1.0
def sq_pos(f, r):
    return Vector(((f - 3.5) * S, (r - 3.5) * S, 0))

# Table
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.3))
bpy.context.object.data.materials.append(m_table)

# Frame
bpy.ops.mesh.primitive_cube_add(location=(0, 0, -0.15))
fr = bpy.context.object
fr.scale = (4.6, 4.6, 0.15)
fr.data.materials.append(m_frame)

# Squares
for f in range(8):
    for r in range(8):
        p = sq_pos(f, r)
        bpy.ops.mesh.primitive_cube_add(location=(p.x, p.y, 0.025))
        o = bpy.context.object
        o.scale = (S / 2, S / 2, 0.025)
        o.data.materials.append(m_light if (f + r) % 2 else m_dark)

def add(prim, loc, m, **kw):
    getattr(bpy.ops.mesh, prim)(location=loc, **kw)
    o = bpy.context.object
    o.data.materials.append(m)
    if prim in ("primitive_uv_sphere_add", "primitive_cylinder_add", "primitive_cone_add"):
        bpy.ops.object.shade_smooth()
    return o

def base(p, m, rad=0.36):
    add("primitive_cylinder_add", (p.x, p.y, 0.1), m, radius=rad, depth=0.1, vertices=32)
    add("primitive_cylinder_add", (p.x, p.y, 0.18), m, radius=rad * 0.8, depth=0.06, vertices=32)

def pawn(p, m):
    base(p, m, 0.3)
    add("primitive_cone_add", (p.x, p.y, 0.4), m, radius1=0.2, radius2=0.08, depth=0.4, vertices=32)
    add("primitive_uv_sphere_add", (p.x, p.y, 0.68), m, radius=0.15)

def rook(p, m):
    base(p, m)
    add("primitive_cylinder_add", (p.x, p.y, 0.5), m, radius=0.22, depth=0.6, vertices=32)
    add("primitive_cylinder_add", (p.x, p.y, 0.85), m, radius=0.28, depth=0.14, vertices=32)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        c = add("primitive_cube_add", (p.x + 0.2 * math.cos(a), p.y + 0.2 * math.sin(a), 0.98), m, size=0.12)

def knight(p, m, facing):
    base(p, m)
    add("primitive_cylinder_add", (p.x, p.y, 0.45), m, radius=0.2, depth=0.5, vertices=32)
    h = add("primitive_cube_add", (p.x, p.y + 0.1 * facing, 0.8), m, size=0.3)
    h.scale = (0.7, 1.6, 0.9)
    h.rotation_euler = (math.radians(-25 * facing), 0, 0)
    add("primitive_cone_add", (p.x + 0.07, p.y - 0.05 * facing, 1.0), m, radius1=0.05, depth=0.15)
    add("primitive_cone_add", (p.x - 0.07, p.y - 0.05 * facing, 1.0), m, radius1=0.05, depth=0.15)

def bishop(p, m):
    base(p, m)
    add("primitive_cone_add", (p.x, p.y, 0.55), m, radius1=0.24, radius2=0.1, depth=0.7, vertices=32)
    e = add("primitive_uv_sphere_add", (p.x, p.y, 1.0), m, radius=0.17)
    e.scale = (1, 1, 1.35)
    add("primitive_uv_sphere_add", (p.x, p.y, 1.26), m, radius=0.06)

def queen(p, m):
    base(p, m, 0.4)
    add("primitive_cone_add", (p.x, p.y, 0.7), m, radius1=0.28, radius2=0.12, depth=1.0, vertices=32)
    add("primitive_cone_add", (p.x, p.y, 1.28), m, radius1=0.12, radius2=0.26, depth=0.2, vertices=32)
    for i in range(8):
        a = i * math.pi / 4
        add("primitive_uv_sphere_add", (p.x + 0.22 * math.cos(a), p.y + 0.22 * math.sin(a), 1.4), m, radius=0.045)
    add("primitive_uv_sphere_add", (p.x, p.y, 1.45), m, radius=0.09)

def king(p, m):
    base(p, m, 0.4)
    add("primitive_cone_add", (p.x, p.y, 0.75), m, radius1=0.29, radius2=0.13, depth=1.1, vertices=32)
    add("primitive_cone_add", (p.x, p.y, 1.38), m, radius1=0.13, radius2=0.24, depth=0.18, vertices=32)
    c = add("primitive_cube_add", (p.x, p.y, 1.65), m, size=1)
    c.scale = (0.07, 0.07, 0.35)
    c = add("primitive_cube_add", (p.x, p.y, 1.7), m, size=1)
    c.scale = (0.24, 0.07, 0.07)

# Mid-game position
W, B = m_white, m_black
for f, r in [(0, 1), (1, 1), (2, 2), (4, 3), (5, 1), (6, 2), (7, 1)]:
    pawn(sq_pos(f, r), W)
for f, r in [(0, 6), (1, 5), (3, 4), (4, 4), (5, 6), (6, 6), (7, 5)]:
    pawn(sq_pos(f, r), B)
rook(sq_pos(0, 0), W); rook(sq_pos(5, 0), W)
rook(sq_pos(0, 7), B); rook(sq_pos(4, 7), B)
knight(sq_pos(5, 2), W, 1); knight(sq_pos(2, 5), B, -1)
bishop(sq_pos(2, 3), W); bishop(sq_pos(6, 5), B)
queen(sq_pos(3, 2), W); queen(sq_pos(3, 6), B)
king(sq_pos(6, 0), W); king(sq_pos(6, 7), B)
# Captured pieces beside board
pawn(Vector((5.3, -2.0, -0.15)), B)
p = Vector((5.3, -1.0, -0.15)); bishop(p, B)
for o in bpy.context.scene.objects:
    pass
pawn(Vector((-5.3, 2.0, -0.15)), W)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(4, -5, 8))
k = bpy.context.object; k.data.energy = 1500; k.data.size = 5
k.rotation_euler = (math.radians(35), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-6, 4, 5))
f = bpy.context.object; f.data.energy = 400; f.data.size = 6
f.rotation_euler = (math.radians(-45), math.radians(-40), 0)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
s = bpy.context.object; s.data.energy = 1.5
s.rotation_euler = (math.radians(40), math.radians(10), math.radians(60))

world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera
bpy.ops.object.camera_add(location=(7.5, -9.5, 7.5))
cam = bpy.context.object
cam.data.lens = 40
d = Vector((0, 0, 0.3)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1; scene.frame_end = 1
