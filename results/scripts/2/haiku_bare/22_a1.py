import bpy
import bmesh
import math
from mathutils import Matrix, Vector

# ---------- Clean up any existing objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection

# Use linear keyframe interpolation so the spin is at constant speed
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'


# ---------- Helpers ----------
def make_material(name, color, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_object(name, build_fn, material):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


# ---------- Materials ----------
mat_ground = make_material("Ground", (0.25, 0.42, 0.18), roughness=0.95)
mat_tower = make_material("Tower", (0.85, 0.85, 0.82), roughness=0.45)
mat_nacelle = make_material("Nacelle", (0.55, 0.58, 0.62), roughness=0.35, metallic=0.6)
mat_blade = make_material("Blade", (0.95, 0.95, 0.93), roughness=0.4)
mat_hub = make_material("Hub", (0.9, 0.35, 0.1), roughness=0.4, metallic=0.2)

# ---------- Geometry ----------
TOWER_H = 14.0
HUB_Y = -2.0
HUB_Z = TOWER_H
BLADE_LEN = 6.0
BLADE_ROOT = 0.6

# Ground
def build_ground(bm):
    bmesh.ops.create_cube(
        bm, size=1.0,
        matrix=Matrix.Translation((0, 0, -0.1)) @ Matrix.Diagonal(Vector((80, 80, 0.2, 1)))
    )
make_object("Ground", build_ground, mat_ground)

# Tapered tower
def build_tower(bm):
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=16,
        radius1=1.1, radius2=0.45, depth=TOWER_H,
        matrix=Matrix.Translation((0, 0, TOWER_H / 2)),
    )
make_object("Tower", build_tower, mat_tower)

# Nacelle (horizontal cylinder along Y)
def build_nacelle(bm):
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=20,
        radius1=0.7, radius2=0.7, depth=3.6,
        matrix=Matrix.Translation((0, 0, HUB_Z)) @ Matrix.Rotation(math.radians(90), 4, 'X'),
    )
make_object("Nacelle", build_nacelle, mat_nacelle)

# Hub (sphere at the front of the nacelle)
def build_hub(bm):
    bmesh.ops.create_uvsphere(
        bm, u_segments=20, v_segments=12, radius=0.85,
        matrix=Matrix.Translation((0, HUB_Y, HUB_Z)),
    )
make_object("Hub", build_hub, mat_hub)

# Three blades, built in local space around the hub origin (rotor plane = XZ)
def build_blades(bm):
    for i in range(3):
        angle = i * 2.0 * math.pi / 3.0
        rot = Matrix.Rotation(angle, 4, 'Z')  # spread blades in the XY plane
        # Blade extends along local +X after spreading; we then move it into XZ plane
        # by rotating the whole arrangement so blades lie in the rotor plane (XZ).
        spread = Matrix.Rotation(angle, 4, 'Y')
        blade_mat = (
            spread
            @ Matrix.Translation((0, 0, BLADE_ROOT + BLADE_LEN / 2))
            @ Matrix.Diagonal(Vector((0.45, 0.12, BLADE_LEN, 1)))
        )
        bmesh.ops.create_cube(bm, size=1.0, matrix=blade_mat)

blades_obj = make_object("Blades", build_blades, mat_blade)
blades_obj.location = (0.0, HUB_Y, HUB_Z)

# Ground-level small details: a base plate
def build_base(bm):
    bmesh.ops.create_cube(
        bm, size=1.0,
        matrix=Matrix.Translation((0, 0, 0.12)) @ Matrix.Diagonal(Vector((3.0, 3.0, 0.24, 1))),
    )
make_object("Base", build_base, mat_tower)

# ---------- Animation: constant-speed spin ----------
scene.frame_start = 1
scene.frame_end = 120
scene.frame_current = 1

REVOLUTIONS = 3  # full turns over the 120 frames
blades_obj.rotation_mode = 'XYZ'
blades_obj.rotation_euler = (0.0, 0.0, 0.0)
blades_obj.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
blades_obj.rotation_euler = (0.0, 2.0 * math.pi * REVOLUTIONS, 0.0)
blades_obj.keyframe_insert(data_path="rotation_euler", index=1, frame=120)

# ---------- World / background ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.72, 0.95, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Lights ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 400.0
fill_data.size = 12.0
fill = bpy.data.objects.new("Fill", fill_data)
collection.objects.link(fill)
fill.location = (-15.0, 12.0, 12.0)
fill.rotation_euler = (math.radians(70), 0.0, math.radians(-130))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)

cam_pos = Vector((20.0, -30.0, 12.0))
target = Vector((0.0, -0.5, 9.0))
direction = target - cam_pos
cam.location = cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
