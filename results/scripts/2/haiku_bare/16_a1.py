import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene


def set_input(node, names, value):
    """Set the first matching input name (handles API naming changes)."""
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


# ---------- Materials ----------
def make_crystal_material():
    mat = bpy.data.materials.new("PurpleCrystal")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], (0.55, 0.12, 0.85, 1.0))
    set_input(bsdf, ["Roughness"], 0.04)
    set_input(bsdf, ["IOR"], 1.55)
    set_input(bsdf, ["Transmission Weight", "Transmission"], 1.0)
    set_input(bsdf, ["Coat Weight", "Clearcoat"], 0.6)
    set_input(bsdf, ["Coat Roughness", "Clearcoat Roughness"], 0.05)
    set_input(bsdf, ["Emission Color"], (0.5, 0.1, 0.9, 1.0))
    set_input(bsdf, ["Emission Strength"], 0.25)
    try:
        mat.blend_method = 'BLEND'
    except Exception:
        pass
    return mat


def make_rock_material():
    mat = bpy.data.materials.new("DarkRock")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], (0.035, 0.032, 0.035, 1.0))
    set_input(bsdf, ["Roughness"], 0.9)
    set_input(bsdf, ["Specular IOR Level", "Specular"], 0.3)
    return mat


crystal_mat = make_crystal_material()
rock_mat = make_rock_material()


# ---------- Geometry helpers ----------
def make_crystal(name, base_xy, height, radius, tilt_axis, tilt_angle, spin):
    """Hexagonal prism with a pointed termination."""
    bm = bmesh.new()
    sides = 6
    tip = height * 0.28
    bottom, top = [], []
    for i in range(sides):
        a = spin + 2 * math.pi * i / sides
        x, y = math.cos(a) * radius, math.sin(a) * radius
        bottom.append(bm.verts.new((x, y, -height * 0.25)))
        top.append(bm.verts.new((x * 0.92, y * 0.92, height)))
    apex = bm.verts.new((0.0, 0.0, height + tip))
    base_c = bm.verts.new((0.0, 0.0, -height * 0.25 - radius * 0.15))

    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
        bm.faces.new((bottom[j], bottom[i], base_c))
    bm.normal_update()

    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)

    axis = Vector(tilt_axis).normalized()
    rot = Matrix.Rotation(tilt_angle, 4, axis)
    obj.matrix_world = Matrix.Translation((base_xy[0], base_xy[1], 0.0)) @ rot
    obj.data.materials.append(crystal_mat)
    bpy.ops.object.shade_smooth()
    return obj


def make_rock():
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        n = 1.0 + random.uniform(-0.12, 0.12)
        # Flatten bottom and top for a slab-like boulder
        v.co = Vector((d.x * 2.6 * n, d.y * 2.2 * n, d.z * 0.9 * n))
        if v.co.z < -0.2:
            v.co.z = -0.2 + (v.co.z + 0.2) * 0.3
    # Extra roughness
    for v in bm.verts:
        v.co += Vector([random.uniform(-0.04, 0.04) for _ in range(3)])
    bm.normal_update()
    mesh = bpy.data.meshes.new("RockMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Rock", mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(rock_mat)
    bpy.ops.object.shade_smooth()
    return obj


# ---------- Build the scene ----------
rock = make_rock()
rock.location = (0.0, 0.0, -0.2)

# Crystal cluster: a central large crystal with smaller ones leaning outward
crystal_specs = [
    # (base_xy, height, radius, tilt_axis, tilt_deg, spin)
    ((0.0, 0.0),    2.2, 0.42, (0, 0, 1), 0,   0.3),
    ((0.55, 0.2),   1.6, 0.34, (0, 1, 0), 22,  0.8),
    ((-0.5, 0.15),  1.8, 0.36, (1, 0, 0), -20, 1.2),
    ((0.1, -0.5),   1.2, 0.28, (1, 0, 0), 35,  0.1),
    ((-0.2, 0.55),  1.0, 0.25, (0, 1, 0), -30, 1.7),
    ((0.8, -0.35),  0.9, 0.22, (0, 1, 0), 48,  2.1),
    ((-0.8, -0.2),  0.8, 0.20, (1, 0, 0), -45, 0.6),
    ((0.35, 0.8),   0.7, 0.18, (1, 0, 0), 55,  2.5),
]

crystals = []
for idx, (xy, h, r, axis, deg, spin) in enumerate(crystal_specs):
    c = make_crystal(f"Crystal_{idx}", xy, h * random.uniform(0.95, 1.05),
                     r, axis, math.radians(deg), spin)
    c.location.z = 0.35
    crystals.append(c)

# ---------- Lighting ----------
def add_light(name, ltype, location, energy, color, size=None):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    ld.color = color
    if size is not None and ltype == 'AREA':
        ld.size = size
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = location
    return lo

key = add_light("KeyLight", 'AREA', (3.5, -3.5, 4.5), 900, (1.0, 0.95, 0.9), size=3.0)
key.rotation_euler = (math.radians(55), 0, math.radians(45))

rim = add_light("PurpleRim", 'POINT', (-2.5, 2.8, 2.2), 350, (0.7, 0.3, 1.0))
fill = add_light("SoftFill", 'AREA', (0.0, -5.0, 1.0), 120, (0.6, 0.6, 0.8), size=5.0)
fill.rotation_euler = (math.radians(80), 0, 0)

# Subtle world background
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wbg = world.node_tree.nodes.get("Background")
if wbg:
    set_input(wbg, ["Color"], (0.01, 0.008, 0.015, 1.0))
    set_input(wbg, ["Strength"], 0.3)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)

target = Vector((0.0, 0.0, 1.0))
cam_pos = Vector((4.2, -5.2, 3.4))
cam.location = cam_pos
direction = target - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# Frame settings (no render, just configuration)
scene.frame_start = 1
scene.frame_end = 1
