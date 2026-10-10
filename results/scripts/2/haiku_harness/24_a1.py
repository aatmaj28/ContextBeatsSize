import bpy
import math
from mathutils import Vector


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                  bpy.data.cameras, bpy.data.curves):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def add_part(kind, name, location, scale, material, rotation=(0, 0, 0)):
    if kind == 'CUBE':
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    elif kind == 'SPHERE':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                             radius=1.0, location=location)
    elif kind == 'CYLINDER':
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=2.0,
                                            location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = rotation
    obj.data.materials.append(material)
    smooth(obj)
    return obj


clear_scene()

# Materials
stone_mat = make_material("Stone", (0.55, 0.53, 0.50), roughness=0.7)
marble_mat = make_material("Marble", (0.85, 0.84, 0.80), roughness=0.35)
base_mat = make_material("Base", (0.25, 0.22, 0.20), roughness=0.6)

# Pedestal
add_part('CUBE', "Pedestal", (0, 0, 0.4), (0.7, 0.7, 0.4), base_mat)
add_part('CUBE', "PedestalCap", (0, 0, 0.85), (0.8, 0.8, 0.05), base_mat)

# Statue body
add_part('SPHERE', "Torso", (0, 0, 1.9), (0.55, 0.38, 0.95), marble_mat)
add_part('CYLINDER', "Neck", (0, 0, 3.05), (0.16, 0.16, 0.15), marble_mat)
add_part('SPHERE', "Head", (0, 0, 3.45), (0.34, 0.34, 0.40), marble_mat)

# Arms, slightly away from the torso
add_part('CYLINDER', "ArmL", (0.62, 0, 2.05), (0.11, 0.11, 0.55), marble_mat,
         rotation=(0, math.radians(12), 0))
add_part('CYLINDER', "ArmR", (-0.62, 0, 2.05), (0.11, 0.11, 0.55), marble_mat,
         rotation=(0, math.radians(-12), 0))

# Base ground disc
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(stone_mat)

# World
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs["Strength"].default_value = 0.6

# Lights
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-4, 3, 3.5))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 300.0
fill.data.size = 4.0
fill.rotation_euler = (math.radians(70), 0, math.radians(-130))

# Target empty at the statue's center of interest
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 1.6))
target = bpy.context.active_object
target.name = "CameraTarget"

# Camera
bpy.ops.object.camera_add(location=(8, 0, 2.5))
cam = bpy.context.active_object
cam.name = "OrbitCamera"
cam.data.lens = 50
cam.data.clip_end = 100

track = cam.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

bpy.context.scene.camera = cam

# Animation: orbit over 100 frames, keyframing location each frame
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 100

radius = 8.0
height = 2.5
frames = scene.frame_end - scene.frame_start + 1

for i in range(frames):
    frame = scene.frame_start + i
    angle = 2.0 * math.pi * i / frames
    cam.location = Vector((radius * math.cos(angle),
                           radius * math.sin(angle),
                           height))
    cam.keyframe_insert(data_path="location", frame=frame)

scene.frame_set(scene.frame_start)
