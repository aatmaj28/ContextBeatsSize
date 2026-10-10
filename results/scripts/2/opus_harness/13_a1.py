import bpy, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough, coat=0.0, metallic=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if coat > 0:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    return m

def make_obj(name, verts, faces, material, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(material)
    return ob

R, r = 1.0, 0.45
plate_top = 0.06
dz = plate_top + r

# Donut dough
nu, nv = 72, 36
verts, faces = [], []
for i in range(nu):
    u = 2 * math.pi * i / nu
    for j in range(nv):
        v = 2 * math.pi * j / nv
        verts.append(((R + r * math.cos(v)) * math.cos(u), (R + r * math.cos(v)) * math.sin(u), r * math.sin(v) * 0.92 + dz))
for i in range(nu):
    for j in range(nv):
        a = i * nv + j; b = ((i + 1) % nu) * nv + j
        c = ((i + 1) % nu) * nv + (j + 1) % nv; d = i * nv + (j + 1) % nv
        faces.append((a, b, c, d))
dough = make_obj("Donut", verts, faces, mat("Dough", (0.62, 0.36, 0.15), 0.55))
dough.modifiers.new("Sub", 'SUBSURF').levels = 1

# Frosting
rf = r + 0.045
ph = [random.uniform(0, 6.28) for _ in range(4)]
def outer_edge(u):
    w = 0.5 * math.sin(5 * u + ph[0]) + 0.3 * math.sin(9 * u + ph[1]) + 0.2 * math.sin(13 * u + ph[2])
    return -0.35 - 0.3 * max(0.0, w)
def inner_edge(u):
    return math.pi + 0.45 + 0.15 * math.sin(7 * u + ph[3])
def frost_point(u, v):
    return Vector(((R + rf * math.cos(v)) * math.cos(u), (R + rf * math.cos(v)) * math.sin(u), rf * math.sin(v) * 0.92 + dz))

nu2, nt = 160, 24
verts, faces = [], []
for i in range(nu2):
    u = 2 * math.pi * i / nu2
    v0, v1 = outer_edge(u), inner_edge(u)
    for j in range(nt):
        t = j / (nt - 1)
        verts.append(tuple(frost_point(u, v0 + (v1 - v0) * t)))
for i in range(nu2):
    for j in range(nt - 1):
        a = i * nt + j; b = ((i + 1) % nu2) * nt + j
        faces.append((a, a + 1, b + 1, b))
frost = make_obj("Frosting", verts, faces, mat("Frosting", (0.95, 0.38, 0.62), 0.15, coat=0.6))
sol = frost.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.04; sol.offset = 0.0
frost.modifiers.new("Sub", 'SUBSURF').levels = 2

# Sprinkles
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.11, vertices=10)
tmp = bpy.context.active_object
sp_mesh = tmp.data
for p in sp_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(tmp, do_unlink=True)
colors = [(1, 1, 1), (0.95, 0.85, 0.1), (0.1, 0.45, 0.95), (0.2, 0.8, 0.3), (0.95, 0.3, 0.1), (0.6, 0.2, 0.85)]
smats = [mat("Sprinkle%d" % k, c, 0.3, coat=0.3) for k, c in enumerate(colors)]
for k in range(220):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(-0.15, math.pi + 0.2)
    p = frost_point(u, v)
    n = (Vector((math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v)))).normalized()
    t = n.orthogonal().normalized()
    t = (Matrix.Rotation(random.uniform(0, 2 * math.pi), 3, n) @ t).normalized()
    a = n.cross(t).normalized()
    rot = Matrix((a, n, t)).transposed()
    ob = bpy.data.objects.new("Sprinkle", sp_mesh.copy() if False else sp_mesh)
    ob.matrix_world = Matrix.Translation(p + n * 0.035) @ rot.to_4x4()
    ob.material_slots and None
    scene.collection.objects.link(ob)
    ob.active_material = None
    ob.data.materials.clear() if k == 0 else None
    if k == 0:
        ob.data.materials.append(smats[0])
    ob.material_slots[0].link = 'OBJECT'
    ob.material_slots[0].material = random.choice(smats)

# Plate (lathe)
profile = [(0.0, plate_top), (1.6, plate_top), (1.9, 0.09), (2.2, 0.18), (2.4, 0.24), (2.45, 0.22),
           (2.3, 0.15), (1.9, 0.05), (1.5, 0.0), (1.4, -0.02), (0.0, -0.02)]
seg = 96
verts, faces = [], []
for i in range(seg):
    ang = 2 * math.pi * i / seg
    for (rr, z) in profile:
        verts.append((rr * math.cos(ang), rr * math.sin(ang), z))
np_ = len(profile)
for i in range(seg):
    for j in range(np_ - 1):
        a = i * np_ + j; b = ((i + 1) % seg) * np_ + j
        faces.append((a, b, b + 1, a + 1))
plate = make_obj("Plate", verts, faces, mat("Plate", (0.95, 0.95, 0.94), 0.08, coat=0.4))
plate.modifiers.new("Sub", 'SUBSURF').levels = 2
plate.location.z = 0.02
for ob in (dough, frost):
    ob.location.z += 0.02

# Table
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
table = bpy.context.active_object
table.data.materials.append(mat("Table", (0.35, 0.42, 0.5), 0.6))

# Lights
def area(name, loc, energy, size, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area("Key", (3, -3, 5), 900, 3)
area("Fill", (-4, -2, 3), 300, 4, (0.9, 0.95, 1))
area("Rim", (0, 4, 4), 500, 3, (1, 0.95, 0.9))

world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.8, 0.85, 0.95, 1); bg.inputs["Strength"].default_value = 0.4

# Camera
cd = bpy.data.cameras.new("Cam"); cd.lens = 55
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam)
cam.location = (0, -5.8, 4.2)
cam.rotation_euler = (Vector((0, 0, 0.35)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x, scene.render.resolution_y = 1600, 1200
