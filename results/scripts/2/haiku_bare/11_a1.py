import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default objects so the scene starts empty
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.render.engine = 'CYCLES'


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


# ---------- World: Sky Texture for background and lighting ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

sky = wnodes.new("ShaderNodeTexSky")
sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(25.0)
sky.sun_rotation = math.radians(30.0)
sky.sun_intensity = 1.0

bg = wnodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0

world_out = wnodes.new("ShaderNodeOutputWorld")

wlinks.new(sky.outputs["Color"], bg.inputs["Color"])
wlinks.new(bg.outputs["Background"], world_out.inputs["Surface"])


# ---------- Materials ----------
def new_principled_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat, mat.node_tree.nodes, mat.node_tree.links


# Checkered floor
floor_mat, fnodes, flinks = new_principled_material("CheckerFloor")
fbsdf = fnodes.get("Principled BSDF")
checker = fnodes.new("ShaderNodeTexChecker")
checker.inputs["Color1"].default_value = (0.8, 0.8, 0.8, 1.0)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
checker.inputs["Scale"].default_value = 8.0
texcoord = fnodes.new("ShaderNodeTexCoord")
flinks.new(texcoord.outputs["Generated"], checker.inputs["Vector"])
flinks.new(checker.outputs["Color"], fbsdf.inputs["Base Color"])
set_input(fbsdf, "Roughness", 0.35)

# Glass sphere
glass_mat, gnodes, glinks = new_principled_material("Glass")
gbsdf = gnodes.get("Principled BSDF")
set_input(gbsdf, "Base Color", (0.9, 0.97, 1.0, 1.0))
set_input(gbsdf, "Roughness", 0.0)
set_input(gbsdf, "IOR", 1.45)
set_input(gbsdf, "Transmission Weight", 1.0)

# Gold sphere
gold_mat, gonodes, golinks = new_principled_material("Gold")
obsdf = gonodes.get("Principled BSDF")
set_input(obsdf, "Base Color", (1.0, 0.766, 0.336, 1.0))
set_input(obsdf, "Metallic", 1.0)
set_input(obsdf, "Roughness", 0.2)


# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0.0, 0.0, 0.0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

sphere_radius = 1.0

bpy.ops.mesh.primitive_uv_sphere_add(
    radius=sphere_radius, segments=64, ring_count=32,
    location=(-1.3, 0.0, sphere_radius))
glass_ball = bpy.context.active_object
glass_ball.name = "GlassSphere"
bpy.ops.object.shade_smooth()
glass_ball.data.materials.append(glass_mat)

bpy.ops.mesh.primitive_uv_sphere_add(
    radius=sphere_radius, segments=64, ring_count=32,
    location=(1.3, 0.0, sphere_radius))
gold_ball = bpy.context.active_object
gold_ball.name = "GoldSphere"
bpy.ops.object.shade_smooth()
gold_ball.data.materials.append(gold_mat)


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

cam_location = Vector((6.5, -7.5, 4.0))
target = Vector((0.0, 0.0, 1.0))
cam_obj.location = cam_location
direction = target - cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj


# ---------- Render settings (no rendering performed) ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
