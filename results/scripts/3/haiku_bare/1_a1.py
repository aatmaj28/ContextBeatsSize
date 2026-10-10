import bpy
import bmesh
import math
import random
from mathutils import Matrix, Vector, Euler

random.seed(7)
scene = bpy.context.scene

# ---------- clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------- helpers ----------
def make_mat(name, base, rough=0.8, emit=None, estr=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = estr
    return m

def add_mesh(name, builder, material):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    builder(bm)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

def frustum(r1, r2, h, segs, M):
    """Centered frustum along local Z. r2 == 0 makes a cone."""
    def build(bm):
        ring1 = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring1.append(bm.verts.new(M @ Vector((r1 * math.cos(a), r1 * math.sin(a), -h / 2))))
        if r2 > 1e-6:
            ring2 = []
            for i in range(segs):
                a = 2 * math.pi * i / segs
                ring2.append(bm.verts.new(M @ Vector((r2 * math.cos(a), r2 * math.sin(a), h / 2))))
            for i in range(segs):
                j = (i + 1) % segs
                bm.faces.new((ring1[i], ring1[j], ring2[j], ring2[i]))
            bm.faces.new(ring2)
        else:
            apex = bm.verts.new(M @ Vector((0, 0, h / 2)))
            for i in range(segs):
                j = (i + 1) % segs
                bm.faces.new((ring1[i], ring1[j], apex))
        bm.faces.new(ring1)
    return build

def blob(subdiv, M):
    def build(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, matrix=M)
    return build

def euler_mat(rx, ry, rz):
    return Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()

# ---------- world (night sky) ----------
world = bpy.data.worlds.new("NightWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.006, 0.009, 0.022, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- materials ----------
mat_ground = make_mat("Earth", (0.05, 0.040, 0.03), rough=1.0)
mat_bark = make_mat("Bark", (0.20, 0.11, 0.06), rough=0.9)
mat_stone = make_mat("Stone", (0.30, 0.30, 0.32), rough=0.85)
mat_flame_o = make_mat("FlameOrange", (1.0, 0.40, 0.06), rough=0.5,
                       emit=(1.0, 0.42, 0.08), estr=6.0)
mat_flame_y = make_mat("FlameYellow", (1.0, 0.80, 0.25), rough=0.5,
                       emit=(1.0, 0.85, 0.3), estr=9.0)
mat_ember = make_mat("Ember", (1.0, 0.3, 0.05), rough=0.6,
                     emit=(1.0, 0.35, 0.05), estr=12.0)

# ---------- ground ----------
def ground_builder(bm):
    s = 7.0
    v = [bm.verts.new(Vector(p)) for p in
         [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)]]
    bm.faces.new(v)

add_mesh("Ground", ground_builder, mat_ground)

# ---------- logs ----------
log_r = 0.13
log_len = 2.2
log_specs = [
    ((0.0, 0.0, log_r), (0.0, math.pi / 2, 0.35)),
    ((0.0, 0.0, log_r * 2 + 0.11), (0.0, math.pi / 2, -0.45)),
    ((0.0, 0.0, log_r + 0.03), (0.0, math.pi / 2, 1.9)),
]
for i, (loc, rot) in enumerate(log_specs):
    M = Matrix.Translation(Vector(loc)) @ euler_mat(*rot)
    add_mesh(f"Log{i}", frustum(log_r, log_r, log_len, 10, M), mat_bark)

# ---------- stone ring ----------
n_stones = 14
for i in range(n_stones):
    a = 2 * math.pi * i / n_stones + random.uniform(-0.12, 0.12)
    rad = 1.35 + random.uniform(-0.12, 0.12)
    x, y = rad * math.cos(a), rad * math.sin(a)
    sx = random.uniform(0.28, 0.42)
    sy = random.uniform(0.25, 0.36)
    sz = random.uniform(0.18, 0.26)
    S = Matrix.Diagonal(Vector((sx, sy, sz, 1.0)))
    R = euler_mat(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2),
                  random.uniform(0, math.pi * 2))
    M = Matrix.Translation(Vector((x, y, sz * 0.55))) @ R @ S
    add_mesh(f"Stone{i}", blob(1, M), mat_stone)

# ---------- flames ----------
flame_base_z = 0.22
# outer orange flames
n_outer = 7
for i in range(n_outer):
    a = 2 * math.pi * i / n_outer + random.uniform(-0.2, 0.2)
    off = random.uniform(0.04, 0.12)
    h = random.uniform(0.9, 1.3)
    r = random.uniform(0.18, 0.24)
    tilt_x = math.sin(a) * random.uniform(0.18, 0.3)
    tilt_y = -math.cos(a) * random.uniform(0.18, 0.3)
    center = Vector((math.cos(a) * off, math.sin(a) * off, flame_base_z + h / 2))
    M = Matrix.Translation(center) @ euler_mat(tilt_x, tilt_y, random.uniform(0, 6.28))
    add_mesh(f"FlameOuter{i}", frustum(r, 0.0, h, 6, M), mat_flame_o)

# inner yellow flames
n_inner = 5
for i in range(n_inner):
    a = 2 * math.pi * i / n_inner + random.uniform(-0.3, 0.3)
    off = random.uniform(0.0, 0.05)
    h = random.uniform(0.6, 0.85)
    r = random.uniform(0.11, 0.15)
    tilt_x = random.uniform(-0.12, 0.12)
    tilt_y = random.uniform(-0.12, 0.12)
    center = Vector((math.cos(a) * off, math.sin(a) * off, flame_base_z + h / 2 - 0.05))
    M = Matrix.Translation(center) @ euler_mat(tilt_x, tilt_y, random.uniform(0, 6.28))
    add_mesh(f"FlameInner{i}", frustum(r, 0.0, h, 5, M), mat_flame_y)

# core flame
core_h = 0.75
M = Matrix.Translation(Vector((0, 0, flame_base_z + core_h / 2 - 0.02)))
add_mesh("FlameCore", frustum(0.16, 0.0, core_h, 6, M), mat_flame_y)

# ---------- embers ----------
for i in range(14):
    a = random.uniform(0, 2 * math.pi)
    rad = random.uniform(0.1, 0.7)
    z = random.uniform(0.6, 1.6)
    s = random.uniform(0.012, 0.025)
    M = Matrix.Translation(Vector((math.cos(a) * rad, math.sin(a) * rad, z))) @ Matrix.Diagonal(Vector((s, s, s, 1.0)))
    add_mesh(f"Ember{i}", blob(0, M), mat_ember)

# ---------- lights ----------
# warm fire light
fire_data = bpy.data.lights.new("FireLight", type='POINT')
fire_data.color = (1.0, 0.55, 0.22)
fire_data.energy = 450.0
fire_data.shadow_soft_size = 0.35
fire_obj = bpy.data.objects.new("FireLight", fire_data)
fire_obj.location = (0.0, 0.0, 0.75)
scene.collection.objects.link(fire_obj)

# flicker keyframes
for f in range(1, 49, 4):
    fire_data.energy = random.uniform(380.0, 520.0)
    fire_data.keyframe_insert(data_path="energy", frame=f)

# faint cold moonlight
moon_data = bpy.data.lights.new("MoonLight", type='SUN')
moon_data.color = (0.45, 0.55, 1.0)
moon_data.energy = 0.6
moon_obj = bpy.data.objects.new("MoonLight", moon_data)
moon_obj.rotation_euler = Euler((math.radians(55), 0.0, math.radians(-30)), 'XYZ')
scene.collection.objects.link(moon_obj)

# ---------- camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = Vector((3.4, -4.8, 2.0))
cam_target = Vector((0.0, 0.0, 0.8))
cam_obj.location = cam_loc
direction = cam_target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- timeline ----------
scene.frame_start = 1
scene.frame_end = 48
