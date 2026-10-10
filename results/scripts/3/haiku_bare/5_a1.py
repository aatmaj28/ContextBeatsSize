import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)
for light in list(bpy.data.lights):
    if light.users == 0:
        bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    if cam.users == 0:
        bpy.data.cameras.remove(cam)

scene = bpy.context.scene
collection = bpy.context.collection


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


def add_sphere(name, radius, location, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=location, segments=64, ring_count=32
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.data.materials.append(mat)
    smooth_shade(obj)
    return obj


def add_flat_ring(name, inner, outer, segments, mat, location=(0, 0, 0), rotation=(0, 0, 0)):
    me = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    inner_verts = []
    outer_verts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        inner_verts.append(bm.verts.new((inner * c, inner * s, 0.0)))
        outer_verts.append(bm.verts.new((outer * c, outer * s, 0.0)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([inner_verts[i], outer_verts[i], outer_verts[j], inner_verts[j]])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


# ---------- World background ----------
world = bpy.data.worlds.get("World")
if world is None:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.006, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Sun ----------
sun_mat = make_material(
    "SunMaterial", (1.0, 0.6, 0.15), roughness=0.4,
    emission_color=(1.0, 0.65, 0.2), emission_strength=25.0
)
sun = add_sphere("Sun", 1.4, (0, 0, 0), sun_mat)

sun_light = bpy.data.lights.new("SunLight", type='POINT')
sun_light.energy = 2500.0
sun_light.color = (1.0, 0.8, 0.55)
sun_light.shadow_soft_size = 0.5
sun_light_obj = bpy.data.objects.new("SunLight", sun_light)
collection.objects.link(sun_light_obj)
sun_light_obj.location = (0, 0, 0)

# Faint fill light so planet night sides are not pure black
fill = bpy.data.lights.new("FillLight", type='AREA')
fill.energy = 150.0
fill.size = 12.0
fill.color = (0.5, 0.6, 1.0)
fill_obj = bpy.data.objects.new("FillLight", fill)
collection.objects.link(fill_obj)
fill_obj.location = (-10, -12, 14)
fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-40))

# ---------- Orbit guides ----------
orbit_mat = make_material(
    "OrbitMaterial", (0.2, 0.25, 0.35), roughness=0.9,
    emission_color=(0.3, 0.4, 0.6), emission_strength=0.6
)
planet_specs = [
    # name, radius, orbit distance, base color, roughness, angle (deg)
    ("Ember",   0.35,  3.2, (0.85, 0.30, 0.18), 0.7, 30.0),
    ("Azure",   0.60,  5.6, (0.20, 0.45, 0.95), 0.4, 140.0),
    ("Gilded",  0.95,  8.6, (0.90, 0.75, 0.45), 0.6, 250.0),
    ("Violet",  0.48, 12.0, (0.55, 0.25, 0.85), 0.5, 75.0),
]

for name, _, dist, _, _, _ in planet_specs:
    add_flat_ring("Orbit_" + name, dist - 0.012, dist + 0.012, 256, orbit_mat)

# ---------- Planets ----------
ring_mat = make_material("RingMaterial", (0.85, 0.78, 0.6), roughness=0.8)
ring_mat.use_backface_culling = False

for name, radius, dist, color, rough, angle_deg in planet_specs:
    a = math.radians(angle_deg)
    loc = (dist * math.cos(a), dist * math.sin(a), 0.0)
    mat = make_material(name + "_Material", color, roughness=rough)
    planet = add_sphere(name, radius, loc, mat)

    if name == "Gilded":
        # Ringed planet
        ring = add_flat_ring(
            "Gilded_Ring",
            inner=radius * 1.35,
            outer=radius * 2.0,
            segments=160,
            mat=ring_mat,
            location=loc,
            rotation=(math.radians(72), math.radians(8), 0.0),
        )
        # Slightly varied ring color via a second thin inner band
        inner_band_mat = make_material(
            "Gilded_InnerBand", (0.55, 0.45, 0.30), roughness=0.9
        )
        inner_band_mat.use_backface_culling = False
        add_flat_ring(
            "Gilded_InnerBand",
            inner=radius * 1.2,
            outer=radius * 1.35,
            segments=160,
            mat=inner_band_mat,
            location=loc,
            rotation=(math.radians(72), math.radians(8), 0.0),
        )

# ---------- Background stars ----------
star_mat = make_material(
    "StarMaterial", (1, 1, 1), roughness=1.0,
    emission_color=(0.9, 0.93, 1.0), emission_strength=5.0
)
for i in range(120):
    direction = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.3, 1)))
    if direction.length < 0.01:
        continue
    direction.normalize()
    pos = direction * random.uniform(60, 90)
    add_sphere("Star_%d" % i, random.uniform(0.04, 0.12), tuple(pos), star_mat)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SystemCamera")
cam_data.lens = 35.0
cam_obj = bpy.data.objects.new("SystemCamera", cam_data)
collection.objects.link(cam_obj)

cam_location = Vector((0.0, -30.0, 17.0))
target = Vector((0.0, 0.0, 0.0))
cam_obj.location = cam_location
direction = target - cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 1
