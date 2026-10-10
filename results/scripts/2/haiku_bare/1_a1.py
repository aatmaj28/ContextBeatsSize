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
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene

# ---------- World ----------
world = bpy.data.worlds.new("NightWorld")
world.color = (0.008, 0.01, 0.02)
scene.world = world

# ---------- Helpers ----------
def make_mat(name, color, roughness=0.8, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m

def add_mesh(name, build, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    bm = bmesh.new()
    build(bm)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale
    bpy.context.collection.objects.link(obj)
    return obj

def cone_builder(radius1, radius2, depth, segments=7):
    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                              segments=segments, radius1=radius1,
                              radius2=radius2, depth=depth)
    return build

def ico_builder(radius, subdiv=1):
    def build(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    return build

# ---------- Materials ----------
mat_ground = make_mat("Ground", (0.05, 0.04, 0.035), roughness=1.0)
mat_bark = make_mat("Bark", (0.22, 0.13, 0.07), roughness=0.9)
mat_char = make_mat("Charcoal", (0.03, 0.025, 0.02), roughness=0.95)
stone_mats = [make_mat(f"Stone{i}",
                       (0.28 + random.uniform(-0.05, 0.05),) * 3,
                       roughness=0.85) for i in range(4)]
for i, m in enumerate(stone_mats):
    g = 0.22 + i * 0.07
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (g * 0.95, g, g * 1.05, 1)

mat_flame_out = make_mat("FlameOuter", (1.0, 0.3, 0.04), 0.4, (1.0, 0.3, 0.04), 6.0)
mat_flame_mid = make_mat("FlameMid", (1.0, 0.55, 0.1), 0.4, (1.0, 0.55, 0.1), 8.0)
mat_flame_core = make_mat("FlameCore", (1.0, 0.85, 0.35), 0.4, (1.0, 0.85, 0.35), 12.0)
mat_ember = make_mat("Ember", (1.0, 0.6, 0.2), 0.5, (1.0, 0.6, 0.2), 15.0)

# ---------- Ground ----------
def ground_build(bm):
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=7.0)
add_mesh("Ground", ground_build, mat_ground, loc=(0, 0, 0))

# Scorched ring on ground
def disc_build(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12,
                          radius1=1.05, radius2=1.05, depth=0.01)
add_mesh("ScorchMark", disc_build, mat_char, loc=(0, 0, 0.005))

# ---------- Crossed logs ----------
def log_rot(angle):
    # Cylinder along Z -> lay on ground along direction (cos a, sin a, 0)
    return (0, math.pi / 2, angle)

log_specs = [
    (0.55, 0.13, 1.9, (0.0, 0.0)),
    (0.55 + math.pi / 2 - 0.25, 0.27, 1.7, (0.0, 0.0)),
    (2.2, 0.12, 1.4, (0.0, 0.0)),
    (-0.7, 0.12, 1.5, (0.0, 0.0)),
]
for i, (ang, z, length, _) in enumerate(log_specs):
    radius = 0.13 if i < 2 else 0.11
    loc = (0.0, 0.0, z) if i < 2 else (
        0.85 * math.cos(ang + 0.3), 0.85 * math.sin(ang + 0.3), radius)
    add_mesh(f"Log{i}", cone_builder(radius, radius, length, 7), mat_bark,
             loc=loc, rot=log_rot(ang))

# A few charred log ends
for i in range(4):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.25, 0.4)
    add_mesh(f"Char{i}", ico_builder(0.07, 1), mat_char,
             loc=(r * math.cos(a), r * math.sin(a), 0.07),
             scale=(1.3, 1.0, 0.7))

# ---------- Ring of stones ----------
stone_count = 11
for i in range(stone_count):
    a = 2 * math.pi * i / stone_count + random.uniform(-0.12, 0.12)
    r = 1.0 + random.uniform(-0.06, 0.06)
    size = random.uniform(0.18, 0.26)
    sx = random.uniform(0.9, 1.3)
    sy = random.uniform(0.8, 1.2)
    sz = random.uniform(0.55, 0.75)
    loc = (r * math.cos(a), r * math.sin(a), size * sz * 0.6)
    add_mesh(f"Stone{i}", ico_builder(size, 1), random.choice(stone_mats),
             loc=loc,
             rot=(random.uniform(0, 0.4), random.uniform(0, 0.4), random.uniform(0, math.tau)),
             scale=(sx, sy, sz))

# ---------- Flames (cones, animated flicker) ----------
flames = []

def make_flame(name, radius, depth, mat, loc, tilt=(0, 0, 0)):
    obj = add_mesh(name, cone_builder(radius, 0.0, depth, 6), mat,
                   loc=(loc[0], loc[1], loc[2] + depth / 2), rot=tilt)
    flames.append(obj)
    return obj

# Main layered flame
make_flame("FlameOuter", 0.42, 1.05, mat_flame_out, (0, 0, 0.12))
make_flame("FlameMid", 0.29, 1.3, mat_flame_mid, (0, 0, 0.12), (0.04, 0.03, 0.0))
make_flame("FlameCore", 0.16, 1.55, mat_flame_core, (0, 0, 0.12), (-0.03, 0.02, 0.0))

# Side tongues
for i in range(6):
    a = 2 * math.pi * i / 6 + random.uniform(-0.3, 0.3)
    rr = random.uniform(0.18, 0.28)
    h = random.uniform(0.6, 0.95)
    rad = random.uniform(0.11, 0.17)
    mat = random.choice([mat_flame_out, mat_flame_mid])
    tilt = (random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), 0)
    make_flame(f"Tongue{i}", rad, h, mat,
               (rr * math.cos(a), rr * math.sin(a), 0.12), tilt)

# Flicker keyframes (loop: first and last frames match)
key_frames = [1, 13, 25, 37, 49]
for obj in flames:
    base_scale = obj.scale.copy()
    first_vals = None
    for f in key_frames:
        if f == key_frames[-1] and first_vals is not None:
            s = first_vals
        else:
            sxy = random.uniform(0.9, 1.12)
            sz = random.uniform(0.9, 1.18)
            s = (sxy, sxy, sz)
            if first_vals is None:
                first_vals = s
        obj.scale = (base_scale.x * s[0], base_scale.y * s[1], base_scale.z * s[2])
        obj.keyframe_insert(data_path="scale", frame=f)

# Embers
for i in range(14):
    a = random.uniform(0, math.tau)
    rr = random.uniform(0.0, 0.5)
    z = random.uniform(1.2, 2.2)
    add_mesh(f"Ember{i}", ico_builder(random.uniform(0.02, 0.04), 1), mat_ember,
             loc=(rr * math.cos(a), rr * math.sin(a), z))

# ---------- Lighting ----------
fire_light_data = bpy.data.lights.new("FireLight", 'POINT')
fire_light_data.energy = 450.0
fire_light_data.color = (1.0, 0.5, 0.15)
fire_light_data.shadow_soft_size = 0.35
fire_light = bpy.data.objects.new("FireLight", fire_light_data)
fire_light.location = (0.0, 0.0, 0.9)
bpy.context.collection.objects.link(fire_light)

# Faint warm bounce low down
bounce_data = bpy.data.lights.new("GroundBounce", 'POINT')
bounce_data.energy = 60.0
bounce_data.color = (1.0, 0.4, 0.12)
bounce_data.shadow_soft_size = 0.8
bounce = bpy.data.objects.new("GroundBounce", bounce_data)
bounce.location = (0.0, 0.0, 0.25)
bpy.context.collection.objects.link(bounce)

# Cool moonlight rim from behind
rim_data = bpy.data.lights.new("MoonRim", 'AREA')
rim_data.energy = 40.0
rim_data.color = (0.5, 0.6, 1.0)
rim_data.size = 4.0
rim = bpy.data.objects.new("MoonRim", rim_data)
rim.location = (-3.5, 4.0, 4.0)
rim.rotation_euler = Vector((0.9, 0.0, 0.0)).to_track_quat('Z', 'Y').to_euler() if False else (math.radians(60), 0, math.radians(-135))
bpy.context.collection.objects.link(rim)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (3.4, -4.6, 2.1)
bpy.context.collection.objects.link(cam)

target = Vector((0.0, 0.0, 0.7))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 49
