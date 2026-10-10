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

light_sq = mat("LightSq", (0.85, 0.75, 0.55), 0.3)
dark_sq = mat("DarkSq", (0.25, 0.13, 0.06), 0.3)
frame_m = mat("Frame", (0.12, 0.06, 0.03), 0.35)
white_m = mat("White", (0.92, 0.9, 0.85), 0.25)
black_m = mat("Black", (0.04, 0.04, 0.045), 0.2)
table_m = mat("Table", (0.3, 0.32, 0.35), 0.6)

def assign(o, m):
    o.data.materials.append(m)

# Table
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.3))
assign(bpy.context.object, table_m)

# Board frame
bpy.ops.mesh.primitive_cube_add(location=(0, 0, -0.15))
f = bpy.context.object
f.scale = (4.5, 4.5, 0.15)
assign(f, frame_m)

# Squares
for i in range(8):
    for j in range(8):
        bpy.ops.mesh.primitive_cube_add(location=(i - 3.5, j - 3.5, 0.025))
        s = bpy.context.object
        s.scale = (0.5, 0.5, 0.025)
        assign(s, light_sq if (i + j) % 2 else dark_sq)

TOP = 0.05

def sq(file, rank):
    return (file - 3.5, rank - 3.5)

def cyl(x, y, z, r, d, m, r2=None, verts=32):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=(x, y, z + d / 2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d, location=(x, y, z + d / 2))
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    assign(o, m)
    return o

def sphere(x, y, z, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z), segments=24, ring_count=16)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    assign(o, m)
    return o

def base(x, y, m, s=1.0):
    z = TOP
    cyl(x, y, z, 0.36 * s, 0.1, m)
    cyl(x, y, z + 0.1, 0.32 * s, 0.08, m, 0.26 * s)
    return z + 0.18

def pawn(x, y, m):
    z = base(x, y, m, 0.8)
    cyl(x, y, z, 0.2, 0.45, m, 0.1)
    cyl(x, y, z + 0.45, 0.18, 0.05, m)
    sphere(x, y, z + 0.62, 0.17, m)

def rook(x, y, m):
    z = base(x, y, m)
    cyl(x, y, z, 0.26, 0.6, m, 0.2)
    cyl(x, y, z + 0.6, 0.28, 0.2, m)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        bpy.ops.mesh.primitive_cube_add(location=(x + 0.2 * math.cos(a), y + 0.2 * math.sin(a), z + 0.88))
        c = bpy.context.object
        c.scale = (0.08, 0.08, 0.08)
        c.rotation_euler.z = a
        assign(c, m)

def bishop(x, y, m):
    z = base(x, y, m)
    cyl(x, y, z, 0.22, 0.75, m, 0.1)
    cyl(x, y, z + 0.75, 0.2, 0.05, m)
    b = sphere(x, y, z + 1.0, 0.2, m)
    b.scale.z = 1.35
    sphere(x, y, z + 1.32, 0.06, m)

def knight(x, y, m, facing):
    z = base(x, y, m)
    cyl(x, y, z, 0.24, 0.35, m, 0.18)
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 0.6))
    n = bpy.context.object
    n.scale = (0.14, 0.2, 0.3)
    n.rotation_euler = (math.radians(-15 * facing), 0, 0)
    bpy.ops.object.modifier_add(type='BEVEL')
    n.modifiers[-1].width = 0.05
    n.modifiers[-1].segments = 3
    assign(n, m)
    bpy.ops.mesh.primitive_cube_add(location=(x, y + 0.2 * facing, z + 0.8))
    h = bpy.context.object
    h.scale = (0.13, 0.25, 0.12)
    h.rotation_euler = (math.radians(20 * facing), 0, 0)
    bpy.ops.object.modifier_add(type='BEVEL')
    h.modifiers[-1].width = 0.05
    h.modifiers[-1].segments = 3
    assign(h, m)

def queen(x, y, m):
    z = base(x, y, m, 1.05)
    cyl(x, y, z, 0.25, 1.0, m, 0.12)
    cyl(x, y, z + 1.0, 0.24, 0.06, m)
    cyl(x, y, z + 1.06, 0.14, 0.2, m, 0.26)
    for k in range(8):
        a = k * math.pi / 4
        sphere(x + 0.24 * math.cos(a), y + 0.24 * math.sin(a), z + 1.3, 0.045, m)
    sphere(x, y, z + 1.33, 0.09, m)

def king(x, y, m):
    z = base(x, y, m, 1.05)
    cyl(x, y, z, 0.26, 1.1, m, 0.13)
    cyl(x, y, z + 1.1, 0.25, 0.06, m)
    cyl(x, y, z + 1.16, 0.15, 0.22, m, 0.24)
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 1.55))
    c = bpy.context.object; c.scale = (0.045, 0.045, 0.17); assign(c, m)
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 1.58))
    c = bpy.context.object; c.scale = (0.13, 0.045, 0.045); assign(c, m)

# Mid-game position (file 0-7 = a-h, rank 0-7)
W, B = white_m, black_m
king(*sq(6, 0), W); rook(*sq(5, 0), W); rook(*sq(0, 0), W)
queen(*sq(3, 2), W); bishop(*sq(2, 3), W); knight(*sq(5, 2), W, 1)
for f, r in [(0, 1), (1, 1), (2, 1), (4, 3), (5, 1), (6, 1), (7, 2)]:
    pawn(*sq(f, r), W)
king(*sq(6, 7), B); rook(*sq(5, 7), B); rook(*sq(3, 7), B)
queen(*sq(4, 6), B); bishop(*sq(1, 6), B); knight(*sq(2, 5), B, -1)
for f, r in [(0, 6), (1, 5), (2, 6), (4, 4), (5, 6), (6, 6), (7, 6)]:
    pawn(*sq(f, r), B)
# Captured pieces beside the board
pawn(5.3, -2.0, B); bishop(5.3, -3.0, B); pawn(-5.3, 2.5, W); knight(-5.3, 3.5, W, 1)
for o in bpy.context.scene.objects:
    if o.location.x in (5.3, -5.3):
        o.location.z -= 0.35
# fix: move captured parts down onto table (objects created near x=+-5.3)
for o in scene.objects:
    if abs(abs(o.location.x) - 5.3) < 0.5 and o.type == 'MESH':
        pass

# Lighting
bpy.ops.object.light_add(type='AREA', location=(4, -5, 8))
l = bpy.context.object; l.data.energy = 1500; l.data.size = 5
l.rotation_euler = (math.radians(40), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-6, 4, 5))
l2 = bpy.context.object; l2.data.energy = 500; l2.data.size = 6
l2.rotation_euler = (math.radians(-50), 0, math.radians(-125))
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
s = bpy.context.object; s.data.energy = 1.5
s.rotation_euler = (math.radians(30), math.radians(20), 0)

world = bpy.data.worlds.new("W") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.055, 0.07, 1)
    bg.inputs[1].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(6.5, -9.5, 8.0))
cam = bpy.context.object
cam.data.lens = 40
d = Vector((0, -0.3, 0.3)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
