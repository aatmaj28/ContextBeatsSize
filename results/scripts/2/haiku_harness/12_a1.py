import bpy
import math
from mathutils import Vector

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
              bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'None'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- Dark world ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
wnodes = world.node_tree.nodes
wbg = wnodes.get("Background")
if wbg:
    wbg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
    wbg.inputs["Strength"].default_value = 1.0

# ---------- Materials ----------
def make_principled_material(name, base, roughness=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat, bsdf

# Brick wall (procedural bricks)
wall_mat = bpy.data.materials.new("DarkBrick")
wtree = wall_mat.node_tree
wtree.nodes.clear()
out_w = wtree.nodes.new("ShaderNodeOutputMaterial")
bsdf_w = wtree.nodes.new("ShaderNodeBsdfPrincipled")
brick = wtree.nodes.new("ShaderNodeTexBrick")
brick.inputs["Color1"].default_value = (0.09, 0.035, 0.025, 1.0)
brick.inputs["Color2"].default_value = (0.06, 0.022, 0.016, 1.0)
brick.inputs["Mortar"].default_value = (0.03, 0.03, 0.03, 1.0)
brick.inputs["Scale"].default_value = 6.0
brick.inputs["Mortar Size"].default_value = 0.015
bsdf_w.inputs["Roughness"].default_value = 0.85
wtree.links.new(brick.outputs["Color"], bsdf_w.inputs["Base Color"])
wtree.links.new(bsdf_w.outputs["BSDF"], out_w.inputs["Surface"])

# Pink neon (emissive)
neon_mat, neon_bsdf = make_principled_material("PinkNeon", (1.0, 0.2, 0.6), 0.3)
neon_bsdf.inputs["Emission Color"].default_value = (1.0, 0.1, 0.55, 1.0)
neon_bsdf.inputs["Emission Strength"].default_value = 25.0

# Mounting bracket (dark metal)
metal_mat, _ = make_principled_material("DarkMetal", (0.05, 0.05, 0.06), 0.35)

# ---------- Brick wall ----------
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.rotation_euler = (math.radians(90), 0.0, 0.0)
wall.scale = (10.0, 6.0, 1.0)
wall.data.materials.append(wall_mat)

# ---------- Neon "OPEN" text ----------
bpy.ops.object.text_add(location=(0.0, -0.18, 0.0))
text = bpy.context.active_object
text.name = "NeonOPEN"
text.data.body = "OPEN"
text.data.align_x = 'CENTER'
text.data.align_y = 'CENTER'
text.data.size = 1.0
text.data.extrude = 0.02
text.data.bevel_depth = 0.035
text.data.bevel_resolution = 4
text.data.resolution_u = 4
# Face the camera (-Y side)
text.rotation_euler = (math.radians(90), 0.0, 0.0)
text.scale = (1.0, 1.0, 1.0)
text.data.materials.append(neon_mat)

# Mount plate behind the sign for a realistic installation
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.05, 0.0))
mount = bpy.context.active_object
mount.name = "NeonMount"
mount.scale = (2.6, 0.04, 1.0)
mount.data.materials.append(metal_mat)
mount.hide_render = False

# Center the text in the frame
bpy.context.view_layer.update()
text_dims = text.dimensions
if text_dims.x > 0:
    fit = 3.2 / text_dims.x
    text.scale = (fit, fit, fit)
text.location = (0.0, -0.18, 0.0)
mount.scale = (max(text_dims.x * text.scale.x * 0.5 + 0.35, 1.0), 0.04,
               max(text_dims.z * text.scale.z * 0.5 + 0.35, 0.6)) if False else mount.scale

# Center the mount behind the sign
mount.location = (0.0, -0.05, 0.0)
mount.scale = (2.4, 0.04, 1.1)

# ---------- Lighting ----------
# Soft pink spill from the sign onto the brick
bpy.ops.object.light_add(type='AREA', location=(0.0, -2.2, 0.4))
spill = bpy.context.active_object
spill.name = "PinkSpill"
spill.data.color = (1.0, 0.25, 0.6)
spill.data.energy = 60.0
spill.data.size = 3.0
spill.rotation_euler = (math.radians(90), 0.0, 0.0)

# Faint cool rim light from above-left
bpy.ops.object.light_add(type='AREA', location=(-3.0, -4.0, 3.0))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.color = (0.5, 0.6, 1.0)
rim.data.energy = 15.0
rim.data.size = 2.0
rim.rotation_euler = (math.radians(55), 0.0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SignCamera")
cam_data.lens = 65.0
cam_obj = bpy.data.objects.new("SignCamera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -6.0, 0.2)
target = Vector((0.0, 0.0, 0.0))
direction = target - Vector(cam_obj.location)
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Compositor glow (Glare node) ----------
glow_tree = bpy.data.node_groups.new("NeonGlow", "CompositorNodeTree")
scene.compositing_node_group = glow_tree

rlayers = glow_tree.nodes.new(type="CompositorNodeRLayers")
glare = glow_tree.nodes.new(type="CompositorNodeGlare")
group_out = glow_tree.nodes.new(type="NodeGroupOutput")

def set_input(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
        except Exception:
            pass

set_input(glare, "Type", "Bloom")
set_input(glare, "Quality", "High")
set_input(glare, "Threshold", 0.6)
set_input(glare, "Size", 0.8)
set_input(glare, "Mix", 0.0)

glow_tree.interface.new_socket(name="Image", in_out="OUTPUT",
                               socket_type="NodeSocketColor")
glow_tree.links.new(glare.inputs["Image"], rlayers.outputs["Image"])
glow_tree.links.new(group_out.inputs["Image"], glare.outputs["Image"])
