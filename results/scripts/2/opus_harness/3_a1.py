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

snow = mat("Snow", (0.92, 0.94, 1.0), 0.6, 0.2)
ground_m = mat("Ground", (0.88, 0.91, 0.98), 0.8, 0.1)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.5)
wood = mat("Wood", (0.25, 0.14, 0.06), 0.8)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
coal = mat("Coal", (0.03, 0.03, 0.03), 0.9)
red = mat("Red", (0.6, 0.03, 0.03), 0.6)

def sphere(loc, r, m, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o

def cyl(loc, r, d, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=48)
    o = bpy.context.object
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.object
g.data.materials.append(ground_m)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=40)
bpy.ops.object.mode_set(mode='OBJECT')
tex = bpy.data.textures.new("SnowNoise", 'CLOUDS')
tex.noise_scale = 2.0
d = g.modifiers.new("Disp", 'DISPLACE'); d.texture = tex; d.strength = 0.25
bpy.ops.object.shade_smooth()

# Body
sphere((0,0,0.85), 1.0, snow, (1,1,0.92))
sphere((0,0,2.2), 0.72, snow, (1,1,0.95))
sphere((0,0,3.2), 0.5, snow)

# Nose
bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.0, depth=0.5, location=(0,-0.7,3.2), rotation=(math.radians(90),0,0), vertices=32)
n = bpy.context.object; n.data.materials.append(carrot)
bpy.ops.object.shade_smooth()

# Eyes and mouth
for x in (-0.17, 0.17):
    sphere((x, -0.45, 3.35), 0.055, coal)
for i in range(7):
    a = math.radians(-50 + i * 100/6)
    x = math.sin(a) * 0.25
    z = 3.05 - math.cos(a) * 0.08 - 0.0
    z = 3.02 + (abs(x) ** 2) * 1.5
    y = -math.sqrt(max(0.5**2 - x**2 - (z-3.2)**2, 0)) - 0.0
    sphere((x, y, z), 0.035, coal)

# Buttons
for z in (2.45, 2.15, 1.85):
    y = -math.sqrt(max(0.72**2 - (z-2.2)**2/0.9, 0.01))
    sphere((0, y + 0.02, z), 0.06, coal)

# Arms
for side in (-1, 1):
    ang = math.radians(60)
    c = cyl((side*1.15, 0, 2.55), 0.035, 1.3, wood, (0, side*ang, 0))
    cyl((side*1.55, -0.02, 2.95), 0.025, 0.35, wood, (0, side*math.radians(20), 0))

# Hat
cyl((0,0,3.62), 0.55, 0.05, black)
cyl((0,0,3.98), 0.36, 0.7, black)
cyl((0,0,3.72), 0.365, 0.12, red)

# Scarf
bpy.ops.mesh.primitive_torus_add(location=(0,0,2.82), major_radius=0.48, minor_radius=0.1)
s = bpy.context.object; s.data.materials.append(red); bpy.ops.object.shade_smooth()
c = cyl((0.25,-0.5,2.5), 0.08, 0.6, red, (0.2, 0.1, 0)); c.scale = (1.3, 0.5, 1)

# World
w = bpy.data.worlds.new("Sky"); scene.world = w
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
bg.inputs["Strength"].default_value = 0.8

# Lights
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-35)))
sun = bpy.context.object; sun.data.energy = 3.5; sun.data.color = (1, 0.95, 0.88)
bpy.ops.object.light_add(type='AREA', location=(-4, -4, 4))
a = bpy.context.object; a.data.energy = 300; a.data.size = 4; a.data.color = (0.8, 0.88, 1)
a.rotation_euler = (Vector((0,0,2)) - a.location).to_track_quat('-Z', 'Y').to_euler()

# Camera
bpy.ops.object.camera_add(location=(4.5, -8.5, 3.5))
cam = bpy.context.object
cam.rotation_euler = (Vector((0,0,2.1)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 1
