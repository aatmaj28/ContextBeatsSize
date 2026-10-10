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
chair_wood = mat("ChairWood", (0.25, 0.13, 0.06), 0.5)
seat_mat = mat("Seat", (0.5, 0.1, 0.08), 0.8)
floor_mat = mat("Floor", (0.55, 0.42, 0.3), 0.6)
wall_mat = mat("Wall", (0.85, 0.82, 0.75), 0.9)

def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    return o

# Room: floor, three walls, ceiling
R = 5.0
H = 3.0
box("Floor", (0, 0, -0.05), (R, R, 0.1), floor_mat)
box("WallBack", (0, R / 2, H / 2), (R, 0.1, H), wall_mat)
box("WallLeft", (-R / 2, 0, H / 2), (0.1, R, H), wall_mat)
box("WallRight", (R / 2, 0, H / 2), (0.1, R, H), wall_mat)
box("Ceiling", (0, 0, H + 0.05), (R, R, 0.1), wall_mat)

# Table
TH = 0.75
box("TableTop", (0, 0, TH - 0.025), (1.4, 0.9, 0.05), wood)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg", (sx * 0.63, sy * 0.38, (TH - 0.05) / 2), (0.06, 0.06, TH - 0.05), wood)

# Chair (built facing +Y local; back on -Y side)
def chair(x, y, angle):
    parts = []
    SH = 0.45
    parts.append(box("Seat", (0, 0, SH), (0.45, 0.45, 0.05), seat_mat))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("ChairLeg", (sx * 0.2, sy * 0.2, (SH - 0.025) / 2), (0.04, 0.04, SH - 0.025), chair_wood))
    for sx in (-1, 1):
        parts.append(box("BackPost", (sx * 0.2, -0.2, SH + 0.25), (0.04, 0.04, 0.5), chair_wood))
    parts.append(box("BackRest", (0, -0.2, SH + 0.42), (0.44, 0.03, 0.15), chair_wood))
    parts.append(box("BackSlat", (0, -0.2, SH + 0.2), (0.44, 0.03, 0.06), chair_wood))

    empty = bpy.data.objects.new("Chair", None)
    scene.collection.objects.link(empty)
    for p in parts:
        p.parent = empty
    empty.location = (x, y, 0)
    empty.rotation_euler = (0, 0, angle)

# Front of chair faces the table
chair(0, -0.75, 0)
chair(0, 0.75, math.pi)
chair(-1.0, 0, -math.pi / 2)
chair(1.0, 0, math.pi / 2)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(0, 0, H - 0.1))
ceiling_light = bpy.context.active_object
ceiling_light.data.energy = 300
ceiling_light.data.size = 1.5

bpy.ops.object.light_add(type='POINT', location=(1.5, -1.8, 2.0))
bpy.context.active_object.data.energy = 150

bpy.ops.object.light_add(type='SUN', location=(0, 0, 5), rotation=(0.6, 0, 0.5))
bpy.context.active_object.data.energy = 1.0

# World (dim ambient)
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera, aimed at the table with a Track To constraint
bpy.ops.object.camera_add(location=(2.0, -2.3, 1.9))
cam = bpy.context.active_object
cam.data.lens = 24

target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0.5)

con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'

scene.camera = cam
