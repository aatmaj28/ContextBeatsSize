import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Default new keyframes to linear
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

scene.frame_start = 1
scene.frame_end = 120

try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass

# World
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.002, 0.002, 0.008, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Materials
def emissive_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def surface_mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = rough
    return m

star_mat = emissive_mat("StarMat", (1.0, 0.7, 0.25, 1.0), 12.0)
ring_mat = emissive_mat("OrbitMat", (0.3, 0.4, 0.8, 1.0), 0.6)
planet_mat = surface_mat("PlanetMat", (0.1, 0.35, 0.8, 1.0), 0.5)

# Star
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0), segments=64, ring_count=32)
star = bpy.context.active_object
star.name = "Star"
star.data.materials.append(star_mat)
bpy.ops.object.shade_smooth()

# Light at star
light_data = bpy.data.lights.new("StarLight", type='POINT')
light_data.energy = 8000
light_data.color = (1.0, 0.85, 0.6)
light_data.shadow_soft_size = 1.5
light = bpy.data.objects.new("StarLight", light_data)
scene.collection.objects.link(light)

# Orbit ring
orbit_r = 6.0
bpy.ops.mesh.primitive_torus_add(major_radius=orbit_r, minor_radius=0.015,
                                 major_segments=128, minor_segments=8)
ring = bpy.context.active_object
ring.name = "OrbitPath"
ring.data.materials.append(ring_mat)

# Pivot empty
pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(orbit_r, 0, 0), segments=48, ring_count=24)
planet = bpy.context.active_object
planet.name = "Planet"
planet.data.materials.append(planet_mat)
bpy.ops.object.shade_smooth()
planet.parent = pivot

# Animate pivot: full circle; frame 121 == frame 1 for seamless loop
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

# Planet self-spin
planet.rotation_euler = (0, 0, 0)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
planet.rotation_euler = (0, 0, 4 * math.pi)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

def get_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    curves = []
    try:
        curves = list(act.fcurves)
        if curves:
            return curves
    except Exception:
        pass
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    curves.extend(cb.fcurves)
    except Exception:
        pass
    return curves

for ob in (pivot, planet):
    for fc in get_fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -13, 9)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_set(1)
