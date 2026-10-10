import bpy
import bmesh
import math
from mathutils import Vector, Matrix

scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear any default content
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_mat(name, rgb, rough=0.5, metal=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


def make_obj(name, kind, mat, loc, scale=(1.0, 1.0, 1.0), rot=(0.0, 0.0, 0.0),
             r1=1.0, r2=1.0, depth=1.0, segs=40):
    bm = bmesh.new()
    if kind == 'cone':
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                              radius1=r1, radius2=r2, depth=depth,
                              matrix=Matrix.Identity(4), calc_uvs=False)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = (kind == 'cone')
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    obj.scale = Vector(scale)
    obj.rotation_euler = rot
    scene.collection.objects.link(obj)
    return obj


def cylinder(name, mat, loc, radius, height, segs=40):
    return make_obj(name, 'cone', mat, loc, r1=radius, r2=radius,
                    depth=height, segs=segs)


def box(name, mat, loc, size, rot=(0.0, 0.0, 0.0)):
    return make_obj(name, 'box', mat, loc, scale=size, rot=rot)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
white_paint = make_mat("RocketWhite", (0.92, 0.92, 0.94), rough=0.35)
red_band = make_mat("RocketRed", (0.75, 0.08, 0.06), rough=0.4)
dark_metal = make_mat("EngineDark", (0.08, 0.08, 0.09), rough=0.5, metal=0.8)
concrete = make_mat("ConcreteGray", (0.42, 0.42, 0.40), rough=0.9)
ground_mat = make_mat("GroundGrass", (0.18, 0.3, 0.12), rough=1.0)
steel = make_mat("TowerSteel", (0.55, 0.56, 0.6), rough=0.4, metal=0.9)
window_mat = make_mat("RocketWindow", (0.05, 0.1, 0.15), rough=0.1)

# ---------------------------------------------------------------------------
# Ground and launch pad
# ---------------------------------------------------------------------------
box("Ground", ground_mat, (0.0, 0.0, -0.1), (80.0, 80.0, 0.2))
box("LaunchPad", concrete, (0.0, 0.0, 0.5), (8.0, 8.0, 1.0))
# Flame trench opening under the pad center
box("FlameTrench", dark_metal, (0.0, 0.0, 0.98), (2.4, 2.4, 0.04))

# ---------------------------------------------------------------------------
# Rocket (base at z = 1.0, the pad top)
# ---------------------------------------------------------------------------
BASE_Z = 1.0

# Engine bell (flared nozzle)
cylinder_bell = make_obj("EngineBell", 'cone', dark_metal,
                         (0.0, 0.0, BASE_Z + 0.6),
                         r1=0.95, r2=0.6, depth=1.2, segs=40)

# Main body
body_h = 14.0
cylinder("RocketBody", white_paint,
         (0.0, 0.0, BASE_Z + 1.2 + body_h / 2.0), 0.9, body_h)

# Red stripe band
cylinder("RocketBand", red_band,
         (0.0, 0.0, BASE_Z + 10.5), 0.93, 0.7)

# Window ring near the top of the body
cylinder("RocketWindow", window_mat,
         (0.0, 0.0, BASE_Z + 4.0), 0.94, 0.9)

# Nose cone
nose_h = 3.0
make_obj("NoseCone", 'cone', white_paint,
         (0.0, 0.0, BASE_Z + 1.2 + body_h + nose_h / 2.0),
         r1=0.9, r2=0.0, depth=nose_h, segs=40)

# Four fins
fin_z = BASE_Z + 3.0
for i in range(4):
    ang = math.radians(90 * i)
    fx = math.cos(ang) * 1.3
    fy = math.sin(ang) * 1.3
    box(f"Fin_{i}", white_paint, (fx, fy, fin_z), (1.2, 0.08, 2.6),
        rot=(0.0, 0.0, ang))

# ---------------------------------------------------------------------------
# Support tower beside the rocket
# ---------------------------------------------------------------------------
TX = 4.8
TOP_Z = 16.0
tower_h = TOP_Z - BASE_Z
tower_mid = BASE_Z + tower_h / 2.0
half = 1.1
leg_w = 0.18

for i, (dx, dy) in enumerate([(-half, -half), (half, -half),
                              (-half, half), (half, half)]):
    box(f"TowerLeg_{i}", steel, (TX + dx, dy, tower_mid),
        (leg_w, leg_w, tower_h))

# Platforms
for j, z in enumerate([4.0, 8.0, 12.0, 16.0]):
    box(f"Platform_{j}", steel, (TX, 0.0, z), (2.4, 2.4, 0.2))

# Diagonal bracing on the four faces
brace_len = math.sqrt(tower_h ** 2 + (2 * half) ** 2)
ang = math.atan2(2 * half, tower_h)
for k, s in enumerate([1, -1]):
    # front and back faces (plane y = +-half), rotate about Y
    for side, yy in enumerate([-half, half]):
        box(f"BraceY_{k}_{side}", steel, (TX, yy, tower_mid),
            (0.12, 0.12, brace_len), rot=(0.0, s * ang, 0.0))
    # left and right faces (plane x = TX +- half), rotate about X
    for side, xx in enumerate([-half, half]):
        box(f"BraceX_{k}_{side}", steel, (TX + xx, 0.0, tower_mid),
            (0.12, 0.12, brace_len), rot=(s * ang, 0.0, 0.0))

# Umbilical arm reaching from tower toward rocket at z = 12
arm_x0 = 1.0
arm_x1 = TX - 1.1
box("ServiceArm", steel, ((arm_x0 + arm_x1) / 2.0, 0.0, 12.0),
    (arm_x1 - arm_x0, 0.2, 0.25))

# ---------------------------------------------------------------------------
# World background
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.72, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.9

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(2.0)
sun = bpy.data.objects.new("KeySun", sun_data)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 600.0
fill_data.size = 12.0
fill = bpy.data.objects.new("FillArea", fill_data)
fill.location = (-14.0, -12.0, 12.0)
fill.rotation_euler = (math.radians(70), 0.0, math.radians(-45))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("RimArea", 'AREA')
rim_data.energy = 400.0
rim_data.size = 6.0
rim = bpy.data.objects.new("RimArea", rim_data)
rim.location = (-6.0, 14.0, 14.0)
rim.rotation_euler = (math.radians(-60), 0.0, math.radians(160))
scene.collection.objects.link(rim)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50.0
cam_data.clip_end = 500.0
cam = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam)

cam_loc = Vector((20.0, -34.0, 12.0))
target = Vector((2.0, 0.0, 9.5))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
