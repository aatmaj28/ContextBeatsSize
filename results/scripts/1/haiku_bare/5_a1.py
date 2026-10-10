import bpy
import math
from mathutils import Vector

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1

# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def smooth_mesh(obj):
    mesh = obj.data
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()

def make_sphere(name, radius, location, material):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=location, segments=48, ring_count=24
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_mesh"
    smooth_mesh(obj)
    obj.data.materials.append(material)
    return obj

# ---------- Sun ----------
sun_mat = make_material(
    "Sun_Mat", (1.0, 0.6, 0.15), roughness=0.4,
    emission_color=(1.0, 0.65, 0.2), emission_strength=25.0
)
sun = make_sphere("Sun", 1.2, (0.0, 0.0, 0.0), sun_mat)

# Sun light (point light at the center of the system)
sun_light_data = bpy.data.lights.new(name="Sun_Light", type='POINT')
sun_light_data.energy = 3000.0
sun_light_data.color = (1.0, 0.85, 0.6)
sun_light_data.shadow_soft_size = 0.2
sun_light = bpy.data.objects.new("Sun_Light", sun_light_data)
sun_light.location = (0.0, 0.0, 0.0)
scene.collection.objects.link(sun_light)

# Soft fill light so the dark sides of planets stay readable
fill_data = bpy.data.lights.new(name="Fill_Light", type='AREA')
fill_data.energy = 150.0
fill_data.size = 10.0
fill = bpy.data.objects.new("Fill_Light", fill_data)
fill.location = (4.0, -12.0, 8.0)
fill.rotation_euler = (math.radians(55), 0.0, math.radians(10))
scene.collection.objects.link(fill)

# ---------- Planets ----------
planets = []

# 1. Small rocky grey-brown planet
rocky_mat = make_material("Rocky_Mat", (0.55, 0.45, 0.38), roughness=0.85)
rocky = make_sphere("Planet_Rocky", 0.35, (2.6, 0.0, 0.0), rocky_mat)
planets.append(rocky)

# 2. Medium ocean-blue planet
ocean_mat = make_material("Ocean_Mat", (0.15, 0.4, 0.9), roughness=0.35)
ocean = make_sphere("Planet_Ocean", 0.6, (4.3, 0.6, 0.0), ocean_mat)
planets.append(ocean)

# 3. Small red desert planet
red_mat = make_material("Red_Mat", (0.85, 0.3, 0.18), roughness=0.7)
red = make_sphere("Planet_Red", 0.45, (6.0, -0.5, 0.0), red_mat)
planets.append(red)

# 4. Large gas giant with a ring
giant_mat = make_material("Giant_Mat", (0.92, 0.78, 0.55), roughness=0.5)
giant = make_sphere("Planet_Giant", 0.95, (8.8, 0.0, 0.0), giant_mat)
planets.append(giant)

# Ring for the gas giant
ring_mat = make_material("Ring_Mat", (0.85, 0.78, 0.62), roughness=0.6)
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.6, minor_radius=0.06,
    major_segments=128, minor_segments=12,
    location=(8.8, 0.0, 0.0)
)
ring = bpy.context.active_object
ring.name = "Giant_Ring"
ring.data.name = "Giant_Ring_mesh"
ring.scale = (1.0, 1.0, 0.35)
ring.rotation_euler = (math.radians(72), 0.0, math.radians(15))
smooth_mesh(ring)
ring.data.materials.append(ring_mat)

# Slight axial tilt for the giant to match its ring plane
giant.rotation_euler = (math.radians(72), 0.0, math.radians(15))

# ---------- World (deep space background) ----------
world = bpy.data.worlds.new("Space_World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.012, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)

cam_location = Vector((4.5, -15.0, 7.0))
target = Vector((4.5, 0.0, 0.0))
cam.location = cam_location
direction = target - cam_location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
