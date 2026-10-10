import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

random.seed(7)
scene = bpy.context.scene

# Clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, rough, transmission=0.0, ior=1.45, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    if emission:
        b.inputs["Emission Color"].default_value = emission
        b.inputs["Emission Strength"].default_value = strength
    return m

crystal_mat = principled("Amethyst", (0.55, 0.15, 0.9, 1), 0.03, 1.0, 1.54,
                         emission=(0.4, 0.05, 0.8, 1), strength=0.15)
crystal_mat2 = principled("AmethystDeep", (0.35, 0.05, 0.7, 1), 0.06, 1.0, 1.54,
                          emission=(0.3, 0.02, 0.6, 1), strength=0.1)
rock_mat = principled("Rock", (0.03, 0.028, 0.03, 1), 0.85)
ground_mat = principled("Ground", (0.015, 0.015, 0.018, 1), 0.9)

# Add noise bump to rock
nt = rock_mat.node_tree
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 12.0
noise.inputs["Detail"].default_value = 8.0
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.6
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])

# ---------- Rock ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
for v in bm.verts:
    p = v.co
    n = 1.0 + 0.12 * math.sin(p.x * 5 + p.y * 3) + 0.08 * math.cos(p.z * 7 + p.x * 4) + random.uniform(-0.04, 0.04)
    v.co = Vector((p.x * 1.6 * n, p.y * 1.3 * n, p.z * 0.7 * n))
    if v.co.z < -0.2:
        v.co.z = -0.2 + (v.co.z + 0.2) * 0.15
rock_mesh = bpy.data.meshes.new("Rock")
bm.to_mesh(rock_mesh); bm.free()
for poly in rock_mesh.polygons:
    poly.use_smooth = True
rock = bpy.data.objects.new("Rock", rock_mesh)
scene.collection.objects.link(rock)
rock.location.z = 0.25
rock.data.materials.append(rock_mat)

# ---------- Crystal builder ----------
def make_crystal(name, radius, height, tip):
    bm = bmesh.new()
    sides = 6
    bottom, top = [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        r = radius * random.uniform(0.85, 1.1)
        bottom.append(bm.verts.new((r * math.cos(a), r * math.sin(a), -0.2)))
        top.append(bm.verts.new((r * 0.92 * math.cos(a), r * 0.92 * math.sin(a), height)))
    apex = bm.verts.new((random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), height + tip))
    bm.faces.new(list(reversed(bottom)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

# ---------- Crystal cluster ----------
center = Vector((0.0, 0.0, 0.6))
count = 16
for i in range(count):
    if i == 0:
        ang, tilt, off = 0, 0, 0
        r, h = 0.28, 1.9
    else:
        ang = random.uniform(0, 2 * math.pi)
        off = random.uniform(0.1, 0.65)
        tilt = math.radians(10 + off * 55 + random.uniform(-8, 8))
        r = random.uniform(0.08, 0.2)
        h = random.uniform(0.5, 1.4) * (1.1 - off * 0.6)
    c = make_crystal(f"Crystal_{i}", r, h, r * random.uniform(1.4, 2.0))
    c.location = center + Vector((math.cos(ang) * off, math.sin(ang) * off * 0.8, -off * 0.25))
    # tilt outward
    axis = Vector((-math.sin(ang), math.cos(ang), 0))
    rot = Matrix.Rotation(tilt, 4, axis) @ Matrix.Rotation(random.uniform(0, math.pi), 4, 'Z')
    c.rotation_euler = rot.to_euler()
    c.data.materials.append(crystal_mat if i % 3 else crystal_mat2)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.05))
ground = bpy.context.active_object
ground.data.materials.append(ground_mat)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
def area(name, loc, energy, color, size):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o

area("Key", (3.5, -3, 4.5), 600, (1.0, 0.92, 0.95), 2.5)
area("Rim", (-3, 3.5, 3), 700, (0.6, 0.4, 1.0), 2.0)
area("Fill", (-4, -2.5, 1.5), 150, (0.7, 0.75, 1.0), 3.0)

pl = bpy.data.lights.new("Inner", 'POINT')
pl.energy = 40; pl.color = (0.7, 0.3, 1.0); pl.shadow_soft_size = 0.3
plo = bpy.data.objects.new("Inner", pl)
scene.collection.objects.link(plo)
plo.location = (0, 0, 1.0)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (4.6, -5.4, 2.9)
target = Vector((0, 0, 1.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.transmission_bounces = 12
scene.cycles.max_bounces = 16
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.frame_start = 1
scene.frame_end = 1
