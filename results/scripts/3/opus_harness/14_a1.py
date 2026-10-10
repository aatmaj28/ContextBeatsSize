import bpy, math

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- World gradient sky ----------
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
cr.elements[0].color = (1.0, 0.35, 0.05, 1)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.12, 0.03, 0.25, 1)
e = cr.elements.new(0.15); e.color = (1.0, 0.55, 0.15, 1)
e = cr.elements.new(0.4); e.color = (0.9, 0.25, 0.35, 1)
e = cr.elements.new(0.7); e.color = (0.4, 0.1, 0.45, 1)
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

def principled(name, color, rough, spec=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    return m, b

def add_bump(mat, bsdf, scale, strength, detail=4):
    n = mat.node_tree.nodes
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# ---------- Sand ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, -10, 0.3))
sand = bpy.context.active_object
sand.name = "Sand"
sand.rotation_euler = (math.radians(-3), 0, 0)
sm, sb = principled("Sand", (0.85, 0.65, 0.42, 1), 0.9)
add_bump(sm, sb, 80, 0.3, 6)
sand.data.materials.append(sm)

# ---------- Ocean ----------
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
om, ob = principled("Ocean", (0.02, 0.12, 0.3, 1), 0.08)
add_bump(om, ob, 3, 0.15, 3)
ocean.data.materials.append(om)

# ---------- Sun disc ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=(0, 300, 10))
disc = bpy.context.active_object
disc.name = "SunDisc"
dm = bpy.data.materials.new("SunDisc")
dn = dm.node_tree.nodes
dn.clear()
em = dn.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.6, 0.2, 1)
em.inputs["Strength"].default_value = 8
mo = dn.new("ShaderNodeOutputMaterial")
dm.node_tree.links.new(em.outputs[0], mo.inputs["Surface"])
disc.data.materials.append(dm)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(0, 50, 10))
sun = bpy.context.active_object
sun.data.energy = 3
sun.data.color = (1.0, 0.6, 0.35)
sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(-84), 0, 0)  # low, from +Y toward camera

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0, -16, 1.8))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(88), 0, 0)
cam.data.lens = 32
cam.data.clip_end = 1000
scene.camera = cam
