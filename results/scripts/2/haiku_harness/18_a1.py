import bpy
import bmesh
import mathutils
import math
import random

random.seed(7)

# ---------- Scene reset ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1


# ---------- Helpers ----------
def set_input(bsdf, name, value):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = value


def make_material(name, color, metallic=0.0, roughness=0.5, aniso=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (color[0], color[1], color[2], 1.0))
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Anisotropic", aniso)
    set_input(bsdf, "Coat Weight", coat)
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def add_bevel(obj, width, segs=3, angle_deg=35):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)


def mesh_obj(name, bm, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    return obj


def box(name, dims, loc, bevel=0.0, segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    obj = mesh_obj(name, bm, loc)
    smooth(obj)
    if bevel > 0:
        add_bevel(obj, bevel, segs)
    return obj


def cylinder(name, radius, depth, loc, rot=(0, 0, 0), segments=48):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    obj = mesh_obj(name, bm, loc, rot)
    smooth(obj)
    return obj


def lathe(name, profile, loc=(0, 0, 0), seg=64):
    """Revolve a (radius, z) profile around the Z axis."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            ring = []
            for i in range(seg):
                a = 2.0 * math.pi * i / seg
                ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rings.append(ring)

    def pick(ring, j):
        return ring[j % len(ring)]

    for i in range(len(rings) - 1):
        ring_a, ring_b = rings[i], rings[i + 1]
        count = max(len(ring_a), len(ring_b))
        n = seg if max(len(ring_a), len(ring_b)) > 1 else 1
        for j in range(n):
            a = pick(ring_a, j)
            b = pick(ring_a, j + 1)
            c = pick(ring_b, j + 1)
            d = pick(ring_b, j)
            verts = []
            for v in (a, b, c, d):
                if v not in verts:
                    verts.append(v)
            if len(verts) >= 3:
                try:
                    bm.faces.new(verts)
                except ValueError:
                    pass
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    obj = mesh_obj(name, bm, loc)
    smooth(obj)
    return obj


def aim(obj, target):
    direction = mathutils.Vector(target) - obj.location
    quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = quat.to_euler()


# ---------- Materials ----------
steel_mat = make_material("BrushedSteel", (0.78, 0.78, 0.80),
                          metallic=1.0, roughness=0.3, aniso=0.6)
black_mat = make_material("MatteBlack", (0.02, 0.02, 0.022),
                          metallic=0.0, roughness=0.65)
chrome_mat = make_material("Chrome", (0.9, 0.9, 0.92),
                           metallic=1.0, roughness=0.08)
ceramic_mat = make_material("CeramicWhite", (0.92, 0.9, 0.86),
                            metallic=0.0, roughness=0.15)
coffee_mat = make_material("Crema", (0.12, 0.06, 0.025),
                           metallic=0.0, roughness=0.25)

# Brushed streak variation on the steel roughness
steel_nodes = steel_mat.node_tree.nodes
steel_links = steel_mat.node_tree.links
bsdf_steel = steel_nodes.get("Principled BSDF")
noise = steel_nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 180.0
noise.inputs["Detail"].default_value = 4.0
noise.inputs["Roughness"].default_value = 0.4
mrange = steel_nodes.new("ShaderNodeMapRange")
mrange.inputs["From Min"].default_value = 0.0
mrange.inputs["From Max"].default_value = 1.0
mrange.inputs["To Min"].default_value = 0.22
mrange.inputs["To Max"].default_value = 0.42
steel_links.new(noise.outputs["Fac"], mrange.inputs["Value"])
steel_links.new(mrange.outputs["Result"], bsdf_steel.inputs["Roughness"])


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


# ---------- Machine geometry ----------
parts = []

# Matte black base / drip support
base = box("Base", (1.0, 0.78, 0.10), (0, 0, 0.05), bevel=0.02)
parts.append(assign(base, black_mat))

# Brushed steel body
body = box("Body", (0.90, 0.62, 0.70), (0, 0, 0.45), bevel=0.035, segs=4)
parts.append(assign(body, steel_mat))

# Black top cap
top = box("TopCap", (0.94, 0.66, 0.03), (0, 0, 0.815), bevel=0.01)
parts.append(assign(top, black_mat))

# Front panel recess (black strip)
panel = box("Panel", (0.62, 0.01, 0.22), (0, -0.316, 0.66), bevel=0.005)
parts.append(assign(panel, black_mat))

# Group head (chrome cylinder pointing forward)
group = cylinder("GroupHead", 0.07, 0.16, (0, -0.36, 0.42),
                 rot=(math.radians(90), 0, 0))
parts.append(assign(group, chrome_mat))

# Group head cap ring
ring = cylinder("GroupRing", 0.09, 0.03, (0, -0.42, 0.42),
                rot=(math.radians(90), 0, 0))
parts.append(assign(ring, chrome_mat))

# Portafilter basket
basket = cylinder("Basket", 0.06, 0.03, (0, -0.47, 0.36),
                  rot=(math.radians(90), 0, 0))
parts.append(assign(basket, steel_mat))

# Portafilter handle
handle = cylinder("PortaHandle", 0.018, 0.22, (0, -0.60, 0.36),
                  rot=(math.radians(90), 0, 0))
parts.append(assign(handle, black_mat))

# Steam wand
wand = cylinder("SteamWand", 0.011, 0.20, (0.30, -0.42, 0.26),
                rot=(math.radians(90), 0, 0))
parts.append(assign(wand, chrome_mat))
wand_tip = cylinder("WandTip", 0.014, 0.03, (0.30, -0.53, 0.26),
                    rot=(math.radians(90), 0, 0))
parts.append(assign(wand_tip, chrome_mat))

# Pressure gauges on the front panel
for x in (-0.18, 0.18):
    gauge = cylinder("Gauge", 0.04, 0.012, (x, -0.33, 0.66),
                     rot=(math.radians(90), 0, 0))
    parts.append(assign(gauge, chrome_mat))
    dial = cylinder("Dial", 0.032, 0.014, (x, -0.335, 0.66),
                    rot=(math.radians(90), 0, 0))
    parts.append(assign(dial, ceramic_mat))

# Control knobs / buttons
for i, x in enumerate((-0.05, 0.05)):
    btn = cylinder("Button", 0.022, 0.02, (x, -0.33, 0.56),
                   rot=(math.radians(90), 0, 0))
    parts.append(assign(btn, black_mat))

# Drip tray (brushed steel grate area)
tray = box("DripTray", (0.72, 0.22, 0.025), (0, -0.44, 0.1125), bevel=0.008)
parts.append(assign(tray, steel_mat))
grate = box("Grate", (0.64, 0.16, 0.008), (0, -0.44, 0.13), bevel=0.003)
parts.append(assign(grate, black_mat))

# Small espresso cup on the tray, under the basket
cup_profile = [
    (0.0, 0.0),
    (0.030, 0.0),
    (0.036, 0.006),
    (0.044, 0.056),
    (0.038, 0.056),
    (0.031, 0.012),
    (0.0, 0.012),
]
cup = lathe("EspressoCup", cup_profile, loc=(0, -0.47, 0.1275))
parts.append(assign(cup, ceramic_mat))

# Espresso in the cup
crema = cylinder("Crema", 0.031, 0.004, (0, -0.47, 0.1275 + 0.045),
                 segments=40)
parts.append(assign(crema, coffee_mat))

# Saucer under the cup
saucer_profile = [
    (0.0, 0.0),
    (0.055, 0.0),
    (0.062, 0.006),
    (0.058, 0.009),
    (0.0, 0.007),
]
saucer = lathe("Saucer", saucer_profile, loc=(0, -0.47, 0.1275 - 0.001))
parts.append(assign(saucer, ceramic_mat))

# Slight random micro-variation to the knob positions is not needed; keep clean.

# ---------- World ----------
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.04, 0.04, 0.045, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lighting ----------
target = (0.0, -0.1, 0.45)


def make_area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    aim(lo, target)
    return lo


key = make_area("KeyLight", (1.9, -1.9, 2.0), 350.0, 1.6, (1.0, 0.97, 0.93))
rim = make_area("RimLight", (-1.6, 1.8, 1.7), 260.0, 1.2, (0.85, 0.92, 1.0))
fill = make_area("FillLight", (1.2, -2.6, 0.7), 90.0, 2.5, (1.0, 1.0, 1.0))

# Soft top light for the metal highlights
top_light = make_area("TopLight", (0.0, -0.3, 2.6), 180.0, 1.5)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55.0
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 2.9
cam_data.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (1.9, -2.35, 1.05)
scene.collection.objects.link(cam)
aim(cam, target)
scene.camera = cam
