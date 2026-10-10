import bpy, bmesh, math, random
from mathutils import Vector, noise

random.seed(7)
scene = bpy.context.scene

# clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    return m

red = mat("Red", (0.6, 0.03, 0.03), 0.4)
white = mat("White", (0.9, 0.9, 0.88), 0.4)
dark = mat("DarkMetal", (0.05, 0.05, 0.06), 0.35, 0.8)
glass = mat("Glass", (0.9, 0.95, 1.0), 0.05, transmission=1.0)
lamp = mat("Lamp", (1, 0.9, 0.6), 0.3, emit=(1, 0.85, 0.5), estr=40)
rock = mat("Rock", (0.18, 0.16, 0.14), 0.9)
moss = mat("RockMoss", (0.12, 0.14, 0.08), 0.95)
water = mat("Water", (0.02, 0.08, 0.14), 0.04)
water.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.8

def assign(obj, m):
    obj.data.materials.append(m)

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# Water
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
assign(bpy.context.active_object, water)

# Rocks
def make_rock(name, loc, scale, subdiv=3, amp=0.35, m=rock):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    off = Vector((random.random()*50, random.random()*50, random.random()*50))
    for v in bm.verts:
        n = noise.noise(v.co * 1.7 + off) + 0.5 * noise.noise(v.co * 4.0 + off)
        v.co *= 1.0 + amp * n
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.scale = scale
    ob.rotation_euler = (0, 0, random.uniform(0, 6.28))
    assign(ob, m)
    return ob

make_rock("Island", (0, 0, -0.6), (7, 6, 1.9), subdiv=4, amp=0.25, m=moss)
make_rock("IslandCore", (0.5, 0.3, -0.2), (4, 3.6, 1.6), subdiv=4, amp=0.3)
for i in range(22):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(4.5, 8.5)
    s = random.uniform(0.4, 1.4)
    make_rock(f"Rock{i}", (math.cos(a)*r, math.sin(a)*r*0.9, random.uniform(-0.3, 0.1)),
              (s*random.uniform(0.8, 1.5), s, s*random.uniform(0.5, 0.9)))

# Tower base
base_z = 1.1
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.6, depth=1.0, location=(0, 0, base_z - 0.3))
assign(bpy.context.active_object, rock)

# Striped tower
H, R0, R1, N = 9.0, 1.3, 0.85, 7
seg = H / N
for i in range(N):
    z0 = base_z + i * seg
    r_a = R0 + (R1 - R0) * (i / N)
    r_b = R0 + (R1 - R0) * ((i + 1) / N)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r_a, radius2=r_b, depth=seg,
                                    location=(0, 0, z0 + seg / 2))
    o = bpy.context.active_object
    smooth(o)
    assign(o, red if i % 2 == 0 else white)

top = base_z + H
# Gallery
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.45, depth=0.2, location=(0, 0, top + 0.1))
assign(bpy.context.active_object, dark)
for i in range(24):
    a = i / 24 * 2 * math.pi
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.03, depth=0.6,
        location=(math.cos(a)*1.38, math.sin(a)*1.38, top + 0.5))
    assign(bpy.context.active_object, dark)
bpy.ops.mesh.primitive_torus_add(major_radius=1.38, minor_radius=0.04, location=(0, 0, top + 0.8))
assign(bpy.context.active_object, dark)

# Lantern room
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.8, depth=0.3, location=(0, 0, top + 0.35))
assign(bpy.context.active_object, red)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.75, depth=1.3, location=(0, 0, top + 1.15))
assign(bpy.context.active_object, glass)
for i in range(12):
    a = (i + 0.5) / 12 * 2 * math.pi
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a)*0.74, math.sin(a)*0.74, top + 1.15))
    o = bpy.context.active_object
    o.scale = (0.05, 0.05, 1.3)
    assign(o, dark)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.3, location=(0, 0, top + 1.15))
assign(bpy.context.active_object, lamp)
bpy.ops.object.light_add(type='POINT', location=(0, 0, top + 1.15))
pl = bpy.context.active_object
pl.data.energy = 300
pl.data.color = (1, 0.85, 0.5)

# Roof
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.95, radius2=0.1, depth=0.8, location=(0, 0, top + 2.2))
smooth(bpy.context.active_object)
assign(bpy.context.active_object, red)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, top + 2.65))
assign(bpy.context.active_object, dark)

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.28, base_z + 0.6))
d = bpy.context.active_object
d.scale = (0.5, 0.15, 1.1)
assign(d, dark)

# Sun
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(55), 0, math.radians(-40))

# World
world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((21, -24, 6.5))
target = Vector((0, 0, 5.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.frame_start = 1
scene.frame_end = 1
