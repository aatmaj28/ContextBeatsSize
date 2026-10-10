import bpy
import bmesh
import math
import random
import mathutils

random.seed(7)

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def link_object(obj):
    collection.objects.link(obj)
    return obj


def make_mat(name, color, roughness=0.5, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def make_sphere(name, radius, location, mat, u=48, v=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v,
                              radius=radius, calc_uvs=True)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    return link_object(obj)


def make_annulus(name, r_in, r_out, segments, mat, location=(0, 0, 0),
                 rot=(0, 0, 0)):
    bm = bmesh.new()
    inner, outer = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        inner.append(bm.verts.new((r_in * c, r_in * s, 0)))
        outer.append(bm.verts.new((r_out * c, r_out * s, 0)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rot
    return link_object(obj)


# ---------- World background (deep space) ----------
world = bpy.data.worlds.new("Space")
scene.world = world
if world.node_tree:
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.005, 0.006, 0.015, 1.0)
        bg.inputs["Strength"].default_value = 1.0


# ---------- Sun ----------
sun_mat = make_mat("Sun", (1.0, 0.6, 0.15), roughness=0.4,
                   emission=(1.0, 0.65, 0.2), strength=14.0)
sun = make_sphere("Sun", 1.4, (0, 0, 0), sun_mat, u=64, v=32)
try:
    sun.visible_shadow = False  # keep the emitter from blocking its own light
except AttributeError:
    pass

# Sun light at the center
sun_light_data = bpy.data.lights.new("SunLight", 'POINT')
sun_light_data.energy = 2500.0
sun_light_data.shadow_soft_size = 0.8
sun_light_data.color = (1.0, 0.85, 0.7)
sun_light = link_object(bpy.data.objects.new("SunLight", sun_light_data))
sun_light.location = (0, 0, 0)

# Soft fill light from the camera side
fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 120.0
fill_data.size = 20.0
fill_data.color = (0.6, 0.7, 1.0)
fill = link_object(bpy.data.objects.new("FillLight", fill_data))
fill.location = (-10, -20, 18)
fill.rotation_euler = (math.radians(50), 0, math.radians(-25))


# ---------- Planets ----------
# name, radius, orbit distance, angle, color, roughness
planet_specs = [
    ("Mercury", 0.28, 3.2, 0.3, (0.62, 0.60, 0.57), 0.9),
    ("Earth",   0.42, 5.4, 2.1, (0.20, 0.48, 0.90), 0.45),
    ("Mars",    0.34, 7.6, 3.7, (0.82, 0.35, 0.20), 0.8),
    ("Saturn",  0.85, 11.0, 5.0, (0.90, 0.78, 0.55), 0.55),
]

planets = {}
for name, radius, dist, angle, color, rough in planet_specs:
    loc = (dist * math.cos(angle), dist * math.sin(angle), 0.0)
    mat = make_mat(name + "Mat", color, roughness=rough)
    planets[name] = make_sphere(name, radius, loc, mat, u=48, v=24)

# Saturn's ring, tilted and attached at its location
ring_mat = make_mat("RingMat", (0.85, 0.78, 0.62), roughness=0.7)
saturn_loc = planets["Saturn"].location
ring = make_annulus("SaturnRing", 1.25, 1.95, 160, ring_mat,
                    location=saturn_loc,
                    rot=(math.radians(22), math.radians(-8), 0))

# Faint orbit tracks
orbit_mat = make_mat("OrbitMat", (0.3, 0.35, 0.5), roughness=1.0,
                     emission=(0.3, 0.4, 0.7), strength=0.6)
for _, _, dist, _, _, _ in planet_specs:
    make_annulus(f"Orbit{dist}", dist - 0.012, dist + 0.012, 160, orbit_mat)


# ---------- Starfield ----------
star_mat = make_mat("Star", (1, 1, 1), roughness=1.0,
                    emission=(1, 0.97, 0.9), strength=8.0)
for i in range(140):
    direction = mathutils.Vector((random.gauss(0, 1),
                                  random.gauss(0, 1),
                                  random.gauss(0, 1)))
    if direction.length < 1e-6:
        continue
    direction.normalize()
    pos = direction * random.uniform(60, 90)
    make_sphere(f"Star{i}", random.uniform(0.12, 0.25), tuple(pos),
                star_mat, u=8, v=4)


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = link_object(bpy.data.objects.new("Camera", cam_data))
cam_loc = mathutils.Vector((0.0, -30.0, 15.0))
cam.location = cam_loc
target = mathutils.Vector((2.0, 0.0, 0.0))
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
