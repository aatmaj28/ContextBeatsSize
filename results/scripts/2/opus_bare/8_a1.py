import bpy, bmesh, math, random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Start from an empty scene
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

red = mat("Red", (0.7, 0.04, 0.03), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
rock = mat("Rock", (0.18, 0.16, 0.14), 0.9)
water = mat("Water", (0.02, 0.12, 0.18), 0.05)
dark = mat("Dark", (0.05, 0.05, 0.06), 0.4, 0.8)
glass = mat("Glass", (1, 0.9, 0.6), 0.1, emit=(1, 0.85, 0.5), strength=15)

# Water
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
bpy.context.object.data.materials.append(water)
bpy.context.object.name = "Water"

# Rocky island: several displaced icospheres
for i in range(14):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, 4.5) if i > 0 else 0
    s = random.uniform(1.5, 3.0) if i > 0 else 4.5
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1,
        location=(math.cos(ang) * r, math.sin(ang) * r, -0.3 if i else -1.5))
    o = bpy.context.object
    o.scale = (s * random.uniform(0.8, 1.2), s * random.uniform(0.8, 1.2),
               s * random.uniform(0.4, 0.7) if i else 2.4)
    o.rotation_euler = (random.random(), random.random(), random.random())
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        v.co *= random.uniform(0.85, 1.12)
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.append(rock)
    for p in o.data.polygons:
        p.use_smooth = False

# Tower stripes (tapered)
base_z = 0.8
H = 12.0
n = 6
r0, r1 = 1.4, 0.95
for i in range(n):
    z0 = base_z + H * i / n
    t0 = i / n
    t1 = (i + 1) / n
    bpy.ops.mesh.primitive_cone_add(vertices=48,
        radius1=r0 + (r1 - r0) * t0, radius2=r0 + (r1 - r0) * t1,
        depth=H / n, location=(0, 0, z0 + H / n / 2))
    o = bpy.context.object
    o.data.materials.append(red if i % 2 == 0 else white)
    bpy.ops.object.shade_smooth()

top = base_z + H
# Gallery platform
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.5, depth=0.25, location=(0, 0, top + 0.12))
bpy.context.object.data.materials.append(dark)
# Railing
bpy.ops.mesh.primitive_torus_add(major_radius=1.45, minor_radius=0.04, location=(0, 0, top + 0.8))
bpy.context.object.data.materials.append(dark)
for k in range(16):
    a = 2 * math.pi * k / 16
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.7,
        location=(1.45 * math.cos(a), 1.45 * math.sin(a), top + 0.6))
    bpy.context.object.data.materials.append(dark)
# Lantern room
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.75, depth=1.3, location=(0, 0, top + 0.9))
bpy.context.object.data.materials.append(glass)
# Roof
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.95, radius2=0.05, depth=0.9, location=(0, 0, top + 2.0))
bpy.context.object.data.materials.append(red)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, top + 2.5))
bpy.context.object.data.materials.append(dark)
# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.38, base_z + 0.8))
bpy.context.object.scale = (0.6, 0.15, 1.4)
bpy.context.object.data.materials.append(dark)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.object
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 0.9))
bpy.context.object.data.energy = 300
bpy.context.object.data.color = (1, 0.85, 0.5)

# World sky
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(24, -26, 9))
cam = bpy.context.object
cam.data.lens = 45
target = Vector((0, 0, 6.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
