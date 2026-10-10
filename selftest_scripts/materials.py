# Known good Blender 5.2 script, category: materials. Glossy donut with frosting on a plate.
import bpy
import math
import random

random.seed(3)
scene = bpy.context.scene


def principled(name, color, roughness=0.5, coat=0.0):
    mat = bpy.data.materials.new(name)  # node tree exists already in 5.x; use_nodes is deprecated
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Coat Weight"].default_value = coat
    return mat


dough = principled("Dough", (0.6, 0.35, 0.15), 0.6)
frosting = principled("Frosting", (0.95, 0.4, 0.6), 0.15, coat=1.0)
plate_mat = principled("Plate", (0.95, 0.95, 0.95), 0.2)

bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.4, location=(0, 0, 0.5))
donut = bpy.context.active_object
donut.data.materials.append(dough)

bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.41, location=(0, 0, 0.56))
icing = bpy.context.active_object
icing.scale = (1.0, 1.0, 0.75)
icing.data.materials.append(frosting)

for i in range(40):
    a = random.uniform(0, 2 * math.pi)
    r = 1.0 + random.uniform(-0.3, 0.3)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.12, location=(math.cos(a) * r, math.sin(a) * r, 0.88),
                                        rotation=(math.pi / 2, 0, random.uniform(0, math.pi)))
    s = bpy.context.active_object
    s.data.materials.append(principled(f"Sprinkle{i}", (random.random(), random.random(), random.random()), 0.3))

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=2.0, depth=0.1, location=(0, 0, 0.05))
bpy.context.active_object.data.materials.append(plate_mat)

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", type="SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(40), 0, math.radians(30))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -4.5, 3.2)
cam.rotation_euler = (math.radians(55), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
