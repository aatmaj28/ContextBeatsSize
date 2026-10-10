import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metal=0.0, rough=0.5, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m

white = mat("White", (0.9, 0.9, 0.9), 0.0, 0.35)
red = mat("Red", (0.7, 0.05, 0.03), 0.0, 0.4)
dark = mat("Dark", (0.08, 0.08, 0.09), 0.6, 0.4)
concrete = mat("Concrete", (0.45, 0.44, 0.42), 0.0, 0.9)
steel = mat("Steel", (0.75, 0.3, 0.1), 0.3, 0.5)
ground_m = mat("Ground", (0.25, 0.3, 0.2), 0.0, 1.0)

def add(obj, m, name=None):
    obj.data.materials.append(m)
    if name: obj.name = name
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=200)
add(bpy.context.object, ground_m, "Ground")

# Launch pad
bpy.ops.mesh.primitive_cylinder_add(radius=6, depth=1, location=(0, 0, 0.5), vertices=64)
add(bpy.context.object, concrete, "Pad")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.2))
o = bpy.context.object; o.scale = (4, 4, 0.4)
add(o, concrete, "Mount")

# Rocket
base_z = 1.4
# engine nozzles
for (x, y) in [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5), (0, 0)]:
    bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0.2, depth=0.8, location=(x, y, base_z + 0.4))
    add(bpy.context.object, dark)
body_z = base_z + 0.8
bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=14, location=(0, 0, body_z + 7), vertices=64)
add(bpy.context.object, white, "Body")
# red bands
for z in [body_z + 2, body_z + 11]:
    bpy.ops.mesh.primitive_cylinder_add(radius=1.42, depth=0.5, location=(0, 0, z), vertices=64)
    add(bpy.context.object, red)
# upper stage
bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=3, location=(0, 0, body_z + 15.5), vertices=64)
add(bpy.context.object, white)
bpy.ops.mesh.primitive_cone_add(radius1=1.4, radius2=1.1, depth=1.0, location=(0, 0, body_z + 14.5), vertices=64)
add(bpy.context.object, white)
bpy.ops.mesh.primitive_cone_add(radius1=1.1, radius2=0.0, depth=3.5, location=(0, 0, body_z + 18.75), vertices=64)
add(bpy.context.object, red, "Nose")
# fins
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 1.9, math.sin(a) * 1.9, body_z + 1.5))
    f = bpy.context.object
    f.scale = (1.2, 0.12, 2.5)
    f.rotation_euler = (0, 0, a)
    add(f, red)

# Support tower
tx, tw, th = 5.0, 2.0, 22.0
for dx in (-tw / 2, tw / 2):
    for dy in (-tw / 2, tw / 2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + dx, dy, 1 + th / 2))
        o = bpy.context.object; o.scale = (0.2, 0.2, th)
        add(o, steel)
levels = 11
for i in range(levels + 1):
    z = 1 + i * th / levels
    for (x, y, sx, sy) in [(tx, -tw/2, tw, 0.15), (tx, tw/2, tw, 0.15), (tx - tw/2, 0, 0.15, tw), (tx + tw/2, 0, 0.15, tw)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        o = bpy.context.object; o.scale = (sx, sy, 0.15)
        add(o, steel)
    if i < levels:
        L = math.hypot(tw, th / levels)
        ang = math.atan2(th / levels, tw)
        for y in (-tw/2, tw/2):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(tx, y, z + th / levels / 2))
            o = bpy.context.object; o.scale = (L, 0.1, 0.1)
            o.rotation_euler = (0, -ang if i % 2 else ang, 0)
            add(o, steel)
# access arms
for z in [body_z + 8, body_z + 15.5]:
    length = tx - tw/2 - 1.2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(tx - tw/2 - length/2, 0, z))
    o = bpy.context.object; o.scale = (length, 0.8, 0.4)
    add(o, steel)
# beacon light
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(tx, 0, th + 1.4))
add(bpy.context.object, mat("Beacon", (1, 0.1, 0.1), emit=(1, 0.1, 0.05)))

# Lighting
bpy.ops.object.light_add(type='SUN', location=(20, -20, 30))
sun = bpy.context.object
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-15, -15, 12))
fill = bpy.context.object
fill.data.energy = 3000; fill.data.size = 10
fill.rotation_euler = (math.radians(60), 0, math.radians(-45))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(-22, -38, 9))
cam = bpy.context.object
cam.data.lens = 40
target = bpy.data.objects.new("Target", None)
target.location = (2, 0, 11)
scene.collection.objects.link(target)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
