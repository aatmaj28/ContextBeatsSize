import bpy, bmesh, math, random
from mathutils import Vector, noise

random.seed(7)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene

def mat(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0, trans=0.0):
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    return m

red = mat("Red", (0.6, 0.03, 0.03), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
dark = mat("DarkMetal", (0.05, 0.05, 0.06), 0.35, 0.8)
glass = mat("Glass", (1.0, 0.95, 0.8), 0.05, emit=(1.0, 0.85, 0.5), estr=4.0, trans=0.6)
rock = mat("Rock", (0.18, 0.16, 0.14), 0.9)
water = mat("Water", (0.02, 0.08, 0.12), 0.05)
concrete = mat("Concrete", (0.5, 0.5, 0.48), 0.8)

def assign(obj, m):
    obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.use_smooth = True

# Water
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
w = bpy.context.active_object
w.data.materials.append(water)

# Rocky island
rock_specs = [((0, 0, -0.3), (5.5, 5.0, 1.8))]
for i in range(14):
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(3.0, 6.5)
    s = random.uniform(0.8, 2.0)
    rock_specs.append(((math.cos(a) * d, math.sin(a) * d, random.uniform(-0.4, 0.1)),
                       (s * random.uniform(0.9, 1.5), s, s * random.uniform(0.5, 0.9))))
for loc, sc in rock_specs:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=loc)
    r = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(r.data)
    off = Vector((random.random() * 10, random.random() * 10, random.random() * 10))
    for v in bm.verts:
        n = noise.fractal(v.co * 1.8 + off, 0.6, 2.0, 4)
        v.co += v.normal * n * 0.25
    bm.to_mesh(r.data)
    bm.free()
    r.scale = sc
    r.rotation_euler = (0, 0, random.uniform(0, 6.28))
    assign(r, rock)

# Base platform
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.8, depth=0.6, location=(0, 0, 1.5))
assign(bpy.context.active_object, concrete)

# Striped tower
base_z, H, n = 1.8, 9.0, 6
r0, r1 = 1.35, 0.85
seg = H / n
for i in range(n):
    ra = r0 + (r1 - r0) * (i / n)
    rb = r0 + (r1 - r0) * ((i + 1) / n)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=ra, radius2=rb, depth=seg,
                                    location=(0, 0, base_z + seg * (i + 0.5)))
    assign(bpy.context.active_object, red if i % 2 == 0 else white)

top = base_z + H
# Gallery
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.3, depth=0.2, location=(0, 0, top + 0.1))
assign(bpy.context.active_object, dark)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.04, location=(0, 0, top + 0.75))
assign(bpy.context.active_object, dark)
for k in range(16):
    a = k / 16 * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.03, depth=0.55,
                                        location=(math.cos(a) * 1.25, math.sin(a) * 1.25, top + 0.475))
    assign(bpy.context.active_object, dark)
# Lantern room
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.7, depth=1.2, location=(0, 0, top + 0.8))
assign(bpy.context.active_object, glass)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.85, depth=0.12, location=(0, 0, top + 1.45))
assign(bpy.context.active_object, dark)
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.85, radius2=0.05, depth=0.8, location=(0, 0, top + 1.9))
assign(bpy.context.active_object, red)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, top + 2.35))
assign(bpy.context.active_object, dark)

# Lantern light
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 0.8))
lp = bpy.context.active_object
lp.data.energy = 400
lp.data.color = (1.0, 0.85, 0.5)

# Sun
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(55), 0, math.radians(35))

# World
world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.empty_add(location=(0, 0, 5.5))
target = bpy.context.active_object
bpy.ops.object.camera_add(location=(20, -24, 6))
cam = bpy.context.active_object
cam.data.lens = 40
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
