import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    bpy.data.cameras.remove(cam)


# ---------- Helpers ----------
def make_mat(name, base, rough=0.8, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def add_obj_from_bmesh(name, build_fn):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------- Materials ----------
mat_ground = make_mat("Ground", (0.05, 0.045, 0.04), rough=0.95)
mat_log = make_mat("Log", (0.22, 0.12, 0.06), rough=0.85)
mat_stone = make_mat("Stone", (0.28, 0.27, 0.26), rough=0.9)
mat_ember = make_mat("Ember", (0.2, 0.04, 0.01), rough=0.6,
                     emit=(1.0, 0.25, 0.02), emit_strength=2.0)
mat_flame_outer = make_mat("FlameOuter", (1.0, 0.35, 0.05), rough=0.4,
                           emit=(1.0, 0.4, 0.05), emit_strength=6.0)
mat_flame_mid = make_mat("FlameMid", (1.0, 0.6, 0.1), rough=0.4,
                         emit=(1.0, 0.65, 0.15), emit_strength=8.0)
mat_flame_core = make_mat("FlameCore", (1.0, 0.9, 0.5), rough=0.3,
                          emit=(1.0, 0.92, 0.6), emit_strength=12.0)

# ---------- Ground ----------
ground = add_obj_from_bmesh("Ground", lambda bm: bmesh.ops.create_grid(
    bm, x_segments=2, y_segments=2, size=8.0))
assign(ground, mat_ground)

# ---------- Ember bed ----------
ember_bed = add_obj_from_bmesh("EmberBed", lambda bm: bmesh.ops.create_icosphere(
    bm, subdivisions=1, radius=0.4))
ember_bed.scale = (1.0, 1.0, 0.25)
ember_bed.location = (0, 0, 0.05)
assign(ember_bed, mat_ember)

# ---------- Crossed logs (teepee-style) ----------
def add_log(name, loc, rot_z, tilt_y, length=1.8, radius=0.1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius,
                                        depth=length, location=loc)
    log = bpy.context.active_object
    log.name = name
    log.rotation_euler = (0.0, math.radians(tilt_y), rot_z)
    assign(log, mat_log)
    return log

# Base pair crossing at the center, lying on the ground
add_log("LogA", (0, 0, 0.12), math.radians(0), 90, length=1.8)
add_log("LogB", (0, 0, 0.12), math.radians(90), 90, length=1.8)
# Upper pair leaning on the base
add_log("LogC", (0.0, -0.22, 0.32), math.radians(45), 88, length=1.5, radius=0.09)
add_log("LogD", (0.0, 0.22, 0.32), math.radians(-45), 88, length=1.5, radius=0.09)

# ---------- Ring of stones ----------
stone_count = 11
for i in range(stone_count):
    ang = (i / stone_count) * math.tau + random.uniform(-0.12, 0.12)
    r = 1.15 + random.uniform(-0.08, 0.08)
    x, y = math.cos(ang) * r, math.sin(ang) * r
    s = random.uniform(0.22, 0.34)

    def build_stone(bm, s=s):
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s)
        # jitter verts for a rough low poly look
        for v in bm.verts:
            v.co += Vector((random.uniform(-0.05, 0.05),
                            random.uniform(-0.05, 0.05),
                            random.uniform(-0.05, 0.05)))

    stone = add_obj_from_bmesh(f"Stone_{i}", build_stone)
    stone.location = (x, y, s * 0.45)
    stone.rotation_euler = (random.uniform(0, math.tau),
                            random.uniform(0, math.tau),
                            random.uniform(0, math.tau))
    stone.scale = (1.0, random.uniform(0.8, 1.1), random.uniform(0.6, 0.8))
    assign(stone, mat_stone)

# ---------- Flames (stacked cones) ----------
flame_specs = [
    # (name, location, radius, depth, material, rotation_z)
    ("FlameOuterA", (0.0, 0.0, 0.55), 0.42, 1.2, mat_flame_outer, 0.0),
    ("FlameOuterB", (0.18, -0.12, 0.45), 0.28, 0.9, mat_flame_outer, 0.8),
    ("FlameOuterC", (-0.2, 0.1, 0.42), 0.26, 0.85, mat_flame_outer, 1.6),
    ("FlameMid", (0.0, 0.0, 0.5), 0.26, 0.9, mat_flame_mid, 0.4),
    ("FlameCore", (0.0, 0.0, 0.42), 0.14, 0.6, mat_flame_core, 0.0),
]

flames = []
for name, loc, rad, dep, mat, rz in flame_specs:
    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=rad, radius2=0.0,
                                    depth=dep, location=loc)
    f = bpy.context.active_object
    f.name = name
    f.rotation_euler = (random.uniform(-0.12, 0.12),
                        random.uniform(-0.12, 0.12), rz)
    assign(f, mat)
    flames.append(f)

# Small flying sparks as tiny cones
for i in range(6):
    ang = random.uniform(0, math.tau)
    r = random.uniform(0.1, 0.35)
    z = random.uniform(0.9, 1.5)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.05, radius2=0.0,
                                    depth=0.12,
                                    location=(math.cos(ang) * r,
                                              math.sin(ang) * r, z))
    spark = bpy.context.active_object
    spark.name = f"Spark_{i}"
    assign(spark, mat_flame_mid)
    flames.append(spark)

# ---------- Lighting ----------
# Warm fire point light
fire_light_data = bpy.data.lights.new(name="FireLight", type='POINT')
fire_light_data.color = (1.0, 0.55, 0.22)
fire_light_data.energy = 350.0
fire_light_data.shadow_soft_size = 0.4
fire_light = bpy.data.objects.new("FireLight", fire_light_data)
bpy.context.collection.objects.link(fire_light)
fire_light.location = (0.0, 0.0, 0.9)

# Dim cool moonlight for contrast
moon_data = bpy.data.lights.new(name="Moon", type='SUN')
moon_data.color = (0.45, 0.55, 0.9)
moon_data.energy = 0.6
moon = bpy.data.objects.new("Moon", moon_data)
bpy.context.collection.objects.link(moon)
moon.rotation_euler = (math.radians(55), 0.0, math.radians(-30))

# ---------- World ----------
world = bpy.data.worlds.new("NightWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.008, 0.01, 0.025, 1.0)
bg.inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world

# ---------- Flicker animation ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 48

base_energy = fire_light_data.energy
for f_idx in range(1, 49, 6):
    fire_light_data.energy = base_energy * random.uniform(0.85, 1.15)
    fire_light_data.keyframe_insert(data_path="energy", frame=f_idx)

    for fl in flames[:5]:
        s = random.uniform(0.9, 1.1)
        fl.scale = (s, s, random.uniform(0.92, 1.12))
        fl.keyframe_insert(data_path="scale", frame=f_idx)

fire_light_data.energy = base_energy

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (3.4, -4.6, 2.1)

target = Vector((0.0, 0.0, 0.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
