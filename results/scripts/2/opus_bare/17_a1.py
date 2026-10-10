import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0,0,0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("PlanetMat")
mat.use_nodes = True
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
tc = nodes.new("ShaderNodeTexCoord"); tc.location = (-800, 0)
noise = nodes.new("ShaderNodeTexNoise"); noise.location = (-550, 0)
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.6
links.new(tc.outputs["Object"], noise.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (-250, 100)
cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.01, 0.05, 0.2, 1)
cr.elements[1].position = 0.48; cr.elements[1].color = (0.03, 0.15, 0.4, 1)
e = cr.elements.new(0.5); e.color = (0.6, 0.55, 0.35, 1)
e = cr.elements.new(0.56); e.color = (0.1, 0.3, 0.08, 1)
e = cr.elements.new(0.68); e.color = (0.35, 0.25, 0.15, 1)
e = cr.elements.new(0.78); e.color = (0.95, 0.95, 0.97, 1)
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
# roughness: water shiny
rr = nodes.new("ShaderNodeMapRange"); rr.location = (-250, -200)
rr.inputs["From Min"].default_value = 0.49
rr.inputs["From Max"].default_value = 0.51
rr.inputs["To Min"].default_value = 0.2
rr.inputs["To Max"].default_value = 0.85
links.new(noise.outputs["Fac"], rr.inputs["Value"])
links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
bump = nodes.new("ShaderNodeBump"); bump.location = (300, -300)
bump.inputs["Strength"].default_value = 0.3
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
planet.data.materials.append(mat)

# Atmosphere
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.06)
atm = bpy.context.active_object
atm.name = "Atmosphere"
bpy.ops.object.shade_smooth()
am = bpy.data.materials.new("AtmosphereMat")
am.use_nodes = True
am.blend_method = 'BLEND' if hasattr(am, "blend_method") else None
try:
    am.surface_render_method = 'BLENDED'
except Exception:
    pass
nt = am.node_tree; n = nt.nodes; l = nt.links
n.clear()
o = n.new("ShaderNodeOutputMaterial"); o.location = (600, 0)
lw = n.new("ShaderNodeLayerWeight"); lw.location = (-400, 0)
lw.inputs["Blend"].default_value = 0.35
pw = n.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.location = (-200, 0)
pw.inputs[1].default_value = 2.0
l.new(lw.outputs["Facing"], pw.inputs[0])
em = n.new("ShaderNodeEmission"); em.location = (100, 100)
em.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
em.inputs["Strength"].default_value = 3.0
tr = n.new("ShaderNodeBsdfTransparent"); tr.location = (100, -100)
mix = n.new("ShaderNodeMixShader"); mix.location = (350, 0)
l.new(pw.outputs[0], mix.inputs["Fac"])
l.new(tr.outputs[0], mix.inputs[1])
l.new(em.outputs[0], mix.inputs[2])
l.new(mix.outputs[0], o.inputs["Surface"])
atm.data.materials.append(am)
atm.visible_shadow = False

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.002, 0.002, 0.005, 1)
bg.inputs["Strength"].default_value = 1.0

# Sun
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(60), math.radians(10), math.radians(-50))

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -5.5, 0.6)
direction = -cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# Slow rotation
scene.frame_start = 1
scene.frame_end = 120
planet.rotation_euler = (math.radians(15), 0, 0)
planet.keyframe_insert("rotation_euler", frame=1)
planet.rotation_euler = (math.radians(15), 0, math.radians(30))
planet.keyframe_insert("rotation_euler", frame=120)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
