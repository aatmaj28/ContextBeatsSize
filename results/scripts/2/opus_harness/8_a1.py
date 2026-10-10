import bpy, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    return m

red = mat("Red", (0.6, 0.03, 0.03), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
dark = mat("DarkMetal", (0.05, 0.05, 0.06), 0.3, 0.8)
glass = mat("LampGlass", (1.0, 0.9, 0.6), 0.1, emit=(1.0, 0.85, 0.5), strength=8.0)
rock = mat("Rock", (0.22, 0.2, 0.18), 0.9)
water = mat("Water", (0.03, 0.12, 0.2), 0.05)
stone = mat("Stone", (0.45, 0.43, 0.4), 0.8)

def assign(obj, m):
    obj.data.materials.append(m)

def cone(r1, r2, depth, z, m, verts=48):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=(0, 0, z))
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    assign(o, m)
    return o

# Water
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
assign(bpy.context.active_object, water)

# Rocky island
def make_rock(loc, scale, sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=loc)
    o = bpy.context.active_object
    for v in o.data.vertices:
        v.co *= 1 + random.uniform(-0.18, 0.18)
    o.scale = scale
    o.rotation_euler = (random.uniform(0, 0.4), random.uniform(0, 0.4), random.uniform(0, 6.28))
    assign(o, rock)
    return o

make_rock((0, 0, -1.0), (9, 8, 3.2), 4)
for i in range(22):
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(5, 10)
    s = random.uniform(1.0, 2.8)
    make_rock((math.cos(a) * d, math.sin(a) * d, random.uniform(-0.6, 0.6)),
              (s * random.uniform(0.8, 1.4), s * random.uniform(0.8, 1.4), s * random.uniform(0.5, 0.9)), 2)

# Lighthouse base
base_z = 2.0
cone(2.6, 2.6, 1.0, base_z + 0.5, stone)

# Striped tower
seg_count = 8
seg_h = 1.5
r_bottom, r_top = 2.0, 1.3
z = base_z + 1.0
for i in range(seg_count):
    t0 = i / seg_count
    t1 = (i + 1) / seg_count
    r1 = r_bottom + (r_top - r_bottom) * t0
    r2 = r_bottom + (r_top - r_bottom) * t1
    cone(r1, r2, seg_h, z + seg_h / 2, red if i % 2 == 0 else white)
    z += seg_h
top = z

# Gallery deck and railing
cone(1.9, 1.9, 0.2, top + 0.1, dark)
for i in range(24):
    a = i / 24 * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.8, location=(math.cos(a) * 1.8, math.sin(a) * 1.8, top + 0.6))
    assign(bpy.context.active_object, dark)
bpy.ops.mesh.primitive_torus_add(major_radius=1.8, minor_radius=0.05, location=(0, 0, top + 1.0))
assign(bpy.context.active_object, dark)

# Lantern room
cone(1.0, 1.0, 1.4, top + 0.9, glass, 12)
cone(1.15, 1.15, 0.15, top + 1.68, dark, 12)
cone(1.15, 0.1, 1.0, top + 2.25, red, 12)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, top + 2.85))
assign(bpy.context.active_object, dark)

# Lamp light
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 0.9))
bpy.context.active_object.data.energy = 800
bpy.context.active_object.data.color = (1.0, 0.85, 0.5)

# Sun
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

# World
world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 0.9

# Camera
bpy.ops.object.camera_add(location=(30, -34, 10))
cam = bpy.context.active_object
cam.data.lens = 45
target = Vector((0, 0, 7))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
