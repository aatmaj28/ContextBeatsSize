import bpy
import math
from mathutils import Vector

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def make_mat(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*color, 1.0)
    return m

mat_ground = make_mat("Grass", (0.15, 0.4, 0.12), 0.9)
mat_tower = make_mat("Stone", (0.85, 0.8, 0.7), 0.8)
mat_roof = make_mat("Roof", (0.45, 0.12, 0.08), 0.6)
mat_wood = make_mat("Wood", (0.35, 0.22, 0.12), 0.6)
mat_sail = make_mat("Sail", (0.92, 0.9, 0.85), 0.8)
mat_door = make_mat("Door", (0.2, 0.12, 0.06), 0.7)

# Ground
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(mat_ground)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.0, radius2=1.3, depth=6, location=(0, 0, 3))
tower = bpy.context.active_object
tower.data.materials.append(mat_tower)

# Roof
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.6, radius2=0.0, depth=1.8, location=(0, 0, 6.9))
roof = bpy.context.active_object
roof.data.materials.append(mat_roof)

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.9, 0.8))
door = bpy.context.active_object
door.scale = (0.8, 0.15, 1.6)
door.data.materials.append(mat_door)

# Axle
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.2, location=(0, -1.6, 5.6),
                                    rotation=(math.radians(90), 0, 0))
axle = bpy.context.active_object
axle.data.materials.append(mat_wood)

# Hub (rotating parent)
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.4, location=(0, -2.2, 5.6),
                                    rotation=(math.radians(90), 0, 0))
hub_mesh = bpy.context.active_object
hub_mesh.data.materials.append(mat_wood)

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -2.3, 5.6))
hub = bpy.context.active_object
hub.name = "BladeHub"
hub_mesh.parent = hub
hub_mesh.location = (0, 0.1, 0)
hub_mesh.rotation_euler = (math.radians(90), 0, 0)

# Blades
for i in range(4):
    a = i * math.pi / 2
    # spar
    bpy.ops.mesh.primitive_cube_add(size=1)
    spar = bpy.context.active_object
    spar.data.materials.append(mat_wood)
    spar.scale = (0.12, 0.08, 4.2)
    spar.parent = hub
    r = 2.1
    spar.location = (math.sin(a) * r, 0, math.cos(a) * r)
    spar.rotation_euler = (0, a, 0)
    # sail
    bpy.ops.mesh.primitive_cube_add(size=1)
    sail = bpy.context.active_object
    sail.data.materials.append(mat_sail)
    sail.scale = (0.8, 0.04, 3.2)
    sail.parent = hub
    r2 = 2.5
    off = 0.45
    sail.location = (math.sin(a) * r2 + math.cos(a) * off, -0.03,
                     math.cos(a) * r2 - math.sin(a) * off)
    sail.rotation_euler = (0, a, 0)

# Constant-speed rotation around Y axis (one full turn over 120 frames)
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass
hub.rotation_euler = (0, 0, 0)
hub.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
hub.rotation_euler = (0, 2 * math.pi, 0)
hub.keyframe_insert(data_path="rotation_euler", index=1, frame=121)

def set_linear(action):
    fcs = []
    try:
        fcs = list(action.fcurves)
    except Exception:
        try:
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        fcs.extend(bag.fcurves)
        except Exception:
            pass
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

if hub.animation_data and hub.animation_data.action:
    set_linear(hub.animation_data.action)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(-6, -8, 6))
fill = bpy.context.active_object
fill.data.energy = 400
fill.data.size = 5
fill.rotation_euler = (Vector((0, 0, 4)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# World
world = bpy.data.worlds.new("Sky") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(7, -16, 4.5))
cam = bpy.context.active_object
target = Vector((0, 0, 4.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 35
scene.camera = cam
