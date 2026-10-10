import bpy, math, bmesh
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

def add(obj, m):
    obj.data.materials.append(m)
    return obj

def cube(name, loc, scale, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL')
        md.width = bevel
        md.segments = 3
    return add(o, m)

def cyl(name, loc, r, d, m, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return add(o, m)

wood = mat("Wood", (0.35, 0.2, 0.1), 0.4)
alu = mat("Aluminum", (0.7, 0.7, 0.72), 0.3, 1.0)
dark = mat("Keys", (0.03, 0.03, 0.03), 0.6)
screen = mat("Screen", (0.02, 0.02, 0.03), 0.2, emit=(0.4, 0.6, 1.0), strength=1.5)
ceramic = mat("Mug", (0.8, 0.25, 0.2), 0.25)
coffee = mat("Coffee", (0.1, 0.05, 0.02), 0.1)
terracotta = mat("Pot", (0.6, 0.28, 0.15), 0.8)
soil = mat("Soil", (0.08, 0.05, 0.03), 1.0)
leaf = mat("Leaf", (0.1, 0.45, 0.12), 0.5)
lampm = mat("Lamp", (0.1, 0.1, 0.1), 0.4, 0.8)
bulb = mat("Bulb", (1, 0.9, 0.7), 0.3, emit=(1, 0.85, 0.6), strength=20)
wall = mat("Wall", (0.85, 0.82, 0.78), 0.9)

# Desk
cube("Desktop", (0, 0, 0.75), (1.2, 0.6, 0.025), wood, 0.005)
for x in (-1.1, 1.1):
    for y in (-0.5, 0.5):
        cube("Leg", (x, y, 0.3625), (0.03, 0.03, 0.3625), wood)
# Floor and wall
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
add(bpy.context.active_object, wall)
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0.8, 5), rotation=(math.radians(90), 0, 0))
add(bpy.context.active_object, wall)

# Laptop
top = 0.775
cube("LaptopBase", (0, -0.05, top + 0.009), (0.17, 0.12, 0.009), alu, 0.003)
cube("Keyboard", (0, -0.02, top + 0.0185), (0.15, 0.06, 0.001), dark)
cube("Touchpad", (0, -0.12, top + 0.0185), (0.05, 0.03, 0.0008), dark)
lid_angle = math.radians(-15)
lid = cube("Lid", (0, 0, 0), (0.17, 0.006, 0.115), alu, 0.003)
scr = cube("Screen", (0, -0.0062, 0.005), (0.16, 0.0005, 0.1), screen)
scr.parent = lid
lid.location = (0, 0.07 + 0.115 * math.sin(-lid_angle), top + 0.018 + 0.115 * math.cos(lid_angle))
lid.rotation_euler = (lid_angle, 0, 0)

# Mug
mx, my = 0.42, -0.12
cyl("Mug", (mx, my, top + 0.05), 0.04, 0.1, ceramic)
cyl("Coffee", (mx, my, top + 0.092), 0.036, 0.004, coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.008, location=(mx + 0.045, my, top + 0.05), rotation=(math.radians(90), 0, 0))
bpy.ops.object.shade_smooth()
add(bpy.context.active_object, ceramic)

# Plant
px, py = -0.5, 0.15
cyl("Pot", (px, py, top + 0.05), 0.06, 0.1, terracotta)
bpy.context.active_object.data.vertices  # tapered via scale of top ring
o = bpy.context.active_object
for v in o.data.vertices:
    if v.co.z < 0:
        v.co.x *= 0.78; v.co.y *= 0.78
cyl("Soil", (px, py, top + 0.095), 0.055, 0.01, soil)
import random
random.seed(3)
for i in range(14):
    a = i * 2.4
    tilt = random.uniform(0.3, 0.9)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.05,
        location=(px + 0.035 * math.cos(a), py + 0.035 * math.sin(a), top + 0.14 + random.uniform(0, 0.06)),
        rotation=(tilt, 0, a + math.pi / 2))
    l = bpy.context.active_object
    l.scale = (0.35, 1.0, 0.08)
    bpy.ops.object.shade_smooth()
    add(l, leaf)

# Desk lamp
lx, ly = 0.75, 0.35
cyl("LampBase", (lx, ly, top + 0.01), 0.08, 0.02, lampm)
arm_len = 0.4
cyl("Arm", (lx, ly, top + 0.02 + arm_len / 2), 0.008, arm_len, lampm, 16)
cyl("Arm2", (lx - 0.12, ly - 0.08, top + 0.02 + arm_len + 0.0), 0.008, 0.3, lampm, 16,
    rot=(math.radians(-35), math.radians(-60), 0))
hx, hy, hz = lx - 0.25, ly - 0.17, top + 0.38
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.08, radius2=0.03, depth=0.12, location=(hx, hy, hz),
    rotation=(math.radians(20), math.radians(-20), 0))
sh = bpy.context.active_object
bpy.ops.object.shade_smooth()
sh.modifiers.new("sol", 'SOLIDIFY').thickness = 0.003
add(sh, lampm)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(hx, hy, hz - 0.03))
add(bpy.context.active_object, bulb)

bpy.ops.object.light_add(type='SPOT', location=(hx, hy, hz - 0.05))
sp = bpy.context.active_object
sp.data.energy = 80
sp.data.color = (1, 0.85, 0.65)
sp.data.spot_size = math.radians(110)
sp.data.spot_blend = 0.8
sp.data.shadow_soft_size = 0.05
sp.rotation_euler = (math.radians(20), math.radians(-20), 0)

bpy.ops.object.light_add(type='POINT', location=(hx, hy, hz - 0.04))
pl = bpy.context.active_object
pl.data.energy = 15
pl.data.color = (1, 0.85, 0.65)
pl.data.shadow_soft_size = 0.1

bpy.ops.object.light_add(type='AREA', location=(-1.5, -2, 2.5))
fill = bpy.context.active_object
fill.data.energy = 120
fill.data.size = 2
fill.data.color = (0.75, 0.82, 1.0)
fill.rotation_euler = (math.radians(50), 0, math.radians(-35))

# World
w = bpy.data.worlds.new("World")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.04, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
scene.world = w

# Camera
bpy.ops.object.camera_add(location=(0.35, -1.55, 1.35))
cam = bpy.context.active_object
cam.data.lens = 40
target = Vector((0.05, 0.05, 0.84))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
