import bpy
import math

scene = bpy.context.scene

# Clear any existing objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Linear keyframe interpolation for a smooth constant-speed orbit
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'


def make_material(name, color, roughness=0.4, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def add_obj(obj, mat):
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


marble = make_material("Marble", (0.85, 0.83, 0.78), roughness=0.35)
stone = make_material("Stone", (0.45, 0.45, 0.48), roughness=0.7)
ground_mat = make_material("Ground", (0.25, 0.25, 0.27), roughness=0.9)

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(ground_mat)

# Pedestal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.4))
pedestal = bpy.context.active_object
pedestal.scale = (0.9, 0.9, 0.4)
add_obj(pedestal, stone)

# Torso
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, location=(0, 0, 1.9))
torso = bpy.context.active_object
torso.scale = (0.38, 0.26, 0.72)
add_obj(torso, marble)

# Neck
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.11, depth=0.3, location=(0, 0, 2.5))
neck = bpy.context.active_object
add_obj(neck, marble)

# Head
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, location=(0, 0, 2.8))
head = bpy.context.active_object
head.scale = (0.25, 0.27, 0.3)
add_obj(head, marble)

# Shoulders
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0, 0, 2.45))
shoulders = bpy.context.active_object
shoulders.scale = (0.5, 0.22, 0.2)
add_obj(shoulders, marble)

# Arms
for side, sign in (("L", 1), ("R", -1)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.09, depth=0.9,
        location=(0.45 * sign, 0, 1.9))
    arm = bpy.context.active_object
    arm.rotation_euler = (0, math.radians(10) * sign, 0)
    add_obj(arm, marble)

# Target empty at statue centre
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 1.7))
target = bpy.context.active_object
target.name = "StatueTarget"

# Pivot empty for orbit
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 1.7))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"

# Camera parented to pivot
cam_data = bpy.data.cameras.new("OrbitCamera")
cam_data.lens = 50
cam = bpy.data.objects.new("OrbitCamera", cam_data)
bpy.context.collection.objects.link(cam)
cam.parent = pivot
cam.location = (0, -8.0, 0.8)  # world ~ (0, -8, 2.5)

# Track To constraint keeps camera aimed at statue
track = cam.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam

# Orbit animation: 100 frames, one full revolution
scene.frame_start = 1
scene.frame_end = 100

pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.radians(360))
pivot.keyframe_insert(data_path="rotation_euler", frame=100)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(0, 0, 6))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
area = bpy.context.active_object
area.data.energy = 600
area.data.size = 4.0
area.rotation_euler = (math.radians(60), 0, math.radians(45))

# Dark world background
world = bpy.data.worlds.new("World")
world.color = (0.04, 0.04, 0.05)
scene.world = world
