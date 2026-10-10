import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------------------
# Materials (node trees are created automatically in 5.x)
# ---------------------------------------------------------------------------
def make_mat(name, base, metallic=0.0, roughness=0.5, anisotropic=0.0,
             brushed=False, coat=0.0):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")

    bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Anisotropic"].default_value = anisotropic
    bsdf.inputs["Coat Weight"].default_value = coat

    if brushed:
        # Stretched noise drives roughness to produce fine brushed streaks
        tc = nodes.new("ShaderNodeTexCoord")
        mp = nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 90.0, 1.0)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 40.0
        noise.inputs["Detail"].default_value = 6.0
        mr = nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 0.18
        mr.inputs["To Max"].default_value = 0.42
        links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        links.new(mp.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


mat_steel = make_mat("BrushedSteel", (0.78, 0.78, 0.80), metallic=1.0,
                     roughness=0.3, anisotropic=0.6, brushed=True)
mat_black = make_mat("MatteBlack", (0.015, 0.015, 0.016), roughness=0.72)
mat_ceramic = make_mat("WhiteCeramic", (0.92, 0.90, 0.86), roughness=0.12)
mat_coffee = make_mat("Espresso", (0.06, 0.03, 0.01), roughness=0.25)
mat_floor = make_mat("ConcreteFloor", (0.09, 0.09, 0.095), roughness=0.6)


# ---------------------------------------------------------------------------
# Geometry helpers (all written in world space into a BMesh)
# ---------------------------------------------------------------------------
def _segment_matrix(p1, p2):
    d = p2 - p1
    length = d.length
    rot = d.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    m = Matrix.Translation((p1 + p2) * 0.5) @ rot
    return m, length


def add_cylinder(bm, p1, p2, r, seg=28):
    p1, p2 = Vector(p1), Vector(p2)
    m, length = _segment_matrix(p1, p2)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r, depth=length, matrix=m)


def add_box(bm, center, size):
    m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal(Vector(size)).to_4x4()
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def add_lathe(bm, profile, center, seg=48):
    cx, cy, cz = center
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((cx, cy, cz + z))])
        else:
            ring = []
            for i in range(seg):
                a = 2.0 * math.pi * i / seg
                ring.append(bm.verts.new((cx + r * math.cos(a),
                                          cy + r * math.sin(a),
                                          cz + z)))
            rings.append(ring)

    for ra, rb in zip(rings[:-1], rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        if len(ra) == 1:
            for i in range(seg):
                i2 = (i + 1) % seg
                bm.faces.new([ra[0], rb[i], rb[i2]])
        elif len(rb) == 1:
            for i in range(seg):
                i2 = (i + 1) % seg
                bm.faces.new([ra[i], ra[i2], rb[0]])
        else:
            for i in range(seg):
                i2 = (i + 1) % seg
                bm.faces.new([ra[i], ra[i2], rb[i2], rb[i]])

    # Close the bottom of the first ring
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))


def finish_object(name, bm, material, bevel=0.0):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    if bevel > 0.0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
    return obj


# ---------------------------------------------------------------------------
# Espresso machine: brushed steel body parts
# ---------------------------------------------------------------------------
bm_steel = bmesh.new()

# Main brushed steel body
add_box(bm_steel, (0.0, 0.0, 0.26), (0.30, 0.22, 0.32))

# Group head protruding from the front face
add_cylinder(bm_steel, (0.0, -0.105, 0.205), (0.0, -0.150, 0.205), 0.030)

# Portafilter basket (metal) at the group outlet
add_cylinder(bm_steel, (0.0, -0.145, 0.205), (0.0, -0.178, 0.205), 0.034)

# Steam wand: horizontal then bent downward
wand_pts = [(0.12, -0.105, 0.28), (0.12, -0.170, 0.28), (0.12, -0.190, 0.22)]
for a, b in zip(wand_pts[:-1], wand_pts[1:]):
    add_cylinder(bm_steel, a, b, 0.006, seg=16)

# Pressure gauge bezel
add_cylinder(bm_steel, (-0.06, -0.110, 0.34), (-0.06, -0.125, 0.34), 0.028)

machine_steel = finish_object("MachineBody", bm_steel, mat_steel, bevel=0.003)


# ---------------------------------------------------------------------------
# Matte black parts
# ---------------------------------------------------------------------------
bm_black = bmesh.new()

# Matte black base
add_box(bm_black, (0.0, 0.0, 0.05), (0.36, 0.26, 0.10))

# Cup warmer tray on top
add_box(bm_black, (0.0, 0.0, 0.43), (0.30, 0.20, 0.02))

# Drip tray grate
add_box(bm_black, (0.0, -0.155, 0.095), (0.25, 0.07, 0.01))

# Portafilter handle
add_cylinder(bm_black, (0.0, -0.176, 0.205), (0.0, -0.265, 0.200), 0.011, seg=20)

# Control knob
add_cylinder(bm_black, (0.05, -0.110, 0.34), (0.05, -0.130, 0.34), 0.012, seg=24)

# Gauge face
add_cylinder(bm_black, (-0.06, -0.124, 0.34), (-0.06, -0.127, 0.34), 0.024, seg=28)

machine_black = finish_object("MachineBlack", bm_black, mat_black, bevel=0.004)


# ---------------------------------------------------------------------------
# Small ceramic espresso cup under the portafilter
# ---------------------------------------------------------------------------
cup_center = (0.0, -0.165, 0.10)
cup_profile = [
    (0.030, 0.000),   # outer base
    (0.038, 0.058),   # outer wall
    (0.041, 0.062),   # rim
    (0.037, 0.060),   # inner rim
    (0.031, 0.012),   # inner wall down
    (0.000, 0.012),   # inner floor center
]
bm_cup = bmesh.new()
add_lathe(bm_cup, cup_profile, cup_center, seg=56)
cup_obj = finish_object("EspressoCup", bm_cup, mat_ceramic)

# Espresso liquid inside the cup
bm_coffee = bmesh.new()
cx, cy, _ = cup_center
add_cylinder(bm_coffee, (cx, cy, 0.112), (cx, cy, 0.130), 0.030, seg=40)
coffee_obj = finish_object("Espresso", bm_coffee, mat_coffee)


# ---------------------------------------------------------------------------
# Floor plane (top surface at z = 0)
# ---------------------------------------------------------------------------
bm_floor = bmesh.new()
add_box(bm_floor, (0.0, 0.0, -0.005), (4.0, 4.0, 0.01))
floor_obj = finish_object("Floor", bm_floor, mat_floor)


# ---------------------------------------------------------------------------
# Lighting: soft key, fill, and rim area lights
# ---------------------------------------------------------------------------
def add_area_light(name, loc, target, energy, size, color=(1.0, 1.0, 1.0)):
    light_data = bpy.data.lights.new(name=name + "_Data", type='AREA')
    light_data.energy = energy
    light_data.size = size
    light_data.color = color
    light_obj = bpy.data.objects.new(name, light_data)
    scene.collection.objects.link(light_obj)
    light_obj.location = Vector(loc)
    direction = Vector(target) - Vector(loc)
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return light_obj


add_area_light("KeyLight", (0.9, -0.9, 1.0), (0.0, 0.0, 0.25),
               energy=350.0, size=0.8, color=(1.0, 0.97, 0.93))
add_area_light("FillLight", (-1.0, -0.6, 0.5), (0.0, 0.0, 0.25),
               energy=120.0, size=1.2, color=(0.9, 0.95, 1.0))
add_area_light("RimLight", (0.2, 0.9, 0.8), (0.0, 0.0, 0.3),
               energy=220.0, size=0.6)

# Soft dark world background
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
world_nt = scene.world.node_tree
bg_node = world_nt.nodes.get("Background")
if bg_node is not None:
    bg_node.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg_node.inputs["Strength"].default_value = 1.0


# ---------------------------------------------------------------------------
# Camera framing the machine and cup
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 70.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((0.85, -1.05, 0.52))
cam_target = Vector((0.0, -0.05, 0.22))
cam_obj.location = cam_loc
cam_obj.rotation_euler = (cam_target - cam_loc).to_track_quat('-Z', 'Y').to_euler()
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = (cam_target - cam_loc).length
cam_data.dof.aperture_fstop = 5.6

scene.camera = cam_obj

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
