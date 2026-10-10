import bpy, math, random

random.seed(3)
scene = bpy.context.scene

# Clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, spec=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

# Ground / table
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
table = bpy.context.object
table.data.materials.append(mat("Table", (0.35, 0.2, 0.1), 0.6))

# Backdrop
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 6, 5), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("Wall", (0.8, 0.78, 0.72), 0.9))

page_mat = mat("Pages", (0.92, 0.88, 0.78), 0.8)
colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.8), (0.1, 0.6, 0.2), (0.9, 0.7, 0.1),
          (0.5, 0.1, 0.6), (0.9, 0.4, 0.1)]

z = 0.0
for i, c in enumerate(colors):
    w = random.uniform(1.6, 2.1); d = random.uniform(1.2, 1.5); h = random.uniform(0.18, 0.32)
    rot = random.uniform(-0.25, 0.25)
    ox, oy = random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)
    cover = mat(f"Cover{i}", c, 0.4)
    # cover
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + h / 2), rotation=(0, 0, rot))
    b = bpy.context.object
    b.scale = (w / 2, d / 2, h / 2)
    b.data.materials.append(cover)
    bev = b.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.02; bev.segments = 3
    # pages (inset, slightly protruding on 3 sides from spine)
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + h / 2), rotation=(0, 0, rot))
    p = bpy.context.object
    p.scale = (w / 2 * 0.97 + 0.005, d / 2 * 0.95 + 0.012, h / 2 * 0.82)
    p.location.x += math.cos(rot) * 0.02
    p.location.y += math.sin(rot) * 0.02
    p.data.materials.append(page_mat)
    z += h

# Apple
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0, 0, z + 0.38), segments=48, ring_count=24)
apple = bpy.context.object
apple.scale = (1, 1, 0.9)
for v in apple.data.vertices:
    r = math.sqrt(v.co.x ** 2 + v.co.y ** 2)
    if v.co.z > 0.3:
        v.co.z -= 0.12 * (1 - r / 0.42) ** 2
    if v.co.z < -0.3:
        v.co.z += 0.08 * (1 - r / 0.42) ** 2
bpy.ops.object.shade_smooth()
apple.data.materials.append(mat("Apple", (0.7, 0.03, 0.03), 0.25))

# Stem
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.25, location=(0.02, 0, z + 0.38 + 0.38), rotation=(0, math.radians(12), 0))
bpy.context.object.data.materials.append(mat("Stem", (0.25, 0.15, 0.05), 0.8))

# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0.15, 0, z + 0.38 + 0.38))
leaf = bpy.context.object
leaf.scale = (1, 0.45, 0.06)
leaf.rotation_euler = (0, math.radians(-25), math.radians(20))
bpy.ops.object.shade_smooth()
leaf.data.materials.append(mat("Leaf", (0.15, 0.5, 0.1), 0.5))

# Lights
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
k = bpy.context.object; k.data.energy = 1200; k.data.size = 4
k.rotation_euler = (math.radians(45), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-5, -2, 3))
f = bpy.context.object; f.data.energy = 300; f.data.size = 5
f.rotation_euler = (math.radians(70), 0, math.radians(-70))

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.6, 0.65, 0.75, 1)
bg.inputs["Strength"].default_value = 0.4

# Camera
target_z = z / 2 + 0.3
bpy.ops.object.empty_add(location=(0, 0, target_z))
tgt = bpy.context.object
bpy.ops.object.camera_add(location=(4.5, -5.5, 3.2))
cam = bpy.context.object
cam.data.lens = 50
c = cam.constraints.new('TRACK_TO'); c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1280
scene.render.resolution_y = 1080
