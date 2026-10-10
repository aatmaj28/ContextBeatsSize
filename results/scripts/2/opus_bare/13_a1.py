import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

def mat(name, color, rough, coat=0.0, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    def s(k, v):
        if k in b.inputs:
            b.inputs[k].default_value = v
    s("Base Color", (*color, 1.0))
    s("Roughness", rough)
    s("Metallic", metallic)
    s("Coat Weight", coat)
    s("Coat Roughness", 0.05)
    return m

R, r = 1.0, 0.45
SQ = 0.85

def torus_point(u, v, rr):
    return Vector(((R + rr*math.cos(v))*math.cos(u), (R + rr*math.cos(v))*math.sin(u), rr*math.sin(v)))

def torus_normal(u, v):
    return Vector((math.cos(v)*math.cos(u), math.cos(v)*math.sin(u), math.sin(v)))

def make_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    for m in mats:
        me.materials.append(m)
    return o

# --- Donut ---
NU, NV = 64, 32
bm = bmesh.new()
grid = []
for i in range(NU):
    u = 2*math.pi*i/NU
    row = []
    for j in range(NV):
        v = 2*math.pi*j/NV
        p = torus_point(u, v, r + 0.01*math.sin(5*u+3*v))
        row.append(bm.verts.new(p))
    grid.append(row)
for i in range(NU):
    for j in range(NV):
        bm.faces.new((grid[i][j], grid[(i+1)%NU][j], grid[(i+1)%NU][(j+1)%NV], grid[i][(j+1)%NV]))
dough = make_obj("Donut", bm, [mat("Dough", (0.72, 0.40, 0.15), 0.55)])
dough.modifiers.new("Sub", 'SUBSURF').levels = 2

# --- Frosting ---
NU2, NV2 = 96, 28
bm = bmesh.new()
grid = []
for i in range(NU2):
    u = 2*math.pi*i/NU2
    a = 0.35 + 0.15*math.sin(3*u) + 0.1*math.sin(7*u+1.0)
    b = 0.30 + 0.12*math.sin(4*u+2.0) + 0.08*math.sin(9*u)
    v0, v1 = -a, math.pi + b
    row = []
    for j in range(NV2+1):
        v = v0 + (v1 - v0)*j/NV2
        p = torus_point(u, v, r + 0.025)
        row.append(bm.verts.new(p))
    grid.append(row)
for i in range(NU2):
    for j in range(NV2):
        bm.faces.new((grid[i][j], grid[(i+1)%NU2][j], grid[(i+1)%NU2][j+1], grid[i][j+1]))
frost = make_obj("Frosting", bm, [mat("Frosting", (1.0, 0.33, 0.55), 0.12, coat=0.8)])
sol = frost.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.04; sol.offset = 1.0
frost.modifiers.new("Sub", 'SUBSURF').levels = 2

# --- Sprinkles ---
cols = [(0.95,0.9,0.1),(0.1,0.6,1.0),(0.1,0.85,0.3),(1,1,1),(0.9,0.15,0.1),(0.6,0.2,0.9),(1.0,0.5,0.0)]
smats = [mat("Sprinkle%d" % k, c, 0.3, coat=0.5) for k, c in enumerate(cols)]
bm = bmesh.new()
for n in range(220):
    u = random.uniform(0, 2*math.pi)
    v = random.uniform(0.15, math.pi - 0.1)
    p = torus_point(u, v, r + 0.075)
    nrm = torus_normal(u, v)
    rnd = Vector((random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)))
    t = (rnd - nrm*rnd.dot(nrm))
    if t.length < 1e-4:
        continue
    t.normalize()
    bvec = t.cross(nrm)
    rot = Matrix((nrm, bvec, t)).transposed().to_4x4()
    m = Matrix.Translation(p) @ rot
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.022, radius2=0.022,
                                depth=0.13, matrix=m)
    idx = random.randrange(len(cols))
    faces = set()
    for vt in res['verts']:
        faces.update(vt.link_faces)
    for f in faces:
        f.material_index = idx
spr = make_obj("Sprinkles", bm, smats)
spr.modifiers.new("Bevel", 'BEVEL').width = 0.008

plate_top = 0.06
zoff = plate_top + r*SQ
for o in (dough, frost, spr):
    o.location = (0, 0, zoff)
    o.scale = (1, 1, SQ)
    o.rotation_euler = (0, 0, 0.3)

# --- Plate ---
bm = bmesh.new()
prof = [(0.001,0.0),(1.5,0.0),(1.7,0.02),(2.2,0.16),(2.45,0.26),(2.5,0.28),(2.45,0.3),
        (2.15,0.21),(1.65,0.07),(1.5,0.06),(0.001,0.06)]
vs = [bm.verts.new((x, 0, z)) for x, z in prof]
edges = [bm.edges.new((vs[k], vs[k+1])) for k in range(len(vs)-1)]
bmesh.ops.spin(bm, geom=vs+edges, cent=(0,0,0), axis=(0,0,1), angle=2*math.pi, steps=96, use_merge=True)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
plate = make_obj("Plate", bm, [mat("Ceramic", (0.95,0.95,0.95), 0.08, coat=1.0)])
plate.modifiers.new("Sub", 'SUBSURF').levels = 2

# --- Table ---
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
table = bpy.context.active_object
table.data.materials.append(mat("Table", (0.45, 0.6, 0.65), 0.5))

# --- World ---
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.8, 0.85, 0.9, 1)
    bg.inputs[1].default_value = 0.4

# --- Lights ---
def area(name, loc, energy, size, color=(1,1,1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    d = Vector((0,0,0.5)) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
area("Key", (-4, -4, 6), 900, 4, (1.0, 0.96, 0.9))
area("Fill", (5, -3, 3), 250, 5, (0.9, 0.95, 1.0))
area("Rim", (1, 5, 4), 500, 3)

# --- Camera ---
cd = bpy.data.cameras.new("Camera")
cd.lens = 45
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (0, -6.0, 4.4)
target = Vector((0, 0, 0.35))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.frame_start = 1
scene.frame_end = 1
