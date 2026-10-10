import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass

# ---------- Planet ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=2.0, location=(0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()
planet.rotation_euler = (math.radians(15), 0, math.radians(30))

pm = bpy.data.materials.new("PlanetMat")
nt = pm.node_tree
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
cr.elements[0].position = 0.0
cr.elements[0].color = (0.01, 0.04, 0.18, 1)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.95, 0.95, 0.97, 1)
for pos, col in [(0.48, (0.03, 0.12, 0.35, 1)), (0.5, (0.75, 0.68, 0.45, 1)),
                 (0.53, (0.12, 0.35, 0.08, 1)), (0.62, (0.25, 0.3, 0.1, 1)),
                 (0.7, (0.35, 0.22, 0.12, 1))]:
    e = cr.elements.new(pos)
    e.color = col
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

rough = nodes.new("ShaderNodeMapRange")
rough.inputs["From Min"].default_value = 0.48
rough.inputs["From Max"].default_value = 0.5
rough.inputs["To Min"].default_value = 0.25
rough.inputs["To Max"].default_value = 0.85
links.new(noise.outputs["Fac"], rough.inputs["Value"])
links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])

bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
planet.data.materials.append(pm)

# ---------- Atmosphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=2.12, location=(0, 0, 0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
bpy.ops.object.shade_smooth()

am = bpy.data.materials.new("AtmosphereMat")
am.use_backface_culling = True
try:
    am.surface_render_method = 'BLENDED'
except Exception:
    pass
ant = am.node_tree
an, al = ant.nodes, ant.links
for n in list(an):
    if n.type != 'OUTPUT_MATERIAL':
        an.remove(n)
out = [n for n in an if n.type == 'OUTPUT_MATERIAL'][0]
lw = an.new("ShaderNodeLayerWeight")
lw.inputs["Blend"].default_value = 0.35
pw = an.new("ShaderNodeMath")
pw.operation = 'POWER'
pw.inputs[1].default_value = 2.0
al.new(lw.outputs["Facing"], pw.inputs[0])
mul = an.new("ShaderNodeMath")
mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = 4.0
al.new(pw.outputs["Value"], mul.inputs[0])
emis = an.new("ShaderNodeEmission")
emis.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
al.new(mul.outputs["Value"], emis.inputs["Strength"])
transp = an.new("ShaderNodeBsdfTransparent")
add = an.new("ShaderNodeAddShader")
al.new(transp.outputs[0], add.inputs[0])
al.new(emis.outputs[0], add.inputs[1])
al.new(add.outputs[0], out.inputs["Surface"])
atmo.data.materials.append(am)

# ---------- World (starfield) ----------
world = bpy.data.worlds.new("Space")
scene.world = world
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn.get("Background")
wnoise = wn.new("ShaderNodeTexNoise")
wnoise.inputs["Scale"].default_value = 400.0
wnoise.inputs["Detail"].default_value = 1.0
wramp = wn.new("ShaderNodeValToRGB")
wramp.color_ramp.elements[0].position = 0.72
wramp.color_ramp.elements[0].color = (0.0, 0.0, 0.003, 1)
wramp.color_ramp.elements[1].position = 0.78
wramp.color_ramp.elements[1].color = (1, 1, 1, 1)
wl.new(wnoise.outputs["Fac"], wramp.inputs["Fac"])
wl.new(wramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# ---------- Light ----------
bpy.ops.object.light_add(type='SUN', location=(5, -3, 3))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(60), math.radians(10), math.radians(60))

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0, -10, 1.8))
cam = bpy.context.active_object
cam.data.lens = 50
d = -cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
