import bpy
import math

scene = bpy.context.scene

# Clear existing objects
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
bronze = mat("Bronze", (0.55, 0.35, 0.15), 0.35, 1.0)
ground_m = mat("Ground", (0.25, 0.3, 0.22), 0.9)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=40)
add(bpy.context.active_object, ground_m)

# Pedestal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.6))
p = bpy.context.active_object
p.scale = (1.6, 1.6, 1.2)
add(p, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.3))
p2 = bpy.context.active_object
p2.scale = (1.9, 1.9, 0.2)
add(p2, stone)

# Statue figure
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.4, location=(0, 0, 2.1))
body = add(bpy.context.active_object, bronze)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 3.1))
add(bpy.context.active_object, bronze)
bpy.ops.object.shade_smooth()
# Arms
for side in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.9, location=(side * 0.5, 0, 2.5),
                                        rotation=(0, math.radians(side * 30), 0))
    add(bpy.context.active_object, bronze)
    bpy.ops.object.shade_smooth()
# Raised torch arm
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.8, location=(0.45, 0, 3.0),
                                    rotation=(0, math.radians(-25), 0))
add(bpy.context.active_object, bronze)

# Target empty
bpy.ops.object.empty_add(location=(0, 0, 2.0))
target = bpy.context.active_object
target.name = "Target"

# Orbit pivot
bpy.ops.object.empty_add(location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"

# Camera
bpy.ops.object.camera_add(location=(8, 0, 3.5))
cam = bpy.context.active_object
cam.data.lens = 40
cam.parent = pivot
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

# Animate pivot rotation
scene.frame_start = 1
scene.frame_end = 100
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, math.radians(360 * 100 / 101))
pivot.keyframe_insert("rotation_euler", index=2, frame=101)
try:
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except Exception:
    pass
try:
    for kp in pivot.animation_data.action.layers[0].strips[0].channelbags[0].fcurves[0].keyframe_points:
        kp.interpolation = 'LINEAR'
except Exception:
    pass

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(45), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-4, 4, 6))
fill = bpy.context.active_object
fill.data.energy = 400
fill.data.size = 4
fill.constraints.new('TRACK_TO').target = target

# World
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.5, 0.65, 0.85, 1)
    bg.inputs[1].default_value = 0.6

scene.frame_set(1)
