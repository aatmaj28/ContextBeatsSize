import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m

white = mat("White", (0.9, 0.9, 0.9), 0.3)
black = mat("Black", (0.03, 0.03, 0.03), 0.4)
red = mat("Red", (0.7, 0.05, 0.03), 0.4)
concrete = mat("Concrete", (0.45, 0.44, 0.42), 0.9)
steel = mat("Steel", (0.6, 0.2, 0.05), 0.5, 0.6)
ground_m = mat("Ground", (0.25, 0.3, 0.2), 1.0)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=200)
add(bpy.context.object, ground_m)

# Launch pad
bpy.ops.mesh.primitive_cylinder_add(radius=6, depth=1, location=(0, 0, 0.5), vertices=64)
add(bpy.context.object, concrete)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.3))
o = bpy.context.object; o.scale = (4, 4, 0.6); add(o, concrete)

# Rocket
R = 1.0
base = 1.6
bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=14, location=(0, 0, base + 7), vertices=48)
o = bpy.context.object; add(o, white); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(radius=R * 1.01, depth=0.8, location=(0, 0, base + 10), vertices=48)
add(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=R * 1.01, depth=0.3, location=(0, 0, base + 3), vertices=48)
add(bpy.context.object, red)
bpy.ops.mesh.primitive_cone_add(radius1=R, radius2=0.05, depth=4, location=(0, 0, base + 16), vertices=48)
o = bpy.context.object; add(o, white); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=1.0, location=(0, 0, base + 0.2), vertices=32)
add(bpy.context.object, black)
# Fins
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * (R + 0.6), math.sin(a) * (R + 0.6), base + 1.8))
    o = bpy.context.object
    o.scale = (1.4, 0.08, 2.6)
    o.rotation_euler = (0, 0, a)
    add(o, red)

# Support tower
tx, ty = 5.0, 0.0
H = 20
w = 2.0
for dx in (-1, 1):
    for dy in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + dx * w / 2, ty + dy * w / 2, 1 + H / 2))
        o = bpy.context.object; o.scale = (0.2, 0.2, H); add(o, steel)
z = 2
while z < H + 1:
    for (sx, sy, lx, ly) in [(w, 0.15, 0, -w / 2), (w, 0.15, 0, w / 2), (0.15, w, -w / 2, 0), (0.15, w, w / 2, 0)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + lx, ty + ly, z))
        o = bpy.context.object; o.scale = (sx, sy, 0.15); add(o, steel)
    z += 2.5
# Access arms
for az in (8.5, 15.5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((tx - w / 2 + R) / 2, 0, base + az))
    o = bpy.context.object; o.scale = (tx - w / 2 - R, 0.5, 0.3); add(o, steel)
# Warning light
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(tx, ty, H + 1.3))
add(bpy.context.object, mat("Lamp", (1, 0.1, 0.1), emit=(1, 0.1, 0.05)))

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.object
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(-22, -30, 9))
cam = bpy.context.object
cam.data.lens = 40
bpy.ops.object.empty_add(location=(2, 0, 9))
tgt = bpy.context.object
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
