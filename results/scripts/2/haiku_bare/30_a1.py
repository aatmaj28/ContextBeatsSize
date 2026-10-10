import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default objects so the scene starts empty
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Text object ----------
curve_data = bpy.data.curves.new(name="HelloText", type='FONT')
curve_data.body = "HELLO"
curve_data.align_x = 'CENTER'
curve_data.align_y = 'CENTER'
curve_data.size = 1.0
curve_data.extrude = 0.08
curve_data.bevel_depth = 0.01
curve_data.bevel_resolution = 4

text_obj = bpy.data.objects.new("HELLO", curve_data)
scene.collection.objects.link(text_obj)

# ---------- Material ----------
mat = bpy.data.materials.new(name="HelloMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.95, 0.45, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.25
text_obj.data.materials.append(mat)

# ---------- Scale animation (elastic easing) ----------
prefs = bpy.context.preferences.edit
old_interp = prefs.keyframe_new_interpolation_type
old_easing = prefs.keyframe_new_easing
prefs.keyframe_new_interpolation_type = 'ELASTIC'
prefs.keyframe_new_easing = 'EASE_OUT'

START_FRAME = 1
END_FRAME = 30

text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=START_FRAME)

text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=END_FRAME)

# Restore user preferences
prefs.keyframe_new_interpolation_type = old_interp
prefs.keyframe_new_easing = old_easing

# Start at scale zero for the first frame
text_obj.scale = (0.0, 0.0, 0.0)

# ---------- Lighting ----------
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 800.0
key_data.size = 6.0
key_obj = bpy.data.objects.new("KeyLight", key_data)
scene.collection.objects.link(key_obj)
key_obj.location = (4.0, -6.0, 6.0)
key_obj.rotation_euler = (math.radians(55), 0.0, math.radians(35))

fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
fill_data.energy = 300.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-5.0, -4.0, 2.0)

sun_data = bpy.data.lights.new(name="RimSun", type='SUN')
sun_data.energy = 2.0
sun_obj = bpy.data.objects.new("RimSun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(-30), math.radians(20), math.radians(160))

# ---------- Ground plane for context ----------
plane_mesh = bpy.data.meshes.new("Ground")
import bmesh
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12.0)
bm.to_mesh(plane_mesh)
bm.free()
ground = bpy.data.objects.new("Ground", plane_mesh)
scene.collection.objects.link(ground)
ground.location = (0.0, 0.0, -0.6)
ground_mat = bpy.data.materials.new(name="GroundMaterial")
ground_mat.use_nodes = True
gb = ground_mat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.08, 0.09, 0.12, 1.0)
    gb.inputs["Roughness"].default_value = 0.6
ground.data.materials.append(ground_mat)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -7.5, 1.6)

target = Vector((0.0, 0.0, 0.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Render/timeline settings ----------
scene.frame_start = START_FRAME
scene.frame_end = END_FRAME
scene.frame_set(START_FRAME)
