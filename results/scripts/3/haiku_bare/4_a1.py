import bpy
import math
from mathutils import Vector

# ---------- Clean up default scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def add_box(name, loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return assign(obj, mat)


def add_cylinder(name, loc, radius, depth, mat, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


def add_cone(name, loc, r1, r2, depth, mat, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=r1, radius2=r2, depth=depth,
        location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


def add_sphere(name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=32, ring_count=16)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


# ---------- Materials ----------
mat_ground = make_material("Ground", (0.22, 0.22, 0.21), roughness=0.95)
mat_concrete = make_material("Concrete", (0.45, 0.45, 0.43), roughness=0.85)
mat_white = make_material("RocketWhite", (0.92, 0.92, 0.94), roughness=0.35, metallic=0.0)
mat_red = make_material("RocketRed", (0.75, 0.08, 0.06), roughness=0.4)
mat_dark = make_material("EngineDark", (0.05, 0.05, 0.06), roughness=0.6, metallic=0.8)
mat_steel = make_material("TowerSteel", (0.55, 0.56, 0.58), roughness=0.4, metallic=0.9)
mat_window = make_material("Window", (0.05, 0.12, 0.2), roughness=0.1)
mat_hazard = make_material("Hazard", (0.9, 0.6, 0.05), roughness=0.5)

# ---------- Ground ----------
add_box("Ground", (0, 0, -0.6), (120, 120, 0.2), mat_ground)

# ---------- Launch pad ----------
add_box("PadBase", (0, 0, -0.3), (7.0, 7.0, 0.6), mat_concrete)
add_box("PadDeck", (0, 0, 0.05), (6.0, 6.0, 0.1), mat_steel)
# Flame trench under rocket
add_box("FlameTrench", (0, 0, -0.45), (2.4, 2.4, 0.3), mat_dark)
# Hazard stripes at pad edges
for i, (x, y, sx, sy) in enumerate([
    (0, 3.02, 6.0, 0.1), (0, -3.02, 6.0, 0.1),
    (3.02, 0, 0.1, 6.0), (-3.02, 0, 0.1, 6.0)
]):
    add_box(f"Hazard{i}", (x, y, 0.11), (sx, sy, 0.02), mat_hazard)

# ---------- Rocket ----------
ROCKET_X, ROCKET_Y = 0.0, 0.0
body_r = 0.6

# Engine bell
add_cone("EngineBell", (ROCKET_X, ROCKET_Y, 0.55), 0.45, 0.6, 0.9, mat_dark, rot=(math.pi, 0, 0))
# Main body
add_cylinder("RocketBody", (ROCKET_X, ROCKET_Y, 5.2), body_r, 8.4, mat_white)
# Lower red band
add_cylinder("RedBand", (ROCKET_X, ROCKET_Y, 1.8), body_r * 1.02, 0.8, mat_red)
# Nose cone
add_cone("NoseCone", (ROCKET_X, ROCKET_Y, 10.0), body_r, 0.0, 2.4, mat_white)
# Nose tip accent
add_sphere("NoseTip", (ROCKET_X, ROCKET_Y, 11.2), 0.07, mat_red)
# Window ring near top
for k in range(4):
    a = k * math.pi / 2
    x = ROCKET_X + math.cos(a) * (body_r + 0.01)
    y = ROCKET_Y + math.sin(a) * (body_r + 0.01)
    add_box(f"Window{k}", (x, y, 7.4), (0.02, 0.22, 0.22), mat_window,
            rot=(0, 0, a))

# Fins (4 around base)
for k in range(4):
    a = k * math.pi / 2
    fx = ROCKET_X + math.cos(a) * (body_r + 0.45)
    fy = ROCKET_Y + math.sin(a) * (body_r + 0.45)
    add_box(f"Fin{k}", (fx, fy, 1.4), (0.9, 0.08, 2.2), mat_red, rot=(0, 0, a))

# Umbilical / small details
add_cylinder("Umbilical", (ROCKET_X + 0.9, ROCKET_Y - 0.4, 4.0), 0.08, 3.0, mat_dark)

# ---------- Support tower ----------
TX, TY = 3.6, -1.6
leg_h = 13.0
half = 0.7
legs = [(TX + sx * half, TY + sy * half) for sx in (-1, 1) for sy in (-1, 1)]
for i, (lx, ly) in enumerate(legs):
    add_cylinder(f"TowerLeg{i}", (lx, ly, leg_h / 2), 0.07, leg_h, mat_steel, verts=12)

# Horizontal braces
levels = [1.5, 4.0, 6.5, 9.0, 11.5]
for li, z in enumerate(levels):
    # X-side and Y-side frames
    add_box(f"BraceX_{li}a", (TX, TY - half, z), (2 * half, 0.05, 0.05), mat_steel)
    add_box(f"BraceX_{li}b", (TX, TY + half, z), (2 * half, 0.05, 0.05), mat_steel)
    add_box(f"BraceY_{li}a", (TX - half, TY, z), (0.05, 2 * half, 0.05), mat_steel)
    add_box(f"BraceY_{li}b", (TX + half, TY, z), (0.05, 2 * half, 0.05), mat_steel)

# Diagonal bracing on the rocket-facing side
for i in range(len(levels) - 1):
    z0, z1 = levels[i], levels[i + 1]
    zc = (z0 + z1) / 2
    dz = z1 - z0
    length = math.hypot(2 * half, dz)
    ang = math.atan2(dz, 2 * half)
    add_box(f"Diag{i}", (TX, TY + half, zc), (length, 0.04, 0.04), mat_steel,
            rot=(0, -ang, 0))

# Service platform arm reaching toward rocket
add_box("ServiceDeck", (TX - 1.8, TY, 9.0), (3.6, 1.6, 0.1), mat_steel)
add_box("ServiceRail", (TX - 1.8, TY + 0.8, 9.6), (3.6, 0.04, 0.6), mat_steel)
add_box("ServiceRailEnd", (TX - 3.6, TY, 9.6), (0.04, 1.6, 0.6), mat_steel)
add_box("ArmHolder", (TX - 1.2, TY, 9.0), (0.2, 0.2, 0.2), mat_hazard)

# Tower top cap
add_box("TowerCap", (TX, TY, leg_h + 0.05), (1.6, 1.6, 0.1), mat_steel)

# ---------- World ----------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Lights ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 4.0
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-12, 10, 8))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 600
fill.data.size = 8
fill.rotation_euler = (math.radians(70), 0, math.radians(-40))

bpy.ops.object.light_add(type='AREA', location=(6, -12, 10))
rim = bpy.context.active_object
rim.name = "RimArea"
rim.data.energy = 400
rim.data.size = 6
rim.rotation_euler = (math.radians(60), 0, math.radians(160))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((-17.0, -26.0, 7.0))
target = Vector((1.0, -0.5, 5.5))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
