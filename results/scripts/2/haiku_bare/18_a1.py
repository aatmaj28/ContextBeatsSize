import bpy
import bmesh
import math
from mathutils import Matrix, Vector, Euler

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
collection = bpy.context.collection


# ---------- Materials ----------
def make_mat(name, color, metallic=0.0, roughness=0.5, aniso=0.0, aniso_rot=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

    def setin(key, value):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value

    setin("Base Color", (color[0], color[1], color[2], 1.0))
    setin("Metallic", metallic)
    setin("Roughness", roughness)
    setin("Anisotropic", aniso)
    setin("Anisotropic Rotation", aniso_rot)
    setin("Coat Weight", coat)
    return mat


metal_brushed = make_mat("BrushedSteel", (0.72, 0.72, 0.74), metallic=1.0,
                         roughness=0.28, aniso=0.8, aniso_rot=0.0)
black_matte = make_mat("MatteBlack", (0.015, 0.015, 0.016), metallic=0.0, roughness=0.9)
black_tank = make_mat("TankBlack", (0.03, 0.03, 0.032), metallic=0.0, roughness=0.55, coat=0.3)
handle_mat = make_mat("HandleBlack", (0.02, 0.02, 0.02), metallic=0.0, roughness=0.35, coat=0.5)
ceramic = make_mat("CeramicWhite", (0.92, 0.91, 0.88), metallic=0.0, roughness=0.18, coat=0.4)
coffee = make_mat("Espresso", (0.12, 0.05, 0.02), metallic=0.0, roughness=0.25, coat=0.6)
chrome = make_mat("Chrome", (0.9, 0.9, 0.92), metallic=1.0, roughness=0.08)
floor_mat = make_mat("Floor", (0.55, 0.54, 0.52), metallic=0.0, roughness=0.8)
accent_red = make_mat("IndicatorRed", (0.8, 0.05, 0.02), metallic=0.0, roughness=0.3, coat=0.3)


# ---------- Geometry helpers ----------
def prim(name, kind, dims, loc, rot=(0.0, 0.0, 0.0), mat=None,
         bevel=0.0, segs=64, smooth=True):
    bm = bmesh.new()
    if kind == "box":
        bmesh.ops.create_cube(bm, size=1.0)
        scale = Matrix.Diagonal((dims[0], dims[1], dims[2], 1.0))
    else:  # cylinder: dims = (radius, height)
        r, h = dims
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                              radius1=0.5, radius2=0.5, depth=1.0)
        scale = Matrix.Diagonal((2.0 * r, 2.0 * r, h, 1.0))

    transform = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ scale
    bmesh.ops.transform(bm, matrix=transform, verts=bm.verts)

    if smooth:
        for f in bm.faces:
            f.smooth = True

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    if mat is not None:
        obj.data.materials.append(mat)

    if bevel > 0.0:
        mod = obj.modifiers.new(name="Bevel", type='BEVEL')
        mod.width = bevel
        mod.segments = 4
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35)

    return obj


# ---------- Espresso machine ----------
parts = []

# Matte black base plinth
parts.append(prim("Base", "box", (0.62, 0.46, 0.08), (0, 0, 0.04),
                  mat=black_matte, bevel=0.02))

# Brushed metal main body
parts.append(prim("Body", "box", (0.52, 0.40, 0.40), (0, 0.0, 0.28),
                  mat=metal_brushed, bevel=0.03))

# Top cap
parts.append(prim("TopCap", "box", (0.54, 0.42, 0.03), (0, 0.0, 0.495),
                  mat=metal_brushed, bevel=0.012))

# Front panel (matte black inset for a two-tone look)
parts.append(prim("FrontPanel", "box", (0.44, 0.01, 0.30), (0, -0.205, 0.29),
                  mat=black_matte, bevel=0.008))

# Water tank on top-rear
parts.append(prim("WaterTank", "box", (0.30, 0.22, 0.18), (0.0, 0.07, 0.62),
                  mat=black_tank, bevel=0.03))

# Tank cap
parts.append(prim("TankCap", "cyl", (0.04, 0.02), (0.0, 0.07, 0.72),
                  mat=chrome))

# Group head (cylinder facing forward along -Y)
parts.append(prim("GroupHead", "cyl", (0.065, 0.10), (0.0, -0.27, 0.29),
                  rot=(math.radians(90), 0, 0), mat=chrome))

# Group head collar
parts.append(prim("GroupCollar", "cyl", (0.085, 0.03), (0.0, -0.245, 0.29),
                  rot=(math.radians(90), 0, 0), mat=metal_brushed))

# Portafilter basket (dark ring)
parts.append(prim("PortafilterBasket", "cyl", (0.055, 0.025), (0.0, -0.335, 0.29),
                  rot=(math.radians(90), 0, 0), mat=black_matte))

# Portafilter handle
parts.append(prim("PortafilterHandle", "cyl", (0.018, 0.22), (0.0, -0.49, 0.27),
                  rot=(math.radians(90), 0, 0), mat=handle_mat))

# Steam wand on the right side, angled outward
parts.append(prim("SteamWand", "cyl", (0.012, 0.22), (0.27, -0.05, 0.22),
                  rot=(math.radians(-15), 0, math.radians(-8)), mat=chrome))

# Steam wand tip
parts.append(prim("SteamTip", "cyl", (0.018, 0.03), (0.275, -0.12, 0.10),
                  rot=(math.radians(-15), 0, math.radians(-8)), mat=chrome))

# Drip tray (matte black, front-bottom)
parts.append(prim("DripTray", "box", (0.40, 0.18, 0.025), (0.0, -0.22, 0.095),
                  mat=black_matte, bevel=0.008))

# Drip grate
parts.append(prim("DripGrate", "box", (0.34, 0.12, 0.006), (0.0, -0.22, 0.11),
                  mat=chrome))

# Control knobs on front panel
for i, x in enumerate([-0.14, 0.0, 0.14]):
    parts.append(prim("Knob%d" % i, "cyl", (0.022, 0.02), (x, -0.22, 0.36),
                      rot=(math.radians(90), 0, 0), mat=chrome))

# Indicator light
parts.append(prim("Indicator", "cyl", (0.008, 0.01), (0.19, -0.222, 0.36),
                  rot=(math.radians(90), 0, 0), mat=accent_red))

# Small drip spout cover pieces
parts.append(prim("SpoutLeft", "box", (0.02, 0.05, 0.03), (-0.10, -0.25, 0.20),
                  mat=metal_brushed, bevel=0.004))

# ---------- Cup and saucer on the drip grate ----------
saucer = prim("Saucer", "cyl", (0.065, 0.008), (0.0, -0.22, 0.12), mat=ceramic)
cup = prim("Cup", "cyl", (0.038, 0.055), (0.0, -0.22, 0.155), mat=ceramic)
cup_coffee = prim("CupCoffee", "cyl", (0.033, 0.002), (0.0, -0.22, 0.2), mat=coffee)
cup_handle = prim("CupHandle", "box", (0.012, 0.02, 0.03), (0.052, -0.22, 0.165),
                  mat=ceramic, bevel=0.005)

# Shadow-catching floor
floor = prim("Floor", "box", (4.0, 4.0, 0.02), (0, 0, -0.01), mat=floor_mat, smooth=False)

# Join visible hierarchy under an empty for tidy organization
root = bpy.data.objects.new("EspressoMachine", None)
collection.objects.link(root)
for p in parts + [saucer, cup, cup_coffee, cup_handle]:
    p.parent = root

# ---------- World ----------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.055, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Lights ----------
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 900.0
key_data.size = 1.2
key_data.color = (1.0, 0.97, 0.94)
key = bpy.data.objects.new("KeyLight", key_data)
collection.objects.link(key)
key.location = (1.1, -1.0, 1.4)
key.rotation_euler = Vector((0.8, 0.0, 0.6)).to_track_quat('-Z', 'Y').to_euler()
key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat('-Z', 'Y').to_euler()

rim_data = bpy.data.lights.new(name="RimLight", type='AREA')
rim_data.energy = 350.0
rim_data.size = 1.0
rim_data.color = (0.8, 0.9, 1.0)
rim = bpy.data.objects.new("RimLight", rim_data)
collection.objects.link(rim)
rim.location = (-1.0, 1.1, 1.0)
rim.rotation_euler = (Vector((0, 0, 0.25)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

fill_data = bpy.data.lights.new(name="FillLight", type='SUN')
fill_data.energy = 1.5
fill_data.color = (0.9, 0.93, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
collection.objects.link(fill)
fill.rotation_euler = Euler((math.radians(60), 0, math.radians(-150)), 'XYZ')

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 58.0
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 1.7
cam_data.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)

cam_loc = Vector((1.05, -1.35, 0.62))
target = Vector((0.0, -0.05, 0.27))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1
