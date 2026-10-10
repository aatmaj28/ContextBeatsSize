import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.002, 0.002, 0.006, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Materials
def emissive_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

star_mat = emissive_mat("StarMat", (1.0, 0.65, 0.2, 1.0), 12.0)
ring_mat = emissive_mat("OrbitMat", (0.3, 0.5, 1.0, 1.0), 0.6)

planet_mat = bpy.data.materials.new("PlanetMat")
bsdf = planet_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.1, 0.35, 0.8, 1.0)
bsdf.inputs["Roughness"].default_value = 0.6

# Star
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, segments=48, ring_count=24, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
bpy.ops.object.shade_smooth()
star.data.materials.append(star_mat)
star.visible_shadow = False

# Star light
light_data = bpy.data.lights.new("StarLight", type='POINT')
light_data.energy = 5000
light_data.color = (1.0, 0.85, 0.6)
light_data.shadow_soft_size = 1.0
light = bpy.data.objects.new("StarLight", light_data)
scene.collection.objects.link(light)

# Orbit pivot
pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)

# Planet
orbit_radius = 6.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, segments=32, ring_count=16, location=(orbit_radius, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()
planet.data.materials.append(planet_mat)
planet.parent = pivot

# Orbit ring guide
bpy.ops.mesh.primitive_torus_add(major_radius=orbit_radius, minor_radius=0.015,
                                 major_segments=128, minor_segments=8)
ring = bpy.context.active_object
ring.name = "OrbitPath"
ring.data.materials.append(ring_mat)
ring.visible_shadow = False

# Animate full orbit (frame 121 == frame 1 so loop is seamless)
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

# Planet self spin
planet.rotation_euler = (0, 0, 0)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
planet.rotation_euler = (0, 0, 4 * math.pi)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

def make_linear(obj):
    ad = obj.animation_data
    if ad and ad.action:
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        if cb:
            for fc in cb.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'

make_linear(pivot)
make_linear(planet)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -14, 8)
direction = -cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
