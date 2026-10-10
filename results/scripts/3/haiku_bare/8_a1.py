import bpy
import bmesh
import math
import random
import mathutils
from mathutils import Vector

random.seed(7)

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0,
                  emission_color=None, emission_strength=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if transmission > 0.0:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def link(obj):
    collection.objects.link(obj)
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------- Materials ----------
mat_red = make_material("StripeRed", (0.75, 0.05, 0.03), roughness=0.55)
mat_white = make_material("StripeWhite", (0.92, 0.92, 0.9), roughness=0.45)
mat_gallery = make_material("GalleryMetal", (0.08, 0.08, 0.09), roughness=0.35, metallic=0.9)
mat_glass = make_material("LanternGlass", (0.9, 0.95, 1.0), roughness=0.05,
                          emission_color=(1.0, 0.85, 0.5), emission_strength=25.0)
mat_roof = make_material("LanternRoof", (0.12, 0.2, 0.15), roughness=0.5, metallic=0.4)
mat_rock = make_material("Rock", (0.32, 0.30, 0.27), roughness=0.95)
mat_grass = make_material("Scrub", (0.18, 0.24, 0.12), roughness=0.9)
mat_water = make_material("Water", (0.02, 0.12, 0.16), roughness=0.08)

# ---------- Island ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
for v in bm.verts:
    co = v.co.copy()
    n = 1.0 + 0.16 * mathutils.noise.noise(co * 1.3)
    co *= n
    if co.z > 0.55:
    # flatten the top into a plateau
        co.z = 0.55 + (co.z - 0.55) * 0.25
    co.x *= 14.0
    co.y *= 14.0
    co.z *= 4.0
    v.co = co
bm.normal_update()
me_island = bpy.data.meshes.new("IslandMesh")
bm.to_mesh(me_island)
bm.free()
island = link(bpy.data.objects.new("Island", me_island))
assign(island, mat_rock)
smooth(island)

# Grass/scrub patch on the plateau
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * 9.0, v.co.y * 9.0, v.co.z * 0.25))
    v.co.z += 0.2 * mathutils.noise.noise(v.co * 0.4)
bm.normal_update()
me_scrub = bpy.data.meshes.new("ScrubMesh")
bm.to_mesh(me_scrub)
bm.free()
scrub = link(bpy.data.objects.new("Scrub", me_scrub))
scrub.location = (0.0, 0.0, 2.1)
assign(scrub, mat_grass)
smooth(scrub)

# Scattered boulders on the island
for i in range(14):
    ang = random.uniform(0, math.tau)
    dist = random.uniform(4.5, 11.0)
    x = math.cos(ang) * dist
    y = math.sin(ang) * dist
    s = random.uniform(0.4, 1.3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s, location=(x, y, 2.0))
    rock = bpy.context.active_object
    rock.scale = (1.0, 1.0, random.uniform(0.5, 0.8))
    rock.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    rock.location.z = 2.0 + s * 0.2
    assign(rock, mat_rock)
    smooth(rock)
    collection.objects.link(rock)
    if rock.name in bpy.context.scene.collection.objects and rock.users_collection[0] != collection:
        pass

# ---------- Tower ----------
TOWER_BASE_Z = 1.8
TOWER_SEGMENTS = 12
SEG_H = 1.4
R_BASE = 1.6
R_TOP = 1.0
tower_parts = []

for i in range(TOWER_SEGMENTS):
    t0 = i / TOWER_SEGMENTS
    t1 = (i + 1) / TOWER_SEGMENTS
    r0 = R_BASE + (R_TOP - R_BASE) * t0
    r1 = R_BASE + (R_TOP - R_BASE) * t1
    z0 = TOWER_BASE_Z + i * SEG_H
    bpy.ops.mesh.primitive_cone_add(
        vertices=40,
        radius1=r0,
        radius2=r1,
        depth=SEG_H,
        location=(0.0, 0.0, z0 + SEG_H * 0.5),
    )
    seg = bpy.context.active_object
    seg.name = f"TowerSeg_{i:02d}"
    assign(seg, mat_red if i % 2 == 0 else mat_white)
    smooth(seg)
    tower_parts.append(seg)

tower_top_z = TOWER_BASE_Z + TOWER_SEGMENTS * SEG_H

# Gallery walkway
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1.45, depth=0.25,
                                    location=(0.0, 0.0, tower_top_z + 0.125))
gallery = bpy.context.active_object
gallery.name = "Gallery"
assign(gallery, mat_gallery)
smooth(gallery)

# Railing ring
bpy.ops.mesh.primitive_torus_add(major_radius=1.38, minor_radius=0.03,
                                 major_segments=40, minor_segments=8,
                                 location=(0.0, 0.0, tower_top_z + 0.85))
rail = bpy.context.active_object
rail.name = "Railing"
assign(rail, mat_gallery)
smooth(rail)

# Lantern room (glass)
LANTERN_H = 1.8
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.85, depth=LANTERN_H,
                                    location=(0.0, 0.0, tower_top_z + 0.25 + LANTERN_H * 0.5))
lantern = bpy.context.active_object
lantern.name = "LanternGlass"
assign(lantern, mat_glass)
smooth(lantern)

# Lantern frame posts
for k in range(8):
    a = k * math.tau / 8
    bpy.ops.mesh.primitive_cube_add(size=1.0,
        location=(math.cos(a) * 0.87, math.sin(a) * 0.87,
                  tower_top_z + 0.25 + LANTERN_H * 0.5))
    post = bpy.context.active_object
    post.scale = (0.05, 0.05, LANTERN_H * 0.5)
    assign(post, mat_gallery)

# Roof
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.05, radius2=0.0, depth=1.0,
                                location=(0.0, 0.0, tower_top_z + 0.25 + LANTERN_H + 0.5))
roof = bpy.context.active_object
roof.name = "LanternRoof"
assign(roof, mat_roof)
smooth(roof)

# Finial
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=12, ring_count=8,
                                     location=(0.0, 0.0, tower_top_z + 0.25 + LANTERN_H + 1.05))
finial = bpy.context.active_object
assign(finial, mat_gallery)

# Small keeper's cottage beside the tower
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.5, 3.0, 2.0 + 1.1))
cottage = bpy.context.active_object
cottage.name = "Cottage"
cottage.scale = (2.6, 2.0, 1.1)
assign(cottage, mat_white)

bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.3, radius2=0.0, depth=1.1,
                                location=(-4.5, 3.0, 2.0 + 2.2 + 0.55))
cottage_roof = bpy.context.active_object
cottage_roof.rotation_euler = (0.0, 0.0, math.radians(45))
assign(cottage_roof, mat_roof)

# ---------- Water ----------
bpy.ops.mesh.primitive_plane_add(size=400.0, location=(0.0, 0.0, -0.2))
water = bpy.context.active_object
water.name = "Water"
assign(water, mat_water)

# ---------- World ----------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
wbg = world.node_tree.nodes.get("Background")
if wbg is None:
    wbg = world.node_tree.nodes.new("ShaderNodeBackground")
wbg.inputs["Color"].default_value = (0.42, 0.58, 0.78, 1.0)
wbg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
bpy.ops.object.light_add(type='SUN', location=(0.0, 0.0, 40.0))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 4.5
sun.data.angle = math.radians(3.0)
sun.data.color = (1.0, 0.96, 0.9)
sun.rotation_euler = (math.radians(55.0), math.radians(10.0), math.radians(35.0))

bpy.ops.object.light_add(type='AREA', location=(-30.0, 30.0, 25.0))
fill = bpy.context.active_object
fill.name = "SkyFill"
fill.data.energy = 600.0
fill.data.size = 30.0
fill.data.color = (0.75, 0.85, 1.0)
fill.rotation_euler = (math.radians(60.0), 0.0, math.radians(-135.0))

# Warm point light at the lantern to suggest it's lit
bpy.ops.object.light_add(type='POINT', location=(0.0, 0.0, tower_top_z + 1.2))
lamp = bpy.context.active_object
lamp.name = "LanternLight"
lamp.data.energy = 800.0
lamp.data.color = (1.0, 0.82, 0.5)
lamp.data.shadow_soft_size = 0.5

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_data.clip_end = 1000.0
camera = link(bpy.data.objects.new("Camera", cam_data))
camera.location = Vector((34.0, -40.0, 15.0))

target = Vector((0.0, 0.0, 10.5))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = camera

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 1
