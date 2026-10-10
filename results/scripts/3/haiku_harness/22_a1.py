import math

import bpy
import bmesh
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear any leftover data in the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def link(obj):
    scene.collection.objects.link(obj)
    return obj


def mesh_object(name, build_fn, material):
    bm = bmesh.new()
    build_fn(bm)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    mesh.update()
    return link(bpy.data.objects.new(name, mesh))


def box_builder(center, size):
    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    return build


def tower_builder(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=16,
                          radius1=0.35, radius2=0.2, depth=7.5)
    bmesh.ops.translate(bm, vec=(0.0, 0.0, 3.75), verts=bm.verts)


def hub_builder(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.35)


def blade_builder(length, width, thickness, hub_offset):
    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(width, thickness, length), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0.0, 0.0, hub_offset + length * 0.5),
                            verts=bm.verts)
    return build


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
mat_ground = make_material("Grass", (0.20, 0.45, 0.15), roughness=0.9)
mat_tower = make_material("TowerWhite", (0.85, 0.85, 0.82), roughness=0.4)
mat_nacelle = make_material("NacelleGrey", (0.45, 0.47, 0.50), roughness=0.35, metallic=0.6)
mat_blade = make_material("BladeCream", (0.92, 0.90, 0.84), roughness=0.5)
mat_hub = make_material("HubRed", (0.75, 0.10, 0.08), roughness=0.3, metallic=0.2)

# ---------------------------------------------------------------------------
# Static geometry
# ---------------------------------------------------------------------------
HUB_Z = 7.5
HUB_Y = -0.6

ground = mesh_object("Ground", box_builder((0, 0, -0.05), (80, 80, 0.1)), mat_ground)
tower = mesh_object("Tower", tower_builder, mat_tower)
nacelle = mesh_object("Nacelle", box_builder((0, 0.4, HUB_Z), (1.0, 2.6, 1.0)), mat_nacelle)

# ---------------------------------------------------------------------------
# Rotor (pivot empty) — spins around its local Y axis
# ---------------------------------------------------------------------------
rotor = bpy.data.objects.new("Rotor", None)
rotor.empty_display_type = 'PLAIN_AXES'
rotor.empty_display_size = 0.5
rotor.location = (0.0, HUB_Y, HUB_Z)
link(rotor)

hub = mesh_object("Hub", hub_builder, mat_hub)
hub.parent = rotor

BLADE_LENGTH = 2.8
BLADE_WIDTH = 0.35
BLADE_THICK = 0.06
HUB_RADIUS = 0.35

for i in range(3):
    blade = mesh_object(
        f"Blade{i}",
        blade_builder(BLADE_LENGTH, BLADE_WIDTH, BLADE_THICK, HUB_RADIUS),
        mat_blade,
    )
    blade.parent = rotor
    blade.rotation_euler = (0.0, math.radians(120.0 * i), 0.0)

# ---------------------------------------------------------------------------
# Constant-speed spin animation (2 full revolutions over 120 frames)
# ---------------------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 120

rotor.rotation_mode = 'XYZ'
rotor.rotation_euler = (0.0, 0.0, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=1)

rotor.rotation_euler = (0.0, 4.0 * math.pi, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=120)

# Make the motion linear so the speed is constant
anim_data = rotor.animation_data
action = anim_data.action
slot = anim_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
if channelbag is not None:
    for fcurve in channelbag.fcurves:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(35.0))
link(sun)

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 300.0
fill_data.size = 6.0
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (-10.0, -8.0, 9.0)
fill.rotation_euler = (math.radians(60.0), 0.0, math.radians(-40.0))
link(fill)

# Sky world background
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.72, 0.95, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------------------
# Camera framing the windmill
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
link(cam)

cam_loc = Vector((12.0, -16.0, 6.0))
target = Vector((0.0, 0.0, 5.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
