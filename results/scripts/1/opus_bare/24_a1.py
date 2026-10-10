import bpy
import math

scene = bpy.context.scene

# Clear any existing objects
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m

stone = mat("Stone", (0.75, 0.73, 0.68), 0.6)
marble = mat("Marble", (0.92, 0.9, 0.87), 0.35)
ground_m = mat("Ground", (0.25, 0.27, 0.25), 0.9)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
add(bpy.context.active_object, ground_m)

# Pedestal: base slab, column, cap
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.15))
o = bpy.context.active_object
o.scale = (1.8, 1.8, 0.3)
add(o, stone)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.9))
o = bpy.context.active_object
o.scale = (1.2, 1.2, 1.2)
add(o, stone)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.6))
o = bpy.context.active_object
o.scale = (1.5, 1.5, 0.2)
add(o, stone)

# Statue figure
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.2, location=(0, 0, 2.3))
o = bpy.context.active_object
add(o, marble)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 3.15), segments=32, ring_count=16)
add(bpy.context.active_object, marble)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0, 0, 2.75), segments=32, ring_count=16)
o = bpy.context.active_object
o.scale = (1.2, 0.8, 0.5)
add(o, marble)
bpy.ops.object.shade_smooth()

# Raised arm
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.9, location=(0.5, 0, 3.05))
o = bpy.context.active_object
o.rotation_euler = (0, math.radians(-30), 0)
add(o, marble)
bpy.ops.object.shade_smooth()

# Lowered arm
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.8, location=(-0.45, 0, 2.4))
o = bpy.context.active_object
o.rotation_euler = (0, math.radians(15), 0)
add(o, marble)
bpy.ops.object.shade_smooth()

# Torch held in the raised hand
bpy.ops.mesh.primitive_cone_add(radius1=0.15, radius2=0.04, depth=0.35, location=(0.75, 0, 3.55))
o = bpy.context.active_object
o.rotation_euler = (math.pi, 0, 0)
add(o, mat("Gold", (1.0, 0.75, 0.3), 0.25, 1.0))

# Empty at the statue's center that the camera tracks
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 2.2)

# Pivot empty rotates once over the animation, carrying the camera with it
pivot = bpy.data.objects.new("Pivot", None)
scene.collection.objects.link(pivot)

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (9, 0, 4)

# Track To constraint keeps the camera pointed at the statue
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'

scene.frame_start = 1
scene.frame_end = 100

pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, math.radians(360 * 99 / 100))
pivot.keyframe_insert("rotation_euler", index=2, frame=100)

# Linear interpolation for constant-speed orbit
ad = pivot.animation_data
if ad and ad.action:
    try:
        curves = ad.action.fcurves
    except AttributeError:
        curves = []
        for layer in ad.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

scene.camera = cam

# Lighting: sun plus a fill area light
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
scene.collection.objects.link(sun)

fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
fill.data.energy = 600
fill.data.size = 5
fill.location = (-5, -5, 7)
scene.collection.objects.link(fill)
fc2 = fill.constraints.new('TRACK_TO')
fc2.target = target

# World background
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.6, 0.75, 1)
    bg.inputs["Strength"].default_value = 0.6
