import bpy, math, random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, emission=None, strength=0.0, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m

mat_ground = make_mat("Ground", (0.05, 0.08, 0.03))
mat_log = make_mat("Log", (0.18, 0.09, 0.04))
mat_char = make_mat("Char", (0.03, 0.02, 0.02), (1.0, 0.25, 0.02), 1.5)
mat_stone = make_mat("Stone", (0.35, 0.34, 0.32))
mat_flame_o = make_mat("FlameOrange", (1.0, 0.35, 0.05), (1.0, 0.35, 0.03), 12)
mat_flame_y = make_mat("FlameYellow", (1.0, 0.8, 0.2), (1.0, 0.75, 0.15), 18)
mat_flame_r = make_mat("FlameRed", (0.9, 0.15, 0.02), (1.0, 0.15, 0.01), 8)

def flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=12, fill_type='NGON')
g = bpy.context.object
g.data.materials.append(mat_ground)

# Ash bed
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.9, depth=0.05, location=(0, 0, 0.025))
a = bpy.context.object
a.data.materials.append(mat_char)

# Logs (crossed, teepee-ish)
n_logs = 5
for i in range(n_logs):
    ang = i * 2 * math.pi / n_logs + random.uniform(-0.15, 0.15)
    r = 0.45
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.1, depth=1.5,
        location=(math.cos(ang) * r, math.sin(ang) * r, 0.35))
    log = bpy.context.object
    log.rotation_euler = (0, math.radians(60), ang + math.pi)
    log.data.materials.append(mat_log)
    log.data.materials.append(mat_char)
    # char the inner end caps
    for p in log.data.polygons:
        if len(p.vertices) > 4:
            p.material_index = 1
    flat(log)

# Two flat crossed logs at the base
for ang in (0.4, 0.4 + math.pi / 2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.11, depth=1.6, location=(0, 0, 0.12))
    log = bpy.context.object
    log.rotation_euler = (math.pi / 2, 0, ang)
    log.data.materials.append(mat_log)
    flat(log)

# Stone ring
n_st = 14
for i in range(n_st):
    ang = i * 2 * math.pi / n_st
    r = 1.15 + random.uniform(-0.05, 0.05)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22,
        location=(math.cos(ang) * r, math.sin(ang) * r, 0.1))
    s = bpy.context.object
    s.scale = (random.uniform(0.9, 1.3), random.uniform(0.8, 1.1), random.uniform(0.6, 0.85))
    s.rotation_euler = (random.random(), random.random(), ang)
    s.data.materials.append(mat_stone)

# Flames (cones)
flames = []
def flame(x, y, z, r, h, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0, depth=h,
        location=(x, y, z + h / 2))
    f = bpy.context.object
    f.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.random())
    f.data.materials.append(mat)
    flames.append(f)

flame(0, 0, 0.1, 0.35, 1.4, mat_flame_r)
for i in range(5):
    ang = i * 2 * math.pi / 5
    flame(math.cos(ang) * 0.2, math.sin(ang) * 0.2, 0.1, 0.18, random.uniform(0.7, 1.0), mat_flame_o)
for i in range(3):
    ang = i * 2 * math.pi / 3 + 0.5
    flame(math.cos(ang) * 0.08, math.sin(ang) * 0.08, 0.15, 0.13, random.uniform(0.8, 1.2), mat_flame_y)
flame(0, 0, 0.15, 0.1, 1.5, mat_flame_y)

# Flame flicker animation
scene.frame_start = 1
scene.frame_end = 96
for f in flames:
    base = f.scale.copy()
    for fr in range(1, 97, 6):
        s = random.uniform(0.85, 1.15)
        f.scale = (base.x * random.uniform(0.9, 1.1), base.y * random.uniform(0.9, 1.1), base.z * s)
        f.keyframe_insert("scale", frame=fr)

# Fire light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.8))
fire = bpy.context.object
fire.data.color = (1.0, 0.45, 0.12)
fire.data.energy = 600
fire.data.shadow_soft_size = 0.4
for fr in range(1, 97, 4):
    fire.data.energy = random.uniform(450, 750)
    fire.data.keyframe_insert("energy", frame=fr)

# Moonlight
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
moon = bpy.context.object
moon.data.color = (0.4, 0.5, 1.0)
moon.data.energy = 0.15
moon.rotation_euler = (math.radians(50), 0, math.radians(30))

# World
world = bpy.data.worlds.new("Night")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.2, 2.6))
cam = bpy.context.object
cam.data.lens = 40
direction = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
