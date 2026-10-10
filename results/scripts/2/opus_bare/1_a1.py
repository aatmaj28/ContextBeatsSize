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
m_log = mat("Log", (0.25, 0.13, 0.06))
m_stone = mat("Stone", (0.35, 0.34, 0.32))
m_ember = mat("Ember", (0.3, 0.05, 0.0), (1.0, 0.2, 0.0), 3.0)
m_flame_o = mat("FlameOuter", (1.0, 0.3, 0.0), (1.0, 0.25, 0.02), 12.0)
m_flame_m = mat("FlameMid", (1.0, 0.55, 0.1), (1.0, 0.5, 0.05), 18.0)
m_flame_i = mat("FlameInner", (1.0, 0.9, 0.4), (1.0, 0.85, 0.3), 25.0)

def flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
g = bpy.context.active_object
g.data.materials.append(m_ground)

# Ash/ember bed
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.9, depth=0.06, location=(0, 0, 0.03))
e = bpy.context.active_object
e.data.materials.append(m_ember)

# Logs crossed in a teepee arrangement
n_logs = 5
for i in range(n_logs):
    a = i * 2 * math.pi / n_logs + random.uniform(-0.1, 0.1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.09, depth=1.6)
    log = bpy.context.active_object
    log.location = (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.35)
    # tilt so the top leans toward the center
    log.rotation_euler = (0, math.radians(-55), a)
    log.data.materials.append(m_log)
    flat(log)

# Two flat crossed logs at the base
for a in (0.3, 0.3 + math.pi / 2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.1, depth=1.5, location=(0, 0, 0.1))
    log = bpy.context.active_object
    log.rotation_euler = (0, math.radians(90), a)
    log.data.materials.append(m_log)

# Ring of stones
n_st = 14
for i in range(n_st):
    a = i * 2 * math.pi / n_st
    r = 1.25 + random.uniform(-0.05, 0.05)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.2,
                                          location=(math.cos(a) * r, math.sin(a) * r, 0.08))
    s = bpy.context.active_object
    s.scale = (random.uniform(0.9, 1.4), random.uniform(0.8, 1.1), random.uniform(0.6, 0.9))
    s.rotation_euler = (random.random(), random.random(), random.random() * 6)
    s.data.materials.append(m_stone)
    flat(s)

# Flames from cones
def flame(loc, r, h, m, rot):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, radius2=0, depth=h,
                                    location=(loc[0], loc[1], loc[2] + h / 2))
    f = bpy.context.active_object
    f.rotation_euler = rot
    f.data.materials.append(m)
    flat(f)
    return f

flame((0, 0, 0.15), 0.45, 1.5, m_flame_o, (0, 0, 0))
for i in range(5):
    a = i * 2 * math.pi / 5
    flame((math.cos(a) * 0.25, math.sin(a) * 0.25, 0.1), 0.2, random.uniform(0.7, 1.1),
          m_flame_o, (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), a))
flame((0, 0, 0.15), 0.3, 1.1, m_flame_m, (0, 0, 0.5))
for i in range(3):
    a = i * 2 * math.pi / 3 + 0.4
    flame((math.cos(a) * 0.15, math.sin(a) * 0.15, 0.15), 0.14, 0.7,
          m_flame_m, (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), a))
flame((0, 0, 0.15), 0.17, 0.75, m_flame_i, (0, 0, 1.0))

# Fire light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.8))
fl = bpy.context.active_object
fl.data.energy = 600
fl.data.color = (1.0, 0.45, 0.15)
fl.data.shadow_soft_size = 0.4

bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.3))
fl2 = bpy.context.active_object
fl2.data.energy = 200
fl2.data.color = (1.0, 0.35, 0.05)

# Cool moonlight
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 0.15
sun.data.color = (0.5, 0.6, 1.0)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

# Night world
world = bpy.data.worlds.new("Night")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.2, 2.6))
cam = bpy.context.active_object
cam.data.lens = 40
target = Vector((0, 0, 0.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
