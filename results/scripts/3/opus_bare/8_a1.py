import bpy, bmesh, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

# Clear
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

red = mat("Red", (0.7, 0.03, 0.03), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
rock = mat("Rock", (0.18, 0.16, 0.14), 0.9)
water = mat("Water", (0.02, 0.12, 0.2), 0.05)
dark = mat("Dark", (0.05, 0.05, 0.05), 0.3, 0.8)
glass = mat("Lamp", (1, 0.9, 0.6), 0.1, emit=(1, 0.85, 0.5), strength=15)

# Water
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
bpy.context.object.data.materials.append(water)

# Rocky island
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=(0, 0, -1.5))
isl = bpy.context.object
isl.scale = (9, 8, 3.5)
for v in isl.data.vertices:
    n = v.co.normalized()
    v.co += n * random.uniform(-0.12, 0.12)
isl.data.materials.append(rock)
bpy.ops.object.shade_flat()

# Boulders
for i in range(25):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(5, 10)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.5, 1.4),
        location=(r * math.cos(a), r * math.sin(a), random.uniform(-0.2, 0.6)))
    b = bpy.context.object
    b.scale = (random.uniform(0.7, 1.4), random.uniform(0.7, 1.4), random.uniform(0.5, 1))
    b.rotation_euler = [random.uniform(0, 3) for _ in range(3)]
    b.data.materials.append(rock)

# Tower stripes (tapered)
base_z = 1.8
H = 12.0
n = 6
r0, r1 = 1.6, 1.0
seg = H / n
for i in range(n):
    za = base_z + i * seg
    ra = r0 + (r1 - r0) * (i / n)
    rb = r0 + (r1 - r0) * ((i + 1) / n)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=ra, radius2=rb, depth=seg,
                                    location=(0, 0, za + seg / 2))
    o = bpy.context.object
    o.data.materials.append(red if i % 2 == 0 else white)
    bpy.ops.object.shade_smooth()

top = base_z + H
# Gallery
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.6, depth=0.25, location=(0, 0, top + 0.12))
bpy.context.object.data.materials.append(dark)
# railing posts
for i in range(16):
    a = i / 16 * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.7, location=(1.5 * math.cos(a), 1.5 * math.sin(a), top + 0.6))
    bpy.context.object.data.materials.append(dark)
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.04, location=(0, 0, top + 0.95))
bpy.context.object.data.materials.append(dark)
# Lantern
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.85, depth=1.4, location=(0, 0, top + 0.95))
bpy.context.object.data.materials.append(glass)
# Roof
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.1, radius2=0.1, depth=1.0, location=(0, 0, top + 2.15))
bpy.context.object.data.materials.append(red)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0, 0, top + 2.7))
bpy.context.object.data.materials.append(dark)

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.55, base_z + 0.9))
d = bpy.context.object
d.scale = (0.7, 0.2, 1.6)
d.data.materials.append(dark)

# Lamp light
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 0.95))
bpy.context.object.data.energy = 800
bpy.context.object.data.color = (1, 0.85, 0.5)

# Sun
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.object
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

# World sky
w = bpy.data.worlds.new("Sky")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.45, 0.65, 0.9, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(26, -30, 9))
cam = bpy.context.object
cam.data.lens = 40
tgt = Vector((0, 0, 7))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
