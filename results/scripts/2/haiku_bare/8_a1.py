import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metallic=0.0, emit=None, emit_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    return mat

mat_red = make_mat("LH_Red", (0.70, 0.07, 0.05), rough=0.45)
mat_white = make_mat("LH_White", (0.92, 0.92, 0.88), rough=0.4)
mat_dark = make_mat("LH_DarkMetal", (0.08, 0.08, 0.09), rough=0.35, metallic=0.6)
mat_glass = make_mat("LH_Glass", (0.9, 0.95, 1.0), rough=0.05, emit=(1.0, 0.85, 0.5),
                     emit_strength=25.0, alpha=0.6)
mat_rock = make_mat("Rock", (0.32, 0.30, 0.27), rough=0.92)
mat_rock_dark = make_mat("RockDark", (0.18, 0.17, 0.16), rough=0.95)
mat_grass = make_mat("Grass", (0.20, 0.30, 0.12), rough=0.9)
mat_water = make_mat("Water", (0.04, 0.22, 0.30), rough=0.04, metallic=0.0)

# ---------- Helpers ----------
def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj

def new_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    return link(obj)

def make_rock(name, center, size, scale, mat, seed_off=0.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co.x + seed_off, v.co.y, v.co.z
        f = (0.14 * math.sin(3.1 * x + 1.7 * z) * math.cos(2.3 * y)
             + 0.10 * math.sin(5.7 * z + 1.3 * x)
             + 0.06 * math.cos(7.9 * y - 2.1 * x)
             + random.uniform(-0.04, 0.04))
        v.co *= (1.0 + f)
    bm.normal_update()
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = new_object(name, mesh)
    obj.location = center
    obj.scale = Vector(scale) * size
    for p in mesh.polygons:
        p.use_smooth = True
    return obj

# ---------- Water ----------
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
water = bpy.context.active_object
water.name = "Water"
water.data.materials.append(mat_water)

# ---------- Island ----------
island = make_rock("Island", (0, 0, -4.0), 11.0, (1.0, 1.0, 0.42), mat_rock, seed_off=0.5)

# Grassy cap (flattened top patch)
bpy.ops.mesh.primitive_circle_add(vertices=40, radius=7.0, fill_type='NGON', location=(0, 0, 0.9))
grass = bpy.context.active_object
grass.name = "GrassPatch"
grass.data.materials.append(mat_grass)

# Scattered boulders around the island edge
for i in range(14):
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(6.0, 10.5)
    s = random.uniform(0.5, 1.4)
    loc = (math.cos(a) * d, math.sin(a) * d, random.uniform(-0.2, 0.3))
    mat = mat_rock if random.random() < 0.6 else mat_rock_dark
    make_rock(f"Boulder_{i}", loc, s, (1.0, 1.0, random.uniform(0.5, 0.8)), mat,
              seed_off=random.uniform(0, 5))

# ---------- Lighthouse tower ----------
H_TOP = 22.0
Z_BOTTOM = -3.0
R_BASE = 2.4
R_TOP = 1.35
N_BANDS = 10
SEGS = 32

bm = bmesh.new()
rings = []
for k in range(N_BANDS + 1):
    t = k / N_BANDS
    z = Z_BOTTOM + (H_TOP - Z_BOTTOM) * t
    r = R_BASE + (R_TOP - R_BASE) * t
    ring = []
    for s in range(SEGS):
        a = 2 * math.pi * s / SEGS
        ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
    rings.append(ring)

for k in range(N_BANDS):
    for s in range(SEGS):
        n = (s + 1) % SEGS
        f = bm.faces.new([rings[k][s], rings[k][n], rings[k + 1][n], rings[k + 1][s]])
        f.material_index = k % 2  # 0 = white, 1 = red

bm.faces.new(rings[-1])  # top cap
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
tower_mesh = bpy.data.meshes.new("TowerMesh")
bm.to_mesh(tower_mesh)
bm.free()
tower_mesh.materials.append(mat_white)
tower_mesh.materials.append(mat_red)
for p in tower_mesh.polygons:
    p.use_smooth = True
tower = new_object("Tower", tower_mesh)

# Gallery deck
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=2.0, depth=0.3,
                                    location=(0, 0, H_TOP + 0.15))
gallery = bpy.context.active_object
gallery.name = "Gallery"
gallery.data.materials.append(mat_dark)

# Railing ring
bpy.ops.mesh.primitive_torus_add(major_radius=1.95, minor_radius=0.06,
                                 major_segments=32, minor_segments=8,
                                 location=(0, 0, H_TOP + 0.9))
rail = bpy.context.active_object
rail.name = "Railing"
rail.data.materials.append(mat_dark)

# Lantern room (glass with emission)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.15, depth=2.4,
                                    location=(0, 0, H_TOP + 1.2))
lantern = bpy.context.active_object
lantern.name = "LanternGlass"
lantern.data.materials.append(mat_glass)

# Lantern frame mullions
for i in range(8):
    a = 2 * math.pi * i / 8
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(math.cos(a) * 1.15, math.sin(a) * 1.15,
                                                        H_TOP + 1.2))
    m = bpy.context.active_object
    m.name = f"Mullion_{i}"
    m.scale = (0.06, 0.06, 1.2)
    m.rotation_euler = (0, 0, a)
    m.data.materials.append(mat_dark)

# Roof
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.45, radius2=0.0, depth=1.1,
                                location=(0, 0, H_TOP + 2.4 + 0.55))
roof = bpy.context.active_object
roof.name = "Roof"
roof.data.materials.append(mat_red)

# Ventilator ball on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, H_TOP + 3.65))
ball = bpy.context.active_object
ball.name = "FinialBall"
ball.data.materials.append(mat_dark)

# Small keeper house at the island base
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.2, -2.6, 1.3))
house = bpy.context.active_object
house.name = "KeeperHouse"
house.scale = (2.6, 2.0, 1.4)
house.data.materials.append(mat_white)

bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.1, radius2=0.0, depth=1.2,
                                location=(-4.2, -2.6, 3.0))
house_roof = bpy.context.active_object
house_roof.name = "KeeperRoof"
house_roof.rotation_euler = (0, 0, math.radians(45))
house_roof.data.materials.append(mat_red)

# ---------- Lighting ----------
# Sun
bpy.ops.object.light_add(type='SUN', location=(0, 0, 40))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 4.5
sun.data.angle = math.radians(2.0)
sun.data.color = (1.0, 0.95, 0.88)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35))

# Lantern glow
bpy.ops.object.light_add(type='POINT', location=(0, 0, H_TOP + 1.2))
glow = bpy.context.active_object
glow.name = "LanternGlow"
glow.data.energy = 2500.0
glow.data.color = (1.0, 0.82, 0.5)
glow.data.shadow_soft_size = 1.0

# World sky gradient
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
bg = wnodes.get("Background")
if bg is None:
    bg = wnodes.new("ShaderNodeBackground")
grad = wnodes.new("ShaderNodeTexGradient")
mapping = wnodes.new("ShaderNodeMapping")
ramp = wnodes.new("ShaderNodeValToRGB")
texcoord = wnodes.new("ShaderNodeTexCoord")
ramp.color_ramp.elements[0].color = (0.75, 0.85, 0.95, 1.0)
ramp.color_ramp.elements[1].color = (0.30, 0.55, 0.90, 1.0)
wlinks.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
wlinks.new(mapping.outputs["Vector"], grad.inputs["Vector"])
wlinks.new(grad.outputs["Fac"], ramp.inputs["Fac"])
wlinks.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("LighthouseCam")
cam_data.lens = 50
cam_data.clip_end = 1000
cam = new_object("LighthouseCam", cam_data)
cam_loc = Vector((30.0, -40.0, 13.0))
target = Vector((0.0, 0.0, 10.5))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
