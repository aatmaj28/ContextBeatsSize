import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if emit:
            try:
                b.inputs["Emission Color"].default_value = (*emit, 1)
                b.inputs["Emission Strength"].default_value = strength
            except KeyError:
                pass
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
        mod = o.modifiers.new("bev", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    return add(o, m)

def cyl(name, loc, r, d, m, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return add(o, m)

wood = mat("Wood", (0.35, 0.2, 0.1), 0.4)
alu = mat("Aluminium", (0.7, 0.7, 0.72), 0.3, 1.0)
dark = mat("Dark", (0.02, 0.02, 0.025), 0.4)
screen = mat("Screen", (0.05, 0.1, 0.2), 0.1, emit=(0.3, 0.55, 0.9), strength=2.0)
ceramic = mat("Ceramic", (0.85, 0.3, 0.2), 0.25)
coffee = mat("Coffee", (0.08, 0.04, 0.02), 0.1)
terracotta = mat("Terracotta", (0.6, 0.28, 0.15), 0.8)
soil = mat("Soil", (0.1, 0.07, 0.04), 1.0)
leaf = mat("Leaf", (0.1, 0.45, 0.12), 0.5)
lampmat = mat("LampMetal", (0.1, 0.12, 0.1), 0.35, 0.8)
bulb = mat("Bulb", (1, 0.9, 0.7), 0.2, emit=(1, 0.85, 0.6), strength=15)
wall = mat("Wall", (0.8, 0.78, 0.74), 0.9)

# Floor / wall
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
add(bpy.context.active_object, mat("Floor", (0.3, 0.3, 0.32), 0.8))
cube("Wall", (0, 3, 3), (10, 0.05, 3), wall)

# Desk
cube("DeskTop", (0, 0, 1.5), (2.2, 1.1, 0.04), wood, 0.01)
for x in (-2.05, 2.05):
    for y in (-0.95, 0.95):
        cube("Leg", (x, y, 0.73), (0.05, 0.05, 0.73), dark)

top = 1.54
# Laptop
cube("LaptopBase", (0, 0, top + 0.02), (0.6, 0.4, 0.02), alu, 0.008)
cube("Keyboard", (0, 0.05, top + 0.041), (0.5, 0.2, 0.002), dark)
cube("Trackpad", (0, -0.25, top + 0.041), (0.15, 0.1, 0.001), mat("Pad", (0.6, 0.6, 0.62), 0.2, 0.8))
pivot = Vector((0, 0.4, top + 0.04))
ang = math.radians(-15)
lid = cube("LaptopLid", (0, 0, 0), (0.6, 0.015, 0.4), alu, 0.008)
lid.location = pivot + Vector((0, 0.4 * math.sin(-ang), 0.4 * math.cos(ang)))
lid.rotation_euler = (ang, 0, 0)
scr = cube("Screen", (0, 0, 0), (0.56, 0.002, 0.36), screen)
scr.location = lid.location + Vector((0, -0.016 * math.cos(ang), 0.016 * math.sin(ang)))
scr.rotation_euler = (ang, 0, 0)

# Mug
mx, my = 1.05, -0.35
cyl("Mug", (mx, my, top + 0.13), 0.12, 0.26, ceramic)
cyl("Coffee", (mx, my, top + 0.24), 0.11, 0.01, coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.018, location=(mx + 0.13, my, top + 0.13), rotation=(math.pi / 2, 0, 0))
h = bpy.context.active_object
bpy.ops.object.shade_smooth()
add(h, ceramic)

# Plant
px, py = -1.3, 0.4
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.13, radius2=0.18, depth=0.3, location=(px, py, top + 0.15))
bpy.ops.object.shade_smooth()
add(bpy.context.active_object, terracotta)
cyl("Soil", (px, py, top + 0.28), 0.16, 0.02, soil)
import random
random.seed(3)
for i in range(14):
    a = i * 2.4
    tilt = random.uniform(0.3, 0.9)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(px, py, top + 0.3))
    l = bpy.context.active_object
    l.scale = (0.04, 0.015, 0.16 + random.uniform(0, 0.06))
    l.rotation_euler = (tilt, 0, a)
    l.location = (px + math.sin(a) * -0.1 * math.sin(tilt) * 1.2, py + math.cos(a) * 0.1 * math.sin(tilt) * 1.2, top + 0.42)
    bpy.ops.object.shade_smooth()
    add(l, leaf)

# Desk lamp
lx, ly = 1.6, 0.6
cyl("LampBase", (lx, ly, top + 0.02), 0.15, 0.04, lampmat)
arm1 = cyl("Arm1", (0, 0, 0), 0.015, 0.6, lampmat, 16)
arm1.location = (lx - 0.1, ly, top + 0.3)
arm1.rotation_euler = (0, math.radians(-20), 0)
arm2 = cyl("Arm2", (0, 0, 0), 0.015, 0.5, lampmat, 16)
arm2.location = (lx - 0.38, ly - 0.05, top + 0.62)
arm2.rotation_euler = (0, math.radians(-70), 0)
hx, hy, hz = lx - 0.62, ly - 0.1, top + 0.62
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.14, radius2=0.05, depth=0.2, location=(hx, hy, hz), rotation=(0, math.radians(-25), 0))
bpy.ops.object.shade_smooth()
sh = bpy.context.active_object
add(sh, lampmat)
sh.modifiers.new("sol", 'SOLIDIFY').thickness = 0.01
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(hx, hy, hz - 0.03))
bpy.ops.object.shade_smooth()
add(bpy.context.active_object, bulb)

bpy.ops.object.light_add(type='SPOT', location=(hx, hy, hz - 0.06))
sp = bpy.context.active_object
sp.data.energy = 120
sp.data.color = (1, 0.85, 0.65)
sp.data.spot_size = math.radians(100)
sp.data.spot_blend = 0.8
sp.data.shadow_soft_size = 0.08
sp.rotation_euler = (0, math.radians(-25), 0)
bpy.ops.object.light_add(type='POINT', location=(hx, hy, hz - 0.03))
pt = bpy.context.active_object
pt.data.energy = 25
pt.data.color = (1, 0.85, 0.6)
pt.data.shadow_soft_size = 0.05

# Fill
bpy.ops.object.light_add(type='AREA', location=(-2, -3, 4))
f = bpy.context.active_object
f.data.energy = 150
f.data.size = 3
f.data.color = (0.75, 0.82, 1.0)
f.rotation_euler = (math.radians(45), 0, math.radians(-35))

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.025, 0.035, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(0.6, -3.6, 2.9))
cam = bpy.context.active_object
cam.data.lens = 35
tgt = Vector((0, 0.1, 1.75))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
