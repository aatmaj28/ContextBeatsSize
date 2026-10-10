import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

scene = bpy.context.scene

# Clear any default objects
for obj in list(bpy.data.objects):
    bpy.data.objects.delete(obj, do_unlink=True)

collection = bpy.context.collection


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def make_material(name, color, roughness, transmission=0.0, ior=1.45,
                  emission=None, emission_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "IOR", ior)
    set_input(bsdf, "Transmission Weight", transmission)
    set_input(bsdf, "Alpha", alpha)
    if emission is not None:
        set_input(bsdf, "Emission Color", emission)
        set_input(bsdf, "Emission Strength", emission_strength)
    return mat


# Materials
crystal_mat = make_material(
    "PurpleCrystal",
    color=(0.55, 0.15, 0.85, 1.0),
    roughness=0.04,
    transmission=1.0,
    ior=1.55,
    emission=(0.35, 0.05, 0.6, 1.0),
    emission_strength=0.15,
)
crystal_mat.diffuse_color = (0.55, 0.15, 0.85, 1.0)

rock_mat = make_material(
    "DarkRock",
    color=(0.05, 0.045, 0.05, 1.0),
    roughness=0.9,
)


def link_object(obj):
    collection.objects.link(obj)
    return obj


def make_rock():
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        # Low-frequency bumps plus fine jitter for a craggy look
        bump = (math.sin(d.x * 3.1 + 0.7) * math.cos(d.y * 2.7)
                + math.sin(d.z * 3.7 + d.x * 1.3)) * 0.12
        jitter = random.uniform(-0.06, 0.06)
        v.co = v.co * (1.0 + bump + jitter)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new("RockMesh")
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new("Rock", mesh)
    link_object(obj)
    obj.scale = (2.0, 1.6, 0.7)
    obj.location = (0.0, 0.0, -0.35)
    obj.data.materials.append(rock_mat)
    return obj


def make_crystal(name, loc, radius, height, euler):
    bm = bmesh.new()
    sides = 6
    angles = [2 * math.pi * i / sides for i in range(sides)]
    bottom = [bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.0))
              for a in angles]
    top_z = height * 0.72
    top = [bm.verts.new((radius * 0.85 * math.cos(a),
                         radius * 0.85 * math.sin(a), top_z))
           for a in angles]
    tip = bm.verts.new((0.0, 0.0, height))

    # Bottom cap
    bm.faces.new(bottom)
    # Side walls
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    # Pointed tip
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((top[i], top[j], tip))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj)
    obj.location = loc
    obj.rotation_euler = euler
    obj.data.materials.append(crystal_mat)
    return obj


# Rock base
make_rock()

# Crystal cluster: a central large crystal with smaller ones leaning outward
cluster = [
    # (x, y, radius, height, tilt_x, tilt_y)
    (0.0, 0.0, 0.20, 1.6, 0.0, 0.0),
    (0.35, -0.15, 0.14, 1.1, 0.35, -0.2),
    (-0.38, 0.1, 0.13, 1.0, -0.4, 0.15),
    (0.1, 0.4, 0.12, 0.85, 0.5, 0.05),
    (-0.15, -0.38, 0.11, 0.75, -0.3, -0.45),
    (0.6, 0.35, 0.09, 0.6, 0.6, 0.3),
    (-0.6, -0.25, 0.10, 0.65, -0.55, -0.2),
]

for idx, (x, y, r, h, tx, ty) in enumerate(cluster):
    rz = random.uniform(0, 2 * math.pi)
    # Base sits slightly into the rock surface
    z_base = 0.55 - 0.25 * (abs(x) + abs(y))
    make_crystal(
        f"Crystal_{idx}",
        loc=(x, y, z_base),
        radius=r,
        height=h,
        euler=(tx, ty, rz),
    )

# Lighting
key = bpy.data.lights.new("KeyArea", type='AREA')
key.energy = 900
key.size = 3.0
key_obj = link_object(bpy.data.objects.new("KeyArea", key))
key_obj.location = (3.5, -4.5, 5.0)
key_obj.rotation_euler = (math.radians(55), 0.0, math.radians(35))

rim = bpy.data.lights.new("PurpleRim", type='POINT')
rim.energy = 250
rim.color = (0.7, 0.4, 1.0)
rim_obj = link_object(bpy.data.objects.new("PurpleRim", rim))
rim_obj.location = (-3.0, 3.0, 2.0)

fill = bpy.data.lights.new("Fill", type='SUN')
fill.energy = 1.2
fill.color = (0.8, 0.85, 1.0)
fill_obj = link_object(bpy.data.objects.new("Fill", fill))
fill_obj.rotation_euler = (math.radians(60), 0.0, math.radians(-150))

# World: near black background
world = bpy.data.worlds.new("DarkWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
set_input(bg, "Color", (0.015, 0.012, 0.02, 1.0))
set_input(bg, "Strength", 1.0)
scene.world = world

# Camera framing the cluster
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
cam_obj = link_object(bpy.data.objects.new("Camera", cam_data))
cam_pos = Vector((4.2, -6.0, 3.0))
target = Vector((0.0, 0.0, 0.7))
cam_obj.location = cam_pos
direction = target - cam_pos
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# Render settings (not rendering, just configuring)
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
