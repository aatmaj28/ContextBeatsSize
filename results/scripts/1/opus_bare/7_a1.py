import bpy
import math

scene = bpy.context.scene

# Clear any existing objects
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rough
    return m

wood = mat("Wood", (0.35, 0.18, 0.08), 0.45)
wood_dark = mat("WoodDark", (0.2, 0.1, 0.05), 0.5)
floor_m = mat("Floor", (0.45, 0.32, 0.2), 0.6)
wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.9)
ceil_m = mat("Ceiling", (0.95, 0.95, 0.95), 0.9)

def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(m)
    return o

# Room (5 x 5 x 3)
W, D, H = 5.0, 5.0, 3.0
box("Floor", (0, 0, -0.05), (W, D, 0.1), floor_m)
box("Ceiling", (0, 0, H + 0.05), (W, D, 0.1), ceil_m)
box("WallBack", (0, D / 2 + 0.05, H / 2), (W, 0.1, H), wall_m)
box("WallLeft", (-W / 2 - 0.05, 0, H / 2), (0.1, D, H), wall_m)
box("WallRight", (W / 2 + 0.05, 0, H / 2), (0.1, D, H), wall_m)
# Baseboards
box("BaseBack", (0, D / 2 - 0.01, 0.06), (W, 0.03, 0.12), wood_dark)
box("BaseLeft", (-W / 2 + 0.01, 0, 0.06), (0.03, D, 0.12), wood_dark)
box("BaseRight", (W / 2 - 0.01, 0, 0.06), (0.03, D, 0.12), wood_dark)

# Table
TW, TD, TH = 1.4, 0.9, 0.75
box("TableTop", (0, 0, TH - 0.025), (TW, TD, 0.05), wood)
box("Apron1", (0, TD / 2 - 0.06, TH - 0.1), (TW - 0.12, 0.03, 0.1), wood)
box("Apron2", (0, -TD / 2 + 0.06, TH - 0.1), (TW - 0.12, 0.03, 0.1), wood)
box("Apron3", (TW / 2 - 0.06, 0, TH - 0.1), (0.03, TD - 0.12, 0.1), wood)
box("Apron4", (-TW / 2 + 0.06, 0, TH - 0.1), (0.03, TD - 0.12, 0.1), wood)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg", (sx * (TW / 2 - 0.07), sy * (TD / 2 - 0.07), (TH - 0.05) / 2),
            (0.06, 0.06, TH - 0.05), wood)

# Chairs: built facing +Y locally (backrest at -Y), then rotated toward the table
def chair(x, y, yaw):
    parts = []
    S, SH = 0.45, 0.45
    parts.append(box("Seat", (0, 0, SH), (S, S, 0.04), wood))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("ChairLeg", (sx * (S / 2 - 0.03), sy * (S / 2 - 0.03), SH / 2),
                             (0.04, 0.04, SH), wood_dark))
    # Back posts and slats
    for sx in (-1, 1):
        parts.append(box("BackPost", (sx * (S / 2 - 0.03), -S / 2 + 0.03, SH + 0.25),
                         (0.04, 0.04, 0.5), wood_dark))
    for z in (0.62, 0.78, 0.92):
        parts.append(box("Slat", (0, -S / 2 + 0.03, z), (S - 0.06, 0.02, 0.06), wood))
    # Parent all parts to an empty, then position and rotate the whole chair
    bpy.ops.object.empty_add(location=(0, 0, 0))
    e = bpy.context.active_object
    e.name = "Chair"
    for p in parts:
        p.parent = e
    e.location = (x, y, 0)
    e.rotation_euler = (0, 0, yaw)

# Rotation that points local +Y from the chair position toward the origin
def yaw_to_center(x, y):
    return math.atan2(-y, -x) - math.pi / 2

for (x, y) in [(0, 0.8), (0, -0.8), (1.05, 0), (-1.05, 0)]:
    chair(x, y, yaw_to_center(x, y))

# Lighting
bpy.ops.object.light_add(type='AREA', location=(0, 0, H - 0.05))
l = bpy.context.active_object
l.data.energy = 300
l.data.size = 1.5
l.data.color = (1.0, 0.92, 0.8)

bpy.ops.object.light_add(type='POINT', location=(1.8, -1.8, 2.2))
bpy.context.active_object.data.energy = 150

bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
s = bpy.context.active_object
s.data.energy = 1.0
s.rotation_euler = (math.radians(50), 0, math.radians(30))

# Ambient world light
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.3, 0.3, 0.32, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(2.0, -2.2, 1.9))
cam = bpy.context.active_object
cam.data.lens = 24
target = (0, 0.1, 0.5)
dx, dy, dz = target[0] - cam.location.x, target[1] - cam.location.y, target[2] - cam.location.z
cam.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
