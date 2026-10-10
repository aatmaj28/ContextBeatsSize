import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clear default scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# ---------- Helpers ----------
def make_mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


def assign(obj, mat):
    obj.data.materials.append(mat)


def cyl(loc, radius, depth, mat, name, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = rot
    assign(o, mat)
    return o


def cone(loc, r1, r2, depth, mat, name, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = rot
    assign(o, mat)
    return o


def box(loc, size, mat, name, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.rotation_euler = rot
    assign(o, mat)
    return o


def bar(p1, p2, radius, mat, name):
    a = Vector(p1)
    b = Vector(p2)
    d = b - a
    L = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=L, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    assign(o, mat)
    return o


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


# ---------- Materials ----------
mat_white = make_mat("WhitePaint", (0.92, 0.92, 0.93), rough=0.35)
mat_red = make_mat("RedStripe", (0.75, 0.08, 0.05), rough=0.4)
mat_dark = make_mat("EngineDark", (0.08, 0.08, 0.09), rough=0.6, metal=0.4)
mat_steel = make_mat("TowerSteel", (0.45, 0.46, 0.5), rough=0.5, metal=0.8)
mat_concrete = make_mat("PadConcrete", (0.36, 0.36, 0.35), rough=0.9)
mat_ground = make_mat("Ground", (0.22, 0.27, 0.16), rough=1.0)

# ---------- Ground and launch pad ----------
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
ground = bpy.context.object
ground.name = "Ground"
assign(ground, mat_ground)

PAD_TOP = 0.6
box((0, 0, PAD_TOP / 2), (7, 7, PAD_TOP), mat_concrete, "LaunchPad")
# Flame trench under the rocket
box((0, 0, PAD_TOP - 0.05), (2.2, 2.2, 0.1), mat_dark, "FlameTrench")

# ---------- Rocket ----------
BODY_R = 0.6
BODY_BOT = 1.4
BODY_H = 9.0
BODY_TOP = BODY_BOT + BODY_H

body = cyl((0, 0, BODY_BOT + BODY_H / 2), BODY_R, BODY_H, mat_white, "RocketBody")
smooth(body)

nose = cone((0, 0, BODY_TOP + 1.1), BODY_R, 0.0, 2.2, mat_white, "RocketNose")
smooth(nose)

# Red band near the lower body
cyl((0, 0, BODY_BOT + 2.6), BODY_R + 0.01, 0.5, mat_red, "RedBand")

# Engine bell (wide at top, narrow at bottom)
bell = cone((0, 0, PAD_TOP + 0.4), 0.3, 0.45, 0.8, mat_dark, "EngineBell")
smooth(bell)

# Four fins
FIN_CENTER_Z = BODY_BOT + 0.9
for i in range(4):
    a = math.radians(45 + 90 * i)
    x = 0.8 * math.cos(a)
    y = 0.8 * math.sin(a)
    box((x, y, FIN_CENTER_Z), (0.5, 0.05, 1.3), mat_white, f"Fin_{i}", rot=(0, 0, a))

# Small window ring
for i in range(6):
    a = math.radians(30 * i)
    x = (BODY_R + 0.01) * math.cos(a)
    y = (BODY_R + 0.01) * math.sin(a)
    cyl((x, y, BODY_BOT + 6.5), 0.09, 0.02, mat_dark, f"Window_{i}",
        rot=(math.radians(90), 0, a))

# ---------- Support tower ----------
TX, TY = -3.2, 0.0
HALF = 0.6
TOP_Z = 11.0
legs = [(TX + sx * HALF, TY + sy * HALF) for sx in (-1, 1) for sy in (-1, 1)]

for idx, (lx, ly) in enumerate(legs):
    bar((lx, ly, PAD_TOP), (lx, ly, TOP_Z), 0.07, mat_steel, f"TowerLeg_{idx}")

levels = [PAD_TOP + 1.2, 4.5, 7.5, TOP_Z]
for li, z in enumerate(levels):
    # Horizontal ring braces
    corners = [(TX - HALF, TY - HALF), (TX + HALF, TY - HALF),
               (TX + HALF, TY + HALF), (TX - HALF, TY + HALF)]
    for ci in range(4):
        p1 = corners[ci]
        p2 = corners[(ci + 1) % 4]
        bar((p1[0], p1[1], z), (p2[0], p2[1], z), 0.04, mat_steel,
            f"Brace_{li}_{ci}")
    # Diagonal braces on each face up to next level
    if li < len(levels) - 1:
        z_next = levels[li + 1]
        for ci in range(4):
            p1 = corners[ci]
            p2 = corners[(ci + 1) % 4]
            bar((p1[0], p1[1], z), (p2[0], p2[1], z_next), 0.03, mat_steel,
                f"Diag_{li}_{ci}")

# Service platform near the rocket
box((TX + 1.4, TY, 8.6), (2.6, 1.8, 0.12), mat_steel, "ServicePlatform")
# Railings
for sy in (-1, 1):
    bar((TX + 0.1, TY + sy * 0.9, 8.6), (TX + 2.7, TY + sy * 0.9, 8.6),
        0.03, mat_steel, f"Rail_{sy}")
    bar((TX + 0.1, TY + sy * 0.9, 8.6), (TX + 0.1, TY + sy * 0.9, 9.4),
        0.03, mat_steel, f"RailPost_{sy}")

# Umbilical arm reaching toward the rocket
bar((TX + 1.4, TY, 7.2), (-BODY_R - 0.05, 0.0, 7.2), 0.06, mat_steel, "UmbilicalArm")
box((-BODY_R - 0.15, 0.0, 7.2), (0.2, 0.2, 0.2), mat_dark, "ArmClamp")

# ---------- World ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.68, 0.92, 1.0)
bg.inputs["Strength"].default_value = 0.9

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))

fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 900
fill_data.size = 10
fill = bpy.data.objects.new("FillArea", fill_data)
scene.collection.objects.link(fill)
fill.location = (-12, -10, 8)
fill.rotation_euler = (math.radians(70), 0, math.radians(-50))

rim_data = bpy.data.lights.new("RimArea", 'AREA')
rim_data.energy = 1200
rim_data.size = 4
rim = bpy.data.objects.new("RimArea", rim_data)
scene.collection.objects.link(rim)
rim.location = (6, 12, 12)
rim.rotation_euler = (math.radians(-130), 0, math.radians(20))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50
cam = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam)
cam.location = (13.0, -19.0, 7.0)

target = Vector((-0.8, 0.0, 6.0))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------- Frame range ----------
scene.frame_start = 1
scene.frame_end = 1
