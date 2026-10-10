import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 45

# --- Text ---
curve = bpy.data.curves.new("HelloCurve", type='FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.extrude = 0.15
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.size = 1.0
text = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)

mat = bpy.data.materials.new("HelloMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.3
curve.materials.append(mat)

# --- Animation ---
text.scale = (0, 0, 0)
text.keyframe_insert(data_path="scale", frame=1)
text.scale = (1, 1, 1)
text.keyframe_insert(data_path="scale", frame=30)

def get_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    action = ad.action
    if hasattr(action, "fcurves"):
        try:
            return list(action.fcurves)
        except Exception:
            pass
    fcs = []
    try:
        for layer in action.layers:
            for strip in layer.strips:
                if ad.action_slot:
                    cb = strip.channelbag(ad.action_slot)
                    if cb:
                        fcs.extend(cb.fcurves)
    except Exception:
        pass
    return fcs

for fc in get_fcurves(text):
    for kp in fc.keyframe_points:
        kp.interpolation = 'ELASTIC'
        kp.easing = 'EASE_OUT'
        kp.amplitude = 0.0
        kp.period = 0.0

# --- Background floor/backdrop ---
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 2, 0), rotation=(math.radians(90), 0, 0))
backdrop = bpy.context.active_object
bmat = bpy.data.materials.new("Backdrop")
bmat.use_nodes = True
bb = bmat.node_tree.nodes.get("Principled BSDF")
if bb:
    bb.inputs["Base Color"].default_value = (0.05, 0.07, 0.12, 1.0)
backdrop.data.materials.append(bmat)

# --- Lights ---
key = bpy.data.lights.new("Key", type='AREA')
key.energy = 600
key.size = 4
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = (3, -5, 4)
key_obj.rotation_euler = (math.radians(55), 0, math.radians(30))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 250
fill.size = 5
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = (-4, -4, 1)
fill_obj.rotation_euler = (math.radians(75), 0, math.radians(-45))
scene.collection.objects.link(fill_obj)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
    bg.inputs["Strength"].default_value = 1.0

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -9, 0.6)
cam.rotation_euler = (math.radians(86), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
scene.frame_set(1)
