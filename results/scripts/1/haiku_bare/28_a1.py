import bpy
import math
from mathutils import Vector

# ---------- Clean up default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(1)

# Make new keyframes Bezier by default (needed for ease in/out)
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
except Exception:
    pass


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return obj


# ---------- Materials ----------
wall_mat = make_material("WallMat", (0.85, 0.82, 0.75), roughness=0.9)
floor_mat = make_material("FloorMat", (0.35, 0.25, 0.18), roughness=0.6)
door_mat = make_material("DoorMat", (0.45, 0.22, 0.10), roughness=0.45)
frame_mat = make_material("FrameMat", (0.9, 0.9, 0.88), roughness=0.4)
handle_mat = make_material("HandleMat", (0.8, 0.65, 0.2), roughness=0.2, metallic=1.0)

# ---------- Environment ----------
# Floor
add_box("Floor", (0, 0.5, -0.05), (3.0, 2.5, 0.05), floor_mat)
# Back wall
add_box("Wall", (0, -0.25, 1.6), (3.0, 0.1, 1.6), wall_mat)

# Door frame (jambs and header), opening is 1.0 wide x 2.2 tall
add_box("FrameLeft", (-0.55, 0.0, 1.1), (0.05, 0.06, 1.15), frame_mat)
add_box("FrameRight", (0.55, 0.0, 1.1), (0.05, 0.06, 1.15), frame_mat)
add_box("FrameTop", (0.0, 0.0, 2.25), (0.6, 0.06, 0.05), frame_mat)

# ---------- Door with hinge pivot ----------
hinge_pos = Vector((-0.5, 0.0, 0.0))
bpy.ops.object.empty_add(type='PLAIN_AXES', location=hinge_pos)
pivot = bpy.context.active_object
pivot.name = "DoorHinge"
pivot.empty_display_size = 0.2

door = add_box("Door", (0.5, 0.0, 1.1), (0.5, 0.025, 1.1), door_mat)
door.parent = pivot
door.matrix_parent_inverse = pivot.matrix_world.inverted()

# Handle on the door (child of door, so it swings with it)
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.15, location=(0.85, -0.05, 1.0))
handle = bpy.context.active_object
handle.name = "DoorHandle"
handle.rotation_euler = (math.radians(90), 0, 0)
handle.data.materials.append(handle_mat)
handle.parent = door
handle.matrix_parent_inverse = door.matrix_world.inverted()

# ---------- Door animation (0 -> 100 degrees over 40 frames, ease in/out) ----------
pivot.rotation_mode = 'XYZ'
pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

pivot.rotation_euler = (0.0, 0.0, math.radians(100))
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

# Enforce ease in/out on the keys
try:
    action = pivot.animation_data.action
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
            kp.easing = 'EASE_IN_OUT'
except Exception:
    pass

# Reset to closed state for frame 1
scene.frame_set(1)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(2, -2, 4))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(55), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(0.0, 2.5, 2.5))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 300.0
fill.data.size = 3.0
fill.rotation_euler = (math.radians(-60), 0, 0)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (1.4, 3.6, 1.4)

target = Vector((0.0, 0.0, 1.1))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
