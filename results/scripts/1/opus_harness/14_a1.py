import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- World: gradient sky ----------
world = bpy.data.worlds.new("SunsetSky")
scene.world = world
nt = world.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.05
mr.inputs["From Max"].default_value = 0.6
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.45, 0.08, 1)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.18, 0.05, 0.35, 1)
e = cr.elements.new(0.12)
e.color = (1.0, 0.3, 0.15, 1)
e = cr.elements.new(0.35)
e.color = (0.85, 0.2, 0.4, 1)
e = cr.elements.new(0.65)
e.color = (0.45, 0.1, 0.5, 1)
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------- Sand ----------
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, -10, 0.4))
sand = bpy.context.active_object
sand.name = "Sand"
sand.rotation_euler = (-0.05, 0, 0)
sand_mat = bpy.data.materials.new("Sand")
snt = sand_mat.node_tree
bsdf = snt.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.85, 0.68, 0.45, 1)
bsdf.inputs["Roughness"].default_value = 0.95
noise = snt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 60.0
noise.inputs["Detail"].default_value = 8.0
bump = snt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
snt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
snt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
sand.data.materials.append(sand_mat)

# ---------- Ocean ----------
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 900, 0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
ocean_mat = bpy.data.materials.new("Ocean")
ont = ocean_mat.node_tree
ob = ont.nodes.get("Principled BSDF")
ob.inputs["Base Color"].default_value = (0.02, 0.12, 0.3, 1)
ob.inputs["Roughness"].default_value = 0.12
ob.inputs["Specular IOR Level"].default_value = 0.6
wn = ont.nodes.new("ShaderNodeTexNoise")
wn.inputs["Scale"].default_value = 8.0
wn.inputs["Detail"].default_value = 4.0
wb = ont.nodes.new("ShaderNodeBump")
wb.inputs["Strength"].default_value = 0.08
ont.links.new(wn.outputs["Fac"], wb.inputs["Height"])
ont.links.new(wb.outputs["Normal"], ob.inputs["Normal"])
ocean.data.materials.append(ocean_mat)

# ---------- Sun disc ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=(0, 600, 18))
disc = bpy.context.active_object
disc.name = "SunDisc"
dm = bpy.data.materials.new("SunDisc")
dnt = dm.node_tree
dnt.nodes.clear()
em = dnt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.6, 0.2, 1)
em.inputs["Strength"].default_value = 8.0
mo = dnt.nodes.new("ShaderNodeOutputMaterial")
dnt.links.new(em.outputs["Emission"], mo.inputs["Surface"])
disc.data.materials.append(dm)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.55, 0.3)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(86), 0, math.radians(180))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 32
cam_data.clip_end = 3000
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -28, 3.0)
cam.rotation_euler = (math.radians(86), 0, 0)
scene.camera = cam
