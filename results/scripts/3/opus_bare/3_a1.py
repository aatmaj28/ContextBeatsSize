import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Subsurface Weight"].default_value = sss
    except Exception:
        pass
    return m

snow = mat("Snow", (0.92, 0.95, 1.0), 0.8, 0.1)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.6)
wood = mat("Wood", (0.25, 0.15, 0.07), 0.9)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
red = mat("Scarf", (0.7, 0.05, 0.05), 0.9)

def assign(o, m):
    o.data.materials.append(m)

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.object
assign(g, snow)
sub = g.modifiers.new("s", 'SUBSURF'); sub.levels = 4; sub.subdivision_type = 'SIMPLE'
tex = bpy.data.textures.new("n", 'CLOUDS'); tex.noise_scale = 3
d = g.modifiers.new("d", 'DISPLACE'); d.texture = tex; d.strength = 0.3
g.location.z = -0.15

# Body
def sphere(r, z, m, loc=(0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(loc[0], loc[1], z), segments=48, ring_count=24)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    assign(o, m)
    return o

sphere(1.0, 0.85, snow)
sphere(0.7, 2.25, snow)
sphere(0.48, 3.25, snow)

# Eyes, buttons (coal)
for x in (-0.16, 0.16):
    sphere(0.06, 3.38, black, (x, -0.43))
for i, z in enumerate((2.55, 2.25, 1.95)):
    y = -math.sqrt(max(0.7**2 - (z-2.25)**2, 0)) + 0.02
    sphere(0.07, z, black, (0, y))
# mouth
for i in range(5):
    a = math.radians(-40 + i*20)
    x = 0.2*math.sin(a); z = 3.12 - 0.06*math.cos(a)+0.03
    sphere(0.035, z, black, (x, -0.43 + abs(x)*0.3))

# Carrot nose
bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.0, depth=0.5, location=(0, -0.68, 3.27), rotation=(math.radians(90), 0, 0))
bpy.ops.object.shade_smooth()
assign(bpy.context.object, carrot)

# Stick arms
def stick(p1, p2, r=0.035):
    p1, p2 = Vector(p1), Vector(p2)
    v = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, location=(p1+p2)/2)
    o = bpy.context.object
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    assign(o, wood)

for s in (1, -1):
    a = (0.6*s, 0, 2.4); b = (1.7*s, 0, 3.0)
    stick(a, b)
    stick((1.35*s, 0, 2.81), (1.55*s, 0, 3.2), 0.022)
    stick((1.5*s, 0, 2.9), (1.85*s, 0.05, 2.85), 0.02)

# Scarf
bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.09, location=(0, 0, 2.85))
bpy.ops.object.shade_smooth()
assign(bpy.context.object, red)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.25, -0.42, 2.55), rotation=(0.2, 0, 0.15))
o = bpy.context.object; o.scale = (0.15, 0.05, 0.5); assign(o, red)

# Top hat
bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.05, location=(0, 0, 3.65), vertices=64)
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.6, location=(0, 0, 3.97), vertices=64)
bpy.ops.object.shade_smooth()
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.355, depth=0.1, location=(0, 0, 3.73), vertices=64)
assign(bpy.context.object, red)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10), rotation=(math.radians(50), 0, math.radians(35)))
sun = bpy.context.object; sun.data.energy = 3.5; sun.data.color = (1, 0.95, 0.88)
bpy.ops.object.light_add(type='AREA', location=(-5, -4, 4))
f = bpy.context.object; f.data.energy = 400; f.data.size = 5; f.data.color = (0.7, 0.8, 1)
f.rotation_euler = (Vector((0, 0, 2)) - f.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.85, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(4.5, -8.5, 3.3))
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 0, 2.1)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam
scene.frame_start = 1; scene.frame_end = 1
