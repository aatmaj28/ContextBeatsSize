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
texco = nodes.new("ShaderNodeTexCoord"); texco.location = (-800, 0)
noise = nodes.new("ShaderNodeTexNoise"); noise.location = (-550, 0)
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.6
ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (-250, 100)
cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.02, 0.06, 0.25, 1)
cr.elements[1].position = 1.0; cr.elements[1].color = (0.9, 0.9, 0.92, 1)
e = cr.elements.new(0.48); e.color = (0.05, 0.2, 0.5, 1)
e = cr.elements.new(0.52); e.color = (0.75, 0.65, 0.4, 1)
e = cr.elements.new(0.58); e.color = (0.15, 0.4, 0.1, 1)
e = cr.elements.new(0.7); e.color = (0.35, 0.25, 0.15, 1)
rough = nodes.new("ShaderNodeMapRange"); rough.location = (-250, -200)
rough.inputs["From Min"].default_value = 0.48
rough.inputs["From Max"].default_value = 0.52
rough.inputs["To Min"].default_value = 0.2
rough.inputs["To Max"].default_value = 0.85
bump = nodes.new("ShaderNodeBump"); bump.location = (300, -300)
bump.inputs["Strength"].default_value = 0.25
links.new(texco.outputs["Object"], noise.inputs["Vector"])
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(noise.outputs["Fac"], rough.inputs["Value"])
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
planet.data.materials.append(mat)

# Atmosphere
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.06, location=(0,0,0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
bpy.ops.object.shade_smooth()
am = bpy.data.materials.new("AtmoMat")
am.use_nodes = True
try:
    am.blend_method = 'BLEND'
except Exception:
    pass
try:
    am.surface_render_method = 'BLENDED'
except Exception:
    pass
an = am.node_tree.nodes; al = am.node_tree.links
an.clear()
aout = an.new("ShaderNodeOutputMaterial"); aout.location = (800, 0)
lw = an.new("ShaderNodeLayerWeight"); lw.location = (-400, 0)
lw.inputs["Blend"].default_value = 0.35
pw = an.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.location = (-200, 0)
pw.inputs[1].default_value = 2.0
em = an.new("ShaderNodeEmission"); em.location = (100, 100)
em.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
em.inputs["Strength"].default_value = 3.0
tr = an.new("ShaderNodeBsdfTransparent"); tr.location = (100, -100)
mix = an.new("ShaderNodeMixShader"); mix.location = (500, 0)
al.new(lw.outputs["Facing"], pw.inputs[0])
al.new(pw.outputs["Value"], mix.inputs["Fac"])
al.new(tr.outputs["BSDF"], mix.inputs[1])
al.new(em.outputs["Emission"], mix.inputs[2])
al.new(mix.outputs["Shader"], aout.inputs["Surface"])
atmo.data.materials.append(am)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -3, 3))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(60), math.radians(20), math.radians(50))

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.002, 0.002, 0.005, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(0, -4.5, 0.8))
cam = bpy.context.active_object
cam.data.lens = 50
d = -cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# Slow rotation animation
scene.frame_start = 1
scene.frame_end = 120
planet.rotation_euler = (0, 0, 0)
planet.keyframe_insert("rotation_euler", frame=1)
planet.rotation_euler = (0, 0, math.radians(45))
planet.keyframe_insert("rotation_euler", frame=120)
