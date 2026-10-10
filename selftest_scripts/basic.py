# Known good Blender 5.2 script, category: basic. Low poly campfire at night.
import bpy
import math

scene = bpy.context.scene


def make_material(name, color, emission=0.0):
    mat = bpy.data.materials.new(name)  # 5.0+: node tree with Principled BSDF is created automatically
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


wood = make_material("Wood", (0.25, 0.12, 0.05))
stone = make_material("Stone", (0.3, 0.3, 0.32))
flame = make_material("Flame", (1.0, 0.35, 0.05), emission=8.0)
ground_mat = make_material("Ground", (0.08, 0.1, 0.06))

bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.active_object.data.materials.append(ground_mat)

for i in range(4):
    angle = i * math.pi / 4
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.12, depth=1.6, location=(0, 0, 0.15),
                                        rotation=(math.pi / 2, 0, angle))
    bpy.context.active_object.data.materials.append(wood)

for i in range(10):
    a = i * 2 * math.pi / 10
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.18, location=(math.cos(a) * 1.1, math.sin(a) * 1.1, 0.1))
    bpy.context.active_object.data.materials.append(stone)

for i, (x, y, h) in enumerate([(0, 0, 0.9), (0.15, 0.1, 0.6), (-0.12, -0.08, 0.7)]):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.22, depth=h, location=(x, y, 0.3 + h / 2))
    bpy.context.active_object.data.materials.append(flame)

light_data = bpy.data.lights.new("Fire", type="POINT")
light_data.energy = 300
light_data.color = (1.0, 0.5, 0.2)
light = bpy.data.objects.new("Fire", light_data)
light.location = (0, 0, 0.8)
scene.collection.objects.link(light)

cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (4.0, -4.0, 2.5)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 0.4)
scene.collection.objects.link(target)
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = cam

world = bpy.data.worlds.new("Night")  # default Background + World Output nodes are created
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.007, 0.02, 1.0)
scene.world = world
