import bpy
import bmesh
import math
from mathutils import noise, Vector

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass

# ---------------- World: gradient sky ----------------
world = bpy.data.worlds.new("SunsetSky")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

texco = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
bg = wn.new("ShaderNodeBackground")
out = wn.new("ShaderNodeOutputWorld")

wl.new(texco.outputs["Generated"], sep.inputs[0])
wl.new(sep.outputs["Z"], ramp.inputs["Fac"])
wl.new(ramp.outputs["Color"], bg.inputs["Color"])
wl.new(bg.outputs["Background"], out.inputs["Surface"])

cr = ramp.color_ramp
cr.interpolation = 'EASE'
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.45, 0.08, 1.0)   # orange horizon
cr.elements[1].position = 0.6
cr.elements[1].color = (0.18, 0.05, 0.35, 1.0)  # purple
e = cr.elements.new(0.08)
e.color = (1.0, 0.3, 0.2, 1.0)                  # coral
e = cr.elements.new(0.25)
e.color = (0.7, 0.2, 0.45, 1.0)                 # pink-magenta
e = cr.elements.new(1.0)
e.color = (0.06, 0.02, 0.15, 1.0)               # deep purple
bg.inputs["Strength"].default_value = 1.2

# ---------------- Sand ----------------
mesh = bpy.data.meshes.new("SandMesh")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=120, y_segments=80, size=1.0)
for v in bm.verts:
    x = v.co.x * 40.0
    y = v.co.y * 22.0 - 12.0   # y from -34 to 10
    z = (5.0 - y) * 0.045
    z += noise.noise(Vector((x * 0.15, y * 0.15, 0.0))) * 0.15
    z += noise.noise(Vector((x * 0.8, y * 0.8, 3.0))) * 0.03
    v.co = Vector((x, y, z))
bm.to_mesh(mesh)
bm.free()
for p in mesh.polygons:
    p.use_smooth = True
sand = bpy.data.objects.new("Sand", mesh)
scene.collection.objects.link(sand)

sand_mat = bpy.data.materials.new("SandMat")
sand_mat.use_nodes = True
sn = sand_mat.node_tree.nodes
sl = sand_mat.node_tree.links
sbsdf = sn.get("Principled BSDF")
sbsdf.inputs["Base Color"].default_value = (0.85, 0.68, 0.45, 1.0)
sbsdf.inputs["Roughness"].default_value = 0.95
snoise = sn.new("ShaderNodeTexNoise")
snoise.inputs["Scale"].default_value = 80.0
sbump = sn.new("ShaderNodeBump")
sbump.inputs["Strength"].default_value = 0.3
sl.new(snoise.outputs["Fac"], sbump.inputs["Height"])
sl.new(sbump.outputs["Normal"], sbsdf.inputs["Normal"])
sand.data.materials.append(sand_mat)

# ---------------- Ocean ----------------
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 280, 0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
ocean_mat = bpy.data.materials.new("OceanMat")
ocean_mat.use_nodes = True
on = ocean_mat.node_tree.nodes
ol = ocean_mat.node_tree.links
obsdf = on.get("Principled BSDF")
obsdf.inputs["Base Color"].default_value = (0.02, 0.12, 0.3, 1.0)
obsdf.inputs["Roughness"].default_value = 0.12
obsdf.inputs["Metallic"].default_value = 0.0
onoise = on.new("ShaderNodeTexNoise")
onoise.inputs["Scale"].default_value = 3.0
onoise.inputs["Detail"].default_value = 6.0
omap = on.new("ShaderNodeMapping")
omap.inputs["Scale"].default_value = (1.0, 4.0, 1.0)
otc = on.new("ShaderNodeTexCoord")
ol.new(otc.outputs["Object"], omap.inputs["Vector"])
ol.new(omap.outputs["Vector"], onoise.inputs["Vector"])
obump = on.new("ShaderNodeBump")
obump.inputs["Strength"].default_value = 0.15
ol.new(onoise.outputs["Fac"], obump.inputs["Height"])
ol.new(obump.outputs["Normal"], obsdf.inputs["Normal"])
ocean.data.materials.append(ocean_mat)

# ---------------- Sun disk ----------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=9, location=(0, 400, 10))
disk = bpy.context.active_object
disk.name = "SunDisk"
dmat = bpy.data.materials.new("SunDiskMat")
dmat.use_nodes = True
dn = dmat.node_tree.nodes
dn.clear()
em = dn.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.6, 0.25, 1.0)
em.inputs["Strength"].default_value = 8.0
dout = dn.new("ShaderNodeOutputMaterial")
dmat.node_tree.links.new(em.outputs["Emission"], dout.inputs["Surface"])
disk.data.materials.append(dmat)

# ---------------- Lighting ----------------
sun_data = bpy.data.lights.new("SunLight", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.6, 0.35)
sun_data.angle = math.radians(1.5)
sun = bpy.data.objects.new("SunLight", sun_data)
sun.rotation_euler = (math.radians(84), 0, math.radians(180))
scene.collection.objects.link(sun)

# ---------------- Camera ----------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 28
cam_data.clip_end = 2000
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -30, 3.2)
cam.rotation_euler = (math.radians(86), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
