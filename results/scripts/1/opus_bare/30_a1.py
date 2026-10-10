import bpy
import math

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 45
scene.render.fps = 24

# --- Text object ---
curve = bpy.data.curves.new("HelloCurve", type='FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.extrude = 0.15
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.size = 1.0
txt = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(txt)
txt.rotation_euler = (math.radians(90), 0, 0)
txt.location = (0, 0, 1.0)

mat = bpy.data.materials.new("TextMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.2
curve.materials.append(mat)

# --- Ground ---
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("GroundMat")
gmat.use_nodes = True
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.08, 0.1, 0.15, 1.0)
    gb.inputs["Roughness"].default_value = 0.6
ground.data.materials.append(gmat)

# --- Animation: scale 0 -> 1 with elastic ease out ---
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'ELASTIC'
except Exception:
    pass

txt.scale = (0.0, 0.0, 0.0)
txt.keyframe_insert(data_path="scale", frame=1)
txt.scale = (1.0, 1.0, 1.0)
txt.keyframe_insert(data_path="scale", frame=31)

def all_fcurves(action):
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

ad = txt.animation_data
if ad and ad.action:
    for fc in all_fcurves(ad.action):
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
key.size = 4
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = (4, -5, 6)
key_obj.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 300
fill.size = 5
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = (-5, -4, 3)
fill_obj.rotation_euler = (math.radians(65), 0, math.radians(-50))
scene.collection.objects.link(fill_obj)

rim = bpy.data.lights.new("Rim", type='SPOT')
rim.energy = 600
rim_obj = bpy.data.objects.new("Rim", rim)
rim_obj.location = (0, 5, 4)
rim_obj.rotation_euler = (math.radians(-45), 0, 0)
scene.collection.objects.link(rim_obj)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.025, 0.04, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -9, 2.2)
scene.collection.objects.link(cam)
track = cam.constraints.new('TRACK_TO')
track.target = txt
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam
scene.frame_set(1)
