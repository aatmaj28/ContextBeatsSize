import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss > 0:
        try:
            b.inputs["Subsurface Weight"].default_value = sss
        except KeyError:
            pass
    return m

snow = mat("Snow", (0.92, 0.94, 1.0), 0.6, sss=0.2)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.5)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
wood = mat("Wood", (0.25, 0.14, 0.06), 0.8)
red = mat("Red", (0.7, 0.05, 0.05), 0.6)

def assign(o, m):
    o.data.materials.append(m)

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.object
assign(g, snow)
bpy.ops.object.modifier_add(type='SUBSURF')
g.modifiers[-1].levels = 2

# Snowballs
balls = [(0.0, 0.9, 0.95), (0.0, 0.62, 2.25), (0.0, 0.42, 3.2)]
for x, r, z in balls:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, 0, z), segments=48, ring_count=24)
    b = bpy.context.object
    b.scale.z = 0.95
    smooth(b)
    assign(b, snow)

head_z, head_r = 3.2, 0.42

# Carrot nose
bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.45,
    location=(0, -head_r - 0.18, head_z), rotation=(math.radians(90), 0, 0))
n = bpy.context.object
smooth(n)
assign(n, carrot)

# Eyes
for sx in (-0.14, 0.14):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(sx, -0.38, head_z + 0.12))
    e = bpy.context.object; smooth(e); assign(e, black)

# Smile
for i in range(5):
    a = math.radians(-40 + i * 20)
    x = math.sin(a) * 0.2
    z = head_z - 0.12 - math.cos(a) * 0.06 + 0.02
    y = -math.sqrt(max(head_r**2 - x**2 - (z - head_z)**2, 0)) + 0.01
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(x, y, z))
    s = bpy.context.object; smooth(s); assign(s, black)

# Buttons
for z in (2.45, 2.2, 1.95):
    dz = z - 2.25
    y = -math.sqrt(0.62**2 - dz**2) + 0.01
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, location=(0, y, z))
    s = bpy.context.object; smooth(s); assign(s, black)

# Top hat
hat_base = head_z + head_r * 0.8
bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.04, location=(0, 0, hat_base), vertices=48)
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.55, location=(0, 0, hat_base + 0.29), vertices=48)
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.305, depth=0.09, location=(0, 0, hat_base + 0.08), vertices=48)
assign(bpy.context.object, red)

# Scarf
bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.08, location=(0, 0, 2.78))
sc = bpy.context.object; smooth(sc); assign(sc, red)

# Stick arms
def stick(p1, p2, r):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p1 + p2) / 2, vertices=8)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    assign(o, wood)

for s in (-1, 1):
    sh = (s * 0.5, 0, 2.4)
    hand = (s * 1.5, 0, 3.0)
    stick(sh, hand, 0.035)
    mid = Vector(sh).lerp(Vector(hand), 0.7)
    stick(mid, (mid.x + s * 0.2, 0, mid.z + 0.35), 0.022)
    stick(hand, (hand[0] + s * 0.25, 0, hand[2] + 0.05), 0.02)
    stick(hand, (hand[0] + s * 0.12, 0, hand[2] + 0.25), 0.02)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10), rotation=(math.radians(45), 0, math.radians(35)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.color = (1.0, 0.95, 0.88)
bpy.ops.object.light_add(type='AREA', location=(-4, -4, 4))
fill = bpy.context.object
fill.data.energy = 400
fill.data.size = 4
fill.data.color = (0.7, 0.8, 1.0)
fill.rotation_euler = (Vector((0, 0, 2)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# World
w = bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(3.5, -8.5, 3.2))
cam = bpy.context.object
cam.data.lens = 50
target = Vector((0, 0, 2.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
