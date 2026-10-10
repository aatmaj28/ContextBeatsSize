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

m_ground = mat("Ground", (0.05, 0.07, 0.04))
m_log = mat("Log", (0.18, 0.09, 0.04))
m_stone = mat("Stone", (0.25, 0.25, 0.27))
m_ember = mat("Ember", (0.1, 0.02, 0.0), (1.0, 0.25, 0.02), 6)
m_f1 = mat("FlameOuter", (1, 0.3, 0.02), (1.0, 0.25, 0.02), 12)
m_f2 = mat("FlameMid", (1, 0.55, 0.1), (1.0, 0.5, 0.05), 15)
m_f3 = mat("FlameCore", (1, 0.9, 0.5), (1.0, 0.85, 0.4), 20)

def assign(o, m):
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
g = bpy.context.object
assign(g, m_ground)

# Stones ring
n = 12
for i in range(n):
    a = i / n * 2 * math.pi
    r = 1.3
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.25,
        location=(r * math.cos(a), r * math.sin(a), 0.12))
    s = bpy.context.object
    s.scale = (random.uniform(0.9, 1.3), random.uniform(0.8, 1.1), random.uniform(0.6, 0.9))
    s.rotation_euler = (random.random(), random.random(), a)
    assign(s, m_stone)

# Logs (crossed, teepee-ish)
nl = 5
for i in range(nl):
    a = i / nl * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.12, depth=1.6,
        location=(0.4 * math.cos(a), 0.4 * math.sin(a), 0.35))
    l = bpy.context.object
    l.rotation_euler = (0, math.radians(60), a + math.pi)
    assign(l, m_log)
# Two flat crossed logs
for ang in (0.3, 0.3 + math.pi / 2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.13, depth=1.8, location=(0, 0, 0.13))
    l = bpy.context.object
    l.rotation_euler = (0, math.radians(90), ang)
    assign(l, m_log)

# Embers
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.45, location=(0, 0, 0.05))
e = bpy.context.object
e.scale.z = 0.3
assign(e, m_ember)

# Flames
def flame(loc, r, h, m, rot=0):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0, depth=h,
        location=(loc[0], loc[1], loc[2] + h / 2))
    f = bpy.context.object
    f.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), rot)
    assign(f, m)
    return f

flame((0, 0, 0.15), 0.42, 1.3, m_f1)
for i in range(5):
    a = i / 5 * 2 * math.pi + 0.4
    flame((0.25 * math.cos(a), 0.25 * math.sin(a), 0.15), 0.2, random.uniform(0.6, 0.9), m_f1, a)
flame((0, 0, 0.15), 0.3, 1.0, m_f2, 0.5)
flame((0, 0, 0.15), 0.17, 0.7, m_f3, 1.0)

# Fire light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.8))
L = bpy.context.object
L.data.energy = 600
L.data.color = (1.0, 0.45, 0.12)
L.data.shadow_soft_size = 0.3
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.3))
L2 = bpy.context.object
L2.data.energy = 150
L2.data.color = (1.0, 0.3, 0.05)

# Moonlight
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-120)))
sun = bpy.context.object
sun.data.energy = 0.15
sun.data.color = (0.5, 0.6, 1.0)

# World
world = bpy.data.worlds.new("Night")
scene.world = world
bg = world.node_tree.nodes.get("Background")
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
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
