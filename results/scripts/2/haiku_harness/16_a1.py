import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, noise
from mathutils import Euler

random.seed(7)

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.transmission_bounces = 16
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = False


# ---------- Helpers ----------
def make_material(name, color, roughness, transmission=0.0, ior=1.5,
                  emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def link_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------- Dark rock base ----------
rock_bm = bmesh.new()
bmesh.ops.create_icosphere(rock_bm, subdivisions=4, radius=1.0)

for v in rock_bm.verts:
    n = v.co.normalized()
    big = noise.noise(v.co * 1.2)
    small = noise.noise(v.co * 4.0)
    r = 1.5 + 0.35 * big + 0.10 * small
    v.co = n * r
    v.co.z *= 0.6  # flatten into a boulder

# Slightly flatten the underside so it reads as sitting on ground
for v in rock_bm.verts:
    if v.co.z < -0.45:
        v.co.z = -0.45 + (v.co.z + 0.45) * 0.3

rock_mesh = bpy.data.meshes.new("RockMesh")
rock_bm.to_mesh(rock_mesh)
rock_bm.free()
rock_mesh.update()
for p in rock_mesh.polygons:
    p.use_smooth = False

rock = link_object("Rock", rock_mesh)
rock_mat = make_material("DarkRock", (0.03, 0.028, 0.032), roughness=0.92)
rock.data.materials.append(rock_mat)

# ---------- Purple transparent crystals ----------
crystal_bm = bmesh.new()


def add_crystal(bm, M, radius, height):
    ring_b, ring_t = [], []
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        x, y = math.cos(a) * radius, math.sin(a) * radius
        ring_b.append(bm.verts.new(M @ Vector((x, y, 0.0))))
        ring_t.append(bm.verts.new(M @ Vector((x * 0.92, y * 0.92, height * 0.72))))
    tip = bm.verts.new(M @ Vector((0.0, 0.0, height)))

    bm.faces.new(ring_b[::-1])
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new((ring_b[i], ring_b[j], ring_t[j], ring_t[i]))
        bm.faces.new((ring_t[i], ring_t[j], tip))


# Crystals placed on the upper surface of the rock, clustered together
crystal_count = 11
for _ in range(crystal_count):
    theta = random.uniform(0.0, 2.0 * math.pi)
    phi = random.uniform(0.0, 0.75)  # keep them on the upper cap
    sx = math.sin(phi) * math.cos(theta)
    sy = math.sin(phi) * math.sin(theta)
    sz = math.cos(phi)

    base = Vector((sx * 1.5, sy * 1.5, sz * 1.5 * 0.6)) - Vector((0, 0, 0.05))
    normal = Vector((sx, sy, sz / 0.6)).normalized()

    # Align crystal up-axis with the surface normal, then add a random spin and tilt
    align = Vector((0, 0, 1)).rotation_difference(normal).to_matrix().to_4x4()
    spin = Matrix.Rotation(random.uniform(0, 2 * math.pi), 4, 'Z')
    tilt = Matrix.Rotation(random.uniform(-0.35, 0.35), 4, 'X')
    M = Matrix.Translation(base) @ align @ spin @ tilt

    radius = random.uniform(0.14, 0.24)
    height = random.uniform(0.55, 1.15)
    add_crystal(crystal_bm, M, radius, height)

crystal_bm.normal_update()
crystal_mesh = bpy.data.meshes.new("CrystalMesh")
crystal_bm.to_mesh(crystal_mesh)
crystal_bm.free()
crystal_mesh.update()
for p in crystal_mesh.polygons:
    p.use_smooth = False

crystals = link_object("PurpleCrystals", crystal_mesh)
crystal_mat = make_material(
    "PurpleGlass",
    color=(0.45, 0.08, 0.85),
    roughness=0.04,
    transmission=1.0,
    ior=1.55,
    emission=(0.5, 0.1, 1.0),
    emission_strength=0.6,
)
crystals.data.materials.append(crystal_mat)

# ---------- World ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.008, 0.015, 1.0)
bg.inputs["Strength"].default_value = 0.5

# ---------- Lighting ----------
key_data = bpy.data.lights.new("KeyArea", type='AREA')
key_data.energy = 900.0
key_data.size = 3.0
key_data.color = (1.0, 0.97, 0.94)
key = link_object("KeyArea", key_data)
key.location = (3.0, -3.5, 4.5)
key.rotation_euler = (math.radians(55), 0.0, math.radians(40))

rim_data = bpy.data.lights.new("PurpleRim", type='POINT')
rim_data.energy = 350.0
rim_data.color = (0.7, 0.3, 1.0)
rim_data.shadow_soft_size = 0.5
rim = link_object("PurpleRim", rim_data)
rim.location = (-2.8, 2.2, 2.0)

fill_data = bpy.data.lights.new("SoftFill", type='AREA')
fill_data.energy = 120.0
fill_data.size = 5.0
fill_data.color = (0.6, 0.65, 1.0)
fill = link_object("SoftFill", fill_data)
fill.location = (-4.0, -2.0, 1.5)
fill.rotation_euler = (math.radians(80), 0.0, math.radians(-60))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55.0
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 7.0
cam_data.dof.aperture_fstop = 4.0
camera = link_object("Camera", cam_data)
camera.location = (4.2, -5.2, 2.9)

target = Vector((0.0, 0.0, 0.7))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = camera

# Still image: keep a single frame
scene.frame_start = 1
scene.frame_end = 1
