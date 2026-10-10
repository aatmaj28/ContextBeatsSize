import bpy
import bmesh
import math
import random
from mathutils import Vector

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
scene.frame_start = 1
scene.frame_end = 1
scene.render.engine = 'BLENDER_EEVEE'


# ---------- Helpers ----------
def make_principled(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_object(name, mesh_builder, location, material):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    mesh_builder(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj


def cone_builder(radius1, radius2, depth, segments):
    def build(bm):
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=segments,
            radius1=radius1,
            radius2=radius2,
            depth=depth,
        )
    return build


# ---------- Materials ----------
bark_mat = make_principled("Bark", (0.16, 0.10, 0.06), 0.95)
leaf_mats = [
    make_principled("Pine_Dark", (0.03, 0.14, 0.05), 0.7),
    make_principled("Pine_Mid", (0.05, 0.20, 0.07), 0.7),
    make_principled("Pine_Blue", (0.04, 0.16, 0.12), 0.65),
]
ground_mat = make_principled("Forest_Floor", (0.06, 0.07, 0.04), 1.0)

# ---------- Ground ----------
def ground_builder(bm):
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80.0)

ground = add_object("Ground", ground_builder, (0, 0, 0), ground_mat)

# ---------- Trees ----------
def make_tree(index, x, y, s):
    root = bpy.data.objects.new(f"Tree_{index:03d}", None)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.01
    root.location = (x, y, 0)
    scene.collection.objects.link(root)

    trunk = add_object(
        f"Trunk_{index:03d}",
        cone_builder(0.15 * s, 0.12 * s, 2.6 * s, 6),
        (0, 0, 1.3 * s),
        bark_mat,
    )
    trunk.parent = root

    tiers = [
        (1.7, 2.6, 1.6),
        (1.25, 2.3, 3.0),
        (0.8, 2.0, 4.2),
        (0.4, 1.6, 5.2),
    ]
    leaf = random.choice(leaf_mats)
    for i, (r, d, base) in enumerate(tiers):
        r_jit = r * random.uniform(0.9, 1.1)
        cone = add_object(
            f"Foliage_{index:03d}_{i}",
            cone_builder(r_jit * s, 0.0, d * s, 10),
            (0, 0, (base + d / 2) * s),
            leaf,
        )
        cone.parent = root

    root.rotation_euler.z = random.uniform(0, math.tau)
    return root


placed = 0
attempts = 0
while placed < 70 and attempts < 2000:
    attempts += 1
    x = random.uniform(-32, 32)
    y = random.uniform(-6, 40)
    # Keep a clear lane in front of the camera
    if abs(x) < 2.5 and y < 12:
        continue
    # Reject overlap
    too_close = False
    for obj in scene.objects:
        if obj.name.startswith("Tree_") and obj.type == 'EMPTY':
            if (Vector((obj.location.x, obj.location.y)) - Vector((x, y))).length < 2.2:
                too_close = True
                break
    if too_close:
        continue
    s = random.uniform(0.8, 1.6)
    make_tree(placed, x, y, s)
    placed += 1

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 2.5
sun_data.angle = math.radians(3)
sun_data.color = (1.0, 0.92, 0.78)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FogFill", 'AREA')
fill_data.energy = 400
fill_data.size = 20
fill_data.color = (0.7, 0.85, 1.0)
fill = bpy.data.objects.new("FogFill", fill_data)
fill.location = (0, -15, 20)
fill.rotation_euler = (math.radians(20), 0, 0)
scene.collection.objects.link(fill)

# ---------- World with volumetric fog ----------
world = bpy.data.worlds.new("ForestFog")
scene.world = world
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links

bg = wnodes.get("Background")
out = wnodes.get("World Output")
bg.inputs["Color"].default_value = (0.05, 0.08, 0.07, 1.0)
bg.inputs["Strength"].default_value = 0.3

vol = wnodes.new("ShaderNodeVolumeScatter")
vol.inputs["Color"].default_value = (0.65, 0.78, 0.72, 1.0)
vol.inputs["Density"].default_value = 0.035
vol.inputs["Anisotropy"].default_value = 0.35
wlinks.new(vol.outputs["Volume"], out.inputs["Volume"])

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam_data.dof.use_dof = False
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)

cam_pos = Vector((0.0, -24.0, 4.5))
target = Vector((0.0, 8.0, 3.0))
cam.location = cam_pos
direction = target - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
