import bpy
import math
import mathutils

# ---------------------------------------------------------------
# Clean scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = bpy.context.collection

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def new_principled(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def new_emission(name, color, strength):
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat

class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []

    def add_box(self, x0, x1, y0, y1, z0, z1):
        base = len(self.verts)
        self.verts += [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        b = base
        self.faces += [
            (b + 0, b + 3, b + 2, b + 1),  # bottom
            (b + 4, b + 5, b + 6, b + 7),  # top
            (b + 0, b + 1, b + 5, b + 4),  # front
            (b + 2, b + 3, b + 7, b + 6),  # back
            (b + 0, b + 4, b + 7, b + 3),  # left
            (b + 1, b + 2, b + 6, b + 5),  # right
        ]

    def to_object(self, name, material):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        me.materials.append(material)
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        return obj

# ---------------------------------------------------------------
# Corridor dimensions
# ---------------------------------------------------------------
W = 2.0        # half width
H = 3.5        # height
Y0 = -15.0     # start
Y1 = 15.0      # end
T = 0.2        # wall thickness

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
mat_floor = new_principled("Floor_Metal", (0.04, 0.045, 0.05, 1), roughness=0.25, metallic=0.7)
mat_wall = new_principled("Wall_Panel", (0.12, 0.14, 0.17, 1), roughness=0.55, metallic=0.4)
mat_ceiling = new_principled("Ceiling_Dark", (0.03, 0.03, 0.035, 1), roughness=0.7, metallic=0.2)
mat_rib = new_principled("Rib_Metal", (0.08, 0.08, 0.09, 1), roughness=0.35, metallic=0.9)

mat_cyan = new_emission("Strip_Cyan", (0.1, 0.9, 1.0, 1), 18.0)
mat_magenta = new_emission("Strip_Magenta", (1.0, 0.1, 0.7, 1), 14.0)
mat_door = new_emission("EndDoor", (0.3, 0.8, 1.0, 1), 6.0)

# ---------------------------------------------------------------
# Corridor structure
# ---------------------------------------------------------------
structure = MeshBuilder()
structure.add_box(-W - T, -W, Y0, Y1, 0, H)      # left wall
structure.add_box(W, W + T, Y0, Y1, 0, H)        # right wall
structure.add_box(-W, W, Y0, Y1, -T, 0)         # floor
structure.add_box(-W, W, Y0, Y1, H, H + T)       # ceiling
structure.add_box(-W, W, Y1, Y1 + T, 0, H)       # end wall
corridor = structure.to_object("Corridor_Structure", mat_wall)

# Floor and ceiling as separate materials
floor_b = MeshBuilder()
floor_b.add_box(-W, W, Y0, Y1, -0.01, 0.0)
floor_obj = floor_b.to_object("Floor", mat_floor)

ceil_b = MeshBuilder()
ceil_b.add_box(-W, W, Y0, Y1, H - 0.01, H)
ceil_obj = ceil_b.to_object("Ceiling", mat_ceiling)

# Wall ribs (vertical panel seams)
ribs = MeshBuilder()
y = Y0 + 2.5
while y < Y1 - 1:
    ribs.add_box(-W, -W + 0.12, y, y + 0.25, 0, H)
    ribs.add_box(W - 0.12, W, y, y + 0.25, 0, H)
    y += 5.0
ribs.to_object("Wall_Ribs", mat_rib)

# ---------------------------------------------------------------
# Glowing light strips
# ---------------------------------------------------------------
strips_cyan = MeshBuilder()
strips_magenta = MeshBuilder()

# Upper wall strips (cyan left, magenta right)
strips_cyan.add_box(-W + 0.02, -W + 0.06, Y0, Y1, 3.0, 3.1)
strips_magenta.add_box(W - 0.06, W - 0.02, Y0, Y1, 3.0, 3.1)

# Lower wall strips
strips_cyan.add_box(-W + 0.02, -W + 0.06, Y0, Y1, 0.4, 0.5)
strips_magenta.add_box(W - 0.06, W - 0.02, Y0, Y1, 0.4, 0.5)

# Floor edge strips
strips_cyan.add_box(-1.8, -1.7, Y0, Y1, 0.0, 0.02)
strips_magenta.add_box(1.7, 1.8, Y0, Y1, 0.0, 0.02)

# Ceiling center strip
strips_cyan.add_box(-0.3, 0.3, Y0, Y1, H - 0.04, H - 0.03)

strips_cyan.to_object("Light_Strips_Cyan", mat_cyan)
strips_magenta.to_object("Light_Strips_Magenta", mat_magenta)

# Glowing door panel at the far end
door = MeshBuilder()
door.add_box(-1.0, 1.0, Y1 - 0.03, Y1 - 0.01, 0.2, 2.8)
door.to_object("End_Door_Glow", mat_door)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
for i, yy in enumerate(range(-12, 13, 6)):
    light_data = bpy.data.lights.new(name=f"Corridor_Light_{i}", type='POINT')
    light_data.energy = 150.0
    light_data.color = (0.45, 0.85, 1.0)
    light_data.shadow_soft_size = 0.3
    light_obj = bpy.data.objects.new(f"Corridor_Light_{i}", light_data)
    light_obj.location = (0.0, yy, 3.0)
    collection.objects.link(light_obj)

# Warm accent light near the far door
accent_data = bpy.data.lights.new(name="Door_Accent", type='POINT')
accent_data.energy = 200.0
accent_data.color = (1.0, 0.3, 0.8)
accent_obj = bpy.data.objects.new("Door_Accent", accent_data)
accent_obj.location = (0.0, 12.0, 1.5)
collection.objects.link(accent_obj)

# ---------------------------------------------------------------
# World
# ---------------------------------------------------------------
world = bpy.data.worlds.new("SciFi_World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is None:
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.01, 0.015, 0.03, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Corridor_Cam")
cam_data.lens = 24.0
cam_data.clip_end = 200.0
cam_obj = bpy.data.objects.new("Corridor_Cam", cam_data)
collection.objects.link(cam_obj)

cam_loc = mathutils.Vector((0.0, -13.5, 1.7))
target = mathutils.Vector((0.0, 6.0, 1.6))
cam_obj.location = cam_loc
direction = (target - cam_loc).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------------------------------------------------------------
# Render settings (no rendering performed)
# ---------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
except Exception:
    pass

scene.frame_start = 1
scene.frame_end = 1

# ---------------------------------------------------------------
# Compositor: vignette
# ---------------------------------------------------------------
ctree = bpy.data.node_groups.new("Corridor_Vignette", "CompositorNodeTree")
ctree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
scene.compositing_node_group = ctree

rlayers = ctree.nodes.new("CompositorNodeRLayers")

ellipse = ctree.nodes.new("CompositorNodeEllipseMask")
for name, value in (("Width", 0.6), ("Height", 0.6)):
    if name in ellipse.inputs:
        ellipse.inputs[name].default_value = value

blur = ctree.nodes.new("CompositorNodeBlur")
if "Size" in blur.inputs:
    blur.inputs["Size"].default_value = (80.0, 80.0)

mix = ctree.nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs["Factor"].default_value = 0.85

color_a = [s for s in mix.inputs if s.type == 'RGBA' and s.name == 'A'][0]
color_b = [s for s in mix.inputs if s.type == 'RGBA' and s.name == 'B'][0]
color_out = [s for s in mix.outputs if s.type == 'RGBA'][0]

group_out = ctree.nodes.new("NodeGroupOutput")

ctree.links.new(rlayers.outputs["Image"], color_a)
ctree.links.new(ellipse.outputs["Mask"], blur.inputs["Image"])
ctree.links.new(blur.outputs["Image"], color_b)
ctree.links.new(color_out, group_out.inputs["Image"])

print("Sci-fi corridor scene built.")
