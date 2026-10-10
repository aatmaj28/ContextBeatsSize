import bpy, math

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 64
except Exception:
    pass

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.002, 0.002, 0.005, 1)
bg.inputs["Strength"].default_value = 1.0

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("PlanetSurface")
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
bsdf = nodes.get("Principled BSDF")
texco = nodes.new("ShaderNodeTexCoord")
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.6
links.new(texco.outputs["Object"], noise.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.45
cr.elements[0].color = (0.02, 0.08, 0.3, 1)
cr.elements[1].position = 0.75
cr.elements[1].color = (0.9, 0.9, 0.85, 1)
e = cr.elements.new(0.5); e.color = (0.05, 0.3, 0.08, 1)
e = cr.elements.new(0.6); e.color = (0.45, 0.35, 0.2, 1)
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
# roughness: water shinier
rough = nodes.new("ShaderNodeMapRange")
rough.inputs["From Min"].default_value = 0.45
rough.inputs["From Max"].default_value = 0.5
rough.inputs["To Min"].default_value = 0.25
rough.inputs["To Max"].default_value = 0.85
links.new(noise.outputs["Fac"], rough.inputs["Value"])
links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
planet.data.materials.append(mat)

# Atmosphere shell
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.06, location=(0, 0, 0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
bpy.ops.object.shade_smooth()
amat = bpy.data.materials.new("AtmosphereGlow")
an = amat.node_tree.nodes
al = amat.node_tree.links
for n in list(an):
    an.remove(n)
out = an.new("ShaderNodeOutputMaterial")
lw = an.new("ShaderNodeLayerWeight")
lw.inputs["Blend"].default_value = 0.35
powr = an.new("ShaderNodeMath"); powr.operation = 'POWER'
powr.inputs[1].default_value = 2.0
al.new(lw.outputs["Facing"], powr.inputs[0])
emit = an.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
emit.inputs["Strength"].default_value = 3.0
transp = an.new("ShaderNodeBsdfTransparent")
mix = an.new("ShaderNodeMixShader")
al.new(powr.outputs[0], mix.inputs["Fac"])
al.new(transp.outputs[0], mix.inputs[1])
al.new(emit.outputs[0], mix.inputs[2])
al.new(mix.outputs[0], out.inputs["Surface"])
try:
    amat.surface_render_method = 'BLENDED'
except Exception:
    pass
atmo.data.materials.append(amat)

# Sun light
bpy.ops.object.light_add(type='SUN', location=(5, -3, 3))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(60), math.radians(10), math.radians(60))

# Camera
bpy.ops.object.camera_add(location=(0, -4.6, 0.8))
cam = bpy.context.active_object
cam.data.lens = 50
c = cam.constraints.new('TRACK_TO')
c.target = planet
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
