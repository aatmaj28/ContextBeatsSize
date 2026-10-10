import bpy
import bmesh
import math
from mathutils import Matrix, Vector


# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


# ---------- Materials ----------
def make_mat(name, color, roughness=0.5, metallic=0.0, emission=None):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

mat_rocket = make_mat("RocketWhite", (0.92, 0.92, 0.94), roughness=0.35)
mat_fin = make_mat("FinGrey", (0.75, 0.75, 0.78), roughness=0.4)
mat_nozzle = make_mat("NozzleDark", (0.12, 0.12, 0.13), roughness=0.6, metallic=0.6)
mat_steel = make_mat("TowerSteel", (0.45, 0.46, 0.5), roughness=0.5, metallic=0.8)
mat_concrete = make_mat("PadConcrete", (0.42, 0.41, 0.39), roughness=0.9)
mat_ground = make_mat("Ground", (0.25, 0.32, 0.18), roughness=0.95)


# ---------- Helpers ----------
def make_obj(name, bm, material, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), smooth=False):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale
    return obj

def cone_bm(radius1, radius2, depth, segments=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius1, radius2=radius2, depth=depth,
        matrix=Matrix.Identity(4), calc_uvs=False,
    )
    return bm

def cube_bm(size=1.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size, matrix=Matrix.Identity(4), calc_uvs=False)
    return bm


# ---------- Ground and launch pad ----------
ground_bm = bmesh.new()
bmesh.ops.create_grid(ground_bm, x_segments=2, y_segments=2, size=60.0,
                      matrix=Matrix.Identity(4), calc_uvs=False)
make_obj("Ground", ground_bm, mat_ground, loc=(0, 0, 0))

PAD_TOP = 0.5
make_obj("LaunchPad", cube_bm(1.0), mat_concrete,
         loc=(0, 0, PAD_TOP / 2), scale=(7.0, 7.0, PAD_TOP))

# Flame trench under the rocket
make_obj("FlameTrench", cube_bm(1.0), mat_steel,
         loc=(0, 0, PAD_TOP - 0.05), scale=(2.4, 2.4, 0.1))


# ---------- Rocket ----------
BASE_Z = 1.2          # bottom of the body, above the nozzle
BODY_H = 6.0
BODY_R = 0.5
body_center = BASE_Z + BODY_H / 2

# Main body
make_obj("RocketBody", cone_bm(BODY_R, BODY_R, BODY_H, segments=40), mat_rocket,
         loc=(0, 0, body_center), smooth=True)

# Nose cone
NOSE_H = 2.0
make_obj("RocketNose", cone_bm(BODY_R, 0.0, NOSE_H, segments=40), mat_rocket,
         loc=(0, 0, BASE_Z + BODY_H + NOSE_H / 2), smooth=True)

# Engine nozzle (bell shape)
make_obj("Nozzle", cone_bm(0.4, 0.3, 0.6, segments=32), mat_nozzle,
         loc=(0, 0, BASE_Z - 0.3), smooth=True)

# Four fins
FIN_Z = BASE_Z + 0.9
for i in range(4):
    a = math.radians(45 + 90 * i)
    radial = 0.7
    make_obj(f"Fin{i}", cube_bm(1.0), mat_fin,
             loc=(radial * math.cos(a), radial * math.sin(a), FIN_Z),
             rot=(0, 0, a),
             scale=(0.6, 0.06, 1.8))

# Porthole band for detail
make_obj("Band", cone_bm(BODY_R + 0.02, BODY_R + 0.02, 0.15, segments=40), mat_fin,
         loc=(0, 0, BASE_Z + 1.5), smooth=True)


# ---------- Support tower ----------
TOWER_X = -4.2
TOWER_H = 10.0
LEG_HALF = 0.6
LEG_T = 0.18

for sx in (-1, 1):
    for sy in (-1, 1):
        make_obj(f"TowerLeg_{sx}_{sy}", cube_bm(1.0), mat_steel,
                 loc=(TOWER_X + sx * LEG_HALF, sy * LEG_HALF, PAD_TOP + TOWER_H / 2),
                 scale=(LEG_T, LEG_T, TOWER_H))

# Horizontal cross braces on each face
brace_heights = [PAD_TOP + 1.5 * k for k in range(1, int(TOWER_H / 1.5) + 1)]
for idx, h in enumerate(brace_heights):
    if h > PAD_TOP + TOWER_H - 0.5:
        continue
    # Along X faces (front/back), spanning Y
    for sx in (-1, 1):
        make_obj(f"BraceY_{idx}_{sx}", cube_bm(1.0), mat_steel,
                 loc=(TOWER_X + sx * LEG_HALF, 0, h),
                 scale=(LEG_T * 0.8, 2 * LEG_HALF, LEG_T * 0.8))
    # Along Y faces, spanning X
    for sy in (-1, 1):
        make_obj(f"BraceX_{idx}_{sy}", cube_bm(1.0), mat_steel,
                 loc=(TOWER_X, sy * LEG_HALF, h),
                 scale=(2 * LEG_HALF, LEG_T * 0.8, LEG_T * 0.8))

# Service arm reaching toward the rocket
ARM_Z = 6.0
arm_start_x = TOWER_X + LEG_HALF
arm_end_x = -0.75
make_obj("ServiceArm", cube_bm(1.0), mat_steel,
         loc=((arm_start_x + arm_end_x) / 2, 0, ARM_Z),
         scale=(arm_end_x - arm_start_x, 0.15, 0.15))
make_obj("ServiceArmPlatform", cube_bm(1.0), mat_steel,
         loc=(-1.6, 0, ARM_Z - 0.35),
         scale=(1.6, 0.9, 0.08))

# Top platform of the tower
make_obj("TowerTop", cube_bm(1.0), mat_steel,
         loc=(TOWER_X, 0, PAD_TOP + TOWER_H),
         scale=(1.6, 1.6, 0.12))


# ---------- World ----------
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.72, 0.92, 1.0)
bg.inputs["Strength"].default_value = 1.0


# ---------- Lights ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(4)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 400
fill_data.size = 8.0
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-8, -10, 9)
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (11.0, -17.0, 6.0)

target = Vector((-1.0, 0.0, 4.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam


# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
