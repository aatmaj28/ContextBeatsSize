import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, metallic=0.0, roughness=0.5, anisotropic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Anisotropic" in bsdf.inputs:
        bsdf.inputs["Anisotropic"].default_value = anisotropic
    if "Anisotropic Rotation" in bsdf.inputs:
        bsdf.inputs["Anisotropic Rotation"].default_value = 0.0
    return mat


def link(obj):
    collection.objects.link(obj)
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def add_bevel(obj, width=0.008, segments=3):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'


def make_box(name, loc, dims, mat, bevel=0.008):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    link(obj)
    obj.data.materials.append(mat)
    if bevel > 0:
        add_bevel(obj, bevel)
    smooth(obj)
    return obj


def make_cylinder(name, radius, depth, loc, rot, mat, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth,
        location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    # Move from default collection to ours
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def make_sphere(name, radius, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=32, ring_count=16)
    obj = bpy.context.active_object
    obj.name = name
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def make_torus(name, major, minor, loc, rot, mat):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, location=loc, rotation=rot,
        major_segments=48, minor_segments=12)
    obj = bpy.context.active_object
    obj.name = name
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


# ---------- Materials ----------
mat_brushed = make_material("BrushedSteel", (0.75, 0.75, 0.77), metallic=1.0,
                            roughness=0.32, anisotropic=0.6)
mat_black = make_material("MatteBlack", (0.02, 0.02, 0.022), metallic=0.0, roughness=0.85)
mat_dark_metal = make_material("DarkChrome", (0.12, 0.12, 0.13), metallic=1.0, roughness=0.2)
mat_ceramic = make_material("WhiteCeramic", (0.92, 0.9, 0.86), metallic=0.0, roughness=0.12)
mat_coffee = make_material("Espresso", (0.12, 0.05, 0.02), metallic=0.0, roughness=0.6)
mat_gauge_glass = make_material("GaugeGlass", (0.05, 0.08, 0.1), metallic=0.0, roughness=0.05)
mat_wood_handle = make_material("HandleBlack", (0.01, 0.01, 0.01), metallic=0.0, roughness=0.4)
mat_floor = make_material("Floor", (0.18, 0.18, 0.19), metallic=0.0, roughness=0.7)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
for c in floor.users_collection:
    c.objects.unlink(floor)
collection.objects.link(floor)
floor.data.materials.append(mat_floor)

# ---------- Espresso machine ----------
# Matte black base / plinth
base = make_box("Base", (0, 0, 0.04), (0.52, 0.40, 0.08), mat_black, bevel=0.012)

# Brushed metal main body
body = make_box("Body", (0, 0.0, 0.33), (0.46, 0.36, 0.50), mat_brushed, bevel=0.022)

# Top cap (rounded, black accent strip on top)
top = make_box("TopCap", (0, 0.0, 0.60), (0.48, 0.38, 0.03), mat_black, bevel=0.010)

# Drip tray recessed in front of base
drip_tray = make_box("DripTray", (0, -0.24, 0.095), (0.36, 0.09, 0.02), mat_dark_metal, bevel=0.005)
drip_grate = make_box("DripGrate", (0, -0.24, 0.108), (0.32, 0.07, 0.004), mat_black, bevel=0.002)

# Front panel with black insert
front_panel = make_box("FrontPanel", (0, -0.185, 0.40), (0.40, 0.01, 0.34), mat_black, bevel=0.006)

# Group head (brew unit) protruding from front panel
group_head = make_cylinder("GroupHead", 0.045, 0.07, (0, -0.215, 0.27),
                           (math.radians(90), 0, 0), mat_dark_metal)
group_ring = make_cylinder("GroupRing", 0.05, 0.02, (0, -0.25, 0.27),
                           (math.radians(90), 0, 0), mat_dark_metal)

# Portafilter: basket, neck, and handle
basket = make_cylinder("PortafilterBasket", 0.032, 0.02, (0, -0.265, 0.205),
                       (math.radians(90), 0, 0), mat_dark_metal, verts=40)
pf_neck = make_cylinder("PortafilterNeck", 0.018, 0.04, (0, -0.30, 0.205),
                        (math.radians(90), 0, 0), mat_dark_metal, verts=32)
pf_handle = make_cylinder("PortafilterHandle", 0.013, 0.16, (0, -0.42, 0.195),
                          (math.radians(90), 0, 0), mat_wood_handle, verts=24)
pf_handle_end = make_sphere("PortafilterHandleEnd", 0.015, (0, -0.505, 0.195), mat_wood_handle)

# Steam wand on the right side
steam_wand = make_cylinder("SteamWand", 0.007, 0.16, (0.20, -0.20, 0.30),
                           (math.radians(70), 0, 0), mat_dark_metal, verts=20)
steam_tip = make_cylinder("SteamTip", 0.009, 0.02, (0.20, -0.27, 0.36),
                          (math.radians(70), 0, 0), mat_dark_metal, verts=20)

# Hot-water wand on left side
hot_wand = make_cylinder("HotWater", 0.006, 0.10, (-0.19, -0.20, 0.26),
                         (math.radians(80), 0, 0), mat_dark_metal, verts=20)

# Pressure gauge on front panel
gauge_ring = make_cylinder("GaugeRing", 0.040, 0.012, (0, -0.196, 0.52),
                           (math.radians(90), 0, 0), mat_dark_metal, verts=48)
gauge_face = make_cylinder("GaugeFace", 0.034, 0.010, (0, -0.197, 0.52),
                           (math.radians(90), 0, 0), mat_gauge_glass, verts=48)

# Steam/hot water knobs
for i, x in enumerate([-0.12, 0.12]):
    knob = make_cylinder(f"Knob{i}", 0.018, 0.025, (x, -0.20, 0.38),
                         (math.radians(90), 0, 0), mat_dark_metal, verts=32)

# Cup wood-free feet/tray detail: small cup warmer strip on top
warmer = make_box("CupWarmer", (0, 0.02, 0.63), (0.30, 0.22, 0.012), mat_dark_metal, bevel=0.004)

# Small cup under the portafilter
CUP_Z = 0.095
cup_outer = make_cylinder("CupBody", 0.036, 0.07, (0, -0.265, CUP_Z + 0.035), (0, 0, 0),
                          mat_ceramic, verts=56)
add_bevel(cup_outer, 0.003, 2)
cup_saucer = make_cylinder("CupSaucer", 0.048, 0.006, (0, -0.265, CUP_Z + 0.003), (0, 0, 0),
                           mat_ceramic, verts=56)
cup_coffee = make_cylinder("CupCoffee", 0.031, 0.002, (0, -0.265, CUP_Z + 0.066), (0, 0, 0),
                           mat_coffee, verts=40)
cup_handle = make_torus("CupHandle", 0.016, 0.0035, (0.046, -0.265, CUP_Z + 0.035),
                        (0, math.radians(90), 0), mat_ceramic)

# Feet under the base
for x in (-0.22, 0.22):
    for y in (-0.16, 0.16):
        make_cylinder(f"Foot_{x}_{y}", 0.018, 0.012, (x, y, 0.006), (0, 0, 0), mat_black, verts=24)

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 0.6
scene.world = world

# ---------- Lights ----------
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 900
key_data.size = 1.2
key_data.color = (1.0, 0.97, 0.93)
key = link(bpy.data.objects.new("KeyLight", key_data))
key.location = (0.9, -0.9, 1.1)
key.rotation_euler = (math.radians(60), 0, math.radians(45))

rim_data = bpy.data.lights.new(name="RimLight", type='AREA')
rim_data.energy = 500
rim_data.size = 0.8
rim_data.color = (0.8, 0.9, 1.0)
rim = link(bpy.data.objects.new("RimLight", rim_data))
rim.location = (-0.9, 0.9, 0.9)
rim.rotation_euler = (math.radians(60), 0, math.radians(-135))

fill_data = bpy.data.lights.new(name="FillLight", type='SUN')
fill_data.energy = 1.5
fill = link(bpy.data.objects.new("FillLight", fill_data))
fill.rotation_euler = (math.radians(70), 0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70
cam_data.dof.use_dof = False
cam = link(bpy.data.objects.new("Camera", cam_data))
cam.location = Vector((0.75, -1.05, 0.62))
target = Vector((0.0, -0.02, 0.32))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Frame range (static scene) ----------
scene.frame_start = 1
scene.frame_end = 1
