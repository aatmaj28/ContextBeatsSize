import bpy, math

scene = bpy.context.scene

def mat(name, color, metal=0.0, rough=0.5, emit=None):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m

white = mat("White", (0.9, 0.9, 0.9), 0.0, 0.35)
black = mat("Black", (0.03, 0.03, 0.03), 0.2, 0.4)
red = mat("Red", (0.7, 0.05, 0.03), 0.0, 0.4)
concrete = mat("Concrete", (0.45, 0.44, 0.42), 0.0, 0.9)
steel = mat("Steel", (0.6, 0.3, 0.1), 0.6, 0.45)
ground = mat("Ground", (0.25, 0.3, 0.2), 0.0, 1.0)

def assign(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
assign(bpy.context.object, ground)

# Launch pad
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=6, depth=1.0, location=(0, 0, 0.5))
assign(bpy.context.object, concrete)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.6))
o = bpy.context.object; o.scale = (4, 4, 1.2)
assign(o, concrete)

# Rocket
R = 0.8
base_z = 2.6
# engine nozzle
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.6, radius2=0.35, depth=0.6, location=(0, 0, base_z + 0.3))
assign(bpy.context.object, black)
body_z = base_z + 0.6
body_h = 12
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=R, depth=body_h, location=(0, 0, body_z + body_h / 2))
o = bpy.context.object
assign(o, white)
bpy.ops.object.shade_smooth()
# black stripes
for z in (body_z + 3, body_z + 9):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=R + 0.01, depth=0.4, location=(0, 0, z))
    assign(bpy.context.object, black)
    bpy.ops.object.shade_smooth()
# nose cone
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=R, radius2=0, depth=3, location=(0, 0, body_z + body_h + 1.5))
assign(bpy.context.object, red)
bpy.ops.object.shade_smooth()
# fins
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * (R + 0.5), math.sin(a) * (R + 0.5), body_z + 1.0))
    f = bpy.context.object
    f.scale = (1.2, 0.08, 2.0)
    f.rotation_euler = (0, 0, a)
    assign(f, red)

# Support tower
tx, ty = 4.5, 0
th = 17
s = 1.6
for dx in (-s / 2, s / 2):
    for dy in (-s / 2, s / 2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + dx, ty + dy, 1 + th / 2))
        o = bpy.context.object; o.scale = (0.15, 0.15, th)
        assign(o, steel)
lev = 0
z = 2.5
while z < 1 + th:
    for (x, y, sx, sy) in ((tx, ty - s / 2, s, 0.1), (tx, ty + s / 2, s, 0.1),
                           (tx - s / 2, ty, 0.1, s), (tx + s / 2, ty, 0.1, s)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        o = bpy.context.object; o.scale = (sx, sy, 0.1)
        assign(o, steel)
    # diagonal brace on front face
    bpy.ops.mesh.primitive_cube_add(size=1, location=(tx - s / 2, ty, z + 1))
    o = bpy.context.object
    o.scale = (0.08, math.hypot(s, 2), 0.08)
    o.rotation_euler = (math.atan2(2, s) * (1 if lev % 2 else -1), 0, 0)
    assign(o, steel)
    z += 2; lev += 1
# access arms to rocket
for az in (body_z + 5, body_z + 11):
    length = tx - s / 2 - R
    bpy.ops.mesh.primitive_cube_add(size=1, location=(R + length / 2, 0, az))
    o = bpy.context.object; o.scale = (length, 0.5, 0.25)
    assign(o, steel)
# beacon on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(tx, ty, 1 + th + 0.2))
assign(bpy.context.object, mat("Beacon", (1, 0.1, 0.1), emit=(1, 0.1, 0.1)))

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.object
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-12, -10, 8))
a = bpy.context.object
a.data.energy = 2000; a.data.size = 8
a.rotation_euler = (math.radians(70), 0, math.radians(-50))

world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(22, -30, 9))
cam = bpy.context.object
cam.data.lens = 40
target = bpy.data.objects.new("Target", None)
target.location = (2, 0, 9)
scene.collection.objects.link(target)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
