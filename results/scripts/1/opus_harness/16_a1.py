import bpy, bmesh, math, random
from mathutils import Vector, noise

random.seed(7)
scene = bpy.context.scene

# Clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, rough, trans=0.0, ior=1.45, emis=None):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = trans
    bsdf.inputs["IOR"].default_value = ior
    if emis:
        bsdf.inputs["Emission Color"].default_value = emis[0]
        bsdf.inputs["Emission Strength"].default_value = emis[1]
    return m

crystal_mat = principled("Amethyst", (0.55, 0.15, 0.9, 1), 0.03, trans=1.0, ior=1.55,
                         emis=((0.4, 0.05, 0.8, 1), 0.15))
crystal_mat2 = principled("AmethystDeep", (0.35, 0.05, 0.7, 1), 0.06, trans=1.0, ior=1.55,
                          emis=((0.3, 0.02, 0.6, 1), 0.1))
rock_mat = principled("DarkRock", (0.03, 0.028, 0.03, 1), 0.85)
ground_mat = principled("Ground", (0.01, 0.01, 0.012, 1), 0.6)

# ---------- Rock ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
for v in bm.verts:
    p = v.co.copy()
    n = noise.fractal(p * 1.5, 0.6, 2.0, 5)
    d = 1.0 + 0.25 * n + 0.1 * noise.noise(p * 5.0)
    v.co = Vector((p.x * 1.6 * d, p.y * 1.3 * d, p.z * 0.7 * d))
    if v.co.z < -0.15:
        v.co.z = -0.15 + (v.co.z + 0.15) * 0.1
rock_me = bpy.data.meshes.new("Rock")
bm.to_mesh(rock_me)
bm.free()
for poly in rock_me.polygons:
    poly.use_smooth = True
rock = bpy.data.objects.new("Rock", rock_me)
scene.collection.objects.link(rock)
rock.data.materials.append(rock_mat)
rock.location.z = 0.15

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(ground_mat)

# ---------- Crystals ----------
def make_crystal(name, radius, height, tip):
    bm = bmesh.new()
    sides = 6
    bot, top = [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        r = radius * random.uniform(0.85, 1.1)
        x, y = math.cos(a) * r, math.sin(a) * r
        bot.append(bm.verts.new((x * 0.9, y * 0.9, -0.3)))
        top.append(bm.verts.new((x, y, height)))
    apex = bm.verts.new((random.uniform(-0.1, 0.1) * radius,
                         random.uniform(-0.1, 0.1) * radius, height + tip))
    bm.faces.new(list(reversed(bot)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = radius * 0.04
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    return ob

def rock_top_z(x, y):
    # raycast down onto rock
    deps = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = scene.ray_cast(deps, Vector((x, y, 5)), Vector((0, 0, -1)))
    return loc.z if hit else 0.5

bpy.context.view_layer.update()
count = 22
for k in range(count):
    if k == 0:
        x, y, s = 0.0, 0.0, 1.4
    else:
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(0.15, 0.9)
        x, y = math.cos(ang) * rad, math.sin(ang) * rad * 0.8
        s = random.uniform(0.4, 1.1) * (1.1 - rad * 0.5)
    z = rock_top_z(x, y)
    r = 0.12 * s + 0.03
    h = random.uniform(0.9, 1.6) * s
    c = make_crystal(f"Crystal_{k}", r, h, r * random.uniform(1.4, 2.2))
    c.location = (x, y, z)
    outward = Vector((x, y, 0)) * random.uniform(0.6, 1.3)
    d = (Vector((0, 0, 1)) + outward + Vector((random.uniform(-0.25, 0.25),
                                               random.uniform(-0.25, 0.25), 0))).normalized()
    q = d.to_track_quat('Z', 'Y')
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = q
    c.data.materials.append(crystal_mat if random.random() < 0.6 else crystal_mat2)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.008, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
def area(name, loc, energy, color, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = (Vector((0, 0, 0.8)) - Vector(loc)).normalized()
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

area("Key", (3.5, -3.0, 4.0), 600, (1.0, 0.92, 0.95), 2.5)
area("Rim", (-3.0, 3.5, 3.0), 900, (0.6, 0.4, 1.0), 2.0)
area("Fill", (-4.0, -2.5, 1.5), 150, (0.7, 0.75, 1.0), 3.0)
area("Back", (0.5, 4.0, 0.8), 400, (0.8, 0.3, 1.0), 1.5)

# ---------- Camera ----------
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0.9)
cd = bpy.data.cameras.new("Camera")
cd.lens = 50
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (4.2, -5.2, 2.6)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
cd.dof.use_dof = True
cd.dof.focus_object = target
cd.dof.aperture_fstop = 4.0
scene.camera = cam

# ---------- Render ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 256
scene.cycles.transmission_bounces = 16
scene.cycles.max_bounces = 16
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
