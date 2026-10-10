import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection

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

def smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True

def add_sphere(name, radius, location, material):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64, ring_count=32, radius=radius, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    smooth_shade(obj)
    obj.data.materials.append(material)
    return obj

def add_torus(name, major, minor, location, material, scale=(1, 1, 1), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=160,
        minor_segments=16,
        major_radius=major,
        minor_radius=minor,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    smooth_shade(obj)
    obj.data.materials.append(material)
    return obj

# ---------- World (dark space) ----------
world = bpy.data.worlds.new("SpaceWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.006, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 0.3
scene.world = world

# ---------- Materials ----------
sun_mat = make_material(
    "SunMat", (1.0, 0.6, 0.15), roughness=0.4,
    emission_color=(1.0, 0.65, 0.2), emission_strength=25.0
)
mercury_mat = make_material("MercuryMat", (0.55, 0.52, 0.5), roughness=0.9)
earth_mat = make_material("EarthMat", (0.15, 0.4, 0.85), roughness=0.6)
mars_mat = make_material("MarsMat", (0.75, 0.3, 0.15), roughness=0.85)
giant_mat = make_material("GiantMat", (0.85, 0.7, 0.45), roughness=0.5)
ring_mat = make_material("RingMat", (0.8, 0.75, 0.6), roughness=0.7)
orbit_mat = make_material("OrbitMat", (0.08, 0.1, 0.14), roughness=1.0)

# ---------- Sun ----------
sun = add_sphere("Sun", 1.6, (0, 0, 0), sun_mat)

# Sun light (illuminates the planets)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
sun_light = bpy.context.active_object
sun_light.name = "SunLight"
sun_light.data.energy = 12000.0
sun_light.data.color = (1.0, 0.85, 0.7)
sun_light.data.shadow_soft_size = 0.5

# Soft fill to keep the dark sides from being pure black
bpy.ops.object.light_add(type='AREA', location=(-6, -12, 10))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300.0
fill.data.size = 10.0
fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

# ---------- Planets ----------
planets = [
    # name, orbit radius, planet radius, angle (deg), material
    ("Mercury", 3.6, 0.45, 20, mercury_mat),
    ("Earth", 5.6, 0.7, 130, earth_mat),
    ("Mars", 7.6, 0.55, 255, mars_mat),
    ("Giant", 11.0, 1.5, 55, giant_mat),
]

# Orbit guide rings
for name, dist, _, _, _ in planets:
    add_torus(f"Orbit_{name}", dist, 0.025, (0, 0, 0), orbit_mat)

for name, dist, rad, angle_deg, mat in planets:
    a = math.radians(angle_deg)
    loc = (dist * math.cos(a), dist * math.sin(a), 0.0)
    planet = add_sphere(name, rad, loc, mat)

    if name == "Giant":
        # Tilted ring system around the gas giant
        tilt = (math.radians(70), 0, math.radians(15))
        add_torus(
            "GiantRing", rad * 1.6, rad * 0.12, loc, ring_mat,
            scale=(1.0, 1.0, 1.0), rotation=tilt
        )
        add_torus(
            "GiantRingInner", rad * 1.3, rad * 0.06, loc, ring_mat,
            scale=(1.0, 1.0, 1.0), rotation=tilt
        )

# ---------- Background stars (small emissive dots) ----------
star_mat = make_material(
    "StarMat", (1, 1, 1), roughness=1.0,
    emission_color=(1, 1, 1), emission_strength=4.0
)
for i in range(120):
    d = random.uniform(40, 60)
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(math.radians(35), math.radians(145))
    x = d * math.sin(phi) * math.cos(theta)
    y = d * math.sin(phi) * math.sin(theta)
    z = d * math.cos(phi)
    add_sphere(f"Star_{i}", random.uniform(0.08, 0.2), (x, y, z), star_mat)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam_obj)

cam_loc = Vector((2.5, -26.0, 16.0))
target = Vector((2.5, 0.0, 0.0))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Timeline (static scene) ----------
scene.frame_start = 1
scene.frame_end = 1
