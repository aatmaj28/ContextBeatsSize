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

def assign(o, m):
    o.data.materials.append(m)
    return o

def cube(loc, scale, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return assign(o, m)

def cyl(loc, r, d, m, rot=(0, 0, 0), v=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    return assign(o, m)

def rod(a, b, r, m):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cyl((a + b) / 2, r, d.length, m, v=16)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return o

wood = mat("Wood", (0.35, 0.2, 0.1), 0.45)
metal_dark = mat("DarkMetal", (0.05, 0.05, 0.06), 0.35, 1.0)
alu = mat("Aluminium", (0.7, 0.72, 0.75), 0.3, 1.0)
keys = mat("Keys", (0.02, 0.02, 0.02), 0.6)
screen = mat("Screen", (0.0, 0.0, 0.0), 0.2, emit=(0.4, 0.6, 1.0), strength=2.5)
ceramic = mat("Ceramic", (0.85, 0.85, 0.82), 0.25)
coffee = mat("Coffee", (0.08, 0.03, 0.01), 0.1)
terracotta = mat("Terracotta", (0.6, 0.25, 0.12), 0.8)
soil = mat("Soil", (0.06, 0.04, 0.02), 1.0)
leafm = mat("Leaf", (0.05, 0.35, 0.08), 0.5)
lampm = mat("LampBody", (0.1, 0.25, 0.2), 0.4, 0.6)
bulb = mat("Bulb", (1, 1, 1), 0.5, emit=(1.0, 0.8, 0.55), strength=20)
wall = mat("Wall", (0.75, 0.72, 0.68), 0.9)
floor = mat("Floor", (0.3, 0.28, 0.26), 0.8)

# Room
cube((0, 0, -0.005), (6, 6, 0.01), floor)
cube((0, 0.7, 1.5), (6, 0.02, 3), wall)

# Desk
cube((0, 0, 0.75), (1.6, 0.8, 0.04), wood)
for x in (-0.75, 0.75):
    for y in (-0.35, 0.35):
        cube((x, y, 0.365), (0.04, 0.04, 0.73), metal_dark)
top = 0.77

# Laptop
cube((0, 0.05, top + 0.01), (0.34, 0.24, 0.02), alu)
cube((0, 0.07, top + 0.0205), (0.30, 0.11, 0.002), keys)
cube((0, -0.02, top + 0.0205), (0.1, 0.06, 0.001), keys)
ang = math.radians(-15)
hinge = Vector((0, 0.17, top + 0.02))
up = Vector((0, -math.sin(ang), math.cos(ang)))
fwd = Vector((0, -math.cos(ang), math.sin(ang)))
c = hinge + up * 0.11
cube(c, (0.34, 0.01, 0.22), alu, rot=(ang, 0, 0))
cube(c + fwd * 0.0055, (0.31, 0.001, 0.19), screen, rot=(ang, 0, 0))

# Mug
mx, my = 0.45, -0.02
cyl((mx, my, top + 0.05), 0.04, 0.1, ceramic)
cyl((mx, my, top + 0.092), 0.036, 0.002, coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007,
                                 location=(mx + 0.045, my, top + 0.05), rotation=(math.pi / 2, 0, 0))
bpy.ops.object.shade_smooth()
assign(bpy.context.object, ceramic)

# Plant
px, py = -0.55, 0.12
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.05, radius2=0.065, depth=0.11,
                                location=(px, py, top + 0.055))
assign(bpy.context.object, terracotta)
cyl((px, py, top + 0.1), 0.06, 0.01, soil)
for i in range(11):
    a = i / 11 * 2 * math.pi + random.uniform(-0.2, 0.2)
    tilt = random.uniform(0.3, 0.8)
    L = random.uniform(0.07, 0.11)
    d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
    base = Vector((px, py, top + 0.105))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=base + d * L)
    lf = bpy.context.object
    lf.scale = (0.022, 0.006, L)
    lf.rotation_mode = 'QUATERNION'
    lf.rotation_quaternion = d.to_track_quat('Z', 'Y')
    bpy.ops.object.shade_smooth()
    assign(lf, leafm)

# Desk lamp
lb = Vector((-0.45, 0.3, top))
cyl(lb + Vector((0, 0, 0.01)), 0.07, 0.02, lampm)
joint = lb + Vector((0.02, -0.02, 0.4))
head = Vector((-0.22, 0.12, top + 0.42))
rod(lb + Vector((0, 0, 0.02)), joint, 0.008, lampm)
rod(joint, head, 0.008, lampm)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=joint)
assign(bpy.context.object, lampm)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.08, radius2=0.025, depth=0.1,
                                location=head - Vector((0, 0, 0.03)), rotation=(0.2, 0.25, 0))
bpy.ops.object.shade_smooth()
sh = bpy.context.object
assign(sh, lampm)
sh.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.003
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=head - Vector((0, 0, 0.06)))
assign(bpy.context.object, bulb)

sd = bpy.data.lights.new("LampSpot", 'SPOT')
sd.energy = 60
sd.color = (1.0, 0.82, 0.6)
sd.spot_size = math.radians(110)
sd.spot_blend = 0.6
sd.shadow_soft_size = 0.05
so = bpy.data.objects.new("LampSpot", sd)
so.location = head - Vector((0, 0, 0.09))
so.rotation_euler = (0.2, 0.25, 0)
scene.collection.objects.link(so)

pd = bpy.data.lights.new("BulbGlow", 'POINT')
pd.energy = 8
pd.color = (1.0, 0.8, 0.55)
pd.shadow_soft_size = 0.03
po = bpy.data.objects.new("BulbGlow", pd)
po.location = head - Vector((0, 0, 0.1))
scene.collection.objects.link(po)

ad = bpy.data.lights.new("Fill", 'AREA')
ad.energy = 60
ad.size = 2.0
ad.color = (0.75, 0.82, 1.0)
ao = bpy.data.objects.new("Fill", ad)
ao.location = (1.5, -1.5, 2.2)
ao.rotation_euler = (math.radians(50), 0, math.radians(45))
scene.collection.objects.link(ao)

# World
scene.world = bpy.data.worlds.new("World")
bg = scene.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)
bg.inputs["Strength"].default_value = 0.5

# Camera
cd = bpy.data.cameras.new("Cam")
cd.lens = 40
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
cam.location = (0.75, -1.25, 1.25)
target = Vector((-0.05, 0.08, 0.86))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.frame_start = 1
scene.frame_end = 1
