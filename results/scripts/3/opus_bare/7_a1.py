import bpy, math
from mathutils import Vector

scene = bpy.context.scene
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

wood = mat("Wood", (0.35, 0.18, 0.08), 0.4)
wood_dark = mat("WoodDark", (0.22, 0.11, 0.05), 0.45)
floor_m = mat("Floor", (0.5, 0.38, 0.25), 0.6)
wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.9)
ceil_m = mat("Ceiling", (0.95, 0.95, 0.95), 0.9)
cushion = mat("Cushion", (0.6, 0.1, 0.1), 0.8)

def box(name, loc, size, m, rot_z=0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.rotation_euler.z = rot_z
    o.data.materials.append(m)
    return o

# Room 5x5x2.8
W, H = 5.0, 2.8
box("Floor", (0, 0, -0.05), (W, W, 0.1), floor_m)
box("Ceiling", (0, 0, H + 0.05), (W, W, 0.1), ceil_m)
box("WallBack", (0, W/2, H/2), (W, 0.1, H), wall_m)
box("WallLeft", (-W/2, 0, H/2), (0.1, W, H), wall_m)
box("WallRight", (W/2, 0, H/2), (0.1, W, H), wall_m)
# baseboards
box("BaseBack", (0, W/2 - 0.06, 0.06), (W, 0.03, 0.12), wood_dark)
box("BaseLeft", (-W/2 + 0.06, 0, 0.06), (0.03, W, 0.12), wood_dark)
box("BaseRight", (W/2 - 0.06, 0, 0.06), (0.03, W, 0.12), wood_dark)

# Table
TH = 0.75
box("TableTop", (0, 0, TH - 0.025), (1.4, 0.9, 0.05), wood)
box("ApronF", (0, -0.4, TH - 0.1), (1.25, 0.03, 0.1), wood_dark)
box("ApronB", (0, 0.4, TH - 0.1), (1.25, 0.03, 0.1), wood_dark)
box("ApronL", (-0.63, 0, TH - 0.1), (0.03, 0.78, 0.1), wood_dark)
box("ApronR", (0.63, 0, TH - 0.1), (0.03, 0.78, 0.1), wood_dark)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg", (sx * 0.62, sy * 0.38, (TH - 0.05) / 2), (0.07, 0.07, TH - 0.05), wood_dark)

# Chair builder
def chair(pos, facing):
    # facing: angle so chair front points toward table
    seat_h = 0.45
    parts = []
    def p(local, size, m):
        c, s = math.cos(facing), math.sin(facing)
        x = local[0] * c - local[1] * s + pos[0]
        y = local[0] * s + local[1] * c + pos[1]
        parts.append(box("ChairPart", (x, y, local[2]), size, m, facing))
    p((0, 0, seat_h), (0.45, 0.45, 0.04), wood)
    p((0, 0, seat_h + 0.035), (0.4, 0.4, 0.03), cushion)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p((sx * 0.2, sy * 0.2, seat_h / 2), (0.04, 0.04, seat_h), wood_dark)
    # backrest at local -y side (away from table)
    for sx in (-1, 1):
        p((sx * 0.2, -0.2, seat_h + 0.25), (0.04, 0.04, 0.5), wood_dark)
    p((0, -0.2, seat_h + 0.45), (0.44, 0.03, 0.1), wood)
    p((0, -0.2, seat_h + 0.25), (0.4, 0.02, 0.05), wood)

# local +y faces table
chair((0, -0.75), 0)
chair((0, 0.75), math.pi)
chair((-1.0, 0), -math.pi / 2)
chair((1.0, 0), math.pi / 2)

# Small vase on table
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.2, location=(0, 0, TH + 0.1))
v = bpy.context.active_object
v.data.materials.append(mat("Vase", (0.2, 0.4, 0.6), 0.2))
bpy.ops.object.shade_smooth()

# Lighting
bpy.ops.object.light_add(type='AREA', location=(0, 0, H - 0.1))
l = bpy.context.active_object
l.data.energy = 400
l.data.size = 1.2
l.data.color = (1.0, 0.92, 0.8)
bpy.ops.object.light_add(type='POINT', location=(-1.5, -1.8, 2.0))
bpy.context.active_object.data.energy = 150
bpy.ops.object.light_add(type='SUN', location=(2, -2, 3))
s = bpy.context.active_object
s.data.energy = 1.0
s.rotation_euler = (math.radians(50), 0, math.radians(30))

world = bpy.data.worlds.new("World") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera (no front wall, view from open side)
bpy.ops.object.camera_add(location=(1.6, -3.4, 1.8))
cam = bpy.context.active_object
cam.data.lens = 24
direction = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
