import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene
collection = scene.collection


# ---------- Materials ----------
def make_material(name, color, metallic=0.0, roughness=0.5, anisotropic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    aniso = bsdf.inputs.get("Anisotropic")
    if aniso is not None:
        aniso.default_value = anisotropic
    return mat


metal_mat = make_material("BrushedMetal", (0.80, 0.80, 0.82, 1.0),
                          metallic=1.0, roughness=0.28, anisotropic=0.7)
black_mat = make_material("MatteBlack", (0.015, 0.015, 0.016, 1.0),
                          metallic=0.0, roughness=0.75)
ceramic_mat = make_material("WhiteCeramic", (0.88, 0.88, 0.85, 1.0),
                            metallic=0.0, roughness=0.15)
coffee_mat = make_material("Espresso", (0.12, 0.06, 0.02, 1.0),
                           metallic=0.0, roughness=0.3)


# ---------- Geometry helpers ----------
def make_obj(name, kind, size, loc, rot=(0.0, 0.0, 0.0), mat=None, bevel=0.0):
    bm = bmesh.new()
    if kind == "box":
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        if bevel > 0.0:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel,
                            segments=4, affect="EDGES")
    elif kind == "cone":
        r1, r2, depth = size
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=48,
                              radius1=r1, radius2=r2, depth=depth)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True

    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = rot
    if mat is not None:
        me.materials.append(mat)
    return ob


HALF_PI = math.pi / 2.0

# ---------- Machine ----------
# Matte black base
make_obj("Base", "box", (1.0, 0.9, 0.12), (0.0, -0.05, 0.06),
         mat=black_mat, bevel=0.03)

# Brushed metal body
make_obj("Body", "box", (0.78, 0.5, 0.85), (0.0, 0.02, 0.545),
         mat=metal_mat, bevel=0.05)

# Cup warmer top plate
make_obj("TopPlate", "box", (0.8, 0.52, 0.03), (0.0, 0.02, 0.985),
         mat=metal_mat, bevel=0.01)

# Group head (protrudes toward -Y)
make_obj("GroupHead", "cone", (0.075, 0.075, 0.1), (0.0, -0.28, 0.55),
         rot=(HALF_PI, 0.0, 0.0), mat=metal_mat)

# Portafilter basket
make_obj("PortafilterBasket", "cone", (0.055, 0.055, 0.04), (0.0, -0.37, 0.55),
         rot=(HALF_PI, 0.0, 0.0), mat=black_mat)

# Portafilter handle
make_obj("PortafilterHandle", "cone", (0.012, 0.012, 0.32), (0.0, -0.56, 0.53),
         rot=(HALF_PI, 0.0, 0.0), mat=black_mat)

# Steam wand on the front-left of the body
make_obj("SteamWand", "cone", (0.012, 0.012, 0.2), (-0.3, -0.33, 0.32),
         rot=(HALF_PI, 0.0, 0.0), mat=metal_mat)

# Drip tray
make_obj("DripTray", "box", (0.7, 0.2, 0.03), (0.0, -0.42, 0.14),
         mat=metal_mat, bevel=0.008)

# Small cup with saucer and coffee
make_obj("Saucer", "cone", (0.055, 0.055, 0.012), (0.2, -0.42, 0.161),
         mat=ceramic_mat)
make_obj("Cup", "cone", (0.03, 0.042, 0.06), (0.2, -0.42, 0.197),
         mat=ceramic_mat)
make_obj("Coffee", "cone", (0.038, 0.038, 0.004), (0.2, -0.42, 0.225),
         mat=coffee_mat)


# ---------- Camera / lighting helpers ----------
def aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


# Lights
def make_area_light(name, loc, energy, size, target):
    light_data = bpy.data.lights.new(name + "_Data", type="AREA")
    light_data.energy = energy
    light_data.size = size
    light_obj = bpy.data.objects.new(name, light_data)
    collection.objects.link(light_obj)
    light_obj.location = Vector(loc)
    aim(light_obj, target)
    return light_obj


target_center = (0.0, -0.05, 0.5)
make_area_light("KeyLight", (1.6, -1.6, 2.4), 900.0, 1.5, target_center)
make_area_light("FillLight", (1.9, -0.6, 0.9), 150.0, 2.0, target_center)
make_area_light("RimLight", (-1.5, 1.6, 1.9), 500.0, 1.2, target_center)

# World background (dark studio)
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.04, 0.04, 0.045, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera_Data")
cam_data.lens = 60.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam_obj)
cam_obj.location = Vector((2.1, -2.5, 1.35))
aim(cam_obj, (0.0, -0.1, 0.5))
scene.camera = cam_obj

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 1
