import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Helpers ----------

def make_material(name, color, roughness=0.5, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def link_object(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def new_mesh_object(name, build_fn, material=None, smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def sphere(name, radius, location, material, segments=48, rings=24):
    def build(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    obj = new_mesh_object(name, build, material)
    obj.location = Vector(location)
    return obj


def cylinder(name, radius, depth, location, material, segments=32):
    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                              segments=segments, radius1=radius,
                              radius2=radius, depth=depth)
    obj = new_mesh_object(name, build, material)
    obj.location = Vector(location)
    return obj


def cone(name, radius, depth, location, material, segments=24):
    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                              segments=segments, radius1=radius,
                              radius2=0.0, depth=depth)
    obj = new_mesh_object(name, build, material)
    obj.location = Vector(location)
    return obj


def plane_ground(name, size, material):
    def build(bm):
        n = 60
        step = size / n
        verts = []
        for i in range(n + 1):
            row = []
            for j in range(n + 1):
                x = -size / 2 + i * step
                y = -size / 2 + j * step
                # gentle rolling snow
                z = 0.06 * math.sin(x * 0.7) * math.cos(y * 0.5) + 0.03 * math.sin(x * 2.3 + y * 1.7)
                row.append(bm.verts.new((x, y, z)))
            verts.append(row)
        for i in range(n):
            for j in range(n):
                bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]))
    return new_mesh_object(name, build, material, smooth=True)


# ---------- Clear default scene objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
snow_mat = make_material("Snow", (0.92, 0.94, 0.97), roughness=0.85, specular=0.3)
ground_mat = make_material("GroundSnow", (0.88, 0.91, 0.95), roughness=0.9, specular=0.25)
carrot_mat = make_material("Carrot", (1.0, 0.45, 0.05), roughness=0.45)
hat_mat = make_material("TopHat", (0.02, 0.02, 0.025), roughness=0.35, specular=0.6)
coal_mat = make_material("Coal", (0.02, 0.02, 0.02), roughness=0.6)
stick_mat = make_material("Twig", (0.30, 0.18, 0.08), roughness=0.8, specular=0.3)
band_mat = make_material("HatBand", (0.6, 0.05, 0.05), roughness=0.5)

# ---------- Ground ----------
ground = plane_ground("Ground", 24.0, ground_mat)

# ---------- Snowman body ----------
bottom = sphere("BodyBottom", 1.0, (0, 0, 1.0), snow_mat)
middle = sphere("BodyMiddle", 0.7, (0, 0, 2.6), snow_mat)
head = sphere("Head", 0.5, (0, 0, 3.8), snow_mat)

# ---------- Carrot nose (points toward -Y, the camera side) ----------
nose = cone("CarrotNose", 0.09, 0.9, (0, -0.55, 3.8), carrot_mat)
nose.rotation_euler = (math.radians(90), 0, 0)

# ---------- Coal eyes ----------
for sx in (-1, 1):
    eye = sphere(f"Eye{sx}", 0.06, (sx * 0.18, -0.44, 3.95), coal_mat, segments=16, rings=8)

# ---------- Coal mouth ----------
for i, x in enumerate([-0.22, -0.11, 0.0, 0.11, 0.22]):
    z = 3.62 + 0.04 * math.cos((x / 0.22) * math.pi / 2.0) * 1.0 - 0.02
    sphere(f"Mouth{i}", 0.035, (x, -0.47, z), coal_mat, segments=12, rings=6)

# ---------- Buttons ----------
for i, z in enumerate([3.05, 2.7, 2.35]):
    sphere(f"Button{i}", 0.06, (0, -0.68, z), coal_mat, segments=16, rings=8)

# ---------- Scarf (small torus-like band around neck) ----------
def scarf_build(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40,
                          radius1=0.5, radius2=0.5, depth=0.12)
scarf = new_mesh_object("ScarfNeck", scarf_build, band_mat)
scarf.location = Vector((0, 0, 3.25))

# ---------- Stick arms ----------
def stick(name, center, angle_y):
    obj = cylinder(name, 0.045, 1.6, center, stick_mat, segments=10)
    obj.rotation_euler = (0, math.radians(angle_y), 0)
    return obj

stick("ArmLeft", (-1.05, 0, 2.95), -55)
stick("ArmRight", (1.05, 0, 2.95), 55)

# small twigs on the arm ends
for name, base, ang in [("TwigL1", (-1.7, 0, 3.7), -20), ("TwigR1", (1.7, 0, 3.7), 20)]:
    t = cylinder(name, 0.02, 0.35, base, stick_mat, segments=8)
    t.rotation_euler = (0, math.radians(ang), math.radians(35 if base[0] > 0 else -35))

# ---------- Top hat ----------
hat_brim = cylinder("HatBrim", 0.62, 0.06, (0, 0, 4.22), hat_mat, segments=40)
hat_body = cylinder("HatBody", 0.36, 0.75, (0, 0, 4.62), hat_mat, segments=40)
hat_band = cylinder("HatBand", 0.37, 0.12, (0, 0, 4.37), band_mat, segments=40)

# tilt the hat slightly for character
for obj in (hat_brim, hat_body, hat_band):
    obj.rotation_euler = (math.radians(-4), 0, math.radians(8))
    obj.location.x += 0.05

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(6)
sun = link_object(bpy.data.objects.new("Sun", sun_data))
sun.location = (4, -4, 8)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 400
fill_data.size = 6
fill = link_object(bpy.data.objects.new("Fill", fill_data))
fill.location = (-6, -5, 4)
fill.rotation_euler = (math.radians(70), 0, math.radians(-50))

rim_data = bpy.data.lights.new(name="Rim", type='AREA')
rim_data.energy = 250
rim_data.size = 4
rim = link_object(bpy.data.objects.new("Rim", rim_data))
rim.location = (0, 6, 5)
rim.rotation_euler = (math.radians(-120), 0, math.radians(180))

# ---------- World ----------
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.78, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
cam = link_object(bpy.data.objects.new("Camera", cam_data))
cam.location = Vector((5.2, -8.0, 3.6))
target = Vector((0, 0, 2.6))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
