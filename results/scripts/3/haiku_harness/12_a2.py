import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear default scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
              bpy.data.cameras, bpy.data.lights):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene

# ---------- World (near black) ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Materials ----------
def make_principled_material(name, base, roughness=0.8, metallic=0.0,
                             emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

brick_colors = [(0.22, 0.07, 0.05), (0.18, 0.06, 0.045), (0.26, 0.09, 0.06)]
brick_mats = [make_principled_material(f"Brick_{i}", c, roughness=0.9)
              for i, c in enumerate(brick_colors)]

mortar_mat = make_principled_material("Mortar", (0.05, 0.05, 0.05), roughness=1.0)

neon_mat = make_principled_material(
    "PinkNeon", (1.0, 0.25, 0.65), roughness=0.3,
    emission=(1.0, 0.2, 0.6), emission_strength=30.0)

# ---------- Brick wall (single bmesh object) ----------
BRICK_W, BRICK_H, BRICK_D = 0.5, 0.2, 0.22
GAP = 0.02
ROWS, COLS = 12, 14
WALL_W = COLS * (BRICK_W + GAP)
WALL_H = ROWS * (BRICK_H + GAP)


def add_cube(bm):
    """Create a unit cube and return (new_verts, new_faces) by set difference."""
    before_v = set(bm.verts)
    before_f = set(bm.faces)
    bmesh.ops.create_cube(bm, size=1.0)
    new_verts = [v for v in bm.verts if v not in before_v]
    new_faces = [f for f in bm.faces if f not in before_f]
    return new_verts, new_faces


bm = bmesh.new()
for row in range(ROWS):
    offset = (BRICK_W + GAP) * 0.5 if row % 2 else 0.0
    for col in range(-1, COLS):
        x0 = -WALL_W / 2 + col * (BRICK_W + GAP) + offset
        z0 = row * (BRICK_H + GAP)
        if x0 + BRICK_W < -WALL_W / 2 or x0 > WALL_W / 2:
            continue
        z_c = z0 + BRICK_H / 2
        # Clamp brick ends so the wall edges stay tidy
        x_min = max(x0, -WALL_W / 2)
        x_max = min(x0 + BRICK_W, WALL_W / 2)
        if x_max - x_min <= 0.01:
            continue
        cx, cw = (x_min + x_max) / 2, (x_max - x_min)
        verts, faces = add_cube(bm)
        for v in verts:
            v.co.x = v.co.x * cw + cx
            v.co.y = v.co.y * BRICK_D
            v.co.z = v.co.z * BRICK_H + z_c
        mat_idx = random.randrange(len(brick_mats))
        for f in faces:
            f.material_index = mat_idx

# Mortar backing slab behind the bricks (touches back face of bricks)
back_verts, back_faces = add_cube(bm)
for v in back_verts:
    v.co.x = v.co.x * (WALL_W + 0.4)
    v.co.y = v.co.y * 0.05 + 0.13
    v.co.z = v.co.z * (WALL_H + 0.4) + WALL_H / 2
for f in back_faces:
    f.material_index = len(brick_mats)

wall_mesh = bpy.data.meshes.new("BrickWallMesh")
bm.to_mesh(wall_mesh)
bm.free()
for m in brick_mats + [mortar_mat]:
    wall_mesh.materials.append(m)
wall_obj = bpy.data.objects.new("BrickWall", wall_mesh)
scene.collection.objects.link(wall_obj)

# ---------- Neon "OPEN" text ----------
curve = bpy.data.curves.new("NeonOpenCurve", type='FONT')
curve.body = "OPEN"
curve.size = 0.5
curve.extrude = 0.015
curve.bevel_depth = 0.012
curve.bevel_resolution = 3
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.materials.append(neon_mat)

neon_obj = bpy.data.objects.new("NeonOpen", curve)
scene.collection.objects.link(neon_obj)
# Lie the text upright, facing -Y (toward the camera)
neon_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
neon_obj.location = (0.0, -0.22, WALL_H * 0.62)

# Small mounting bracket plate, sitting against the bricks
plate_mesh = bpy.data.meshes.new("SignPlate")
pbm = bmesh.new()
pverts, _ = add_cube(pbm)
for v in pverts:
    v.co.x *= 1.9
    v.co.y *= 0.03
    v.co.z *= 0.7
pbm.to_mesh(plate_mesh)
pbm.free()
plate_mesh.materials.append(mortar_mat)
plate_obj = bpy.data.objects.new("SignPlate", plate_mesh)
scene.collection.objects.link(plate_obj)
plate_obj.location = (0.0, -0.12, WALL_H * 0.62)

# ---------- Lighting (subtle, so the neon dominates) ----------
key_data = bpy.data.lights.new("FillLight", type='AREA')
key_data.energy = 40.0
key_data.size = 3.0
key_obj = bpy.data.objects.new("FillLight", key_data)
scene.collection.objects.link(key_obj)
key_obj.location = (2.5, -3.5, 2.8)
key_obj.rotation_euler = (math.radians(60), 0.0, math.radians(20))

rim_data = bpy.data.lights.new("RimLight", type='AREA')
rim_data.energy = 15.0
rim_data.size = 2.0
rim_data.color = (0.8, 0.85, 1.0)
rim_obj = bpy.data.objects.new("RimLight", rim_data)
scene.collection.objects.link(rim_obj)
rim_obj.location = (-3.0, -2.0, 3.5)
rim_obj.rotation_euler = (math.radians(45), 0.0, math.radians(-40))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = Vector((0.0, -3.6, WALL_H * 0.6))
target = Vector((0.0, 0.0, WALL_H * 0.6))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Render settings ----------
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1

# ---------- Compositor: Glare glow ----------
comp_tree = bpy.data.node_groups.new("NeonGlowCompositor", "CompositorNodeTree")
scene.compositing_node_group = comp_tree

rlayers = comp_tree.nodes.new(type="CompositorNodeRLayers")
glare = comp_tree.nodes.new(type="CompositorNodeGlare")
group_out = comp_tree.nodes.new(type="NodeGroupOutput")

for socket_name, value in (("Type", "Bloom"), ("Quality", "High")):
    try:
        glare.inputs[socket_name].default_value = value
    except Exception:
        pass
for socket_name, value in (("Threshold", 0.6), ("Size", 8), ("Mix", 0.0)):
    try:
        glare.inputs[socket_name].default_value = value
    except Exception:
        pass

comp_tree.interface.new_socket(name="Image", in_out="OUTPUT",
                               socket_type="NodeSocketColor")
comp_tree.links.new(glare.inputs["Image"], rlayers.outputs["Image"])
comp_tree.links.new(group_out.inputs["Image"], glare.outputs["Image"])
