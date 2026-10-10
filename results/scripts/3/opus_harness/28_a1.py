import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

def box(name, loc, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o

m_wall = mat("Wall", (0.85, 0.82, 0.75), 0.8)
m_floor = mat("Floor", (0.35, 0.22, 0.12), 0.4)
m_frame = mat("Frame", (0.95, 0.95, 0.93), 0.4)
m_door = mat("Door", (0.45, 0.12, 0.08), 0.35)
m_knob = mat("Brass", (0.9, 0.7, 0.3), 0.2, 1.0)

# Floor
box("Floor", (0, 0, -0.05), (10, 10, 0.1), m_floor)

# Wall with opening (opening width 1.04, height 2.12)
W, H, T = 1.04, 2.12, 0.2
box("WallL", (-(W / 2 + 2), 0, 1.5), (4, T, 3), m_wall)
box("WallR", ((W / 2 + 2), 0, 1.5), (4, T, 3), m_wall)
box("WallTop", (0, 0, H + (3 - H) / 2), (W, T, 3 - H), m_wall)

# Door frame trim
ft = 0.07
box("FrameL", (-W / 2 - ft / 2, 0, H / 2), (ft, T + 0.04, H), m_frame)
box("FrameR", (W / 2 + ft / 2, 0, H / 2), (ft, T + 0.04, H), m_frame)
box("FrameTop", (0, 0, H + ft / 2), (W + 2 * ft, T + 0.04, ft), m_frame)

# Hinge pivot
hinge = bpy.data.objects.new("Hinge", None)
scene.collection.objects.link(hinge)
hinge.location = (-0.5, 0, 0.01)

door = box("Door", (0.5, 0, 1.05), (1.0, 0.05, 2.08), m_door)
door.parent = hinge
door.location = (0.5, 0, 1.05)

# Panels (decorative insets)
for z in (0.55, 1.5):
    p = box("Panel", (0.5, -0.03, z), (0.7, 0.01, 0.75), m_door)
    p.parent = hinge
    p.location = (0.5, -0.03, z)

# Knobs
for y in (-0.06, 0.06):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, 0))
    k = bpy.context.active_object
    k.name = "Knob"
    k.data.materials.append(m_knob)
    bpy.ops.object.shade_smooth()
    k.parent = hinge
    k.location = (0.88, y, 1.0)

# Animation: swing open over 40 frames with ease in/out
scene.frame_start = 1
scene.frame_end = 50
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert("rotation_euler", index=2, frame=1)
hinge.rotation_euler = (0, 0, math.radians(100))
hinge.keyframe_insert("rotation_euler", index=2, frame=41)

ad = hinge.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
if cb:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

# Lighting
sun = bpy.data.lights.new("Key", 'AREA')
sun.energy = 400
sun.size = 3
ko = bpy.data.objects.new("KeyLight", sun)
scene.collection.objects.link(ko)
ko.location = (2.5, -3.5, 3.5)
ko.rotation_euler = (Vector((0, 0, 1)) - ko.location).to_track_quat('-Z', 'Y').to_euler()

back = bpy.data.lights.new("Back", 'POINT')
back.energy = 300
back.color = (1.0, 0.85, 0.6)
bo = bpy.data.objects.new("BackLight", back)
scene.collection.objects.link(bo)
bo.location = (0.3, 2.5, 2.0)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (2.2, -4.8, 1.7)
target = Vector((0, 0, 1.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_set(1)
