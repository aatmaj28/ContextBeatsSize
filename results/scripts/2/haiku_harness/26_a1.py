import bpy
import math
from mathutils import Vector


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for light in list(bpy.data.lights):
        if light.users == 0:
            bpy.data.lights.remove(light)


def make_material(name, color, roughness=0.5, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


clear_scene()

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 96

# World: dark neutral background so the pulsing light reads clearly
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 0.2

# Materials
mat_floor = make_material("Floor", (0.8, 0.8, 0.8), roughness=0.9)
mat_sphere = make_material("Sphere", (0.9, 0.85, 0.8), roughness=0.25, metallic=0.0)
mat_metal = make_material("Metal", (0.8, 0.6, 0.3), roughness=0.2, metallic=1.0)
mat_teal = make_material("Teal", (0.1, 0.6, 0.6), roughness=0.4)
mat_red = make_material("Red", (0.8, 0.15, 0.1), roughness=0.5)

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, mat_floor)

# Central sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32,
                                     location=(0, 0, 1.0))
sphere = bpy.context.active_object
sphere.name = "Sphere"
bpy.ops.object.shade_smooth()
assign(sphere, mat_sphere)

# Supporting objects
bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.25,
                                 location=(0, 0, 0.25))
torus = bpy.context.active_object
torus.name = "Torus"
assign(torus, mat_metal)

bpy.ops.mesh.primitive_cube_add(size=1.2, location=(-3.2, 1.5, 0.6))
cube_a = bpy.context.active_object
cube_a.name = "CubeA"
cube_a.rotation_euler = (0, 0, math.radians(30))
assign(cube_a, mat_teal)

bpy.ops.mesh.primitive_cube_add(size=0.9, location=(2.8, -1.8, 0.45))
cube_b = bpy.context.active_object
cube_b.name = "CubeB"
cube_b.rotation_euler = (0, 0, math.radians(-20))
assign(cube_b, mat_red)

bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=1.8, location=(-1.5, -3.0, 0.9))
cone = bpy.context.active_object
cone.name = "Cone"
assign(cone, mat_metal)

# Pulsing point light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 3.2))
light = bpy.context.active_object
light.name = "PulseLight"
light.data.name = "PulseLightData"
light.data.color = (1.0, 0.8, 0.6)
light.data.shadow_soft_size = 0.2

DIM = 20.0
BRIGHT = 800.0

# Dim -> bright -> dim every 48 frames, spanning frames 1..96
# Keys: 1 dim, 25 bright, 49 dim, 73 bright, 97 dim
key_frames = [(1, DIM), (25, BRIGHT), (49, DIM), (73, BRIGHT), (97, DIM)]
for frame, energy in key_frames:
    light.data.energy = energy
    light.data.keyframe_insert(data_path="energy", frame=frame)

# Camera framing the scene
bpy.ops.object.camera_add(location=(7.5, -7.5, 5.0))
camera = bpy.context.active_object
camera.name = "Camera"
camera.data.lens = 50
target = Vector((0, 0, 0.8))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
