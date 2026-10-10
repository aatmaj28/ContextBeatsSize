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

white = mat("White", (0.9, 0.9, 0.9), 0.35)
black = mat("Black", (0.03, 0.03, 0.03), 0.5)
red = mat("Red", (0.7, 0.05, 0.03), 0.4)
concrete = mat("Concrete", (0.45, 0.44, 0.42), 0.9)
steel = mat("Steel", (0.6, 0.15, 0.1), 0.5, 0.6)
ground = mat("Ground", (0.25, 0.3, 0.2), 1.0)

def setm(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=200)
setm(bpy.context.object, ground)

# Launch pad
bpy.ops.mesh.primitive_cylinder_add(radius=8, depth=1.0, location=(0, 0, 0.5))
setm(bpy.context.object, concrete)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.25))
p = bpy.context.object; p.scale = (6, 6, 0.5)
setm(p, concrete)
# flame trench hole look
bpy.ops.mesh.primitive_cylinder_add(radius=1.6, depth=0.05, location=(0, 0, 1.51))
setm(bpy.context.object, black)

# Rocket
base_z = 1.5
# engine nozzles
for dx, dy in [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)]:
    bpy.ops.mesh.primitive_cone_add(radius1=0.45, radius2=0.25, depth=0.8, location=(dx, dy, base_z + 1.0))
    setm(bpy.context.object, black)
# hold-down stand
bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=0.6, location=(0, 0, base_z + 0.3))
setm(bpy.context.object, steel)
# body
body_h = 16
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=body_h, vertices=48, location=(0, 0, base_z + 1.4 + body_h / 2))
o = bpy.context.object; setm(o, white)
bpy.ops.object.shade_smooth()
top = base_z + 1.4 + body_h
# bands
for z in [base_z + 3.0, top - 4.0]:
    bpy.ops.mesh.primitive_cylinder_add(radius=1.52, depth=0.6, vertices=48, location=(0, 0, z))
    setm(bpy.context.object, black); bpy.ops.object.shade_smooth()
# upper stage
bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=4, vertices=48, location=(0, 0, top + 2))
setm(bpy.context.object, white); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cone_add(radius1=1.5, radius2=1.3, depth=0.5, vertices=48, location=(0, 0, top + 0.25))
setm(bpy.context.object, white); bpy.ops.object.shade_smooth()
# nose cone
bpy.ops.mesh.primitive_cone_add(radius1=1.3, radius2=0.05, depth=4, vertices=48, location=(0, 0, top + 6))
setm(bpy.context.object, red); bpy.ops.object.shade_smooth()
# fins
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 2.0, math.sin(a) * 2.0, base_z + 2.8))
    f = bpy.context.object
    f.scale = (1.4, 0.12, 2.4)
    f.rotation_euler = (0, 0, a)
    setm(f, red)

# Support tower
tx, ty = -5.5, 0
tower_h = 26
w = 3.0
for sx in (-1, 1):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + sx * w / 2, ty + sy * w / 2, 1.5 + tower_h / 2))
        c = bpy.context.object; c.scale = (0.25, 0.25, tower_h); setm(c, steel)
z = 1.5
lvl = 0
while z <= 1.5 + tower_h:
    for (dx, dy, sx, sy) in [(0, w/2, w, 0.18), (0, -w/2, w, 0.18), (w/2, 0, 0.18, w), (-w/2, 0, 0.18, w)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + dx, ty + dy, z))
        c = bpy.context.object; c.scale = (sx, sy, 0.18); setm(c, steel)
    # diagonal braces
    if z + 3 <= 1.5 + tower_h:
        L = math.hypot(w, 3)
        ang = math.atan2(3, w) * (1 if lvl % 2 else -1)
        for dy in (w/2, -w/2):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(tx, ty + dy, z + 1.5))
            c = bpy.context.object; c.scale = (L, 0.12, 0.12)
            c.rotation_euler = (0, -ang, 0); setm(c, steel)
    z += 3; lvl += 1
# access arms
for az in [top - 1, top + 3]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=((tx + w/2 - 1.3) / 2 + 0.2, 0, az))
    c = bpy.context.object; c.scale = (abs(tx + w/2) - 1.2, 1.0, 0.4); setm(c, steel)
# beacon
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(tx, ty, 1.5 + tower_h + 0.5))
setm(bpy.context.object, mat("Beacon", (1, 0.1, 0.1), emit=(1, 0.1, 0.1)))

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.object
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(15, -15, 10))
fill = bpy.context.object
fill.data.energy = 3000; fill.data.size = 10
fill.rotation_euler = (math.radians(70), 0, math.radians(45))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(32, -38, 12))
cam = bpy.context.object
cam.data.lens = 40
bpy.ops.object.empty_add(location=(-1.5, 0, 13))
tgt = bpy.context.object
tc = cam.constraints.new('TRACK_TO')
tc.target = tgt
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
