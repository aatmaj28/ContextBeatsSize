import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metal=0.0, rough=0.5, emit=None):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m

white = mat("White", (0.9, 0.9, 0.9), 0.0, 0.35)
black = mat("Black", (0.03, 0.03, 0.03), 0.2, 0.4)
red = mat("Red", (0.7, 0.05, 0.03), 0.0, 0.4)
concrete = mat("Concrete", (0.45, 0.44, 0.42), 0.0, 0.9)
steel = mat("Steel", (0.6, 0.6, 0.62), 0.9, 0.35)
orange = mat("Tower", (0.75, 0.25, 0.05), 0.4, 0.5)
ground = mat("Ground", (0.25, 0.3, 0.2), 0.0, 1.0)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

def cyl(r, d, loc, m, verts=48, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, vertices=verts)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=d, location=loc, vertices=verts)
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    return add(o, m)

def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    return add(o, m)

# Ground and pad
bpy.ops.mesh.primitive_plane_add(size=200)
add(bpy.context.active_object, ground)
box((14, 14, 1), (0, 0, 0.5), concrete)
cyl(2.5, 0.2, (0, 0, 1.1), steel)  # flame plate ring
# Pedestal legs
for i in range(4):
    a = i * math.pi / 2 + math.pi / 4
    box((0.4, 0.4, 1.4), (1.6 * math.cos(a), 1.6 * math.sin(a), 1.9), steel)
cyl(1.8, 0.3, (0, 0, 2.6), steel)

# Rocket
base = 2.75
cyl(0.7, 0.8, (0, 0, base + 0.4), black, r2=0.45)  # engine bell
cyl(1.0, 12, (0, 0, base + 0.8 + 6), white)
cyl(1.02, 0.4, (0, 0, base + 4), black)
cyl(1.02, 0.25, (0, 0, base + 10), red)
cyl(1.0, 2.0, (0, 0, base + 13.8), white, r2=0.85)
cyl(0.85, 2.8, (0, 0, base + 16.2), white, r2=0.05)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, 0, base + 17.6))
add(bpy.context.active_object, red)
# Fins
for i in range(4):
    a = i * math.pi / 2
    f = box((1.2, 0.08, 1.8), (1.4 * math.cos(a), 1.4 * math.sin(a), base + 1.7), red, rot=(0, 0, a))

# Tower (lattice)
tx, ty, s, H = 5.0, 0.0, 2.0, 20.0
corners = [(tx - s/2, ty - s/2), (tx + s/2, ty - s/2), (tx + s/2, ty + s/2), (tx - s/2, ty + s/2)]
for cx, cy in corners:
    box((0.15, 0.15, H), (cx, cy, 1 + H / 2), orange)
levels = 10
for k in range(levels + 1):
    z = 1 + k * H / levels
    box((s, 0.12, 0.12), (tx, ty - s/2, z), orange)
    box((s, 0.12, 0.12), (tx, ty + s/2, z), orange)
    box((0.12, s, 0.12), (tx - s/2, ty, z), orange)
    box((0.12, s, 0.12), (tx + s/2, ty, z), orange)
    if k < levels:
        dz = H / levels
        L = math.hypot(s, dz)
        ang = math.atan2(dz, s)
        sign = 1 if k % 2 == 0 else -1
        box((L, 0.08, 0.08), (tx, ty - s/2, z + dz/2), orange, rot=(0, -ang * sign, 0))
        box((L, 0.08, 0.08), (tx, ty + s/2, z + dz/2), orange, rot=(0, ang * sign, 0))
        box((0.08, L, 0.08), (tx + s/2, ty, z + dz/2), orange, rot=(ang * sign, 0, 0))
# Access arms
for z in (8.0, 15.0):
    box((3.0, 0.6, 0.15), (tx - s/2 - 1.4, ty, z), steel)
    box((3.0, 0.06, 0.6), (tx - s/2 - 1.4, ty + 0.3, z + 0.35), orange)
# Tower top light
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(tx, ty, 1 + H + 0.3))
add(bpy.context.active_object, mat("Beacon", (1, 0.1, 0.1), emit=(1, 0.1, 0.05)))
box((s + 0.4, s + 0.4, 0.2), (tx, ty, 1 + H), steel)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-15, -15, 10))
fill = bpy.context.active_object
fill.data.energy = 3000
fill.data.size = 10
fill.rotation_euler = (Vector((0, 0, 8)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.6, 0.85, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(-24, -32, 9))
cam = bpy.context.active_object
cam.data.lens = 45
target = Vector((2, 0, 9.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1350
