import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# --- Clear default objects (safety for background runs) ---
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# --- Material ---
mat = bpy.data.materials.new(name="HelloMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.95, 0.45, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.25

# --- Text object ---
text_curve = bpy.data.curves.new(name="HelloText", type='FONT')
text_curve.body = "HELLO"
text_curve.size = 1.0
text_curve.extrude = 0.08
text_curve.bevel_depth = 0.02
text_curve.bevel_resolution = 3
text_curve.align_x = 'CENTER'
text_curve.align_y = 'CENTER'
text_curve.materials.append(mat)

text_obj = bpy.data.objects.new("HELLO", text_curve)
scene.collection.objects.link(text_obj)
text_obj.location = (0.0, 0.0, 0.0)

# --- Start with zero scale and keyframe the grow-in ---
text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)

text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=30)

# --- Elastic easing on the scale curves ---
if text_obj.animation_data and text_obj.animation_data.action:
    for fc in text_obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'ELASTIC'
            kp.easing = 'EASE_OUT'
        fc.update()

# --- Ground plane for a bit of context ---
plane_mat = bpy.data.materials.new(name="GroundMaterial")
plane_mat.use_nodes = True
pb = plane_mat.node_tree.nodes.get("Principled BSDF")
if pb:
    pb.inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1.0)
    pb.inputs["Roughness"].default_value = 0.8

plane_mesh = bpy.data.meshes.new("GroundMesh")
plane_mesh.from_pydata(
    [(-10, -10, -0.6), (10, -10, -0.6), (10, 10, -0.6), (-10, 10, -0.6)],
    [],
    [(0, 1, 2, 3)],
)
plane_mesh.update()
plane_obj = bpy.data.objects.new("Ground", plane_mesh)
scene.collection.objects.link(plane_obj)
plane_obj.data.materials.append(plane_mat)

# --- Lighting ---
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(30))

area_data = bpy.data.lights.new(name="FillArea", type='AREA')
area_data.energy = 800.0
area_data.size = 6.0
area_obj = bpy.data.objects.new("FillArea", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (4.0, -6.0, 5.0)
area_obj.rotation_euler = (math.radians(60), 0.0, math.radians(35))

# --- Camera ---
cam_data = bpy.data.cameras.new(name="MainCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = Vector((0.0, -9.0, 1.2))
direction = Vector((0.0, 0.0, 0.0)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# --- Timeline ---
scene.frame_start = 1
scene.frame_end = 30
scene.frame_set(1)
