import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear the default scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)  # default node tree is created here
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def assign(obj, mat):
    obj.data.materials.append(mat)

# ---------------------------------------------------------------
# World (dark backdrop so the pulse reads clearly)
# ---------------------------------------------------------------
world = bpy.data.worlds.new("DarkWorld")  # default nodes are created here
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------
# Floor
bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, make_material("FloorMat", (0.8, 0.8, 0.78), roughness=0.7))

# Central subject: glossy sphere on a pedestal
bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.4, location=(0, 0, 0.2))
pedestal = bpy.context.active_object
pedestal.name = "Pedestal"
assign(pedestal, make_material("PedestalMat", (0.25, 0.25, 0.28), roughness=0.4))

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32, location=(0, 0, 1.4))
sphere = bpy.context.active_object
sphere.name = "Subject_Sphere"
bpy.ops.object.shade_smooth()
assign(sphere, make_material("SubjectMat", (0.7, 0.3, 0.15), roughness=0.15, metallic=0.2))

# Torus ring around the sphere
bpy.ops.mesh.primitive_torus_add(major_radius=1.6, minor_radius=0.08, location=(0, 0, 1.4))
torus = bpy.context.active_object
torus.name = "Ring"
torus.rotation_euler = (math.radians(70), 0, math.radians(20))
assign(torus, make_material("RingMat", (0.9, 0.85, 0.5), roughness=0.2, metallic=1.0))

# Scattered cubes for context
cube_specs = [
    ((-2.8, 1.6, 0.4), 0.4, (0.2, 0.5, 0.8)),
    ((2.6, 1.9, 0.3), 0.3, (0.3, 0.7, 0.4)),
    ((-1.9, -2.3, 0.5), 0.5, (0.6, 0.6, 0.65)),
    ((2.2, -2.0, 0.35), 0.35, (0.75, 0.2, 0.3)),
]
for i, (loc, size, col) in enumerate(cube_specs):
    bpy.ops.mesh.primitive_cube_add(size=size * 2, location=loc)
    c = bpy.context.active_object
    c.name = f"Cube_{i}"
    c.rotation_euler = (0, 0, math.radians(15 * i + 10))
    assign(c, make_material(f"CubeMat_{i}", col, roughness=0.45))

# ---------------------------------------------------------------
# Pulsing point light
# ---------------------------------------------------------------
LIGHT_POS = Vector((2.8, -3.2, 3.6))

light_data = bpy.data.lights.new(name="PulseLightData", type='POINT')
light_data.shadow_soft_size = 0.25
light_data.color = (1.0, 0.82, 0.6)
light_data.energy = 20.0

light_obj = bpy.data.objects.new("PulseLight", light_data)
light_obj.location = LIGHT_POS
scene.collection.objects.link(light_obj)

# Small visible emitter marking the light position
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=LIGHT_POS)
bulb = bpy.context.active_object
bulb.name = "LightBulb"
bpy.ops.object.shade_smooth()
assign(bulb, make_material("BulbMat", (1.0, 0.85, 0.6), roughness=0.3,
                           emission=(1.0, 0.85, 0.6), emission_strength=10.0))

# Keyframes: 48-frame period, dim at 1/49/97, bright at 25/73
DIM = 20.0
BRIGHT = 1500.0
for f in (1, 49, 97):
    light_data.energy = DIM
    light_data.keyframe_insert(data_path="energy", frame=f)
for f in (25, 73):
    light_data.energy = BRIGHT
    light_data.keyframe_insert(data_path="energy", frame=f)

# Smooth interpolation on the energy F-Curve (layered action API)
ad = light_data.animation_data
action = ad.action
slot = ad.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
fcurve = channelbag.fcurves.find("energy")
if fcurve:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
    fcurve.update()

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)

cam_obj.location = Vector((7.0, -8.5, 4.5))
target = Vector((0.0, 0.0, 1.2))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 96
scene.frame_set(1)
