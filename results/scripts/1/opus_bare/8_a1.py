import bpy, bmesh, math, random
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

red = mat("Red", (0.7, 0.05, 0.04), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
rock = mat("Rock", (0.18, 0.16, 0.14), 0.95)
water = mat("Water", (0.02, 0.08, 0.12), 0.05)
black = mat("Black", (0.03, 0.03, 0.03), 0.3, 0.8)
glass = mat("Lamp", (1, 0.9, 0.6), 0.1, emit=(1, 0.85, 0.5), strength=15)

# Water
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
bpy.context.object.data.materials.append(water)

# Rocky island
random.seed(3)
for i in range(14):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, 4.5) if i > 0 else 0
    s = random.uniform(1.5, 3.0) if i > 0 else 4.5
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s,
        location=(r * math.cos(a), r * math.sin(a), random.uniform(-0.6, 0.2)))
    o = bpy.context.object
    o.scale = (random.uniform(0.8, 1.3), random.uniform(0.8, 1.3), random.uniform(0.4, 0.7))
    o.rotation_euler = (random.random(), random.random(), random.random())
    for v in o.data.vertices:
        v.co += Vector([random.uniform(-0.25, 0.25) for _ in range(3)])
    o.data.materials.append(rock)

# Tower base on rocks
base_z = 2.0
bpy.ops.mesh.primitive_cylinder_add(radius=1.8, depth=1.0, location=(0, 0, base_z - 0.3))
bpy.context.object.data.materials.append(white)

# Striped tower (tapered segments)
bands = 6
H = 9.0
seg = H / bands
r_bot, r_top = 1.5, 1.0
for i in range(bands):
    z0 = base_z + 0.2 + i * seg
    rb = r_bot + (r_top - r_bot) * (i / bands)
    rt = r_bot + (r_top - r_bot) * ((i + 1) / bands)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=rb, radius2=rt, depth=seg,
                                    location=(0, 0, z0 + seg / 2))
    o = bpy.context.object
    o.data.materials.append(red if i % 2 == 0 else white)
    bpy.ops.object.shade_smooth()

top = base_z + 0.2 + H
# Gallery deck
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.5, depth=0.2, location=(0, 0, top + 0.1))
bpy.context.object.data.materials.append(black)
# Railing
bpy.ops.mesh.primitive_torus_add(major_radius=1.45, minor_radius=0.03, location=(0, 0, top + 0.8))
bpy.context.object.data.materials.append(black)
for k in range(16):
    a = k / 16 * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.7,
        location=(1.45 * math.cos(a), 1.45 * math.sin(a), top + 0.5))
    bpy.context.object.data.materials.append(black)
# Lantern
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.8, depth=1.3, location=(0, 0, top + 0.85))
bpy.context.object.data.materials.append(glass)
# Roof
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.0, radius2=0.05, depth=1.0, location=(0, 0, top + 2.0))
bpy.context.object.data.materials.append(red)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, top + 2.55))
bpy.context.object.data.materials.append(black)

# Lamp light
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 0.85))
bpy.context.object.data.energy = 800
bpy.context.object.data.color = (1, 0.85, 0.5)

# Sun
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.object
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(22, -24, 8))
cam = bpy.context.object
cam.data.lens = 40
target = Vector((0, 0, 5.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
