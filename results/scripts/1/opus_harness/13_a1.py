import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.4, coat=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
    return m

def obj_from_bm(name, bm, mats, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

R, r = 0.5, 0.22
ZC = 0.04 + r

def tpos(u, phi, rad):
    return Vector(((R + rad*math.cos(phi))*math.cos(u), (R + rad*math.cos(phi))*math.sin(u), ZC + rad*math.sin(phi)))

def grid_surface(name, nu, nv, func, closed_v):
    bm = bmesh.new()
    rows = []
    for i in range(nu):
        rows.append([bm.verts.new(func(i/nu, j/(nv if closed_v else nv-1))) for j in range(nv)])
    for i in range(nu):
        a, b = rows[i], rows[(i+1) % nu]
        jr = nv if closed_v else nv-1
        for j in range(jr):
            j2 = (j+1) % nv
            bm.faces.new((a[j], b[j], b[j2], a[j2]))
    return bm

# Donut dough
dough_mat = mat("Dough", (0.62, 0.36, 0.15), 0.55, 0.0, 0.1)
def dough_f(s, t):
    u, phi = s*2*math.pi, t*2*math.pi
    return tpos(u, phi, r*(1 + 0.02*math.sin(5*u + 3*phi)))
donut = obj_from_bm("Donut", grid_surface("Donut", 96, 48, dough_f, True), [dough_mat])
donut.modifiers.new("Sub", 'SUBSURF').levels = 2

# Frosting with wavy drips
frost_mat = mat("Frosting", (0.95, 0.35, 0.6), 0.15, 0.6)
def wave(u):
    return 0.18*math.sin(7*u) + 0.1*math.sin(13*u + 1.3) + 0.08*math.sin(23*u)
def frost_f(s, t):
    u = s*2*math.pi
    p0 = -0.35 + wave(u)
    p1 = math.pi + 0.3 - 0.7*wave(u + 2.0)
    phi = p0 + (p1 - p0)*t
    return tpos(u, phi, r*1.07)
frost = obj_from_bm("Frosting", grid_surface("Frosting", 160, 40, frost_f, False), [frost_mat])
sol = frost.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.02; sol.offset = -1
frost.modifiers.new("Sub", 'SUBSURF').levels = 2

# Sprinkles
cols = [(1, 0.1, 0.1), (1, 0.85, 0.1), (0.1, 0.5, 1), (0.2, 0.85, 0.3), (1, 1, 1), (0.6, 0.2, 0.9), (1, 0.5, 0.05)]
smats = [mat("Sprinkle%d" % i, c, 0.25, 0.5) for i, c in enumerate(cols)]
bm = bmesh.new()
for k in range(220):
    u = random.uniform(0, 2*math.pi)
    phi = random.uniform(0.25, 2.75)
    n = Vector((math.cos(phi)*math.cos(u), math.cos(phi)*math.sin(u), math.sin(phi)))
    rv = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    t = (rv - n*rv.dot(n)).normalized()
    x = n.cross(t)
    rot = Matrix((x, n, t)).transposed().to_4x4()
    pos = tpos(u, phi, r*1.07 + 0.026)
    M = Matrix.Translation(pos) @ rot
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.011, radius2=0.011, depth=0.06, matrix=M)
    mi = random.randrange(len(cols))
    fs = set()
    for v in res['verts']:
        fs.update(v.link_faces)
    for f in fs:
        f.material_index = mi
sprinkles = obj_from_bm("Sprinkles", bm, smats)

# Plate (lathe)
plate_mat = mat("Plate", (0.95, 0.95, 0.93), 0.08, 0.8)
prof = [(0.0, 0.04), (0.7, 0.04), (0.85, 0.06), (1.0, 0.11), (1.1, 0.14), (1.14, 0.135),
        (1.08, 0.1), (0.95, 0.05), (0.75, 0.02), (0.6, 0.0), (0.0, 0.0)]
def plate_f(s, t):
    a = s*2*math.pi
    idx = t*(len(prof)-1)
    i = min(int(idx), len(prof)-2); f = idx - i
    rr = prof[i][0]*(1-f) + prof[i+1][0]*f
    z = prof[i][1]*(1-f) + prof[i+1][1]*f
    return Vector((rr*math.cos(a), rr*math.sin(a), z))
plate = obj_from_bm("Plate", grid_surface("Plate", 96, len(prof), plate_f, False), [plate_mat])
plate.modifiers.new("Sub", 'SUBSURF').levels = 2

# Table
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(mat("Table", (0.35, 0.5, 0.6), 0.6))

# World
world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1)
bg.inputs["Strength"].default_value = 0.4

# Lights
def area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    scene.collection.objects.link(lo)
    d = Vector((0, 0, 0.2)) - Vector(loc)
    lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
area("Key", (2.5, -2.0, 3.0), 400, 2.0, (1, 0.95, 0.9))
area("Fill", (-3.0, -1.5, 2.0), 150, 3.0, (0.85, 0.9, 1))
area("Rim", (-1.0, 3.0, 2.5), 250, 1.5)

# Camera
cd = bpy.data.cameras.new("Cam"); cd.lens = 55
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam)
cam.location = (0, -3.0, 2.2)
cam.rotation_euler = (Vector((0, 0, 0.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
