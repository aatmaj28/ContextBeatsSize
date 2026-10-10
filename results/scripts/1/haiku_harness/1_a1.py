import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


# ---------- Helpers ----------
def make_mat(name, color, roughness=0.8, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def rot_to(direction):
    d = direction.normalized()
    return Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()


def add_cone(bm, base, direction, r1, r2, depth, segs=7):
    """Cone/cylinder with its base at 'base' pointing along 'direction'."""
    d = direction.normalized()
    center = base + d * (depth * 0.5)
    M = Matrix.Translation(center) @ rot_to(d)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r1, radius2=r2, depth=depth, matrix=M, calc_uvs=False)


def add_log(bm, center, yaw_deg, pitch_deg, radius=0.085, length=1.5):
    y = math.radians(yaw_deg)
    p = math.radians(pitch_deg)
    d = Vector((math.cos(y) * math.cos(p), math.sin(y) * math.cos(p), math.sin(p)))
    base = center - d * (length * 0.5)
    add_cone(bm, base, d, radius, radius, length, segs=8)


def add_blob(bm, center, radius, scale, yaw, jitter=0.02):
    M = (Matrix.Translation(center)
         @ Matrix.Rotation(yaw, 4, 'Z')
         @ Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1.0))))
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius, matrix=M, calc_uvs=False)
    for v in res["verts"]:
        v.co += Vector((random.uniform(-jitter, jitter),
                        random.uniform(-jitter, jitter),
                        random.uniform(-jitter, jitter)))


def to_object(name, bm, mat, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    scene.collection.objects.link(ob)
    return ob


# ---------- Materials ----------
bark_mat = make_mat("Bark", (0.20, 0.11, 0.06, 1), 0.9)
stone_mat = make_mat("Stone", (0.30, 0.29, 0.28, 1), 0.95)
ground_mat = make_mat("Ground", (0.06, 0.05, 0.04, 1), 1.0)
flame_out_mat = make_mat("FlameOrange", (1.0, 0.35, 0.05, 1), 0.5,
                         emission=(1.0, 0.35, 0.05, 1), strength=6.0)
flame_in_mat = make_mat("FlameYellow", (1.0, 0.8, 0.2, 1), 0.5,
                        emission=(1.0, 0.8, 0.25, 1), strength=12.0)
ember_mat = make_mat("Ember", (0.6, 0.1, 0.02, 1), 0.7,
                     emission=(1.0, 0.2, 0.03, 1), strength=3.0)

# ---------- Ground ----------
bm = bmesh.new()
res = bmesh.ops.create_grid(bm, x_segments=10, y_segments=10, size=4.0)
for v in res["verts"]:
    v.co.z += random.uniform(-0.03, 0.03) * (1 if abs(v.co.x) + abs(v.co.y) > 0.5 else 0.3)
to_object("Ground", bm, ground_mat)

# ---------- Logs (crossed, leaning) ----------
bm = bmesh.new()
add_log(bm, Vector((0.0, 0.0, 0.085)), 20, 0)
add_log(bm, Vector((0.02, 0.0, 0.20)), -55, 0)
add_log(bm, Vector((0.0, 0.0, 0.30)), 60, 22, radius=0.075, length=1.3)
add_log(bm, Vector((-0.05, 0.02, 0.24)), 130, 8, radius=0.07, length=1.1)
to_object("Logs", bm, bark_mat)

# ---------- Stone ring ----------
bm = bmesh.new()
count = 11
ring_r = 1.15
for i in range(count):
    ang = i / count * math.tau + random.uniform(-0.2, 0.2)
    r = random.uniform(0.17, 0.27)
    pos = Vector((math.cos(ang) * ring_r, math.sin(ang) * ring_r, r * 0.35))
    scale = (random.uniform(1.0, 1.35), random.uniform(0.9, 1.2), random.uniform(0.55, 0.75))
    add_blob(bm, pos, r, scale, random.uniform(0, math.tau))
to_object("Stones", bm, stone_mat)

# ---------- Outer flames (orange cones) ----------
bm = bmesh.new()
outer_count = 7
for i in range(outer_count):
    a = i / outer_count * math.tau + random.uniform(-0.25, 0.25)
    off = random.uniform(0.04, 0.12)
    base = Vector((math.cos(a) * off, math.sin(a) * off, 0.0))
    tilt = math.radians(random.uniform(8, 18))
    d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
    h = random.uniform(0.55, 0.9)
    r = random.uniform(0.17, 0.25)
    add_cone(bm, base, d, r, 0.01, h, segs=6)
flames_outer = to_object("FlamesOuter", bm, flame_out_mat, loc=(0, 0, 0.1))

# ---------- Inner flames (yellow cones) and ember core ----------
bm = bmesh.new()
inner_count = 4
for i in range(inner_count):
    a = i / inner_count * math.tau + random.uniform(-0.3, 0.3)
    base = Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.0))
    tilt = math.radians(random.uniform(4, 10))
    d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
    h = random.uniform(0.4, 0.6)
    add_cone(bm, base, d, random.uniform(0.09, 0.13), 0.01, h, segs=6)
flames_inner = to_object("FlamesInner", bm, flame_in_mat, loc=(0, 0, 0.1))

bm = bmesh.new()
add_blob(bm, Vector((0, 0, 0.02)), 0.16, (1.3, 1.3, 0.5), 0.0, jitter=0.015)
to_object("Embers", bm, ember_mat, loc=(0, 0, 0.1))

# ---------- Lighting ----------
# Warm fire light
fire_data = bpy.data.lights.new("FireLight", 'POINT')
fire_data.energy = 180.0
fire_data.color = (1.0, 0.45, 0.15)
fire_data.shadow_soft_size = 0.25
fire = bpy.data.objects.new("FireLight", fire_data)
fire.location = (0, 0, 0.55)
scene.collection.objects.link(fire)

# Cool, dim moonlight for night contrast
moon_data = bpy.data.lights.new("Moon", 'SUN')
moon_data.energy = 0.6
moon_data.color = (0.45, 0.55, 0.9)
moon = bpy.data.objects.new("Moon", moon_data)
moon.rotation_euler = (math.radians(55), 0, math.radians(-30))
scene.collection.objects.link(moon)

# Night world
world = bpy.data.worlds.new("NightWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.008, 0.01, 0.025, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Flicker animation ----------
scene.frame_start = 1
scene.frame_end = 48
base_energy = fire_data.energy
for f in range(1, 49, 3):
    fire_data.energy = base_energy * random.uniform(0.75, 1.2)
    fire_data.keyframe_insert("energy", frame=f)
    s = random.uniform(0.85, 1.15)
    flames_inner.scale = (random.uniform(0.95, 1.05), random.uniform(0.95, 1.05), s)
    flames_inner.keyframe_insert("scale", frame=f)
    flames_outer.scale = (1.0, 1.0, random.uniform(0.92, 1.08))
    flames_outer.keyframe_insert("scale", frame=f)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam_loc = Vector((3.2, -4.4, 1.7))
target = Vector((0.0, 0.0, 0.6))
cam.location = cam_loc
cam.rotation_euler = (target - cam_loc).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
