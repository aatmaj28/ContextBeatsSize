import bpy
import math

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Make new keyframes linear by default
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

scene.frame_start = 1
scene.frame_end = 120

# World
world = bpy.data.worlds.new("SpaceWorld") if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.002, 0.002, 0.006, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Materials
def emission_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

def surface_mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = rough
    return m

star_mat = emission_mat("StarMat", (1.0, 0.65, 0.2, 1.0), 8.0)
planet_mat = surface_mat("PlanetMat", (0.1, 0.35, 0.8, 1.0))
orbit_mat = emission_mat("OrbitMat", (0.4, 0.4, 0.5, 1.0), 0.5)

# Star
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0), segments=64, ring_count=32)
star = bpy.context.active_object
star.name = "Star"
star.data.materials.append(star_mat)
bpy.ops.object.shade_smooth()

# Star light
light_data = bpy.data.lights.new("StarLight", type='POINT')
light_data.energy = 5000
light_data.color = (1.0, 0.8, 0.6)
light_data.shadow_soft_size = 1.5
light = bpy.data.objects.new("StarLight", light_data)
scene.collection.objects.link(light)

# Orbit pivot
pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)

orbit_radius = 6.0

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(orbit_radius, 0, 0), segments=48, ring_count=24)
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
ring.data.materials.append(orbit_mat)

# Animation: full rotation, frame 121 == frame 1 for seamless loop
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

def iter_fcurves(action):
    if action is None:
        return
    fcs = getattr(action, "fcurves", None)
    if fcs is not None:
        try:
            for fc in fcs:
                yield fc
        except Exception:
            pass
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    yield fc

if pivot.animation_data and pivot.animation_data.action:
    for fc in iter_fcurves(pivot.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.extrapolation = 'LINEAR'

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

# Faint fill light so the night side isn't pitch black
fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 0.05
fill = bpy.data.objects.new("Fill", fill_data)
fill.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(fill)

scene.frame_set(1)
