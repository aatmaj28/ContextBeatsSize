import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough, coat=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat > 0:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    return m

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# Table
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
table = bpy.context.active_object
table.data.materials.append(mat("Table", (0.35, 0.22, 0.13), 0.5))

# Plate via spin
bm = bmesh.new()
prof = [(0, 0.01), (1.4, 0.01), (1.6, 0.04), (2.1, 0.17), (2.2, 0.2), (2.17, 0.22),
        (2.08, 0.2), (1.58, 0.09), (1.4, 0.07), (0, 0.07)]
vs = [bm.verts.new((r, 0, z)) for r, z in prof]
es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=96, use_merge=True)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
me = bpy.data.meshes.new("Plate")
bm.to_mesh(me); bm.free()
plate = bpy.data.objects.new("Plate", me)
scene.collection.objects.link(plate)
smooth(plate)
plate.modifiers.new("Sub", "SUBSURF").levels = 2
plate.data.materials.append(mat("PlateMat", (0.95, 0.95, 0.93), 0.08, coat=0.6))

R, r, SZ = 1.0, 0.42, 0.85
CZ = 0.07 + r * SZ
# Donut bread
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=72, minor_segments=36, location=(0, 0, CZ))
donut = bpy.context.active_object
donut.scale.z = SZ
smooth(donut)
donut.modifiers.new("Sub", "SUBSURF").levels = 1
donut.data.materials.append(mat("Dough", (0.78, 0.47, 0.2), 0.55))

# Frosting
rf = 0.445
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=rf, major_segments=96, minor_segments=48, location=(0, 0, CZ))
frost = bpy.context.active_object
frost.scale.z = SZ
bm = bmesh.new(); bm.from_mesh(frost.data)
kill = []
for v in bm.verts:
    u = math.atan2(v.co.y, v.co.x)
    rad = math.hypot(v.co.x, v.co.y)
    th = 0.02 + 0.07 * math.sin(5 * u) + 0.04 * math.sin(13 * u + 1.3)
    if rad < R:
        th = 0.05 + 0.04 * math.sin(7 * u + 0.5)
    if v.co.z < th:
        kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(frost.data); bm.free()
smooth(frost)
so = frost.modifiers.new("Solid", "SOLIDIFY"); so.thickness = 0.02; so.offset = 1
frost.modifiers.new("Sub", "SUBSURF").levels = 2
frost.data.materials.append(mat("Frosting", (1.0, 0.32, 0.55), 0.15, coat=0.8))

# Sprinkles
cols = [(1, 0.9, 0.1), (0.1, 0.5, 1), (0.2, 0.85, 0.3), (1, 1, 1), (0.6, 0.2, 0.9), (1, 0.45, 0.05)]
bm = bmesh.new()
for i in range(260):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(0.35, math.pi - 0.35)
    radial = Vector((math.cos(u), math.sin(u), 0))
    n = (radial * math.cos(v) + Vector((0, 0, 1)) * math.sin(v)).normalized()
    p = radial * R + n * (rf + 0.03)
    p.z = p.z * SZ + CZ
    a = n.orthogonal().normalized()
    b = n.cross(a)
    ang = random.uniform(0, 2 * math.pi)
    t = (a * math.cos(ang) + b * math.sin(ang)).normalized()
    t = (t + n * random.uniform(-0.15, 0.15)).normalized()
    x = n.cross(t).normalized(); y = t.cross(x)
    m = Matrix((
        (x.x, y.x, t.x, p.x),
        (x.y, y.y, t.y, p.y),
        (x.z, y.z, t.z, p.z),
        (0, 0, 0, 1)))
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.018, radius2=0.018,
                                depth=0.12, matrix=m)
    idx = random.randrange(len(cols))
    fs = {f for vv in res['verts'] for f in vv.link_faces}
    for f in fs:
        f.material_index = idx
        f.smooth = True
me = bpy.data.meshes.new("Sprinkles")
bm.to_mesh(me); bm.free()
spr = bpy.data.objects.new("Sprinkles", me)
scene.collection.objects.link(spr)
for i, c in enumerate(cols):
    me.materials.append(mat("Sprinkle%d" % i, c, 0.2, coat=0.5))

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
bg.inputs["Strength"].default_value = 0.4

# Lights
def area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy; ld.size = size; ld.color = color
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 0.4)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area("Key", (3.5, -3, 5), 900, 3, (1, 0.95, 0.88))
area("Fill", (-4, -2, 3), 300, 4, (0.85, 0.9, 1))
area("Rim", (0, 5, 4), 500, 3)

# Camera
cd = bpy.data.cameras.new("Cam"); cd.lens = 50
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
cam.location = (0, -6.0, 4.2)
cam.rotation_euler = (Vector((0, 0, 0.35)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
