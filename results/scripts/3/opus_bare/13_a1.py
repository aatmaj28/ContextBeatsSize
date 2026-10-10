import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def make_mat(name, color, rough=0.5, coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    for k, v in (("Coat Weight", coat), ("Coat Roughness", 0.05)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m

# Materials
dough = bpy.data.materials.new("Dough")
dough.use_nodes = True
nt = dough.node_tree
bsdf = nt.nodes.get("Principled BSDF")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 8.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.45, 0.22, 0.07, 1)
ramp.color_ramp.elements[1].color = (0.85, 0.55, 0.25, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.6

frost_mat = make_mat("Frosting", (0.95, 0.35, 0.6), rough=0.12, coat=1.0)
plate_mat = make_mat("Plate", (0.95, 0.95, 0.95), rough=0.15, coat=0.6)
sprinkle_cols = [(0.9, 0.1, 0.1), (0.1, 0.4, 0.95), (0.1, 0.8, 0.2),
                 (1.0, 0.85, 0.1), (0.95, 0.95, 0.95), (0.6, 0.2, 0.9)]
sprinkle_mats = [make_mat(f"Sprinkle{i}", c, rough=0.3, coat=0.5) for i, c in enumerate(sprinkle_cols)]

R, r = 1.0, 0.42
DZ = 0.42

# Donut
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64,
                                 minor_segments=32, location=(0, 0, DZ))
donut = bpy.context.active_object
donut.name = "Donut"
donut.data.materials.append(dough)
donut.modifiers.new("Sub", "SUBSURF").levels = 2
bpy.ops.object.shade_smooth()

# Frosting
fr = 0.445
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=fr, major_segments=128,
                                 minor_segments=48, location=(0, 0, DZ))
frost = bpy.context.active_object
frost.name = "Frosting"
bm = bmesh.new()
bm.from_mesh(frost.data)
dele = []
for v in bm.verts:
    u = math.atan2(v.co.y, v.co.x)
    thr = -0.08 + 0.07 * math.sin(5 * u) + 0.05 * math.sin(13 * u + 1.3)
    if v.co.z < thr:
        dele.append(v)
bmesh.ops.delete(bm, geom=dele, context='VERTS')
bm.to_mesh(frost.data)
bm.free()
frost.data.materials.append(frost_mat)
sol = frost.modifiers.new("Solid", "SOLIDIFY")
sol.thickness = 0.04
sol.offset = -1
frost.modifiers.new("Sub", "SUBSURF").levels = 2
bpy.ops.object.shade_smooth()

# Sprinkles
sp_meshes = []
for i, m in enumerate(sprinkle_mats):
    me = bpy.data.meshes.new(f"SprinkleMesh{i}")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                          radius1=0.022, radius2=0.022, depth=0.13)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    sp_meshes.append(me)

for k in range(220):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(0.25, math.pi - 0.25)
    n = Vector((math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v)))
    pos = Vector((R * math.cos(u), R * math.sin(u), DZ)) + n * (fr + 0.012)
    rnd = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    t = (rnd - n * rnd.dot(n)).normalized()
    b = t.cross(n)
    rot = Matrix((n, b, t)).transposed().to_4x4()
    ob = bpy.data.objects.new(f"Sprinkle{k}", random.choice(sp_meshes))
    ob.matrix_world = Matrix.Translation(pos) @ rot
    scene.collection.objects.link(ob)

# Plate (spun profile)
profile = [(0.0, 0.0), (1.5, 0.0), (1.85, 0.06), (2.15, 0.18), (2.35, 0.27), (2.42, 0.29)]
me = bpy.data.meshes.new("PlateMesh")
bm = bmesh.new()
vs = [bm.verts.new((x, 0, z)) for x, z in profile]
edges = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
bmesh.ops.spin(bm, geom=vs + edges, cent=(0, 0, 0), axis=(0, 0, 1),
               angle=2 * math.pi, steps=96, use_duplicate=False)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
plate = bpy.data.objects.new("Plate", me)
scene.collection.objects.link(plate)
plate.data.materials.append(plate_mat)
ps = plate.modifiers.new("Solid", "SOLIDIFY")
ps.thickness = 0.06
ps.offset = -1
plate.modifiers.new("Sub", "SUBSURF").levels = 2

# Table
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.07))
table = bpy.context.active_object
table.data.materials.append(make_mat("Table", (0.35, 0.25, 0.18), rough=0.5))

# Lights
def area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    c = lo.constraints.new('TRACK_TO')
    c.target = donut
    return lo

area("Key", (3, -3, 5), 800, 3)
area("Fill", (-4, -2, 3), 300, 4, (0.9, 0.95, 1.0))
area("Rim", (0, 4, 4), 500, 3, (1.0, 0.95, 0.9))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1)
bg.inputs["Strength"].default_value = 0.4

# Camera
cd = bpy.data.cameras.new("Cam")
cd.lens = 50
cam = bpy.data.objects.new("Camera", cd)
cam.location = (0, -5.8, 4.2)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 0.3)
scene.collection.objects.link(target)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
