import bpy
import bmesh
import math
import random
from mathutils import Matrix, Vector

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear default scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

collection = bpy.data.collections.new("Forest")
scene.collection.children.link(collection)


def link(obj):
    collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_principled(name, color, roughness=0.8, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


foliage_mats = [
    make_principled("Foliage_Dark", (0.05, 0.18, 0.07), 0.7),
    make_principled("Foliage_Mid", (0.08, 0.26, 0.10), 0.7),
    make_principled("Foliage_Pale", (0.14, 0.32, 0.16), 0.7),
]
bark_mat = make_principled("Bark", (0.20, 0.13, 0.08), 0.9)
ground_mat = make_principled("Forest_Floor", (0.06, 0.07, 0.05), 0.95)
moss_mat = make_principled("Moss", (0.10, 0.16, 0.07), 0.9)


# ---------------------------------------------------------------
# Ground
# ---------------------------------------------------------------
ground_me = bpy.data.meshes.new("GroundMesh")
gbm = bmesh.new()
half = 120.0
verts = [
    gbm.verts.new((-half, -half, 0.0)),
    gbm.verts.new((half, -half, 0.0)),
    gbm.verts.new((half, half, 0.0)),
    gbm.verts.new((-half, half, 0.0)),
]
gbm.faces.new(verts)
# subdivide for gentle undulation
bmesh.ops.subdivide_edges(gbm, edges=gbm.edges[:], cuts=40)
for v in gbm.verts:
    v.co.z = 0.6 * math.sin(v.co.x * 0.08) * math.cos(v.co.y * 0.07) \
             + random.uniform(-0.05, 0.05)
gbm.to_mesh(ground_me)
gbm.free()
ground_me.materials.append(ground_mat)
ground = link(bpy.data.objects.new("Ground", ground_me))


# ---------------------------------------------------------------
# Trees (stacked cones on a cylinder trunk)
# ---------------------------------------------------------------
def build_tree(name, base, height, radius, mat_foliage):
    bm = bmesh.new()

    trunk_h = height * 0.25
    # trunk: cylinder centered at its midpoint
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=6,
        radius1=radius * 0.12,
        radius2=radius * 0.10,
        depth=trunk_h,
        matrix=Matrix.Translation((0.0, 0.0, trunk_h * 0.5)),
    )

    # stacked foliage cones
    tiers = random.randint(3, 4)
    tier_base = trunk_h * 0.6
    usable = height - tier_base
    for i in range(tiers):
        t = i / float(tiers)
        tier_h = usable * (0.55 - 0.08 * i)
        tier_r = radius * (1.0 - 0.22 * i) * random.uniform(0.92, 1.08)
        z_center = tier_base + usable * t * 0.85 + tier_h * 0.5
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=random.choice([9, 10, 11, 12]),
            radius1=tier_r,
            radius2=0.0,
            depth=tier_h,
            matrix=Matrix.Translation((0.0, 0.0, z_center)),
        )

    # slight random lean and tilt
    lean = Matrix.Rotation(random.uniform(-0.08, 0.08), 4, "X") @ \
           Matrix.Rotation(random.uniform(-0.08, 0.08), 4, "Y")
    bmesh.ops.transform(bm, matrix=lean, verts=bm.verts[:])

    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()

    # shade smooth and assign materials
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(bark_mat)
    me.materials.append(mat_foliage)

    # assign faces: trunk faces get bark (material 0), others foliage (1)
    trunk_face_count = 6 + 2  # side quads + two caps for the 6-seg trunk
    for idx, poly in enumerate(me.polygons):
        poly.material_index = 0 if idx < trunk_face_count else 1

    obj = bpy.data.objects.new(name, me)
    obj.location = base
    obj.rotation_euler = (0.0, 0.0, random.uniform(0, math.tau))
    return link(obj)


tree_positions = []
attempts = 0
while len(tree_positions) < 140 and attempts < 5000:
    attempts += 1
    x = random.uniform(-70, 70)
    y = random.uniform(-70, 70)
    # keep a clearing near the camera path
    if abs(x) < 4.5 and y < -8:
        continue
    # keep a clearing in front of the main subject
    if abs(x) < 3 and y > 4 and y < 40:
        continue
    too_close = False
    for (px, py, pr) in tree_positions:
        if (px - x) ** 2 + (py - y) ** 2 < (pr + 2.0) ** 2:
            too_close = True
            break
    if too_close:
        continue
    height = random.uniform(7.0, 16.0)
    radius = height * random.uniform(0.22, 0.32)
    tree_positions.append((x, y, radius))
    build_tree(
        f"Tree_{len(tree_positions):03d}",
        Vector((x, y, 0.0)),
        height,
        radius,
        random.choice(foliage_mats),
    )

# some low undergrowth cones
for i in range(120):
    x = random.uniform(-45, 45)
    y = random.uniform(-45, 45)
    if abs(x) < 4.5 and y < -6:
        continue
    h = random.uniform(1.2, 3.0)
    build_tree(
        f"Shrub_{i:03d}",
        Vector((x, y, 0.0)),
        h,
        h * 0.55,
        random.choice(foliage_mats),
    )


# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("MistSun", type="SUN")
sun_data.energy = 2.2
sun_data.color = (0.85, 0.92, 1.0)
sun_data.angle = math.radians(6.0)
sun = link(bpy.data.objects.new("MistSun", sun_data))
sun.rotation_euler = (math.radians(55), 0.0, math.radians(35))

# soft fill light from behind the camera
fill_data = bpy.data.lights.new("FillArea", type="AREA")
fill_data.energy = 250.0
fill_data.color = (0.6, 0.75, 0.9)
fill_data.size = 30.0
fill = link(bpy.data.objects.new("FillArea", fill_data))
fill.location = (0.0, -40.0, 25.0)
fill.rotation_euler = (math.radians(60), 0.0, 0.0)


# ---------------------------------------------------------------
# World: volumetric fog
# ---------------------------------------------------------------
world = bpy.data.worlds.new("ForestFogWorld")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
wnt.nodes.clear()

bg_node = wnt.nodes.new("ShaderNodeBackground")
bg_node.inputs["Color"].default_value = (0.42, 0.48, 0.52, 1.0)
bg_node.inputs["Strength"].default_value = 0.35

vol_node = wnt.nodes.new("ShaderNodeVolumeScatter")
vol_node.inputs["Color"].default_value = (0.75, 0.82, 0.88, 1.0)
vol_node.inputs["Density"].default_value = 0.035
vol_node.inputs["Anisotropy"].default_value = 0.35

out_node = wnt.nodes.new("ShaderNodeOutputWorld")
out_node.location = (300, 0)

wnt.links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])
wnt.links.new(vol_node.outputs["Volume"], out_node.inputs["Volume"])

# Eevee volumetric settings (guarded for version differences)
eevee = getattr(scene, "eevee", None)
if eevee is not None:
    if hasattr(eevee, "volumetric_start"):
        eevee.volumetric_start = 0.5
    if hasattr(eevee, "volumetric_end"):
        eevee.volumetric_end = 120.0
    if hasattr(eevee, "volumetric_tile_size"):
        eevee.volumetric_tile_size = "2"
    if hasattr(eevee, "use_volumetric_shadows"):
        eevee.use_volumetric_shadows = True
    if hasattr(eevee, "volumetric_samples"):
        eevee.volumetric_samples = 64


# ---------------------------------------------------------------
# Camera (slow dolly through the fog)
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("ForestCam")
cam_data.lens = 32.0
cam_data.clip_end = 300.0
cam = link(bpy.data.objects.new("ForestCam", cam_data))
scene.camera = cam

target = Vector((0.0, 22.0, 5.0))
start_loc = Vector((-2.0, -30.0, 3.0))
end_loc = Vector((2.0, -12.0, 3.5))


def aim_rotation(loc):
    direction = target - loc
    return direction.to_track_quat("-Z", "Y").to_euler()


scene.frame_start = 1
scene.frame_end = 120

cam.location = start_loc
cam.rotation_euler = aim_rotation(start_loc)
cam.keyframe_insert(data_path="location", frame=1)
cam.keyframe_insert(data_path="rotation_euler", frame=1)

cam.location = end_loc
cam.rotation_euler = aim_rotation(end_loc)
cam.keyframe_insert(data_path="location", frame=120)
cam.keyframe_insert(data_path="rotation_euler", frame=120)

scene.frame_set(1)
