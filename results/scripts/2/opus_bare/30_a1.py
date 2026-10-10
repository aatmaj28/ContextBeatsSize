import bpy
import math

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 30

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# --- Text ---
curve = bpy.data.curves.new("HelloCurve", type='FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.extrude = 0.12
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.size = 1.5
text = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)

mat = bpy.data.materials.new("HelloMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.2
curve.materials.append(mat)

# --- Ground / backdrop ---
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 2, -1.2))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("FloorMat")
fmat.use_nodes = True
fb = fmat.node_tree.nodes.get("Principled BSDF")
if fb:
    fb.inputs["Base Color"].default_value = (0.08, 0.1, 0.15, 1.0)
    fb.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fmat)

# --- Animation with elastic easing ---
prefs = bpy.context.preferences.edit
old_interp = prefs.keyframe_new_interpolation_type
try:
    prefs.keyframe_new_interpolation_type = 'ELASTIC'
except Exception:
    pass

text.scale = (0.0, 0.0, 0.0)
text.keyframe_insert(data_path="scale", frame=1)
text.scale = (1.0, 1.0, 1.0)
text.keyframe_insert(data_path="scale", frame=31)

try:
    prefs.keyframe_new_interpolation_type = old_interp
except Exception:
    pass

def iter_fcurves(action):
    fcs = []
    try:
        fcs = list(action.fcurves)
    except Exception:
        pass
    if not fcs:
        try:
            for layer in action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs.extend(cb.fcurves)
        except Exception:
            pass
    return fcs

ad = text.animation_data
if ad and ad.action:
    for fc in iter_fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'ELASTIC'
            kp.easing = 'EASE_OUT'
            try:
                kp.amplitude = 0.0
                kp.period = 6.0
            except Exception:
                pass

# --- Lighting ---
key = bpy.data.lights.new("Key", type='AREA')
key.energy = 800
key.size = 5
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = (4, -6, 5)
key_obj.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 300
fill.size = 6
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = (-5, -5, 2)
fill_obj.rotation_euler = (math.radians(70), 0, math.radians(-45))
scene.collection.objects.link(fill_obj)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.03, 0.04, 0.07, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -11, 1.2)
cam.rotation_euler = (math.radians(85), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_set(1)
