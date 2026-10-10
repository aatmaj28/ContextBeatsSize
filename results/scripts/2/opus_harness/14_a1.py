import bpy, math, random
from mathutils import Vector, noise

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

random.seed(3)

# ---------- Sand ----------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=60, location=(0, -10, 0))
sand = bpy.context.active_object
sand.name = "Sand"
for v in sand.data.vertices:
    wx = v.co.x + sand.location.x
    wy = v.co.y + sand.location.y
    n = noise.noise(Vector((wx * 0.15, wy * 0.15, 0.0))) * 0.15
    v.co.z = -0.05 * wy - 0.08 + n
bpy.ops.object.shade_smooth()

sand_mat = bpy.data.materials.new("SandMat")
nt = sand_mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.82, 0.66, 0.45, 1)
bsdf.inputs["Roughness"].default_value = 0.95
tex = nt.nodes.new("ShaderNodeTexNoise")
tex.inputs["Scale"].default_value = 300.0
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
sand.data.materials.append(sand_mat)

# ---------- Ocean ----------
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 280, 0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
ocean_mat = bpy.data.materials.new("OceanMat")
nt = ocean_mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.02, 0.12, 0.3, 1)
bsdf.inputs["Roughness"].default_value = 0.12
bsdf.inputs["Metallic"].default_value = 0.0
wave = nt.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 2.0
wave.inputs["Distortion"].default_value = 6.0
wbump = nt.nodes.new("ShaderNodeBump")
wbump.inputs["Strength"].default_value = 0.15
nt.links.new(wave.outputs["Fac"], wbump.inputs["Height"])
nt.links.new(wbump.outputs["Normal"], bsdf.inputs["Normal"])
ocean.data.materials.append(ocean_mat)

# ---------- Sun disc ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=8, location=(0, 400, 14))
disc = bpy.context.active_object
disc.name = "SunDisc"
dmat = bpy.data.materials.new("SunDiscMat")
nt = dmat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.55, 0.2, 1)
em.inputs["Strength"].default_value = 15.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
disc.data.materials.append(dmat)

# ---------- World gradient ----------
world = bpy.data.worlds.new("SunsetWorld")
scene.world = world
wt = world.node_tree
for n in list(wt.nodes):
    wt.nodes.remove(n)
tc = wt.nodes.new("ShaderNodeTexCoord")
sep = wt.nodes.new("ShaderNodeSeparateXYZ")
mr = wt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.02
mr.inputs["From Max"].default_value = 0.6
ramp = wt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.45, 0.08, 1)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.18, 0.05, 0.35, 1)
mid = cr.elements.new(0.3)
mid.color = (0.9, 0.25, 0.35, 1)
bg = wt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
wout = wt.nodes.new("ShaderNodeOutputWorld")
wt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wt.links.new(sep.outputs["Z"], mr.inputs["Value"])
wt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
wt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
wt.links.new(bg.outputs["Background"], wout.inputs["Surface"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.6, 0.35)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(-82), 0, 0)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 30
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (2.0, -18.0, 2.2)
direction = Vector((0, 20, 0.6)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
