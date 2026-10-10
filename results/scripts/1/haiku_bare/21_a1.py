import bpy
import math
from mathutils import Vector

# ---------- Scene setup ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.frame_set(1)

# Make every newly inserted keyframe use linear interpolation
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass


def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def set_linear_interpolation(obj):
    """Force every keyframe on the object's action to LINEAR interpolation."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    action = ad.action
    fcurves = []
    if hasattr(action, "fcurves") and len(action.fcurves) > 0:
        fcurves = list(action.fcurves)
    elif hasattr(action, "layers"):
        # Blender 4.4+/5.x layered actions
        for layer in action.layers:
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []):
                    fcurves.extend(cb.fcurves)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()


# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(make_material("FloorMat", (0.8, 0.8, 0.78), roughness=0.9))

# ---------- Ball ----------
radius = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=radius, location=(0, 0, 3))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball.data.materials.append(make_material("BallMat", (0.9, 0.25, 0.1), roughness=0.3, metallic=0.0))

# Bounce path: (frame, x, z). Ground contacts sit at z = radius.
ground = radius
keys = [
    (1,  -6.0, 3.0),        # drop start
    (15, -4.0, ground),     # bounce 1 contact
    (22, -2.0, 2.5),        # apex 1
    (30,  0.0, ground),     # bounce 2 contact
    (37,  2.0, 1.5),        # apex 2
    (45,  4.0, ground),     # bounce 3 contact
    (52,  6.0, 0.8),        # apex 3
    (60,  8.0, ground),     # final landing
]

for frame, x, z in keys:
    ball.location = (x, 0.0, z)
    ball.keyframe_insert(data_path="location", frame=frame)

set_linear_interpolation(ball)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
area = bpy.context.active_object
area.name = "FillArea"
area.data.energy = 300.0
area.data.size = 6.0
area.rotation_euler = (math.radians(60), 0, math.radians(-30))

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(3.5, -14, 5))
cam = bpy.context.active_object
cam.name = "Camera"
target = Vector((4.0, 0.0, 1.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
