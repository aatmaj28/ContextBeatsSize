import bpy
import math
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

def box(name, loc, size, material, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    if parent:
        o.parent = parent
        o.location = loc
    return o

m_wall = mat("Wall", (0.85, 0.82, 0.76), 0.8)
m_floor = mat("Floor", (0.35, 0.22, 0.12), 0.4)
m_door = mat("Door", (0.45, 0.12, 0.08), 0.35)
m_trim = mat("Trim", (0.95, 0.95, 0.93), 0.3)
m_brass = mat("Brass", (0.85, 0.65, 0.25), 0.25, 1.0)
m_room = mat("Room", (0.6, 0.7, 0.8), 0.9)

# Floor
box("Floor", (0, 0, -0.025), (8, 8, 0.05), m_floor)
# Wall with opening (opening x: -0.47..0.47, z: 0..2.07)
box("WallL", (-1.735, 0, 1.5), (2.53, 0.15, 3), m_wall)
box("WallR", (1.735, 0, 1.5), (2.53, 0.15, 3), m_wall)
box("WallTop", (0, 0, 2.535), (0.94, 0.15, 0.93), m_wall)
# Room behind
box("BackWall", (0, 3, 1.5), (6, 0.1, 3), m_room)
# Frame trim
box("TrimL", (-0.51, -0.08, 1.06), (0.08, 0.04, 2.12), m_trim)
box("TrimR", (0.51, -0.08, 1.06), (0.08, 0.04, 2.12), m_trim)
box("TrimTop", (0, -0.08, 2.11), (1.1, 0.04, 0.08), m_trim)

# Hinge pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.46, -0.03, 0))
hinge = bpy.context.active_object
hinge.name = "Hinge"

door = box("Door", (0.46, 0, 1.03), (0.91, 0.05, 2.05), m_door, hinge)
# Panels
for z in (0.55, 1.5):
    box("Panel", (0.46, -0.03, z), (0.65, 0.02, 0.7), m_door, hinge)
# Handle
box("HandleBase", (0.82, -0.04, 1.0), (0.04, 0.02, 0.15), m_brass, hinge)
box("Handle", (0.76, -0.08, 1.02), (0.14, 0.025, 0.025), m_brass, hinge)

# Animation: ease in / ease out swing
scene.frame_start = 1
scene.frame_end = 40
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert("rotation_euler", index=2, frame=1)
hinge.rotation_euler = (0, 0, math.radians(-100))
hinge.keyframe_insert("rotation_euler", index=2, frame=40)

ad = hinge.animation_data
try:
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()
except Exception:
    pass

# Lights
bpy.ops.object.light_add(type='AREA', location=(2.5, -3.5, 3.5))
key = bpy.context.active_object
key.data.energy = 600
key.data.size = 3
key.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='POINT', location=(0, 2.0, 2.2))
inner = bpy.context.active_object
inner.data.energy = 300
inner.data.color = (1.0, 0.8, 0.55)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(2.6, -4.6, 1.7))
cam = bpy.context.active_object
cam.data.lens = 35
bpy.ops.object.empty_add(location=(0, -0.3, 1.0))
target = bpy.context.active_object
target.name = "CamTarget"
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam
