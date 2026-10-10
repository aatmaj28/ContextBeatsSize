import bpy, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def setmat(o, m):
    o.data.materials.append(m)
    return o

def cube(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.shade_smooth()
    return setmat(o, m)

def cyl(name, loc, r, d, m, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return setmat(o, m)

wood = mat("Wood", (0.36, 0.2, 0.1), 0.45)
wallm = mat("Wall", (0.75, 0.72, 0.66), 0.9)
floorm = mat("Floor", (0.25, 0.22, 0.2), 0.7)
alu = mat("Aluminium", (0.7, 0.71, 0.73), 0.3, 0.9)
dark = mat("DarkPlastic", (0.03, 0.03, 0.035), 0.4)
screen = mat("Screen", (0.02, 0.03, 0.05), 0.2, emit=(0.35, 0.55, 0.9), strength=2.5)
ceramic = mat("Ceramic", (0.85, 0.3, 0.2), 0.25)
coffee = mat("Coffee", (0.08, 0.035, 0.015), 0.1)
terracotta = mat("Terracotta", (0.6, 0.27, 0.15), 0.8)
soil = mat("Soil", (0.08, 0.05, 0.03), 1.0)
leaf = mat("Leaf", (0.08, 0.35, 0.1), 0.5)
lampm = mat("LampMetal", (0.1, 0.25, 0.2), 0.35, 0.6)
bulb = mat("Bulb", (1, 0.9, 0.7), 0.3, emit=(1.0, 0.8, 0.55), strength=15)

# Room
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
setmat(bpy.context.active_object, floorm)
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0.6, 3), rotation=(math.radians(90), 0, 0))
setmat(bpy.context.active_object, wallm)

# Desk
top = 0.75
cube("DeskTop", (0, 0.1, top - 0.02), (1.6, 0.8, 0.04), wood)
for x in (-0.75, 0.75):
    for y in (-0.25, 0.45):
        cube("Leg", (x, y, (top - 0.04) / 2), (0.05, 0.05, top - 0.04), wood)

# Laptop
lx, ly = -0.05, 0.05
cube("LaptopBase", (lx, ly, top + 0.008), (0.34, 0.23, 0.016), alu)
cube("Keyboard", (lx, ly + 0.02, top + 0.0165), (0.29, 0.1, 0.002), dark)
cube("Trackpad", (lx, ly - 0.07, top + 0.0165), (0.1, 0.06, 0.001), mat("Pad", (0.6, 0.6, 0.62), 0.4, 0.8))
t = math.radians(15)
hinge = Vector((lx, ly + 0.115, top + 0.016))
h = 0.22
c = hinge + Vector((0, math.sin(t) * h / 2, math.cos(t) * h / 2))
cube("LaptopLid", c, (0.34, 0.008, h), alu, rot=(-t, 0, 0))
n = Vector((0, -math.cos(t), math.sin(t)))
cube("Display", c + n * 0.0045, (0.31, 0.002, h - 0.025), screen, rot=(-t, 0, 0))

# Mug
mx, my = 0.36, -0.05
cyl("Mug", (mx, my, top + 0.05), 0.042, 0.1, ceramic)
cyl("Coffee", (mx, my, top + 0.093), 0.037, 0.002, coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007,
                                 location=(mx + 0.045, my, top + 0.05), rotation=(math.radians(90), 0, 0))
bpy.ops.object.shade_smooth()
setmat(bpy.context.active_object, ceramic)

# Potted plant
px, py = -0.55, 0.2
bpy.ops.mesh.primitive_cone_add(radius1=0.055, radius2=0.075, depth=0.11, location=(px, py, top + 0.055), vertices=48)
bpy.ops.object.shade_smooth()
setmat(bpy.context.active_object, terracotta)
cyl("Soil", (px, py, top + 0.105), 0.07, 0.005, soil)
for i in range(14):
    a = i / 14 * 2 * math.pi + random.uniform(-0.2, 0.2)
    tilt = random.uniform(0.35, 0.9)
    L = random.uniform(0.08, 0.13)
    d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
    loc = Vector((px, py, top + 0.11)) + d * L * 0.6
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=16, ring_count=8)
    o = bpy.context.active_object
    o.scale = (0.022, 0.006, L * 0.6)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    bpy.ops.object.shade_smooth()
    setmat(o, leaf)

# Desk lamp
bx, by = 0.6, 0.3
cyl("LampBase", (bx, by, top + 0.012), 0.08, 0.024, lampm)
p0 = Vector((bx, by, top + 0.02))
p1 = Vector((bx - 0.05, by - 0.02, top + 0.33))
p2 = Vector((bx - 0.2, by - 0.12, top + 0.42))
for a, b in ((p0, p1), (p1, p2)):
    v = b - a
    o = cyl("Arm", (a + b) / 2, 0.009, v.length, lampm, verts=16)
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=p1)
setmat(bpy.context.active_object, lampm)
shade_dir = Vector((-0.4, -0.3, -1)).normalized()
bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.025, depth=0.12, end_fill_type='NOTHING',
                                location=p2 + shade_dir * 0.03, vertices=48)
sh = bpy.context.active_object
sh.rotation_euler = (-shade_dir).to_track_quat('Z', 'Y').to_euler()
sh.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.003
bpy.ops.object.shade_smooth()
setmat(sh, lampm)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=p2 + shade_dir * 0.05)
bpy.ops.object.shade_smooth()
setmat(bpy.context.active_object, bulb)

bpy.ops.object.light_add(type='SPOT', location=p2 + shade_dir * 0.06)
spot = bpy.context.active_object
spot.rotation_euler = (-shade_dir).to_track_quat('Z', 'Y').to_euler()
spot.data.energy = 60
spot.data.color = (1.0, 0.82, 0.6)
spot.data.spot_size = math.radians(95)
spot.data.spot_blend = 0.6
spot.data.shadow_soft_size = 0.05

bpy.ops.object.light_add(type='POINT', location=p2 + shade_dir * 0.05)
pt = bpy.context.active_object
pt.data.energy = 8
pt.data.color = (1.0, 0.8, 0.55)
pt.data.shadow_soft_size = 0.03

bpy.ops.object.light_add(type='AREA', location=(-1.2, -1.2, 2.0))
fill = bpy.context.active_object
fill.data.energy = 60
fill.data.size = 2.0
fill.data.color = (0.75, 0.82, 1.0)
fill.rotation_euler = (Vector((0, 0.1, top)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)
bg.inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(0.15, -1.25, 1.2))
cam = bpy.context.active_object
cam.data.lens = 38
target = Vector((0.0, 0.12, top + 0.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.frame_start = 1
scene.frame_end = 1
