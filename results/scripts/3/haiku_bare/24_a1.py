import bpy
import math

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 100
scene.frame_set(1)

def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

# Materials
stone_mat = make_material("Stone", (0.55, 0.53, 0.50), roughness=0.6)
marble_mat = make_material("Marble", (0.85, 0.84, 0.82), roughness=0.25)
base_mat = make_material("Pedestal", (0.25, 0.22, 0.20), roughness=0.7)

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, make_material("Ground", (0.12, 0.12, 0.13), roughness=0.9))

# Statue parts
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.4))
pedestal = bpy.context.active_object
pedestal.name = "Pedestal"
pedestal.scale = (1.2, 1.2, 0.4)
bpy.ops.object.transform_apply(scale=True)
assign(pedestal, base_mat)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.45, depth=1.8,
                                    location=(0, 0, 1.7))
torso = bpy.context.active_object
torso.name = "Torso"
assign(torso, marble_mat)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.5,
                                     location=(0, 0, 2.7))
shoulders = bpy.context.active_object
shoulders.name = "Shoulders"
shoulders.scale = (1.0, 0.8, 0.6)
assign(shoulders, marble_mat)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.33,
                                     location=(0, 0, 3.25))
head = bpy.context.active_object
head.name = "Head"
assign(head, marble_mat)

# Raised arm
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=1.1,
                                    location=(0.55, 0, 2.5))
arm = bpy.context.active_object
arm.name = "Arm"
arm.rotation_euler = (0, math.radians(35), 0)
assign(arm, marble_mat)

# Lowered arm holding nothing (slightly out)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=1.0,
                                    location=(-0.55, 0, 1.9))
arm2 = bpy.context.active_object
arm2.name = "Arm2"
arm2.rotation_euler = (0, math.radians(-12), 0)
assign(arm2, marble_mat)

# Subject center target
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 1.8))
target = bpy.context.active_object
target.name = "StatueTarget"

# Orbit pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 1.8))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"

# Camera
bpy.ops.object.camera_add(location=(0, -9, 0))
cam = bpy.context.active_object
cam.name = "OrbitCamera"
cam.data.lens = 50
cam.data.clip_end = 100
cam.parent = pivot
cam.location = (0, -9.0, 0.6)

track = cam.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam

# Animate orbit: one full revolution over 100 frames, linear
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

pivot.rotation_euler = (0.0, 0.0, 0.0)
pivot.keyframe_insert(data_path="rotation_euler", frame=1)
pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", frame=100)

# Ensure linear interpolation on the orbit curves
if pivot.animation_data and pivot.animation_data.action:
    action = pivot.animation_data.action
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        for fc in fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(4, -6, 8))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-5, -4, 4))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 400
fill.data.size = 4.0
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))

bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
rim = bpy.context.active_object
rim.name = "RimArea"
rim.data.energy = 300
rim.data.size = 3.0
rim.rotation_euler = (math.radians(70), 0, math.radians(180))

# World background
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.6
