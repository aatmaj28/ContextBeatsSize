import bpy
import math
from mathutils import Vector

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

def mat(name, color, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.8)
frame_m = mat("Frame", (0.95, 0.95, 0.93), 0.4)
door_m = mat("Door", (0.35, 0.18, 0.08), 0.45)
knob_m = mat("Knob", (0.9, 0.7, 0.3), 0.25, 1.0)
floor_m = mat("Floor", (0.45, 0.32, 0.22), 0.6)

def box(name, loc, size, m):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    return o

# Floor
box("Floor", (0, 0, -0.05), (10, 10, 0.1), floor_m)

# Wall with opening (opening x -0.5..0.5, z 0..2.1)
T = 0.15
box("WallLeft", (-1.75, 0, 1.5), (2.5, T, 3.0), wall_m)
box("WallRight", (1.75, 0, 1.5), (2.5, T, 3.0), wall_m)
box("WallTop", (0, 0, 2.55), (1.0, T, 0.9), wall_m)

# Door frame trim
box("TrimL", (-0.55, -0.01, 1.1), (0.1, T + 0.04, 2.2), frame_m)
box("TrimR", (0.55, -0.01, 1.1), (0.1, T + 0.04, 2.2), frame_m)
box("TrimT", (0, -0.01, 2.15), (1.2, T + 0.04, 0.1), frame_m)

# Hinge pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.49, -0.02, 0))
hinge = bpy.context.active_object
hinge.name = "Hinge"

# Door panel (local to hinge)
door = box("Door", (0, 0, 0), (0.97, 0.05, 2.08), door_m)
door.parent = hinge
door.location = (0.485, 0, 1.04)
bevel = door.modifiers.new("Bevel", 'BEVEL')
bevel.width = 0.01
bevel.segments = 2

# Raised panels for detail
for z in (0.55, 1.5):
    p = box("Panel", (0, 0, 0), (0.7, 0.07, 0.75), door_m)
    p.parent = hinge
    p.location = (0.485, 0, z)

# Knobs
for y in (-0.06, 0.06):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, 0))
    k = bpy.context.active_object
    k.name = "Knob"
    k.data.materials.append(knob_m)
    bpy.ops.object.shade_smooth()
    k.parent = hinge
    k.location = (0.85, y, 1.0)

# Animation: swing open toward camera over 40 frames
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=10)
hinge.rotation_euler = (0, 0, math.radians(-100))
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=50)

def get_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        if cb:
            return list(cb.fcurves)
    except Exception:
        pass
    try:
        return list(act.fcurves)
    except Exception:
        return []

for fc in get_fcurves(hinge):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
    fc.update()

# Lighting
bpy.ops.object.light_add(type='SUN', location=(4, -5, 6))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

bpy.ops.object.light_add(type='POINT', location=(0, 2.0, 2.0))
inner = bpy.context.active_object
inner.data.energy = 600
inner.data.color = (1.0, 0.8, 0.55)

bpy.ops.object.light_add(type='AREA', location=(-2, -4, 3))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size = 3
fill.rotation_euler = (Vector((0, 0, 1)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(2.6, -5.5, 1.8))
cam = bpy.context.active_object
cam.data.lens = 35
target = Vector((-0.1, 0, 1.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_set(1)
