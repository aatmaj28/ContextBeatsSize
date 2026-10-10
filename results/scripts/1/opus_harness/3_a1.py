import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, sss=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.8, 0.9, 1.0)
    return m

snow = mat("Snow", (0.92, 0.95, 1.0), 0.6, 0.15)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.5)
wood = mat("Wood", (0.25, 0.14, 0.06), 0.8)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
red = mat("Red", (0.6, 0.05, 0.05), 0.5)
ground_m = mat("Ground", (0.88, 0.92, 1.0), 0.7, 0.1)

def assign(o, m):
    o.data.materials.append(m)

def sphere(loc, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.shade_smooth()
    assign(o, m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.active_object
assign(g, ground_m)
d = g.modifiers.new("sub", "SUBSURF")
d.subdivision_type = 'SIMPLE'; d.levels = 6; d.render_levels = 6
tex = bpy.data.textures.new("bumps", 'CLOUDS'); tex.noise_scale = 2.0
disp = g.modifiers.new("disp", "DISPLACE"); disp.texture = tex; disp.strength = 0.25
bpy.ops.object.shade_smooth()

# Body
sphere((0, 0, 0.75), 0.9, snow, (1, 1, 0.92))
sphere((0, 0, 1.95), 0.65, snow, (1, 1, 0.95))
head = sphere((0, 0, 2.85), 0.45, snow)

# Eyes and mouth
for x in (-0.16, 0.16):
    sphere((x, -0.4, 2.98), 0.05, black)
for i in range(5):
    a = math.radians(-40 + i * 20)
    sphere((math.sin(a) * 0.22, -0.41 + abs(math.sin(a)) * 0.05, 2.72 - math.cos(a) * 0.06 + 0.06), 0.03, black)
# Buttons
for z, yy in ((2.15, -0.6), (1.9, -0.65), (1.65, -0.6)):
    sphere((0, yy, z), 0.06, black)

# Carrot nose
bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.0, depth=0.5, location=(0, -0.65, 2.86),
                                rotation=(math.radians(90), 0, 0))
bpy.ops.object.shade_smooth()
assign(bpy.context.active_object, carrot)

# Stick arms
def stick(p1, p2, r=0.035):
    p1, p2 = Vector(p1), Vector(p2)
    v = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, location=(p1 + p2) / 2)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = v.to_track_quat('Z', 'Y')
    assign(o, wood)
    return o

for s in (1, -1):
    base = (s * 0.55, 0, 2.05)
    tip = (s * 1.5, 0.05, 2.6)
    stick(base, tip)
    mid = Vector(base).lerp(Vector(tip), 0.7)
    stick(mid, (s * 1.45, -0.05, 2.95), 0.022)
    stick(tip, (s * 1.75, 0.0, 2.7), 0.018)

# Top hat
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.04, location=(0, 0, 3.22))
assign(bpy.context.active_object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.32, depth=0.55, location=(0, 0, 3.5))
assign(bpy.context.active_object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.325, depth=0.1, location=(0, 0, 3.3))
assign(bpy.context.active_object, red)
hat_parts = [o for o in bpy.context.scene.objects if o.location.z > 3.15 and o.type == 'MESH']
for o in hat_parts:
    o.rotation_euler = (math.radians(-6), math.radians(5), 0)

# Scarf
bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.09, location=(0, 0, 2.45))
bpy.ops.object.shade_smooth()
assign(bpy.context.active_object, red)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.25, -0.47, 2.15), rotation=(0.1, 0, 0.15))
o = bpy.context.active_object; o.scale = (0.14, 0.05, 0.55)
assign(o, red)

# Lighting
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.5; sun.color = (1, 0.95, 0.88)
so = bpy.data.objects.new("Sun", sun); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
fill = bpy.data.lights.new("Fill", 'AREA'); fill.energy = 400; fill.size = 5; fill.color = (0.7, 0.8, 1)
fo = bpy.data.objects.new("Fill", fill); scene.collection.objects.link(fo)
fo.location = (-5, -4, 4)
fo.rotation_euler = (Vector((0, 0, 2)) - fo.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("W"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.68, 0.9, 1); bg.inputs["Strength"].default_value = 0.8

# Camera
cam = bpy.data.cameras.new("Cam"); cam.lens = 50
co = bpy.data.objects.new("Cam", cam); scene.collection.objects.link(co)
co.location = (3.5, -8.5, 3.2)
co.rotation_euler = (Vector((0, 0, 1.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = co
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
