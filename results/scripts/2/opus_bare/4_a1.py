import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m

white = mat("White", (0.9, 0.9, 0.9), 0.3)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
red = mat("Red", (0.7, 0.05, 0.03), 0.4)
concrete = mat("Concrete", (0.35, 0.34, 0.32), 0.9)
steel = mat("Steel", (0.6, 0.3, 0.08), 0.5, 0.6)
ground_m = mat("Ground", (0.25, 0.3, 0.18), 1.0)
window = mat("Window", (0.1, 0.2, 0.4), 0.1, emit=(0.2, 0.4, 0.8))

def add(obj, m):
    obj.data.materials.append(m)
    return obj

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

# Ground and pad
bpy.ops.mesh.primitive_plane_add(size=200)
add(bpy.context.object, ground_m)
bpy.ops.mesh.primitive_cylinder_add(radius=9, depth=1, location=(0, 0, 0.5), vertices=64)
add(bpy.context.object, concrete)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.2))
o = bpy.context.object; o.scale = (6, 6, 0.4); add(o, concrete)
# flame trench
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.42))
o = bpy.context.object; o.scale = (2.5, 2.5, 0.05); add(o, black)

# Rocket
base_z = 1.4
# Engine nozzle
bpy.ops.mesh.primitive_cone_add(radius1=0.9, radius2=0.5, depth=1.0, location=(0, 0, base_z + 0.9), vertices=32)
o = bpy.context.object; add(o, black); smooth(o)
# Body
body_h = 14
bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=body_h, location=(0, 0, base_z + 1.4 + body_h / 2), vertices=48)
o = bpy.context.object; add(o, white); smooth(o)
body_top = base_z + 1.4 + body_h
# Stripes
for z in (base_z + 3.0, body_top - 1.5):
    bpy.ops.mesh.primitive_cylinder_add(radius=1.22, depth=0.4, location=(0, 0, z), vertices=48)
    o = bpy.context.object; add(o, black); smooth(o)
bpy.ops.mesh.primitive_cylinder_add(radius=1.22, depth=0.6, location=(0, 0, base_z + 9), vertices=48)
o = bpy.context.object; add(o, red); smooth(o)
# Nose cone
bpy.ops.mesh.primitive_cone_add(radius1=1.2, radius2=0.0, depth=4, location=(0, 0, body_top + 2), vertices=48)
o = bpy.context.object; add(o, white); smooth(o)
# Window
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, -1.1, body_top - 3.5))
o = bpy.context.object; o.scale = (1, 0.4, 1); add(o, window); smooth(o)
# Fins
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.scale = (1.4, 0.12, 2.5)
    o.location = (math.cos(a) * 1.8, math.sin(a) * 1.8, base_z + 2.8)
    o.rotation_euler = (0, 0, a)
    add(o, red)

# Support tower
tx, ty = 5.0, 0.0
tw, th = 2.4, 22
for dx in (-1, 1):
    for dy in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + dx * tw / 2, ty + dy * tw / 2, 1.4 + th / 2))
        o = bpy.context.object; o.scale = (0.2, 0.2, th); add(o, steel)
levels = 11
for k in range(levels + 1):
    z = 1.4 + k * th / levels
    for (sx, sy, lx, ly) in [(0, -1, tw, 0.12), (0, 1, tw, 0.12), (-1, 0, 0.12, tw), (1, 0, 0.12, tw)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + sx * tw / 2, ty + sy * tw / 2, z))
        o = bpy.context.object; o.scale = (lx, ly, 0.12); add(o, steel)
    if k < levels:
        # diagonal braces
        seg = th / levels
        L = math.hypot(tw, seg)
        ang = math.atan2(seg, tw) * (1 if k % 2 else -1)
        for sy in (-1, 1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(tx, ty + sy * tw / 2, z + seg / 2))
            o = bpy.context.object; o.scale = (L, 0.08, 0.08); o.rotation_euler = (0, -ang, 0); add(o, steel)
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + sx * tw / 2, ty, z + seg / 2))
            o = bpy.context.object; o.scale = (0.08, L, 0.08); o.rotation_euler = (ang, 0, 0); add(o, steel)
# Access arms
for z in (base_z + 6, body_top - 2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((tx - tw / 2 + 1.2) / 2 + 0.0, 0, z))
    o = bpy.context.object
    o.scale = (tx - tw / 2 - 1.2, 0.8, 0.25); o.location.x = 1.2 + (tx - tw / 2 - 1.2) / 2
    add(o, steel)
# Warning light on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(tx, ty, 1.4 + th + 0.3))
add(bpy.context.object, mat("Light", (1, 0, 0), emit=(1, 0.05, 0)))

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.object; sun.data.energy = 4; sun.rotation_euler = (math.radians(45), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-15, -15, 10))
a = bpy.context.object; a.data.energy = 3000; a.data.size = 10
a.rotation_euler = (math.radians(60), 0, math.radians(-45))

world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1); bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(-22, -34, 9))
cam = bpy.context.object
cam.data.lens = 35
bpy.ops.object.empty_add(location=(1.5, 0, 10))
tgt = bpy.context.object
c = cam.constraints.new('TRACK_TO'); c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.camera = cam
scene.frame_start = 1; scene.frame_end = 1
