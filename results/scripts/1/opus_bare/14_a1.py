import bpy
import math
import random
from mathutils import Vector

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_sand():
    m = bpy.data.materials.new("Sand")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.76, 0.6, 0.38, 1)
    bsdf.inputs["Roughness"].default_value = 0.95
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 60.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m

def make_ocean():
    m = bpy.data.materials.new("Ocean")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.02, 0.12, 0.3, 1)
    bsdf.inputs["Roughness"].default_value = 0.12
    bsdf.inputs["Metallic"].default_value = 0.1
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8.0
    noise.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m

# ---------- Geometry ----------
# Sand: displaced grid, sloping gently down toward the sea
bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=60, location=(0, -15, 0))
sand = bpy.context.active_object
sand.name = "Sand"
random.seed(3)
for v in sand.data.vertices:
    x, y = v.co.x, v.co.y
    # slope: higher toward -y (land), lower toward +y (sea)
    v.co.z = -0.04 * y + 0.08 * math.sin(x * 0.5) * math.cos(y * 0.4) + random.uniform(-0.02, 0.02)
sand.data.materials.append(make_sand())
for p in sand.data.polygons:
    p.use_smooth = True

# Ocean
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 200 - 15 + 0, 0.3))
ocean = bpy.context.active_object
ocean.name = "Ocean"
ocean.location = (0, 190, 0.3)
ocean.data.materials.append(make_ocean())

# ---------- World sky gradient ----------
world = bpy.data.worlds.new("SunsetSky")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
texco = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.35, 0.05, 1)
cr.elements[1].position = 0.45
cr.elements[1].color = (0.25, 0.05, 0.4, 1)
e = cr.elements.new(0.12)
e.color = (1.0, 0.25, 0.25, 1)
e2 = cr.elements.new(0.25)
e2.color = (0.6, 0.12, 0.45, 1)
nt.links.new(texco.outputs["Generated"], sep.inputs["Vector"])
# Generated z on world: map normalized direction z
mapr = nt.nodes.new("ShaderNodeMapRange")
mapr.inputs["From Min"].default_value = 0.0
mapr.inputs["From Max"].default_value = 1.0
nt.links.new(texco.outputs["Generated"], sep.inputs["Vector"])
sep2 = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(texco.outputs["Normal"], sep2.inputs["Vector"])
nt.links.new(sep2.outputs["Z"], mapr.inputs["Value"])
nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.55, 0.3)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
# Low sun over the sea (light points toward -y, i.e., toward camera)
sun.rotation_euler = (math.radians(-84), 0, 0)

# Visible sun disc near the horizon
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=(0, 380, 14))
disc = bpy.context.active_object
disc.name = "SunDisc"
dm = bpy.data.materials.new("SunDisc")
dm.use_nodes = True
dnt = dm.node_tree
dnt.nodes.clear()
em = dnt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.6, 0.2, 1)
em.inputs["Strength"].default_value = 8.0
dout = dnt.nodes.new("ShaderNodeOutputMaterial")
dnt.links.new(em.outputs["Emission"], dout.inputs["Surface"])
disc.data.materials.append(dm)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 30
cam_data.clip_end = 1000
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -25, 3.0)
direction = Vector((0, 60, 1.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass
