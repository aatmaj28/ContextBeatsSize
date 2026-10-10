import bpy
import math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m

def box(name, loc, dims, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.8)
floor_m = mat("Floor", (0.35, 0.22, 0.12), 0.4)
door_m = mat("Door", (0.45, 0.12, 0.08), 0.45)
trim_m = mat("Trim", (0.95, 0.95, 0.92), 0.3)
brass_m = mat("Brass", (0.85, 0.65, 0.25), 0.25, 1.0)
inner_m = mat("Inner", (0.6, 0.65, 0.75), 0.8)

# Floor
box("Floor", (0, 0, -0.025), (10, 10, 0.05), floor_m)

# Wall with opening
W, T = 0.9, 0.15
box("WallL", (-1.725, 0, 1.5), (2.55, T, 3), wall_m)
box("WallR", (1.725, 0, 1.5), (2.55, T, 3), wall_m)
box("WallTop", (0, 0, 2.55), (0.9, T, 0.9), wall_m)
# Back room wall
box("BackWall", (0, 3.5, 1.5), (6, 0.1, 3), inner_m)

# Door frame trim
box("TrimL", (-0.5, -0.09, 1.08), (0.1, 0.04, 2.16), trim_m)
box("TrimR", (0.5, -0.09, 1.08), (0.1, 0.04, 2.16), trim_m)
box("TrimTop", (0, -0.09, 2.15), (1.1, 0.04, 0.1), trim_m)

# Hinge pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.45, 0, 0))
hinge = bpy.context.active_object
hinge.name = "Hinge"

door = box("Door", (0, 0, 0), (0.89, 0.045, 2.09), door_m)
door.parent = hinge
door.location = (0.45, 0, 1.05)

# Panels on door
for z in (0.55, 1.5):
    p = box("Panel", (0, 0, 0), (0.6, 0.01, 0.7), door_m)
    p.parent = hinge
    p.location = (0.45, -0.028, z)

# Knobs
for y in (-0.06, 0.06):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0, 0, 0))
    k = bpy.context.active_object
    k.data.materials.append(brass_m)
    bpy.ops.object.shade_smooth()
    k.parent = hinge
    k.location = (0.8, y, 1.0)

# Animation: ease in/out (Bezier, auto-clamped default)
scene.frame_start = 1
scene.frame_end = 40
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
hinge.rotation_euler = (0, 0, math.radians(100))
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=40)
try:
    ad = hinge.animation_data
    fcs = []
    if ad and ad.action:
        if hasattr(ad.action, "fcurves"):
            fcs = list(ad.action.fcurves)
        else:
            for layer in ad.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs.extend(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'AUTO'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()
except Exception:
    pass

# Lighting
bpy.ops.object.light_add(type='SUN', location=(3, -4, 6))
sun = bpy.context.active_object
sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(0, 2.5, 2.8))
inner = bpy.context.active_object
inner.data.energy = 300
inner.data.size = 2
inner.data.color = (1.0, 0.85, 0.6)

bpy.ops.object.light_add(type='AREA', location=(1.5, -3, 3))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size = 3
fill.rotation_euler = (math.radians(45), 0, math.radians(25))

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.07, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(2.3, -4.8, 1.7))
cam = bpy.context.active_object
cam.data.lens = 35
target = Vector((0, 0.3, 1.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
