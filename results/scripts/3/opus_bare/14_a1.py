import bpy, math, random, bmesh
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# --- Sand ground ---
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, -20, 0))
sand = bpy.context.active_object
sand.name = "Sand"
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=60)
bpy.ops.object.mode_set(mode='OBJECT')
random.seed(3)
for v in sand.data.vertices:
    wy = v.co.y + sand.location.y
    # slope down toward the ocean (positive y)
    v.co.z = -0.04 * (wy + 10) * 0.5 if wy > -10 else 0.0
    v.co.z += 0.05 * math.sin(v.co.x * 0.8) * math.cos(v.co.y * 0.6) + random.uniform(-0.015, 0.015)
for p in sand.data.polygons:
    p.use_smooth = True

sm = bpy.data.materials.new("SandMat")
sm.use_nodes = True
nt = sm.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.82, 0.66, 0.42, 1)
bsdf.inputs["Roughness"].default_value = 0.95
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 200
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.15
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
sand.data.materials.append(sm)

# --- Ocean ---
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 200, -0.15))
ocean = bpy.context.active_object
ocean.name = "Ocean"
om = bpy.data.materials.new("OceanMat")
om.use_nodes = True
nt = om.node_tree
b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.02, 0.12, 0.3, 1)
b.inputs["Roughness"].default_value = 0.12
b.inputs["Metallic"].default_value = 0.0
wave = nt.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 3
wave.inputs["Distortion"].default_value = 6
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (0.05, 0.6, 1)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
bp = nt.nodes.new("ShaderNodeBump")
bp.inputs["Strength"].default_value = 0.08
nt.links.new(wave.outputs["Fac"], bp.inputs["Height"])
nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
ocean.data.materials.append(om)

# --- World gradient sky ---
world = bpy.data.worlds.new("SunsetSky")
scene.world = world
world.use_nodes = True
wn = world.node_tree
for n in list(wn.nodes):
    wn.nodes.remove(n)
out = wn.nodes.new("ShaderNodeOutputWorld")
bg = wn.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
tcw = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
ramp = wn.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.35, 0.05, 1)
cr.elements[1].position = 0.55
cr.elements[1].color = (0.12, 0.03, 0.3, 1)
e = cr.elements.new(0.15)
e.color = (1.0, 0.25, 0.15, 1)
e = cr.elements.new(0.3)
e.color = (0.6, 0.15, 0.4, 1)
wn.links.new(tcw.outputs["Generated"], sep.inputs["Vector"])
wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
wn.links.new(ramp.outputs["Color"], bg.inputs["Color"])
wn.links.new(bg.outputs["Background"], out.inputs["Surface"])

# --- Sun light (low, warm) ---
bpy.ops.object.light_add(type='SUN', location=(0, 50, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.color = (1.0, 0.55, 0.3)
sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(-84), 0, 0)  # pointing toward camera from horizon

# Visible sun disc
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=(0, 380, 18))
disc = bpy.context.active_object
dm = bpy.data.materials.new("SunDisc")
dm.use_nodes = True
dn = dm.node_tree
for n in list(dn.nodes):
    dn.nodes.remove(n)
em = dn.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.6, 0.2, 1)
em.inputs["Strength"].default_value = 8
mo = dn.nodes.new("ShaderNodeOutputMaterial")
dn.links.new(em.outputs[0], mo.inputs["Surface"])
disc.data.materials.append(dm)
disc.visible_shadow = False

# --- Camera ---
bpy.ops.object.camera_add(location=(0, -18, 1.8))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(87), 0, 0)
cam.data.lens = 30
cam.data.clip_end = 1000
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.view_settings.look = 'AgX - Medium High Contrast' if hasattr(scene.view_settings, 'look') else scene.view_settings.look
scene.frame_start = 1
scene.frame_end = 1
