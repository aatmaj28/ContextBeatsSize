import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default scene contents
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    bpy.data.cameras.remove(cam)


def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def link(obj):
    scene.collection.objects.link(obj)
    return obj


# Materials
mat_floor = make_material("Floor", (0.8, 0.8, 0.8), roughness=0.9)
mat_sphere = make_material("Sphere", (0.9, 0.35, 0.1), roughness=0.3, metallic=0.0)
mat_cube = make_material("Cube", (0.2, 0.5, 0.9), roughness=0.4)
mat_metal = make_material("Metal", (0.9, 0.9, 0.95), roughness=0.15, metallic=1.0)

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(mat_floor)

# Central sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1.0), segments=64, ring_count=32)
sphere = bpy.context.active_object
sphere.name = "Sphere"
sphere.data.materials.append(mat_sphere)
bpy.ops.object.shade_smooth()

# Cube on the left
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(-2.2, 0.6, 0.6))
cube = bpy.context.active_object
cube.name = "Cube"
cube.rotation_euler = (0, 0, math.radians(30))
cube.data.materials.append(mat_cube)

# Metallic torus on the right
bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.3,
                                 location=(2.3, 0.4, 0.3))
torus = bpy.context.active_object
torus.name = "Torus"
torus.rotation_euler = (math.radians(90), 0, math.radians(-20))
torus.data.materials.append(mat_metal)

# Pulsing point light
light_data = bpy.data.lights.new(name="PulseLight", type='POINT')
light_data.shadow_soft_size = 0.3
light_obj = bpy.data.objects.new("PulseLight", light_data)
light_obj.location = (3.0, -3.0, 4.0)
link(light_obj)

DIM_ENERGY = 20.0
BRIGHT_ENERGY = 1200.0

# Cycle is 48 frames: dim at 1, bright at 25, dim at 49, bright at 73, dim at 97 (wrap)
keys = {
    1: DIM_ENERGY,
    25: BRIGHT_ENERGY,
    49: DIM_ENERGY,
    73: BRIGHT_ENERGY,
    97: DIM_ENERGY,
}
for frame, energy in keys.items():
    light_data.energy = energy
    light_data.keyframe_insert(data_path="energy", frame=frame)

# Camera framing the subject
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = (7.0, -7.5, 4.0)
link(cam_obj)

target = Vector((0.0, 0.0, 1.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# Simple lighting fill: soft area light so the scene isn't pitch black between pulses
fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 60.0
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
fill_obj.location = (-5.0, 5.0, 6.0)
fill_obj.rotation_euler = (math.radians(45), 0, math.radians(-135))
link(fill_obj)

# Timeline
scene.frame_start = 1
scene.frame_end = 96
scene.frame_set(1)
