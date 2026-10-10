import bpy, math, random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Start from an empty scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, emit=None, strength=0.0, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

m_ground = mat("Ground", (0.05, 0.07, 0.04))
m_log = mat("Log", (0.22, 0.12, 0.06))
m_stone = mat("Stone", (0.3, 0.3, 0.32))
m_ember = mat("Ember", (0.3, 0.05, 0.0), (1.0, 0.25, 0.02), 6)
m_f1 = mat("FlameOuter", (1.0, 0.3, 0.02), (1.0, 0.3, 0.02), 12)
m_f2 = mat("FlameMid", (1.0, 0.55, 0.05), (1.0, 0.55, 0.05), 18)
m_f3 = mat("FlameCore", (1.0, 0.85, 0.3), (1.0, 0.85, 0.3), 25)

def flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=12, fill_type='NGON')
g = bpy.context.object
g.data.materials.append(m_ground)

# Logs: crossed, leaning into a teepee
n_logs = 5
for i in range(n_logs):
    a = i * 2 * math.pi / n_logs + random.uniform(-0.15, 0.15)
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.12, depth=1.6)
    lg = bpy.context.object
    lg.location = (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.35)
    lg.rotation_euler = (0, math.radians(55), a + math.pi)
    lg.data.materials.append(m_log)
    flat(lg)

# Two logs lying crossed at the base
for a in (0.4, 0.4 + math.pi / 2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.13, depth=1.8)
    lg = bpy.context.object
    lg.location = (0, 0, 0.13)
    lg.rotation_euler = (0, math.radians(90), a)
    lg.data.materials.append(m_log)
    flat(lg)

# Embers at the base
for i in range(10):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.06, 0.12))
    e = bpy.context.object
    r = random.uniform(0, 0.4)
    a = random.uniform(0, 2 * math.pi)
    e.location = (r * math.cos(a), r * math.sin(a), 0.05)
    e.data.materials.append(m_ember)

# Ring of stones
n_st = 14
for i in range(n_st):
    a = i * 2 * math.pi / n_st
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22)
    s = bpy.context.object
    s.location = (math.cos(a) * 1.25, math.sin(a) * 1.25, 0.08)
    s.scale = (random.uniform(0.9, 1.3), random.uniform(0.8, 1.1), random.uniform(0.6, 0.9))
    s.rotation_euler = (random.random(), random.random(), a)
    s.data.materials.append(m_stone)

# Flames made of cones, with a simple flicker animation
flames = []
specs = [(m_f1, 0.28, 1.4, 6, 0.15), (m_f2, 0.2, 1.0, 5, 0.1), (m_f3, 0.12, 0.7, 4, 0.05)]
for m, rad, h, count, spread in specs:
    for i in range(count):
        a = i * 2 * math.pi / count + random.random()
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=rad, radius2=0, depth=h * random.uniform(0.8, 1.2))
        c = bpy.context.object
        c.location = (math.cos(a) * spread, math.sin(a) * spread, 0.25 + c.dimensions.z / 2)
        c.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.random())
        c.data.materials.append(m)
        flames.append(c)

scene.frame_start = 1
scene.frame_end = 96
for c in flames:
    base = c.scale.copy()
    for f in range(1, 97, 6):
        c.scale = (base.x * random.uniform(0.9, 1.1), base.y * random.uniform(0.9, 1.1),
                   base.z * random.uniform(0.85, 1.15))
        c.keyframe_insert("scale", frame=f)

# Fire light (flickering)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.9))
fl = bpy.context.object
fl.data.color = (1.0, 0.5, 0.15)
fl.data.shadow_soft_size = 0.3
for f in range(1, 97, 4):
    fl.data.energy = random.uniform(500, 750)
    fl.data.keyframe_insert("energy", frame=f)

# Dim moonlight
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-40)))
sun = bpy.context.object
sun.data.color = (0.4, 0.5, 1.0)
sun.data.energy = 0.15

# Night world
w = bpy.data.worlds.new("Night")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.2, 2.6))
cam = bpy.context.object
cam.data.lens = 40
direction = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# Bloom-friendly settings where available
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass
