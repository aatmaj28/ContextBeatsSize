import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------------------
# Scene reset
# ---------------------------------------------------------------------------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
col = scene.collection


def link(obj):
    col.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def make_material(name, base, metallic=0.0, roughness=0.5,
                  noise=None, anisotropic=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", base)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Anisotropic", anisotropic)

    if noise is not None:
        lo, hi, scale = noise
        tc = nodes.new("ShaderNodeTexCoord")
        mp = nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale
        nz = nodes.new("ShaderNodeTexNoise")
        set_input(nz, "Detail", 8.0)
        mr = nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = lo
        mr.inputs["To Max"].default_value = hi
        links.new(tc.outputs["Object"], mp.inputs["Vector"])
        links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        links.new(nz.outputs["Fac"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


brushed_steel = make_material(
    "BrushedSteel", (0.78, 0.78, 0.80, 1.0), metallic=1.0,
    noise=(0.16, 0.40, (2.0, 60.0, 2.0)), anisotropic=0.6)
matte_black = make_material(
    "MatteBlack", (0.015, 0.015, 0.016, 1.0), metallic=0.0, roughness=0.75)
ceramic = make_material(
    "WhiteCeramic", (0.92, 0.91, 0.88, 1.0), metallic=0.0, roughness=0.12)
coffee = make_material(
    "Espresso", (0.12, 0.055, 0.02, 1.0), metallic=0.0, roughness=0.35)
floor_mat = make_material(
    "Floor", (0.10, 0.10, 0.105, 1.0), metallic=0.0, roughness=0.6)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def smooth(me):
    for p in me.polygons:
        p.use_smooth = True


def box_obj(name, loc, size, mat, bevel=0.006, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    smooth(me)
    o = bpy.data.objects.new(name, me)
    link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    if bevel > 0:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
    return o


def cyl_obj(name, radius, depth, loc, rot, mat, seg=48):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=radius, radius2=radius, depth=depth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    smooth(me)
    o = bpy.data.objects.new(name, me)
    link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    return o


def lathe_obj(name, profile, loc, mat, segments=64):
    n = len(profile)
    verts = []
    for (r, z) in profile:
        for s in range(segments):
            a = 2.0 * math.pi * s / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    faces = []
    for i in range(n - 1):
        for s in range(segments):
            a = i * segments + s
            b = i * segments + (s + 1) % segments
            c = (i + 1) * segments + (s + 1) % segments
            d = (i + 1) * segments + s
            faces.append((a, b, c, d))
    faces.append(tuple(range(0, segments)))
    faces.append(tuple((n - 1) * segments + s for s in reversed(range(segments))))

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    smooth(me)
    o = bpy.data.objects.new(name, me)
    link(o)
    o.location = loc
    o.data.materials.append(mat)
    return o


def torus_obj(name, major, minor, loc, rot, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    smooth(o.data)
    return o


# ---------------------------------------------------------------------------
# Espresso machine
# ---------------------------------------------------------------------------
# Floor
box_obj("Floor", (0, 0, -0.01), (4.0, 4.0, 0.02), floor_mat, bevel=0.0)

# Matte black base / plinth (z 0 .. 0.10)
box_obj("Base", (0, 0, 0.05), (0.56, 0.42, 0.10), matte_black, bevel=0.02)

# Brushed metal body (z 0.10 .. 0.41)
box_obj("Body", (0, 0, 0.255), (0.50, 0.36, 0.31), brushed_steel, bevel=0.015)

# Matte black top cover (z 0.41 .. 0.44)
box_obj("TopCover", (0, 0, 0.425), (0.52, 0.40, 0.03), matte_black, bevel=0.01)

# Drip tray (brushed metal, sits on base front)
box_obj("DripTray", (0, -0.23, 0.106), (0.34, 0.09, 0.012),
        brushed_steel, bevel=0.003)

# Group head protruding from the front of the body
box_obj("GroupHead", (0, -0.21, 0.24), (0.13, 0.08, 0.11),
        brushed_steel, bevel=0.008)

# Portafilter basket and handle
cyl_obj("PortafilterBasket", 0.035, 0.03, (0, -0.245, 0.23),
        (math.pi / 2, 0, 0), brushed_steel)
cyl_obj("PortafilterHandle", 0.012, 0.16, (0, -0.335, 0.23),
        (math.pi / 2, 0, 0), matte_black)

# Front control knobs
for x in (-0.10, 0.10):
    cyl_obj(f"Knob_{x:+.2f}", 0.013, 0.02, (x, -0.19, 0.36),
            (math.pi / 2, 0, 0), matte_black, seg=32)

# Pressure gauge
cyl_obj("Gauge", 0.03, 0.012, (0.0, -0.19, 0.34),
        (math.pi / 2, 0, 0), ceramic, seg=48)
cyl_obj("GaugeRim", 0.033, 0.006, (0.0, -0.186, 0.34),
        (math.pi / 2, 0, 0), brushed_steel, seg=48)

# Steam wand: vertical arm plus horizontal tip
cyl_obj("SteamWandVertical", 0.008, 0.16, (0.19, -0.20, 0.22),
        (0, 0, 0), brushed_steel, seg=24)
cyl_obj("SteamWandTip", 0.008, 0.07, (0.19, -0.235, 0.14),
        (math.pi / 2, 0, 0), brushed_steel, seg=24)

# Cup on the drip tray
cup_loc = (0.0, -0.245, 0.112)
cup_profile = [
    (0.028, 0.000),
    (0.032, 0.000),
    (0.038, 0.030),
    (0.043, 0.070),
    (0.045, 0.090),
    (0.0415, 0.090),
    (0.039, 0.070),
    (0.034, 0.030),
    (0.030, 0.012),
]
lathe_obj("Cup", cup_profile, cup_loc, ceramic, segments=64)

# Espresso in the cup
cyl_obj("Espresso", 0.037, 0.003, (cup_loc[0], cup_loc[1], cup_loc[2] + 0.074),
        (0, 0, 0), coffee, seg=48)

# Cup handle
torus_obj("CupHandle", 0.014, 0.0035,
          (cup_loc[0] + 0.052, cup_loc[1], cup_loc[2] + 0.05),
          (0, math.pi / 2, 0), ceramic)


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
def aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def area_light(name, loc, energy, size, target, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    link(lo)
    lo.location = loc
    aim(lo, target)
    return lo


area_light("KeyLight", (0.9, -0.9, 1.0), 260, 1.0, (0, -0.05, 0.22))
area_light("FillLight", (-1.0, -0.6, 0.6), 90, 1.5, (0, -0.05, 0.22),
           color=(0.85, 0.92, 1.0))
area_light("RimLight", (-0.4, 1.0, 0.9), 220, 0.8, (0, 0, 0.25),
           color=(1.0, 0.97, 0.92))

# Dark studio world
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.03, 0.035, 1.0)
bg.inputs["Strength"].default_value = 1.0


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
link(cam)
cam.location = (0.80, -0.95, 0.50)
aim(cam, (0.0, -0.04, 0.21))
scene.camera = cam
