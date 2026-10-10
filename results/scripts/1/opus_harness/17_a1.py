import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("PlanetMat")
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
texco = nodes.new("ShaderNodeTexCoord"); texco.location = (-800, 0)
noise = nodes.new("ShaderNodeTexNoise"); noise.location = (-600, 0)
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.6
links.new(texco.outputs["Object"], noise.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (-300, 100)
cr = ramp.color_ramp
cr.elements[0].position = 0.45; cr.elements[0].color = (0.02, 0.08, 0.3, 1)
cr.elements[1].position = 0.75; cr.elements[1].color = (0.9, 0.9, 0.85, 1)
e = cr.elements.new(0.5); e.color = (0.05, 0.25, 0.5, 1)
e = cr.elements.new(0.52); e.color = (0.6, 0.55, 0.35, 1)
e = cr.elements.new(0.58); e.color = (0.15, 0.4, 0.1, 1)
e = cr.elements.new(0.68); e.color = (0.35, 0.25, 0.15, 1)
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
# Roughness: water shinier
rmap = nodes.new("ShaderNodeMapRange"); rmap.location = (-300, -200)
rmap.inputs["From Min"].default_value = 0.49
rmap.inputs["From Max"].default_value = 0.51
rmap.inputs["To Min"].default_value = 0.25
rmap.inputs["To Max"].default_value = 0.9
links.new(noise.outputs["Fac"], rmap.inputs["Value"])
links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])
bump = nodes.new("ShaderNodeBump"); bump.location = (300, -300)
bump.inputs["Strength"].default_value = 0.3
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
planet.data.materials.append(mat)

# Atmosphere shell
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.06, location=(0, 0, 0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
bpy.ops.object.shade_smooth()
amat = bpy.data.materials.new("AtmoMat")
amat.blend_method = 'BLEND' if hasattr(amat, "blend_method") else None
an = amat.node_tree.nodes; al = amat.node_tree.links
an.clear()
aout = an.new("ShaderNodeOutputMaterial"); aout.location = (600, 0)
lw = an.new("ShaderNodeLayerWeight"); lw.location = (-400, 0)
lw.inputs["Blend"].default_value = 0.35
pw = an.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.location = (-200, 0)
pw.inputs[1].default_value = 2.0
links_ = al
al.new(lw.outputs["Facing"], pw.inputs[0])
emit = an.new("ShaderNodeEmission"); emit.location = (0, -150)
emit.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
emit.inputs["Strength"].default_value = 3.0
transp = an.new("ShaderNodeBsdfTransparent"); transp.location = (0, 100)
mix = an.new("ShaderNodeMixShader"); mix.location = (300, 0)
al.new(pw.outputs[0], mix.inputs["Fac"])
al.new(transp.outputs[0], mix.inputs[1])
al.new(emit.outputs[0], mix.inputs[2])
al.new(mix.outputs[0], aout.inputs["Surface"])
atmo.data.materials.append(amat)

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.002, 0.002, 0.005, 1)
bg.inputs["Strength"].default_value = 1.0

# Sun
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(60), math.radians(10), math.radians(-50))

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -5.5, 1.2)
direction = -cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
