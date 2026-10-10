import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Animation range
scene.frame_start = 1
scene.frame_end = 60
scene.frame_current = 1

# Make newly inserted keyframes use linear interpolation
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

def make_principled_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def iter_fcurves(action):
    if hasattr(action, "fcurves"):
        for fc in action.fcurves:
            yield fc
    else:
        # Slotted actions (Blender 4.4+)
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        yield fc

# ---------- Floor ----------
floor_mesh = bpy.data.meshes.new("FloorMesh")
floor_bm = bmesh.new()
s = 12.0
verts = [floor_bm.verts.new(v) for v in [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)]]
floor_bm.faces.new(verts)
floor_bm.to_mesh(floor_mesh)
floor_bm.free()
floor = bpy.data.objects.new("Floor", floor_mesh)
scene.collection.objects.link(floor)
floor.data.materials.append(make_principled_material("FloorMat", (0.75, 0.75, 0.72), 0.8))

# ---------- Ball ----------
radius = 0.5
ball_mesh = bpy.data.meshes.new("BallMesh")
ball_bm = bmesh.new()
bmesh.ops.create_uvsphere(ball_bm, u_segments=40, v_segments=24, radius=radius)
for f in ball_bm.faces:
    f.smooth = True
ball_bm.to_mesh(ball_mesh)
ball_bm.free()
ball = bpy.data.objects.new("Ball", ball_mesh)
scene.collection.objects.link(ball)
ball.data.materials.append(make_principled_material("BallMat", (0.85, 0.15, 0.1), 0.3))

# Keyframes: (frame, x, z)
# Contacts with floor at frames 10, 30, 50 (three bounces), apexes between them.
keys = [
    (1,  -6.0, 4.0),   # drop start
    (10, -4.0, radius),  # bounce 1 contact
    (20, -2.0, 2.8),   # apex 1
    (30,  0.0, radius),  # bounce 2 contact
    (40,  2.0, 1.8),   # apex 2
    (50,  4.0, radius),  # bounce 3 contact
    (60,  6.0, radius),  # rolls to rest
]

for frame, x, z in keys:
    ball.location = Vector((x, 0.0, z))
    ball.keyframe_insert(data_path="location", frame=frame)

# Ensure every fcurve uses linear interpolation
if ball.animation_data and ball.animation_data.action:
    for fc in iter_fcurves(ball.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

ball.location = Vector((keys[0][1], 0.0, keys[0][2]))

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 800.0
area_data.size = 8.0
area = bpy.data.objects.new("FillArea", area_data)
scene.collection.objects.link(area)
area.location = (0.0, -8.0, 8.0)
area.rotation_euler = (math.radians(60), 0, 0)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -18.0, 6.0)

target = Vector((0.0, 0.0, 1.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# World background
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0
