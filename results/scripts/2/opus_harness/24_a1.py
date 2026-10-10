import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

stone = make_mat("Stone", (0.55, 0.53, 0.5), 0.8)
marble = make_mat("Marble", (0.9, 0.88, 0.84), 0.3)
bronze = make_mat("Bronze", (0.6, 0.4, 0.2), 0.35, 1.0)
ground_mat = make_mat("Ground", (0.15, 0.17, 0.15), 0.9)

def add(obj, mat):
    obj.data.materials.append(mat)
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
add(bpy.context.active_object, ground_mat)

# Pedestal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.1))
o = bpy.context.active_object; o.scale = (2.2, 2.2, 0.2); add(o, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.85))
o = bpy.context.active_object; o.scale = (1.6, 1.6, 1.3); add(o, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.6))
o = bpy.context.active_object; o.scale = (1.9, 1.9, 0.2); add(o, stone)

# Figure
base_z = 1.7
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.0, location=(-0.2, 0, base_z + 0.5))
add(bpy.context.active_object, marble)  # leg
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.0, location=(0.2, 0, base_z + 0.5))
add(bpy.context.active_object, marble)  # leg
bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=1.1, location=(0, 0, base_z + 1.5))
o = bpy.context.active_object; o.scale = (1, 0.65, 1); add(o, marble)  # torso
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0, 0, base_z + 2.05), segments=32, ring_count=16)
o = bpy.context.active_object; o.scale = (1.1, 0.7, 0.4); add(o, marble)  # shoulders
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.25, location=(0, 0, base_z + 2.25))
add(bpy.context.active_object, marble)  # neck
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, base_z + 2.55), segments=32, ring_count=16)
o = bpy.context.active_object; bpy.ops.object.shade_smooth(); add(o, marble)  # head
# Arms
bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.95, location=(-0.55, 0, base_z + 1.6))
o = bpy.context.active_object; o.rotation_euler = (0, math.radians(-12), 0); add(o, marble)
bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.95, location=(0.62, 0, base_z + 2.35))
o = bpy.context.active_object; o.rotation_euler = (0, math.radians(20), 0); add(o, marble)
# Raised torch / orb in hand
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0.8, 0, base_z + 2.9))
o = bpy.context.active_object; bpy.ops.object.shade_smooth(); add(o, bronze)

# Target empty at statue center
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 2.6)
scene.collection.objects.link(target)

# Orbit pivot
pivot = bpy.data.objects.new("OrbitPivot", None)
pivot.location = (0, 0, 0)
scene.collection.objects.link(pivot)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (0, -9, 3.8)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

# Animate orbit
scene.frame_start = 1
scene.frame_end = 100
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert("rotation_euler", index=2, frame=101)
ad = pivot.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
if cb:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Lighting
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", 'AREA')
area_data.energy = 600
area_data.size = 5
area = bpy.data.objects.new("Fill", area_data)
area.location = (-5, 4, 6)
scene.collection.objects.link(area)
c = area.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.4, 0.5, 0.65, 1.0)
bg.inputs["Strength"].default_value = 0.6

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_set(1)
