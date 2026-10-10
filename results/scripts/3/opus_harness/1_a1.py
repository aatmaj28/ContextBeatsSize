import bpy, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

# Clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, emit=None, strength=0.0, rough=0.8):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

m_ground = mat("Ground", (0.06, 0.08, 0.04))
m_stone = mat("Stone", (0.25, 0.24, 0.22))
m_log = mat("Log", (0.22, 0.11, 0.05))
m_ember = mat("Ember", (0.1, 0.02, 0.0), (1.0, 0.25, 0.02), 3.0)
m_f1 = mat("FlameOuter", (1.0, 0.3, 0.02), (1.0, 0.3, 0.02), 8.0)
m_f2 = mat("FlameMid", (1.0, 0.55, 0.05), (1.0, 0.55, 0.05), 12.0)
m_f3 = mat("FlameCore", (1.0, 0.85, 0.3), (1.0, 0.85, 0.3), 18.0)

def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
g = bpy.context.object
g.data.materials.append(m_ground)

# Stone ring
n = 12
for i in range(n):
    a = i / n * 2 * math.pi
    r = 1.3
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.25,
        location=(r * math.cos(a), r * math.sin(a), 0.12))
    s = bpy.context.object
    s.scale = (random.uniform(1.0, 1.4), random.uniform(0.8, 1.1), random.uniform(0.6, 0.9))
    s.rotation_euler = (random.random(), random.random(), a)
    s.data.materials.append(m_stone)
    flat(s)

# Logs (crossed, teepee-ish)
nl = 5
for i in range(nl):
    a = i / nl * 2 * math.pi + 0.3
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.1, depth=1.6,
        location=(0.35 * math.cos(a), 0.35 * math.sin(a), 0.3))
    l = bpy.context.object
    l.rotation_euler = (0, math.radians(65), a + math.pi)
    l.data.materials.append(m_log)
    flat(l)
# Flat crossed base logs
for a in (0.2, 1.8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.11, depth=1.8, location=(0, 0, 0.11))
    l = bpy.context.object
    l.rotation_euler = (0, math.radians(90), a)
    l.data.materials.append(m_log)
    flat(l)

# Embers
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.55, depth=0.08, location=(0, 0, 0.04))
e = bpy.context.object
e.data.materials.append(m_ember)

# Flames
def flame(x, y, rad, h, m, rot):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=rad, radius2=0, depth=h,
        location=(x, y, 0.15 + h / 2))
    f = bpy.context.object
    f.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), rot)
    f.data.materials.append(m)
    flat(f)

for i in range(6):
    a = i / 6 * 2 * math.pi
    flame(0.22 * math.cos(a), 0.22 * math.sin(a), 0.18, random.uniform(0.7, 1.0), m_f1, a)
for i in range(4):
    a = i / 4 * 2 * math.pi + 0.5
    flame(0.1 * math.cos(a), 0.1 * math.sin(a), 0.15, random.uniform(1.0, 1.3), m_f2, a)
flame(0, 0, 0.13, 1.6, m_f3, 0)

# Lights
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.8))
fl = bpy.context.object
fl.data.energy = 600
fl.data.color = (1.0, 0.5, 0.15)
fl.data.shadow_soft_size = 0.3

bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
moon = bpy.context.object
moon.data.energy = 0.15
moon.data.color = (0.5, 0.6, 1.0)
moon.rotation_euler = (math.radians(50), 0, math.radians(30))

# World
w = bpy.data.worlds.new("Night")
scene.world = w
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.2, 2.6))
cam = bpy.context.object
d = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 40
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 1
