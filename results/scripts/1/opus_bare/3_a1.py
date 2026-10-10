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

snow = mat("Snow", (0.92, 0.95, 1.0), 0.8, 0.15)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.6)
wood = mat("Wood", (0.25, 0.14, 0.06), 0.9)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
red = mat("Red", (0.6, 0.03, 0.03), 0.7)

def assign(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.object
assign(g, snow)

# Body
for z, r in [(0.75, 0.8), (1.95, 0.58), (2.85, 0.42)]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, z), segments=48, ring_count=24)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    assign(o, snow)

# Nose
bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.45, location=(0, -0.6, 2.85), rotation=(math.radians(90), 0, 0))
o = bpy.context.object; bpy.ops.object.shade_smooth(); assign(o, carrot)

# Eyes
for x in (-0.14, 0.14):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x, -0.37, 2.98))
    assign(bpy.context.object, black)
# Mouth
for i in range(5):
    a = math.radians(-40 + i * 20)
    x = math.sin(a) * 0.18
    z = 2.72 - math.cos(a) * 0.06 + 0.06
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(x, -0.39, z - 0.04))
    assign(bpy.context.object, black)
# Buttons
for z, y in [(2.15, -0.55), (1.9, -0.58), (1.65, -0.54)]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, y, z))
    assign(bpy.context.object, black)

# Arms
def stick(p1, p2, r=0.035):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p1 + p2) / 2)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    assign(o, wood)

for s in (1, -1):
    a = (s * 0.5, 0, 2.05); b = (s * 1.5, 0, 2.6)
    stick(a, b)
    stick((s * 1.2, 0, 2.43), (s * 1.4, -0.05, 2.8), 0.02)
    stick((s * 1.35, 0, 2.52), (s * 1.65, 0.05, 2.5), 0.02)

# Hat
bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.05, location=(0, 0, 3.22), vertices=64)
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.34, depth=0.6, location=(0, 0, 3.52), vertices=64)
assign(bpy.context.object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.345, depth=0.1, location=(0, 0, 3.3), vertices=64)
assign(bpy.context.object, red)
for o in bpy.context.scene.objects:
    pass

# Scarf
bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.08, location=(0, 0, 2.48))
o = bpy.context.object; bpy.ops.object.shade_smooth(); assign(o, red)

# Lights
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10), rotation=(math.radians(45), 0, math.radians(35)))
bpy.context.object.data.energy = 3.5
bpy.context.object.data.color = (1, 0.95, 0.88)
bpy.ops.object.light_add(type='AREA', location=(-5, -4, 4))
l = bpy.context.object; l.data.energy = 400; l.data.size = 5; l.data.color = (0.75, 0.85, 1)
l.rotation_euler = (Vector((0, 0, 2)) - l.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.7, 0.9, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(3.5, -8, 2.8))
cam = bpy.context.object
cam.data.lens = 45
cam.rotation_euler = (Vector((0, 0, 2.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
