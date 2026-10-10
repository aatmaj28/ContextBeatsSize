import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene
collection = scene.collection


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def make_material(name, color, roughness=0.6, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def link_object(obj):
    collection.objects.link(obj)
    return obj


def make_sphere(name, radius, material, segments=48, rings=24):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    return link_object(obj)


def make_ring(name, inner_r, outer_r, material, segments=128):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    inner_verts = []
    outer_verts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        inner_verts.append(bm.verts.new((inner_r * c, inner_r * s, 0.0)))
        outer_verts.append(bm.verts.new((outer_r * c, outer_r * s, 0.0)))
    bm.verts.ensure_lookup_table()
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((inner_verts[i], outer_verts[i], outer_verts[j], inner_verts[j]))
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    return link_object(obj)


# ---------- Clean up and world ----------
clear_scene()

world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Sun ----------
sun_color = (1.0, 0.72, 0.28)
sun_mat = make_material("Sun", sun_color, roughness=0.4,
                        emission_color=sun_color, emission_strength=30.0)
sun = make_sphere("Sun", 1.2, sun_mat)
sun.visible_shadow = False  # keeps the point light at origin from being blocked
sun.location = (0.0, 0.0, 0.0)

corona_mat = make_material("Corona", (1.0, 0.45, 0.1), roughness=1.0,
                           emission_color=(1.0, 0.45, 0.1), emission_strength=3.5)
corona = make_sphere("SunCorona", 1.6, corona_mat, segments=32, rings=16)
corona.visible_shadow = False
corona.location = (0.0, 0.0, 0.0)

# Light source at the sun's center
sun_light_data = bpy.data.lights.new("SunLight", type='POINT')
sun_light_data.energy = 3500.0
sun_light_data.color = (1.0, 0.85, 0.7)
sun_light_data.shadow_soft_size = 0.3
sun_light = link_object(bpy.data.objects.new("SunLight", sun_light_data))
sun_light.location = (0.0, 0.0, 0.0)

# ---------- Planets ----------
planets_spec = [
    # name, radius, color, roughness, orbit radius, angle (deg)
    ("Rocky", 0.35, (0.55, 0.52, 0.5), 0.9, 3.6, 25.0),
    ("Ocean", 0.55, (0.15, 0.40, 0.85), 0.35, 5.8, 115.0),
    ("Desert", 0.45, (0.80, 0.35, 0.18), 0.8, 8.2, 205.0),
    ("GasGiant", 1.05, (0.85, 0.72, 0.50), 0.5, 11.8, 300.0),
]

planets = {}
for name, radius, color, rough, orbit_r, angle_deg in planets_spec:
    mat = make_material(name + "_Mat", color, roughness=rough)
    planet = make_sphere(name, radius, mat)
    a = math.radians(angle_deg)
    planet.location = (orbit_r * math.cos(a), orbit_r * math.sin(a), 0.0)
    planets[name] = planet

# Ring around the gas giant, tilted
gas = planets["GasGiant"]
ring_mat = make_material("RingMat", (0.78, 0.70, 0.58), roughness=0.7)
ring = make_ring("GasGiantRing", 1.35, 2.1, ring_mat)
ring.location = gas.location
ring.rotation_euler = (math.radians(70.0), 0.0, math.radians(20.0))

# ---------- Starfield ----------
star_mats = [
    make_material("Star_Warm", (1, 1, 1), emission_color=(1.0, 0.9, 0.75), emission_strength=8.0),
    make_material("Star_Cool", (1, 1, 1), emission_color=(0.7, 0.85, 1.0), emission_strength=8.0),
]
for i in range(90):
    u = random.uniform(-1.0, 1.0)
    theta = random.uniform(0.0, 2.0 * math.pi)
    r = random.uniform(70.0, 95.0)
    s = math.sqrt(1.0 - u * u)
    pos = Vector((r * s * math.cos(theta), r * s * math.sin(theta), r * u))
    star = make_sphere(f"Star_{i:03d}", random.uniform(0.08, 0.18),
                       random.choice(star_mats), segments=8, rings=4)
    star.location = pos
    star.visible_shadow = False

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SolarCamera")
cam_data.lens = 50.0
cam = link_object(bpy.data.objects.new("SolarCamera", cam_data))
cam.location = (0.0, -32.0, 16.0)
target = Vector((0.0, 0.0, 0.0))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no rendering performed) ----------
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.frame_start = 1
scene.frame_end = 1
