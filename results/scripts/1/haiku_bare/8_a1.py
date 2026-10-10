import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)

scene = bpy.context.scene

# ---- Clear default scene ----
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


# ---- Materials ----
def make_material(name, color, roughness=0.5, metallic=0.0,
                  emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

mat_red = make_material("Lighthouse_Red", (0.75, 0.05, 0.04), roughness=0.45)
mat_white = make_material("Lighthouse_White", (0.92, 0.92, 0.9), roughness=0.4)
mat_dark = make_material("Iron_Dark", (0.06, 0.06, 0.07), roughness=0.5, metallic=0.6)
mat_glass = make_material("Lamp_Glass", (0.9, 0.95, 1.0), roughness=0.05,
                          emission=(1.0, 0.9, 0.6), emission_strength=25.0)
mat_rock = make_material("Rock", (0.28, 0.26, 0.24), roughness=0.95)
mat_water = make_material("Water", (0.02, 0.12, 0.18), roughness=0.08, metallic=0.0)


# ---- Helpers ----
def make_object(name, bm, mat, smooth=False):
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def frustum(name, r0, r1, z0, z1, mat, segs=40):
    bm = bmesh.new()
    h = z1 - z0
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segs,
        radius1=r0,
        radius2=r1,
        depth=h,
        matrix=Matrix.Translation((0, 0, z0 + h / 2.0)),
    )
    return make_object(name, bm, mat, smooth=True)


# ---- Rocky island ----
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
for v in bm.verts:
    x, y, z = v.co
    f = (1.0
         + 0.18 * math.sin(3.1 * x + 0.7) * math.cos(2.7 * y)
         + 0.12 * math.sin(5.3 * z + 1.1)
         + random.uniform(-0.07, 0.07))
    v.co = Vector((x * f, y * f, z * f))
bmesh.ops.scale(bm, vec=(7.0, 6.0, 1.7), verts=bm.verts)
rock = make_object("Island_Rock", bm, mat_rock, smooth=False)

# Small boulders around the island edge
for i in range(9):
    ang = random.uniform(0, math.tau)
    dist = random.uniform(6.0, 8.0)
    size = random.uniform(0.4, 1.0)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co *= random.uniform(0.8, 1.2)
    bmesh.ops.scale(bm, vec=(size, size, size * 0.6), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(math.cos(ang) * dist, math.sin(ang) * dist, 0.1),
                        verts=bm.verts)
    make_object(f"Boulder_{i}", bm, mat_rock, smooth=False)


# ---- Water ----
bm = bmesh.new()
s = 150.0
v0 = bm.verts.new((-s, -s, 0.0))
v1 = bm.verts.new((s, -s, 0.0))
v2 = bm.verts.new((s, s, 0.0))
v3 = bm.verts.new((-s, s, 0.0))
bm.faces.new((v0, v1, v2, v3))
make_object("Water", bm, mat_water)


# ---- Lighthouse tower (alternating red/white bands) ----
base_z = 1.2
top_z = 15.0
r_base = 2.2
r_top = 1.4

def radius_at(z):
    t = (z - base_z) / (top_z - base_z)
    return r_base + (r_top - r_base) * t

bands = 10
step = (top_z - base_z) / bands
for i in range(bands):
    zb = base_z + i * step
    zt = zb + step
    mat = mat_red if i % 2 == 0 else mat_white
    frustum(f"Tower_Band_{i}", radius_at(zb), radius_at(zt), zb, zt, mat)

# Gallery walkway
frustum("Gallery", 1.75, 1.75, top_z, top_z + 0.3, mat_dark, segs=40)
# Gallery railing ring
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40,
                      radius1=1.85, radius2=1.85, depth=0.9,
                      matrix=Matrix.Translation((0, 0, top_z + 0.75)))
rail_bm = bmesh.new()
# Lamp room (glass)
lamp_z0 = top_z + 0.3
lamp_z1 = lamp_z0 + 1.9
frustum("Lamp_Glass", 1.05, 1.05, lamp_z0, lamp_z1, mat_glass, segs=32)
# Lamp frame top and bottom
frustum("Lamp_Frame_Bottom", 1.15, 1.15, lamp_z0, lamp_z0 + 0.12, mat_dark, segs=32)
frustum("Lamp_Frame_Top", 1.15, 1.15, lamp_z1 - 0.12, lamp_z1, mat_dark, segs=32)

# Roof dome cone
roof_z0 = lamp_z1
roof_z1 = roof_z0 + 1.2
frustum("Roof", 1.35, 0.0, roof_z0, roof_z1, mat_red, segs=32)

# Finial
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.14)
bmesh.ops.translate(bm, vec=(0, 0, roof_z1 + 0.1), verts=bm.verts)
make_object("Finial", bm, mat_dark, smooth=True)

# Ground-level door
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=(0.5, 0.25, 1.1), verts=bm.verts)
bmesh.ops.translate(bm, vec=(0.0, -(radius_at(2.5) + 0.05), 2.5), verts=bm.verts)
make_object("Door", bm, mat_dark)


# ---- Lighting ----
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(3)
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(55), math.radians(-10), math.radians(30))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 400.0
fill_data.size = 12.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = (-20.0, 18.0, 14.0)
fill_obj.rotation_euler = (math.radians(70), 0, math.radians(-130))

# Lamp point light, warm glow from lantern
lamp_light_data = bpy.data.lights.new(name="LampGlow", type='POINT')
lamp_light_data.energy = 800.0
lamp_light_data.color = (1.0, 0.85, 0.55)
lamp_light_data.shadow_soft_size = 0.5
lamp_light = bpy.data.objects.new("LampGlow", lamp_light_data)
bpy.context.collection.objects.link(lamp_light)
lamp_light.location = (0.0, 0.0, lamp_z0 + 0.9)


# ---- World ----
world = bpy.data.worlds.get("World")
if world is None:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 1.0


# ---- Camera ----
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_data.clip_end = 1000.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam_loc = Vector((26.0, -34.0, 11.0))
target = Vector((0.0, 0.0, 8.5))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam


# ---- Timeline ----
scene.frame_start = 1
scene.frame_end = 1
