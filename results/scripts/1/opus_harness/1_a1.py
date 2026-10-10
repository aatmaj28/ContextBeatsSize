import bpy, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

def mat(name, color, emit=None, strength=0.0, rough=0.8):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

m_ground = mat("Ground", (0.08, 0.06, 0.04))
m_stone = mat("Stone", (0.25, 0.24, 0.23))
m_log = mat("Log", (0.25, 0.13, 0.06))
m_char = mat("Char", (0.05, 0.03, 0.02), emit=(1.0, 0.25, 0.02), strength=0.6)
m_f1 = mat("FlameOuter", (1, 0.3, 0.02), emit=(1.0, 0.25, 0.02), strength=8)
m_f2 = mat("FlameMid", (1, 0.55, 0.1), emit=(1.0, 0.5, 0.05), strength=12)
m_f3 = mat("FlameCore", (1, 0.85, 0.4), emit=(1.0, 0.85, 0.3), strength=18)

def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=12, fill_type='NGON')
g = bpy.context.object; g.data.materials.append(m_ground)

# Stones ring
n = 12
for i in range(n):
    a = i / n * 2 * math.pi
    r = 1.3
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.25,
        location=(r * math.cos(a), r * math.sin(a), 0.1))
    s = bpy.context.object
    s.scale = (random.uniform(0.9, 1.4), random.uniform(0.8, 1.1), random.uniform(0.6, 0.9))
    s.rotation_euler = (random.random(), random.random(), a)
    s.data.materials.append(m_stone); flat(s)

# Crossed logs (teepee-ish)
nl = 5
for i in range(nl):
    a = i / nl * 2 * math.pi + 0.3
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.11, depth=1.6)
    l = bpy.context.object
    d = Vector((math.cos(a), math.sin(a), 0))
    l.location = d * 0.35 + Vector((0, 0, 0.35))
    l.rotation_euler = (0, math.radians(60), a + math.pi)
    l.data.materials.append(m_log); l.data.materials.append(m_char); flat(l)
    for p in l.data.polygons:
        if p.center.z > 0.5: p.material_index = 1
# Base logs crossing
for a in (0.2, 0.2 + math.pi / 2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.12, depth=1.9,
        location=(0, 0, 0.12), rotation=(0, math.pi / 2, a))
    l = bpy.context.object; l.data.materials.append(m_log); flat(l)

# Embers
for i in range(10):
    a = random.uniform(0, 6.28); r = random.uniform(0, 0.5)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.05, 0.1),
        location=(r * math.cos(a), r * math.sin(a), 0.04))
    e = bpy.context.object; e.data.materials.append(m_char); flat(e)

# Flames
def flame(loc, r, h, m):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, depth=h,
        location=(loc[0], loc[1], h / 2 + 0.15),
        rotation=(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.random()))
    f = bpy.context.object; f.data.materials.append(m); flat(f)

flame((0, 0, 0), 0.38, 1.4, m_f1)
for i in range(5):
    a = i / 5 * 6.28
    flame((0.22 * math.cos(a), 0.22 * math.sin(a), 0), 0.18, random.uniform(0.7, 1.0), m_f1)
for i in range(3):
    a = i / 3 * 6.28 + 0.5
    flame((0.1 * math.cos(a), 0.1 * math.sin(a), 0), 0.2, random.uniform(0.9, 1.2), m_f2)
flame((0, 0, 0), 0.15, 0.8, m_f3)

# Fire light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.9))
L = bpy.context.object; L.data.energy = 600; L.data.color = (1, 0.45, 0.12); L.data.shadow_soft_size = 0.4
bpy.ops.object.light_add(type='POINT', location=(0.2, -0.2, 0.4))
L2 = bpy.context.object; L2.data.energy = 150; L2.data.color = (1, 0.3, 0.05)
# Moonlight
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-30)))
S = bpy.context.object; S.data.energy = 0.15; S.data.color = (0.4, 0.5, 1.0)

# World
w = bpy.data.worlds.new("Night"); scene.world = w
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.2, 2.6))
cam = bpy.context.object; cam.data.lens = 40
d = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
try:
    scene.eevee.use_bloom = True
except Exception:
    pass
scene.view_settings.view_transform = 'AgX'
scene.frame_start = 1; scene.frame_end = 1
