import bpy, math
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

def assign(o, m):
    o.data.materials.append(m)
    return o

def cube(name, loc, scale, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    return assign(o, m)

def cyl(name, loc, r, d, m, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return assign(o, m)

wood = mat("Wood", (0.35, 0.2, 0.1), 0.4)
alu = mat("Aluminum", (0.7, 0.7, 0.72), 0.3, 1.0)
dark = mat("DarkKeys", (0.05, 0.05, 0.05), 0.6)
screen = mat("Screen", (0.02, 0.02, 0.03), 0.2, emit=(0.4, 0.6, 1.0), strength=2.0)
ceramic = mat("Ceramic", (0.8, 0.25, 0.2), 0.25)
coffee = mat("Coffee", (0.1, 0.05, 0.02), 0.1)
terracotta = mat("Terracotta", (0.6, 0.3, 0.15), 0.8)
soil = mat("Soil", (0.08, 0.05, 0.03), 1.0)
leaf = mat("Leaf", (0.1, 0.45, 0.12), 0.5)
lampmat = mat("LampBody", (0.1, 0.1, 0.1), 0.3, 0.8)
bulb = mat("Bulb", (1, 0.9, 0.7), 0.5, emit=(1, 0.85, 0.6), strength=15)
wall = mat("Wall", (0.85, 0.82, 0.78), 0.9)

# Desk, legs, floor, wall
cube("Desk", (0, 0, 0.75), (1.2, 0.6, 0.025), wood)
for x in (-1.1, 1.1):
    for y in (-0.5, 0.5):
        cube("Leg", (x, y, 0.37), (0.03, 0.03, 0.37), wood)
bpy.ops.mesh.primitive_plane_add(size=10)
assign(bpy.context.active_object, mat("Floor", (0.3, 0.3, 0.32), 0.8))
cube("Wall", (0, 0.8, 1.5), (3, 0.02, 1.5), wall)

top = 0.775
# Laptop
cube("LaptopBase", (0, -0.05, top + 0.01), (0.32, 0.22, 0.01), alu)
cube("Keyboard", (0, -0.0, top + 0.021), (0.28, 0.1, 0.002), dark)
cube("Trackpad", (0, -0.17, top + 0.021), (0.08, 0.05, 0.001), dark)
hinge = Vector((0, 0.17, top + 0.02))
ang = math.radians(15)
lid_c = hinge + Vector((0, math.sin(ang) * 0.21, math.cos(ang) * 0.21))
cube("Lid", lid_c, (0.32, 0.008, 0.21), alu, rot=(-ang, 0, 0))
scr_c = lid_c + Vector((0, -math.cos(ang) * 0.009, math.sin(ang) * 0.009))
cube("Screen", scr_c, (0.3, 0.001, 0.19), screen, rot=(-ang, 0, 0))

# Mug
mx, my = 0.6, -0.15
cyl("Mug", (mx, my, top + 0.05), 0.045, 0.1, ceramic)
cyl("Coffee", (mx, my, top + 0.092), 0.04, 0.005, coffee)
bpy.ops.mesh.primitive_torus_add(location=(mx + 0.05, my, top + 0.05), rotation=(math.pi / 2, 0, 0),
                                 major_radius=0.028, minor_radius=0.008)
bpy.ops.object.shade_smooth()
assign(bpy.context.active_object, ceramic)

# Plant
px, py = -0.75, 0.2
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.06, radius2=0.08, depth=0.13, location=(px, py, top + 0.065))
bpy.ops.object.shade_smooth()
assign(bpy.context.active_object, terracotta)
cyl("Soil", (px, py, top + 0.12), 0.074, 0.01, soil)
for i in range(9):
    a = i * 2 * math.pi / 9
    tilt = math.radians(25 + (i % 3) * 10)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1,
                                         location=(px + math.cos(a) * 0.04, py + math.sin(a) * 0.04, top + 0.2))
    o = bpy.context.active_object
    o.scale = (0.02, 0.008, 0.09)
    o.rotation_euler = (0, tilt, a)
    o.rotation_mode = 'XYZ'
    o.rotation_euler = (math.cos(a + math.pi / 2) * -tilt, math.sin(a + math.pi / 2) * -tilt, a)
    bpy.ops.object.shade_smooth()
    assign(o, leaf)

# Desk lamp
lx, ly = 0.85, 0.35
cyl("LampBase", (lx, ly, top + 0.01), 0.08, 0.02, lampmat)
arm_len = 0.45
cyl("LampArm", (lx, ly - 0.05, top + 0.22), 0.01, arm_len, lampmat, rot=(math.radians(-15), 0, 0))
head = Vector((lx - 0.08, ly - 0.18, top + 0.44))
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.08, radius2=0.03, depth=0.12, location=head,
                                rotation=(math.radians(20), math.radians(-25), 0))
bpy.ops.object.shade_smooth()
assign(bpy.context.active_object, lampmat)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=head - Vector((0, 0, 0.03)))
assign(bpy.context.active_object, bulb)

bpy.ops.object.light_add(type='SPOT', location=head - Vector((0, 0, 0.05)))
spot = bpy.context.active_object
spot.data.energy = 60
spot.data.color = (1, 0.85, 0.65)
spot.data.spot_size = math.radians(100)
spot.data.spot_blend = 0.8
spot.data.shadow_soft_size = 0.1
d = Vector((-0.2, -0.2, top)) - spot.location
spot.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.light_add(type='AREA', location=(-1.5, -2, 2.5))
fill = bpy.context.active_object
fill.data.energy = 120
fill.data.size = 2
fill.data.color = (0.8, 0.85, 1.0)
fill.rotation_euler = (Vector((0, 0, top)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)

# Camera
bpy.ops.object.camera_add(location=(0.3, -2.0, 1.45))
cam = bpy.context.active_object
cam.data.lens = 40
cam.rotation_euler = (Vector((0, 0.05, top + 0.12)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
