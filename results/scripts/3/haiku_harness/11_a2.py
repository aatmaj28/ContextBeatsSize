import bpy
import math
from mathutils import Vector

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'  # path tracing for glass refraction
scene.frame_start = 1
scene.frame_end = 1


# ---------- Helpers ----------
def new_material(name):
    mat = bpy.data.materials.new(name)
    # Materials always use nodes in Blender 5.x; the default tree already exists.
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    return mat, tree


def add_object_with_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------- World: Sky Texture background and lighting ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
wtree = world.node_tree
for node in list(wtree.nodes):
    wtree.nodes.remove(node)

sky = wtree.nodes.new("ShaderNodeTexSky")
# Blender 5.2 names the former Nishita model SINGLE_SCATTERING
sky.sky_type = 'SINGLE_SCATTERING'
sky.sun_elevation = math.radians(35.0)
sky.sun_rotation = math.radians(30.0)
sky.location = (-400, 0)

bg = wtree.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
bg.location = (-150, 0)

world_out = wtree.nodes.new("ShaderNodeOutputWorld")
world_out.location = (100, 0)

wtree.links.new(sky.outputs["Color"], bg.inputs["Color"])
wtree.links.new(bg.outputs["Background"], world_out.inputs["Surface"])


# ---------- Materials ----------

# Checkered floor
floor_mat, ft = new_material("CheckerFloor")
tex_coord = ft.nodes.new("ShaderNodeTexCoord")
tex_coord.location = (-700, 0)
checker = ft.nodes.new("ShaderNodeTexChecker")
checker.inputs["Color1"].default_value = (0.8, 0.8, 0.8, 1.0)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
checker.inputs["Scale"].default_value = 8.0
checker.location = (-400, 0)
floor_bsdf = ft.nodes.new("ShaderNodeBsdfPrincipled")
floor_bsdf.inputs["Roughness"].default_value = 0.3
floor_bsdf.location = (-100, 0)
floor_out = ft.nodes.new("ShaderNodeOutputMaterial")
floor_out.location = (200, 0)
ft.links.new(tex_coord.outputs["Generated"], checker.inputs["Vector"])
ft.links.new(checker.outputs["Color"], floor_bsdf.inputs["Base Color"])
ft.links.new(floor_bsdf.outputs["BSDF"], floor_out.inputs["Surface"])

# Glass sphere
glass_mat, gt = new_material("Glass")
glass_bsdf = gt.nodes.new("ShaderNodeBsdfGlass")
glass_bsdf.inputs["Color"].default_value = (0.9, 0.97, 1.0, 1.0)
glass_bsdf.inputs["Roughness"].default_value = 0.02
glass_bsdf.inputs["IOR"].default_value = 1.45
glass_bsdf.location = (-100, 0)
glass_out = gt.nodes.new("ShaderNodeOutputMaterial")
glass_out.location = (200, 0)
gt.links.new(glass_bsdf.outputs["BSDF"], glass_out.inputs["Surface"])

# Gold sphere
gold_mat, ot = new_material("Gold")
gold_bsdf = ot.nodes.new("ShaderNodeBsdfPrincipled")
gold_bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
gold_bsdf.inputs["Metallic"].default_value = 1.0
gold_bsdf.inputs["Roughness"].default_value = 0.22
gold_bsdf.location = (-100, 0)
gold_out = ot.nodes.new("ShaderNodeOutputMaterial")
gold_out.location = (200, 0)
ot.links.new(gold_bsdf.outputs["BSDF"], gold_out.inputs["Surface"])


# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (12, 12, 1)
add_object_with_material(floor, floor_mat)

bpy.ops.mesh.primitive_uv_sphere_add(
    radius=1.0, segments=96, ring_count=48, location=(-1.3, 0, 1.0)
)
glass_ball = bpy.context.active_object
glass_ball.name = "GlassSphere"
bpy.ops.object.shade_smooth()
add_object_with_material(glass_ball, glass_mat)

bpy.ops.mesh.primitive_uv_sphere_add(
    radius=1.0, segments=96, ring_count=48, location=(1.3, 0, 1.0)
)
gold_ball = bpy.context.active_object
gold_ball.name = "GoldSphere"
bpy.ops.object.shade_smooth()
add_object_with_material(gold_ball, gold_mat)


# ---------- Sun light (matches the sky's sun direction) ----------
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.name = "Sun"
sun.rotation_euler = (math.radians(55), 0.0, math.radians(30))
sun.data.energy = 3.0
sun.data.angle = math.radians(2.0)


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0.0, -9.0, 3.2))

target = Vector((0.0, 0.0, 0.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
