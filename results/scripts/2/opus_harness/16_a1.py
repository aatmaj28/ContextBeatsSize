import bpy, bmesh, math, random
from mathutils import Vector, noise

random.seed(7)
scene = bpy.context.scene

# Clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, rough, transmission=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    return m, b

crystal_mat, cb = principled("Amethyst", (0.55, 0.2, 0.9, 1), 0.03, 1.0, 1.54)
cb.inputs["Specular IOR Level"].default_value = 0.6
# volume absorption for deeper color
nt = crystal_mat.node_tree
vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
vol.inputs["Color"].default_value = (0.6, 0.25, 0.95, 1)
vol.inputs["Density"].default_value = 1.5
out = nt.nodes.get("Material Output")
nt.links.new(vol.outputs[0], out.inputs["Volume"])

rock_mat, rb = principled("Rock", (0.035, 0.03, 0.03, 1), 0.85)
ground_mat, gb = principled("Ground", (0.015, 0.015, 0.018, 1), 0.6)

# ---------- Rock ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
for v in bm.verts:
    p = v.co.copy()
    d = noise.fractal(p * 1.5, 0.6, 2.0, 5) * 0.25 + noise.noise(p * 5) * 0.05
    v.co = p * (1 + d)
    v.co.x *= 1.7; v.co.y *= 1.4; v.co.z *= 0.75
rock_me = bpy.data.meshes.new("Rock")
bm.to_mesh(rock_me); bm.free()
for p in rock_me.polygons:
    p.use_smooth = True
rock = bpy.data.objects.new("Rock", rock_me)
rock.location = (0, 0, 0.35)
rock.data.materials.append(rock_mat)
scene.collection.objects.link(rock)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.2))
bpy.context.active_object.data.materials.append(ground_mat)

# ---------- Crystals ----------
def crystal_mesh(name, r, h, t):
    verts, faces = [], []
    n = 6
    for z in (-0.3, h):
        for i in range(n):
            a = 2 * math.pi * i / n
            jit = random.uniform(0.85, 1.1)
            verts.append((r * jit * math.cos(a), r * jit * math.sin(a), z))
    verts.append((random.uniform(-0.1, 0.1) * r, random.uniform(-0.1, 0.1) * r, h + t))
    tip = len(verts) - 1
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((n + i, n + j, tip))
    faces.append(tuple(reversed(range(n))))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me

center = Vector((0.1, 0.0, 1.0))
specs = [(0.0, 0.0, 0.28, 2.2)]
for i in range(14):
    specs.append((random.uniform(0, 50), random.uniform(0, 2 * math.pi),
                  random.uniform(0.08, 0.2), random.uniform(0.5, 1.6)))
for idx, (tilt_deg, az, r, h) in enumerate(specs):
    tilt = math.radians(tilt_deg)
    d = Vector((math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt)))
    me = crystal_mesh(f"Crystal{idx}", r, h, r * random.uniform(1.4, 2.2))
    ob = bpy.data.objects.new(f"Crystal{idx}", me)
    ob.data.materials.append(crystal_mat)
    off = Vector((d.x, d.y, 0)) * 0.35
    ob.location = center + off - Vector((0, 0, 0.12 * math.sin(tilt)))
    ob.rotation_mode = 'QUATERNION'
    q = Vector((0, 0, 1)).rotation_difference(d)
    from mathutils import Quaternion
    ob.rotation_quaternion = q @ Quaternion((0, 0, 1), random.uniform(0, math.pi))
    scene.collection.objects.link(ob)

# ---------- Lights ----------
def area(name, loc, energy, color, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.color = color; ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_mode = 'QUATERNION'
    lo.rotation_quaternion = (Vector((0, 0, 1.2)) - Vector(loc)).to_track_quat('-Z', 'Y')
    scene.collection.objects.link(lo)

area("Key", (4, -3, 5), 900, (1.0, 0.95, 0.9), 3)
area("Rim", (-3, 4, 3), 700, (0.7, 0.5, 1.0), 2)
area("Fill", (-4, -4, 2), 150, (0.8, 0.85, 1.0), 4)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.008, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cd = bpy.data.cameras.new("Camera")
cd.lens = 55
cam = bpy.data.objects.new("Camera", cd)
cam.location = (5.5, -5.5, 3.2)
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (Vector((0, 0, 1.3)) - cam.location).to_track_quat('-Z', 'Y')
scene.collection.objects.link(cam)
scene.camera = cam

# ---------- Render ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.transmission_bounces = 16
scene.cycles.max_bounces = 16
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
