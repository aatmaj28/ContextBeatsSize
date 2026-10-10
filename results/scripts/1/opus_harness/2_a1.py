import bpy, math
from mathutils import Vector, Matrix

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
    o.data.materials.clear()
    o.data.materials.append(m)
    return o

def box(name, size, loc, m, rot=(0, 0, 0), offset=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.data.transform(Matrix.Diagonal((*size, 1)))
    o.data.transform(Matrix.Translation(offset))
    o.location = loc
    o.rotation_euler = rot
    return assign(o, m)

def cyl(name, r, d, loc, m, rot=(0, 0, 0), r2=None, verts=48):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return assign(o, m)

# Materials
wood = mat("Wood", (0.35, 0.2, 0.1), 0.45)
floor_m = mat("Floor", (0.25, 0.22, 0.2), 0.7)
wall_m = mat("Wall", (0.75, 0.72, 0.68), 0.9)
alu = mat("Aluminium", (0.7, 0.7, 0.72), 0.3, 0.9)
dark = mat("DarkPlastic", (0.03, 0.03, 0.035), 0.4)
screen_m = mat("Screen", (0.02, 0.05, 0.1), 0.2, emit=(0.35, 0.55, 0.9), strength=2.0)
ceramic = mat("Ceramic", (0.85, 0.3, 0.2), 0.25)
coffee = mat("Coffee", (0.08, 0.03, 0.01), 0.1)
terracotta = mat("Terracotta", (0.6, 0.28, 0.15), 0.8)
soil = mat("Soil", (0.08, 0.05, 0.03), 1.0)
leaf = mat("Leaf", (0.08, 0.35, 0.08), 0.5)
lamp_m = mat("LampMetal", (0.1, 0.25, 0.2), 0.35, 0.7)
bulb = mat("Bulb", (1, 0.9, 0.7), 0.2, emit=(1, 0.85, 0.6), strength=15.0)

# Room
bpy.ops.mesh.primitive_plane_add(size=8)
assign(bpy.context.active_object, floor_m)
box("Wall", (8, 0.1, 4), (0, 1.0, 2), wall_m)

# Desk
top = 0.76
box("DeskTop", (1.6, 0.8, 0.04), (0, 0.2, top - 0.02), wood)
for x in (-0.75, 0.75):
    for y in (-0.15, 0.55):
        box("Leg", (0.05, 0.05, top - 0.04), (x, y, (top - 0.04) / 2), wood)

# Laptop
box("LaptopBase", (0.34, 0.24, 0.018), (0, 0.05, top + 0.009), alu)
box("Keyboard", (0.3, 0.1, 0.002), (0, 0.08, top + 0.019), dark)
box("Trackpad", (0.1, 0.06, 0.001), (0, -0.02, top + 0.0185), dark)
tilt = math.radians(-15)
box("LaptopLid", (0.34, 0.012, 0.23), (0, 0.17, top + 0.018), alu, rot=(tilt, 0, 0), offset=(0, 0, 0.115))
box("Display", (0.31, 0.002, 0.2), (0, 0.17, top + 0.018), screen_m, rot=(tilt, 0, 0), offset=(0, -0.007, 0.115))

# Mug
mx, my = 0.38, -0.02
cyl("Mug", 0.042, 0.1, (mx, my, top + 0.05), ceramic)
cyl("Coffee", 0.037, 0.002, (mx, my, top + 0.093), coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007,
                                 location=(mx + 0.045, my, top + 0.05), rotation=(math.radians(90), 0, 0))
h = bpy.context.active_object
bpy.ops.object.shade_smooth()
assign(h, ceramic)

# Plant
px, py = -0.5, 0.3
cyl("Pot", 0.065, 0.11, (px, py, top + 0.055), terracotta, r2=0.05)
cyl("Soil", 0.06, 0.004, (px, py, top + 0.106), soil)
for i in range(9):
    a = i * 2 * math.pi / 9
    tiltl = math.radians(35 + (i % 3) * 12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8)
    l = bpy.context.active_object
    l.data.transform(Matrix.Diagonal((0.025, 0.006, 0.09, 1)))
    l.data.transform(Matrix.Translation((0, 0, 0.08)))
    l.location = (px, py, top + 0.1)
    l.rotation_euler = (tiltl, 0, a)
    bpy.ops.object.shade_smooth()
    assign(l, leaf)

# Desk lamp
lx, ly = 0.62, 0.42
cyl("LampBase", 0.08, 0.025, (lx, ly, top + 0.0125), lamp_m)
p1 = Vector((lx, ly, top + 0.025))
p2 = Vector((lx + 0.02, ly - 0.05, top + 0.42))
p3 = Vector((lx - 0.15, ly - 0.2, top + 0.5))
for a, b in ((p1, p2), (p2, p3)):
    d = b - a
    o = cyl("Arm", 0.01, d.length, (a + b) / 2, lamp_m, verts=16)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=p2)
assign(bpy.context.active_object, lamp_m)
head_dir = Vector((-0.4, -0.2, -1)).normalized()
head = cyl("LampHead", 0.08, 0.12, p3 + head_dir * 0.03, lamp_m, r2=0.025)
head.rotation_euler = (-head_dir).to_track_quat('Z', 'Y').to_euler()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=p3 + head_dir * 0.07)
assign(bpy.context.active_object, bulb)

# Lights
spot_data = bpy.data.lights.new("LampSpot", 'SPOT')
spot_data.energy = 60
spot_data.color = (1, 0.82, 0.6)
spot_data.spot_size = math.radians(85)
spot_data.spot_blend = 0.6
spot_data.shadow_soft_size = 0.05
spot = bpy.data.objects.new("LampSpot", spot_data)
spot.location = p3 + head_dir * 0.08
spot.rotation_euler = head_dir.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(spot)

fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 40
fill_data.size = 2.0
fill_data.color = (0.75, 0.85, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (-1.5, -1.5, 2.2)
fill.rotation_euler = (Vector((0, 0.2, top)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(fill)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.02, 0.025, 0.035, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0.15, -1.25, 1.2)
target = Vector((0.02, 0.15, top + 0.12))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
