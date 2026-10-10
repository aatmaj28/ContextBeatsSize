# category: anim
# expect: pass
# Only a light energy animates (no object motion), looping every 48 frames over 0-96. Must pass.
import bpy
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 0, 96
bpy.ops.mesh.primitive_uv_sphere_add()
ld = bpy.data.lights.new("Pulse", type="POINT"); lo = bpy.data.objects.new("Pulse", ld); lo.location = (2, -2, 2); scene.collection.objects.link(lo)
for f, e in [(0, 50), (24, 1000), (48, 50), (72, 1000), (96, 50)]:
    ld.energy = e; ld.keyframe_insert("energy", frame=f)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); cam.location = (0, -8, 0); scene.collection.objects.link(cam); scene.camera = cam
