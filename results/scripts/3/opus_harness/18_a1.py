import bpy, bmesh, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, metal=0.0, rough=0.5, aniso=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    return m, b

brushed, bb = principled("BrushedMetal", (0.78, 0.78, 0.8), 1.0, 0.3, 0.7)
nt = brushed.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (300, 300, 3)
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 4.0
nz.inputs["Detail"].default_value = 8.0
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["To Min"].default_value = 0.2
mr.inputs["To Max"].default_value = 0.38
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], bb.inputs["Roughness"])

matte_black, _ = principled("MatteBlack", (0.02, 0.02, 0.022), 0.0, 0.65)
chrome, _ = principled("Chrome", (0.9, 0.9, 0.92), 1.0, 0.08)
ceramic, _ = principled("Ceramic", (0.92, 0.9, 0.86), 0.0, 0.12)
coffee, _ = principled("Coffee", (0.12, 0.05, 0.02), 0.0, 0.15)
gauge_face, _ = principled("GaugeFace", (0.95, 0.95, 0.93), 0.0, 0.3)
red, _ = principled("Needle", (0.8, 0.05, 0.03), 0.0, 0.4)
counter, _ = principled("Counter", (0.35, 0.22, 0.13), 0.0, 0.45)

# ---------- Helpers ----------
def link(obj, mat):
    obj.data.materials.append(mat)
    return obj

def box(name, size, loc, mat, bevel=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 3
    bpy.ops.object.shade_smooth()
    return link(o, mat)

def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width = min(r, depth) * 0.15
    m.segments = 2
    m.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    return link(o, mat)

def lathe(name, profile, loc, mat, segs=64):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile])
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for j in range(len(profile) - 1):
            try:
                bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.location = loc
    return link(o, mat)

# ---------- Counter ----------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
link(bpy.context.active_object, counter)

# ---------- Machine ----------
box("Base", (0.40, 0.44, 0.06), (0, 0, 0.03), matte_black, 0.01)
box("BodyBack", (0.34, 0.24, 0.30), (0, 0.08, 0.06 + 0.15), brushed, 0.008)
box("TopHead", (0.34, 0.42, 0.11), (0, -0.01, 0.36 + 0.055), brushed, 0.01)
box("TopTrim", (0.345, 0.425, 0.012), (0, -0.01, 0.36), matte_black, 0.003)
box("CupWarmer", (0.30, 0.36, 0.008), (0, -0.01, 0.474), chrome, 0.003)
# warmer rail
for x in (-0.15, 0.15):
    cyl("Rail", 0.005, 0.36, (x, -0.01, 0.49), chrome, rot=(math.pi / 2, 0, 0), verts=16)

# drip tray + grate bars
box("DripTray", (0.30, 0.20, 0.02), (0, -0.1, 0.07), matte_black, 0.004)
bar = box("GrateBar", (0.28, 0.008, 0.006), (0, -0.19, 0.083), chrome, 0.002)
arr = bar.modifiers.new("Array", "ARRAY")
arr.count = 12
arr.relative_offset_displace = (0, 2.2, 0)

# group head & portafilter
cyl("GroupHead", 0.045, 0.04, (0, -0.1, 0.34), chrome)
lathe("Basket", [(0, 0.0), (0.035, 0.0), (0.042, 0.01), (0.044, 0.035), (0.05, 0.04), (0, 0.04)],
      (0, -0.1, 0.28), chrome)
cyl("PFNeck", 0.009, 0.06, (0, -0.17, 0.298), chrome, rot=(math.radians(80), 0, 0), verts=24)
cyl("PFHandle", 0.014, 0.13, (0, -0.26, 0.287), matte_black, rot=(math.radians(80), 0, 0), verts=32)
# spouts
for x in (-0.012, 0.012):
    cyl("Spout", 0.005, 0.025, (x, -0.1, 0.268), chrome, verts=16)

# steam wand
cyl("WandJoint", 0.012, 0.03, (0.14, -0.17, 0.345), chrome)
cyl("SteamWand", 0.005, 0.2, (0.15, -0.19, 0.25), chrome, rot=(math.radians(-8), math.radians(4), 0), verts=16)
cyl("WandKnob", 0.018, 0.025, (0.14, -0.2, 0.43), matte_black, rot=(math.pi / 2, 0, 0))

# gauge
cyl("GaugeRim", 0.032, 0.015, (0.07, -0.222, 0.42), chrome, rot=(math.pi / 2, 0, 0))
cyl("GaugeFace", 0.027, 0.004, (0.07, -0.231, 0.42), gauge_face, rot=(math.pi / 2, 0, 0))
needle = box("Needle", (0.002, 0.001, 0.022), (0.07, -0.234, 0.427), red, 0)
needle.rotation_euler = (0, math.radians(35), 0)

# buttons
for i, x in enumerate((-0.12, -0.085, -0.05)):
    cyl("Button%d" % i, 0.011, 0.012, (x, -0.222, 0.42), matte_black, rot=(math.pi / 2, 0, 0), verts=32)

# feet
for x in (-0.17, 0.17):
    for y in (-0.19, 0.19):
        cyl("Foot", 0.015, 0.01, (x, y, 0.0), matte_black, verts=24)

# ---------- Cup ----------
cup_z = 0.086
cup_prof = [(0, 0), (0.022, 0), (0.026, 0.004), (0.03, 0.045), (0.032, 0.058), (0.029, 0.058),
            (0.027, 0.046), (0.022, 0.008), (0, 0.008)]
lathe("Cup", cup_prof, (0, -0.1, cup_z), ceramic)
lathe("Crema", [(0, 0), (0.0272, 0)], (0, -0.1, cup_z + 0.04), coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.004,
                                 location=(0.036, -0.1, cup_z + 0.03), rotation=(math.pi / 2, 0, 0))
h = bpy.context.active_object
h.name = "CupHandle"
bpy.ops.object.shade_smooth()
link(h, ceramic)

# ---------- World & Lights ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
bg.inputs["Strength"].default_value = 0.6

def area(name, loc, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    direction = Vector((0, -0.05, 0.25)) - Vector(loc)
    o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return o

area("Key", (-0.8, -0.9, 1.0), 120, 0.8, (1.0, 0.95, 0.9))
area("Fill", (1.0, -0.6, 0.5), 40, 1.2, (0.85, 0.9, 1.0))
area("Rim", (0.3, 1.0, 1.0), 80, 0.6)

# ---------- Camera ----------
cam_d = bpy.data.cameras.new("Camera")
cam_d.lens = 50
cam = bpy.data.objects.new("Camera", cam_d)
scene.collection.objects.link(cam)
cam.location = (0.62, -1.05, 0.55)
target = Vector((0, -0.03, 0.24))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
scene.frame_start = 1
scene.frame_end = 1
