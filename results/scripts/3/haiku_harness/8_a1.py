import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene


# ---------- Clear existing scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Materials ----------
def make_mat(name, base, rough=0.5, metal=0.0, emit=None, emit_strength=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    try:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    except KeyError:
        pass
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

red_stripe = make_mat("RedStripe", (0.70, 0.04, 0.03), rough=0.45)
white_stripe = make_mat("WhiteStripe", (0.90, 0.90, 0.87), rough=0.40)
roof_red = make_mat("RoofRed", (0.45, 0.05, 0.04), rough=0.5)
metal_dark = make_mat("DarkMetal", (0.08, 0.08, 0.09), rough=0.35, metal=0.9)
glass = make_mat("LampGlass", (0.9, 0.95, 0.8), rough=0.05,
                 emit=(1.0, 0.85, 0.55), emit_strength=18.0)
rock_mat = make_mat("Rock", (0.20, 0.17, 0.14), rough=0.92)
water_mat = make_mat("Water", (0.02, 0.12, 0.16), rough=0.04, spec=0.8)


# ---------- Helpers ----------
def link(obj):
    scene.collection.objects.link(obj)
    return obj


def lathe(name, profile, seg, band_fn, mats):
    """Revolve a (radius, z) profile into a mesh with per-band material indices."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    angles = [2.0 * math.pi * i / seg for i in range(seg)]
    rings = []
    for r, z in profile:
        ring = [bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in angles]
        rings.append(ring)
    for i in range(len(rings) - 1):
        zmid = 0.5 * (profile[i][1] + profile[i + 1][1])
        idx = band_fn(zmid)
        for j in range(seg):
            k = (j + 1) % seg
            f = bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
            f.material_index = idx
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    for p in mesh.polygons:
        p.use_smooth = True
    return link(bpy.data.objects.new(name, mesh))


# ---------- Rocky island ----------
def make_rock(name, scale, loc, roughness_amt=0.18, subdiv=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        n = v.co.normalized()
        v.co = n * (1.0 + random.uniform(-roughness_amt, roughness_amt))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(rock_mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = link(bpy.data.objects.new(name, mesh))
    obj.scale = scale
    obj.location = loc
    return obj

island = make_rock("Island", (7.5, 6.5, 1.3), (0.0, 0.0, -0.75), 0.16, 3)

# Smaller boulders around the base
boulders = [
    ((4.2, -3.5, -0.2), (1.1, 0.9, 0.5)),
    ((-4.8, 2.9, -0.3), (0.9, 0.8, 0.45)),
    ((2.0, 4.6, -0.35), (0.7, 0.6, 0.35)),
    ((-2.6, -4.4, -0.3), (0.8, 0.7, 0.4)),
]
for i, (loc, sc) in enumerate(boulders):
    make_rock(f"Boulder{i}", sc, loc, 0.22, 2)


# ---------- Lighthouse tower (striped) ----------
BAND_H = 2.0
tower_profile = []
for k in range(41):
    z = 0.5 * k  # 0 .. 20
    r = 2.4 + (1.3 - 2.4) * (z / 20.0)
    tower_profile.append((r, z))

tower = lathe("Tower", tower_profile, 40,
              lambda z: int(z // BAND_H) % 2,
              [red_stripe, white_stripe])

# Gallery deck
lathe("Gallery", [(1.95, 19.9), (1.95, 20.2)], 40,
      lambda z: 0, [metal_dark])

# Lantern room (glass)
lathe("LanternGlass", [(1.15, 20.2), (1.15, 22.5)], 24,
      lambda z: 0, [glass])

# Lantern frame posts (dark metal)
for k in range(8):
    a = 2.0 * math.pi * k / 8
    post = bpy.data.meshes.new(f"Post{k}")
    bm = bmesh.new()
    cx, cy = 1.18 * math.cos(a), 1.18 * math.sin(a)
    bmesh.ops.create_cube(bm, size=0.12)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, 21.35))
    bm.to_mesh(post)
    bm.free()
    post.materials.append(metal_dark)
    link(bpy.data.objects.new(f"Post{k}", post))

# Roof
lathe("Roof", [(1.6, 22.5), (0.05, 24.2)], 24,
      lambda z: 0, [roof_red])

# Finial
lathe("Finial", [(0.12, 24.2), (0.12, 24.6), (0.03, 24.75)], 12,
      lambda z: 0, [metal_dark])


# ---------- Water ----------
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
water = bpy.context.active_object
water.name = "Water"
water.data.materials.append(water_mat)
water.data.name = "WaterMesh"


# ---------- Lighting ----------
lamp_data = bpy.data.lights.new("LampLight", 'POINT')
lamp_data.energy = 4000.0
lamp_data.color = (1.0, 0.85, 0.6)
lamp_data.shadow_soft_size = 0.5
lamp = link(bpy.data.objects.new("LampLight", lamp_data))
lamp.location = (0.0, 0.0, 21.3)

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(6)
sun = link(bpy.data.objects.new("Sun", sun_data))
sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))

# Sky world
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.72, 0.95, 1.0)
bg.inputs["Strength"].default_value = 1.0


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = link(bpy.data.objects.new("Camera", cam_data))
cam_loc = Vector((28.0, -44.0, 14.0))
target = Vector((0.0, 0.0, 11.0))
cam.location = cam_loc
direction = (target - cam_loc).normalized()
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
