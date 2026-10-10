import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# World
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.002, 0.002, 0.008, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Materials
star_mat = bpy.data.materials.new("StarMat")
nt = star_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.65, 0.2, 1.0)
emit.inputs["Strength"].default_value = 8.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

planet_mat = bpy.data.materials.new("PlanetMat")
bsdf = planet_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.1, 0.35, 0.8, 1.0)
bsdf.inputs["Roughness"].default_value = 0.6

ring_mat = bpy.data.materials.new("OrbitMat")
rnt = ring_mat.node_tree
for n in list(rnt.nodes):
    rnt.nodes.remove(n)
re = rnt.nodes.new("ShaderNodeEmission")
re.inputs["Color"].default_value = (0.4, 0.5, 0.7, 1.0)
re.inputs["Strength"].default_value = 0.4
ro = rnt.nodes.new("ShaderNodeOutputMaterial")
rnt.links.new(re.outputs["Emission"], ro.inputs["Surface"])

# Star
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
star.data.materials.append(star_mat)
bpy.ops.object.shade_smooth()
star.visible_shadow = False

# Star light
light_data = bpy.data.lights.new("StarLight", type='POINT')
light_data.energy = 20000
light_data.color = (1.0, 0.85, 0.6)
light_data.shadow_soft_size = 1.0
light = bpy.data.objects.new("StarLight", light_data)
scene.collection.objects.link(light)

# Orbit pivot
pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)

orbit_radius = 6.0

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=48, ring_count=24, location=(orbit_radius, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
planet.data.materials.append(planet_mat)
bpy.ops.object.shade_smooth()
planet.parent = pivot

# Orbit path ring
bpy.ops.mesh.primitive_torus_add(major_radius=orbit_radius, minor_radius=0.015,
                                 major_segments=128, minor_segments=8)
ring = bpy.context.active_object
ring.name = "OrbitPath"
ring.data.materials.append(ring_mat)
ring.visible_shadow = False

# Animation: full circle over 120 frames (frame 121 = 360 deg so loop is seamless)
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

anim = pivot.animation_data
cb = anim_utils.action_get_channelbag_for_slot(anim.action, anim.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
    fc.update()

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -14, 9)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_set(1)
