import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

wood = mat("Wood", (0.35, 0.18, 0.08), 0.45)
wood_dark = mat("WoodDark", (0.2, 0.1, 0.05), 0.5)
floor_m = mat("Floor", (0.5, 0.38, 0.25), 0.6)
wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.9)
ceil_m = mat("Ceiling", (0.95, 0.95, 0.95), 0.9)

def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    return o

# Room 6x6x3
W, H = 6.0, 3.0
box("Floor", (0, 0, -0.05), (W, W, 0.1), floor_m)
box("Ceiling", (0, 0, H + 0.05), (W, W, 0.1), ceil_m)
box("WallN", (0, W / 2, H / 2), (W, 0.1, H), wall_m)
box("WallS", (0, -W / 2, H / 2), (W, 0.1, H), wall_m)
box("WallE", (W / 2, 0, H / 2), (0.1, W, H), wall_m)
box("WallW", (-W / 2, 0, H / 2), (0.1, W, H), wall_m)

# Table
TH = 0.75
box("TableTop", (0, 0, TH - 0.025), (1.4, 0.9, 0.05), wood)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg", (sx * 0.62, sy * 0.38, (TH - 0.05) / 2), (0.06, 0.06, TH - 0.05), wood_dark)
box("ApronX1", (0, 0.38, TH - 0.1), (1.2, 0.03, 0.1), wood_dark)
box("ApronX2", (0, -0.38, TH - 0.1), (1.2, 0.03, 0.1), wood_dark)

# Chair builder: local frame, back toward +y then rotated
def chair(x, y, angle):
    parts = []
    SH = 0.45
    parts.append(box("Seat", (0, 0, SH), (0.45, 0.45, 0.04), wood))
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = SH if sy < 0 else 0.95
            parts.append(box("ChairLeg", (sx * 0.2, sy * 0.2, h / 2), (0.04, 0.04, h), wood_dark))
    parts.append(box("BackRail", (0, 0.2, 0.88), (0.44, 0.03, 0.1), wood))
    parts.append(box("BackRail2", (0, 0.2, 0.68), (0.44, 0.03, 0.06), wood))
    empty = bpy.data.objects.new("Chair", None)
    scene.collection.objects.link(empty)
    for p in parts:
        p.parent = empty
    empty.location = (x, y, 0)
    empty.rotation_euler = (0, 0, angle)

# Chairs face table (back away from table)
chair(0, 0.85, 0)
chair(0, -0.85, math.pi)
chair(1.05, 0, -math.pi / 2)
chair(-1.05, 0, math.pi / 2)

# Lights
bpy.ops.object.light_add(type='AREA', location=(0, 0, H - 0.1))
l = bpy.context.active_object
l.data.energy = 400
l.data.size = 1.5
bpy.ops.object.light_add(type='POINT', location=(2, -2, 2.2))
bpy.context.active_object.data.energy = 150

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera
bpy.ops.object.camera_add(location=(2.6, -2.6, 1.9))
cam = bpy.context.active_object
cam.data.lens = 24
tgt = bpy.data.objects.new("Target", None)
scene.collection.objects.link(tgt)
tgt.location = (0, 0, 0.5)
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
