import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render engine (try EEVEE, fallback to Cycles)
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass

# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
bg = wn.get("Background")
if bg is None:
    bg = wn.new("ShaderNodeBackground")
    out = wn.new("ShaderNodeOutputWorld")
    wl.new(bg.outputs[0], out.inputs[0])
bg.inputs["Color"].default_value = (0.002, 0.003, 0.008, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Planet ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
for p in planet.data.polygons:
    p.use_smooth = True

pm = bpy.data.materials.new("PlanetMat")
pm.use_nodes = True
nt = pm.node_tree
n = nt.nodes
l = nt.links
n.clear()
out = n.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
bsdf = n.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
texco = n.new("ShaderNodeTexCoord"); texco.location = (-800, 0)
noise = n.new("ShaderNodeTexNoise"); noise.location = (-550, 0)
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.6
ramp = n.new("ShaderNodeValToRGB"); ramp.location = (-250, 150)
cr = ramp.color_ramp
cr.elements[0].position = 0.40
cr.elements[0].color = (0.02, 0.08, 0.30, 1)   # deep ocean
cr.elements[1].position = 0.70
cr.elements[1].color = (0.85, 0.85, 0.80, 1)   # snowy peaks
e = cr.elements.new(0.48); e.color = (0.05, 0.25, 0.45, 1)  # shallow
e = cr.elements.new(0.50); e.color = (0.55, 0.50, 0.30, 1)  # beach
e = cr.elements.new(0.54); e.color = (0.12, 0.35, 0.10, 1)  # forest
e = cr.elements.new(0.62); e.color = (0.35, 0.25, 0.15, 1)  # mountains
rough_ramp = n.new("ShaderNodeValToRGB"); rough_ramp.location = (-250, -150)
rough_ramp.color_ramp.elements[0].position = 0.48
rough_ramp.color_ramp.elements[0].color = (0.15, 0.15, 0.15, 1)
rough_ramp.color_ramp.elements[1].position = 0.50
rough_ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)
bump = n.new("ShaderNodeBump"); bump.location = (250, -250)
bump.inputs["Strength"].default_value = 0.3
l.new(texco.outputs["Object"], noise.inputs["Vector"])
l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
l.new(noise.outputs["Fac"], rough_ramp.inputs["Fac"])
l.new(noise.outputs["Fac"], bump.inputs["Height"])
l.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
l.new(rough_ramp.outputs["Color"], bsdf.inputs["Roughness"])
l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
planet.data.materials.append(pm)

# ---------- Atmosphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.06, location=(0, 0, 0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
for p in atmo.data.polygons:
    p.use_smooth = True

am = bpy.data.materials.new("AtmosphereMat")
am.use_nodes = True
for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
    try:
        setattr(am, attr, val)
    except Exception:
        pass
try:
    am.use_backface_culling = True
except Exception:
    pass
an = am.node_tree.nodes
al = am.node_tree.links
an.clear()
aout = an.new("ShaderNodeOutputMaterial"); aout.location = (700, 0)
lw = an.new("ShaderNodeLayerWeight"); lw.location = (-400, 0)
lw.inputs["Blend"].default_value = 0.35
aramp = an.new("ShaderNodeValToRGB"); aramp.location = (-150, 0)
aramp.color_ramp.elements[0].position = 0.0
aramp.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
aramp.color_ramp.elements[1].position = 0.9
aramp.color_ramp.elements[1].color = (1, 1, 1, 1)
emis = an.new("ShaderNodeEmission"); emis.location = (200, -150)
emis.inputs["Color"].default_value = (0.3, 0.6, 1.0, 1)
emis.inputs["Strength"].default_value = 3.0
transp = an.new("ShaderNodeBsdfTransparent"); transp.location = (200, 100)
mix = an.new("ShaderNodeMixShader"); mix.location = (450, 0)
al.new(lw.outputs["Facing"], aramp.inputs["Fac"])
al.new(aramp.outputs["Color"], mix.inputs["Fac"])
al.new(transp.outputs[0], mix.inputs[1])
al.new(emis.outputs[0], mix.inputs[2])
al.new(mix.outputs[0], aout.inputs["Surface"])
atmo.data.materials.append(am)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(60), math.radians(10), math.radians(-50))

fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 0.15
fill_data.color = (0.4, 0.5, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.rotation_euler = (math.radians(-60), 0, math.radians(130))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -5.2, 1.0)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

# Slow rotation animation
scene.frame_start = 1
scene.frame_end = 240
planet.rotation_euler = (0, 0, 0)
planet.keyframe_insert(data_path="rotation_euler", frame=1)
planet.rotation_euler = (0, 0, math.radians(90))
planet.keyframe_insert(data_path="rotation_euler", frame=240)
try:
    for fc in planet.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except Exception:
    pass
