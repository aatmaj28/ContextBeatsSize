import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = bpy.context.collection


# ---------- Helpers ----------
def make_mat(name, base, rough=0.8, emit=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def make_obj(name, build_fn, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def add_cone(bm, cx, cy, z0, r, h, seg, tx=0.0, ty=0.0):
    """Open-ended low poly cone with a closed base and a tip offset (for flames)."""
    ring = []
    for i in range(seg):
        a = 2 * math.pi * i / seg + random.uniform(-0.15, 0.15)
        rr = r * random.uniform(0.85, 1.15)
        ring.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z0)))
    tip = bm.verts.new((cx + tx, cy + ty, z0 + h))
    try:
        bm.faces.new(ring)
    except ValueError:
        pass
    for i in range(seg):
        try:
            bm.faces.new((ring[i], ring[(i + 1) % seg], tip))
        except ValueError:
            pass


# ---------- Materials ----------
mat_bark = make_mat("Bark", (0.22, 0.12, 0.06), rough=0.95)
mat_charred = make_mat("CharredWood", (0.04, 0.03, 0.025), rough=1.0)
mat_stone = make_mat("Stone", (0.30, 0.30, 0.31), rough=0.9)
mat_ash = make_mat("Ash", (0.05, 0.05, 0.05), rough=1.0)
mat_ground = make_mat("Ground", (0.04, 0.045, 0.035), rough=1.0)
mat_flame_outer = make_mat("FlameOuter", (1.0, 0.3, 0.02), rough=0.5,
                           emit=(1.0, 0.35, 0.05), emit_strength=6.0)
mat_flame_inner = make_mat("FlameInner", (1.0, 0.8, 0.3), rough=0.5,
                           emit=(1.0, 0.85, 0.4), emit_strength=10.0)
mat_ember = make_mat("Ember", (1.0, 0.4, 0.1), rough=0.6,
                     emit=(1.0, 0.45, 0.12), emit_strength=15.0)

# ---------- Ground and ash bed ----------
def build_ground(bm):
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=7.0)

ground = make_obj("Ground", build_ground, mat_ground)
ground.location = (0, 0, 0)

def build_ash(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=9, radius=0.75)

ash = make_obj("AshBed", build_ash, mat_ash)
ash.location = (0, 0, 0.005)

# ---------- Logs (crossed) ----------
def build_log(bm, radius=0.12, length=1.7):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=7,
                          radius1=radius, radius2=radius, depth=length)

log_specs = [
    # (location, z-rotation, material)
    ((0.0, 0.0, 0.12), 0.35, mat_bark),
    ((0.0, 0.02, 0.12 + 0.20), -0.25 + math.pi / 2, mat_bark),
    ((0.12, -0.05, 0.36), 0.9, mat_charred),
    ((-0.22, 0.10, 0.09), 0.2, mat_charred),
]
for i, (loc, zrot, mat) in enumerate(log_specs):
    log = make_obj(f"Log{i}", build_log, mat)
    log.location = loc
    log.rotation_euler = (0.0, math.pi / 2, zrot)

# ---------- Stone ring ----------
def make_stone_builder(radius):
    def build(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=1, diameter=radius * 2)
        for v in bm.verts:
            v.co += Vector((random.uniform(-0.05, 0.05),
                            random.uniform(-0.05, 0.05),
                            random.uniform(-0.03, 0.03)))
    return build

stone_count = 11
ring_radius = 1.15
for i in range(stone_count):
    a = 2 * math.pi * i / stone_count + random.uniform(-0.12, 0.12)
    r = ring_radius * random.uniform(0.92, 1.08)
    s = random.uniform(0.22, 0.32)
    stone = make_obj(f"Stone{i}", make_stone_builder(s), mat_stone)
    stone.location = (r * math.cos(a), r * math.sin(a), s * 0.45)
    stone.rotation_euler = (random.uniform(0, math.tau),
                            random.uniform(0, math.tau),
                            random.uniform(0, math.tau))
    stone.scale = (random.uniform(0.9, 1.2), random.uniform(0.9, 1.2), random.uniform(0.6, 0.8))

# ---------- Flames (outer orange and inner yellow cones) ----------
outer_bm = bmesh.new()
for _ in range(7):
    a = random.uniform(0, math.tau)
    d = random.uniform(0.0, 0.14)
    add_cone(outer_bm, math.cos(a) * d, math.sin(a) * d, 0.22,
             random.uniform(0.16, 0.28), random.uniform(0.6, 1.05), 6,
             tx=random.uniform(-0.08, 0.08), ty=random.uniform(-0.08, 0.08))
outer_mesh = bpy.data.meshes.new("FlameOuterMesh")
outer_bm.to_mesh(outer_mesh)
outer_bm.free()
outer_mesh.update()
flame_outer = bpy.data.objects.new("FlameOuter", outer_mesh)
collection.objects.link(flame_outer)
outer_mesh.materials.append(mat_flame_outer)

inner_bm = bmesh.new()
for _ in range(5):
    a = random.uniform(0, math.tau)
    d = random.uniform(0.0, 0.08)
    add_cone(inner_bm, math.cos(a) * d, math.sin(a) * d, 0.24,
             random.uniform(0.08, 0.14), random.uniform(0.45, 0.7), 5,
             tx=random.uniform(-0.04, 0.04), ty=random.uniform(-0.04, 0.04))
inner_mesh = bpy.data.meshes.new("FlameInnerMesh")
inner_bm.to_mesh(inner_mesh)
inner_bm.free()
inner_mesh.update()
flame_inner = bpy.data.objects.new("FlameInner", inner_mesh)
collection.objects.link(flame_inner)
inner_mesh.materials.append(mat_flame_inner)

# ---------- Embers ----------
def build_ember(bm):
    bmesh.ops.create_icosphere(bm, subdivisions=1, diameter=0.04)

for i in range(9):
    a = random.uniform(0, math.tau)
    d = random.uniform(0.0, 0.35)
    ember = make_obj(f"Ember{i}", build_ember, mat_ember)
    ember.location = (math.cos(a) * d, math.sin(a) * d, random.uniform(0.3, 1.1))

# ---------- Lighting ----------
fire_data = bpy.data.lights.new("FireLight", 'POINT')
fire_data.energy = 350.0
fire_data.color = (1.0, 0.45, 0.15)
fire_data.shadow_soft_size = 0.35
fire_light = bpy.data.objects.new("FireLight", fire_data)
collection.objects.link(fire_light)
fire_light.location = (0.0, 0.0, 0.55)

glow_data = bpy.data.lights.new("FlameGlow", 'POINT')
glow_data.energy = 90.0
glow_data.color = (1.0, 0.6, 0.25)
glow_data.shadow_soft_size = 0.5
glow = bpy.data.objects.new("FlameGlow", glow_data)
collection.objects.link(glow)
glow.location = (0.0, 0.0, 1.0)

# ---------- World (night sky) ----------
world = bpy.data.worlds.new("NightWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.004, 0.006, 0.02, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam.location = (3.4, -4.6, 2.0)
target = Vector((0.0, 0.0, 0.6))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
