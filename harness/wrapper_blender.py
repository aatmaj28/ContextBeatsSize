"""Runs INSIDE Blender 5.2 (its bundled Python). Self-contained: no harness imports.

<blender> --background --factory-startup --python wrapper_blender.py -- \
    --script <file> --result <json> --category <cat> [--render <png>]

Reset to an empty scene, exec the generated script, run the pass checks,
optionally render (Cycles CPU 640x360, 32 samples, denoise), write a result JSON.
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import bpy

GEOMETRY_TYPES = {"MESH", "CURVE", "FONT", "SURFACE", "META"}
LAYOUT_NODES = {"NodeReroute", "NodeFrame"}
# Compositor nodes that only feed data in or take it out; anything else counts as an effect node.
COMPOSITOR_IO_NODES = LAYOUT_NODES | {
    "NodeGroupInput", "NodeGroupOutput",
    "CompositorNodeRLayers", "CompositorNodeImage", "CompositorNodeMovieClip", "CompositorNodeMask",
    "CompositorNodeRGB", "CompositorNodeValue", "ShaderNodeValue", "CompositorNodeBlankImage",
    "CompositorNodeSceneTime", "CompositorNodeTime", "CompositorNodeImageInfo",
    "CompositorNodeImageCoordinates", "CompositorNodeTrackPos", "CompositorNodeBokehImage",
    "CompositorNodeSequencerStripInfo",
    "CompositorNodeViewer", "CompositorNodeOutputFile",
}
# The spec compares frame_start with the middle frame. A correct periodic animation (e.g. blades doing
# exactly 2 turns, a light looping every N/2 frames) can coincide there, so if those two match we also
# sample the quarter and three-quarter frames before declaring "nothing animates". Set False for strict.
ANIM_EXTRA_SAMPLES = True
EPS = 1e-4


class CheckFailed(Exception):
    pass


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--script", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--render", default=None)
    return p.parse_args(argv)


def write_result(path, result):
    Path(path).write_text(json.dumps(result, indent=2, default=str))


def script_traceback(exc, script_file):
    """Format the traceback starting at the first frame inside the generated script."""
    if isinstance(exc, SyntaxError):
        return "".join(traceback.format_exception_only(type(exc), exc))
    tb = exc.__traceback__
    while tb is not None and tb.tb_frame.f_code.co_filename != script_file:
        tb = tb.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb if tb is not None else exc.__traceback__))


def middle_frame(scene):
    return (scene.frame_start + scene.frame_end) // 2


# ---------------------------------------------------------------- checks
def render_visible(obj, scene, view_layer):
    if obj.hide_render or obj.name not in view_layer.objects:
        return False
    return any(c == scene.collection or not c.hide_render for c in obj.users_collection)


def geometry_objects(scene):
    vl = bpy.context.view_layer
    return [o for o in scene.objects if o.type in GEOMETRY_TYPES and render_visible(o, scene, vl)]


def check_common(scene):
    if scene.camera is None:
        raise CheckFailed("Check failed: bpy.context.scene.camera is not set.")
    if not geometry_objects(scene):
        raise CheckFailed("Check failed: the scene has no visible geometry object "
                          "(MESH, CURVE, FONT, SURFACE or META).")


def _snapshot(scene, frame):
    scene.frame_set(frame)
    mats = {o.name: [v for row in o.matrix_world for v in row] for o in scene.objects}
    energies = {o.name: float(o.data.energy) for o in scene.objects if o.type == "LIGHT"}
    return mats, energies


def _differs(a, b):
    mats_a, en_a = a
    mats_b, en_b = b
    for name, m in mats_a.items():
        if name in mats_b and any(abs(x - y) > EPS for x, y in zip(m, mats_b[name])):
            return True
    for name, e in en_a.items():
        if name in en_b and abs(e - en_b[name]) > EPS * max(1.0, abs(e)):
            return True
    return False


def check_anim(scene, info):
    fs, fe = scene.frame_start, scene.frame_end
    if fe <= fs:
        raise CheckFailed(f"Check failed: scene.frame_end ({fe}) must be greater than scene.frame_start ({fs}).")
    base = _snapshot(scene, fs)
    frames = [middle_frame(scene)]
    if ANIM_EXTRA_SAMPLES:
        frames += [fs + (fe - fs) // 4, fs + 3 * (fe - fs) // 4]
    for f in frames:
        if f != fs and _differs(base, _snapshot(scene, f)):
            info["anim_moving_frame"] = f
            scene.frame_set(fs)
            return
    scene.frame_set(fs)
    raise CheckFailed(f"Check failed: nothing animates. Object world matrices and light energies are the same "
                      f"at frame_start ({fs}) and the middle frame ({middle_frame(scene)}).")


def check_gn(scene, info):
    found_mod = found_group = False
    for o in scene.objects:
        for m in o.modifiers:
            if m.type != "NODES":
                continue
            found_mod = True
            ng = m.node_group
            if ng is None:
                continue
            found_group = True
            extra = [it for it in ng.interface.items_tree
                     if it.item_type == "SOCKET" and it.in_out == "INPUT" and it.socket_type != "NodeSocketGeometry"]
            if extra:
                info["gn_inputs"] = [f"{o.name}/{m.name}: {it.name} ({it.socket_type})" for it in extra]
                return
    if not found_mod:
        raise CheckFailed("Check failed: no object has a Geometry Nodes modifier.")
    if not found_group:
        raise CheckFailed("Check failed: the Geometry Nodes modifier has no node group assigned.")
    raise CheckFailed("Check failed: the Geometry Nodes node group has no inputs besides Geometry "
                      "(no exposed modifier input).")


def check_compositor(scene, info):
    tree = getattr(scene, "compositing_node_group", None)
    if tree is None:
        raise CheckFailed("Check failed: the scene has no compositor node tree (scene.compositing_node_group is None).")
    effects = [n for n in tree.nodes if n.bl_idname not in COMPOSITOR_IO_NODES]
    if not effects:
        raise CheckFailed("Check failed: the compositor node tree has no effect node besides input and output nodes.")
    info["compositor_effects"] = [n.bl_idname for n in effects]


def check_world(scene, info):
    w = scene.world
    if w is None:
        raise CheckFailed("Check failed: scene.world is not set.")
    if w.node_tree is None:
        raise CheckFailed("Check failed: the scene world has no node tree.")
    rest = [n.bl_idname for n in w.node_tree.nodes if n.bl_idname not in LAYOUT_NODES]
    for default in ("ShaderNodeBackground", "ShaderNodeOutputWorld"):
        if default in rest:
            rest.remove(default)
    if not rest:
        raise CheckFailed("Check failed: the world node tree has no nodes beyond the default Background and World Output.")
    info["world_extra_nodes"] = rest


def check_materials(scene, info):
    for o in geometry_objects(scene):
        if any(s.material is not None for s in o.material_slots):
            return
    raise CheckFailed("Check failed: no visible geometry object has a material assigned.")


CATEGORY_CHECKS = {
    "anim": check_anim,
    "gn": check_gn,
    "compositor": check_compositor,
    "world": check_world,
    "materials": check_materials,
    "basic": None,
}


# ---------------------------------------------------------------- render
def apply_render_settings(scene, png_path, category):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 640, 360, 100
    r.image_settings.media_type = "IMAGE"  # 5.0+: must be set before file_format
    r.image_settings.file_format = "PNG"
    r.filepath = str(png_path)
    if category == "anim":
        scene.frame_set(middle_frame(scene))


# ---------------------------------------------------------------- main
def main():
    args = parse_args()
    script_file = str(Path(args.script).resolve())
    result = {"passed": False, "stage": "reset", "error_type": None, "error_message": None,
              "traceback": None, "checks": {}, "exec_s": None, "render": None, "render_time_s": None,
              "render_error": None, "blender_version": bpy.app.version_string}
    write_result(args.result, result)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    result["stage"] = "exec"
    write_result(args.result, result)
    t0 = time.time()
    try:
        source = Path(script_file).read_text()
        code = compile(source, script_file, "exec")
        exec(code, {"__name__": "__main__", "__file__": script_file})
    except (Exception, SystemExit) as exc:
        result["exec_s"] = round(time.time() - t0, 3)
        result["error_type"] = type(exc).__name__
        result["error_message"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = script_traceback(exc, script_file)
        write_result(args.result, result)
        return
    result["exec_s"] = round(time.time() - t0, 3)

    result["stage"] = "checks"
    scene = bpy.context.scene
    try:
        # Sync the view layer first: objects linked with collection.objects.link() are not listed in
        # view_layer.objects until the next update, which would make visible geometry look missing.
        bpy.context.view_layer.update()
        check_common(scene)
        fn = CATEGORY_CHECKS.get(args.category)
        if fn is not None:
            fn(scene, result["checks"])
    except CheckFailed as exc:
        result["error_type"] = "check_failed"
        result["error_message"] = str(exc)
        write_result(args.result, result)
        return
    except Exception as exc:  # the script left the scene in a state the checks cannot read
        result["error_type"] = "check_failed"
        result["error_message"] = f"Check failed: could not inspect the scene ({type(exc).__name__}: {exc})"
        result["traceback"] = traceback.format_exc()
        write_result(args.result, result)
        return

    result["passed"] = True
    result["stage"] = "done"
    write_result(args.result, result)

    if args.render:
        result["stage"] = "render"
        t1 = time.time()
        try:
            Path(args.render).parent.mkdir(parents=True, exist_ok=True)
            apply_render_settings(scene, args.render, args.category)
            bpy.ops.render.render(write_still=True)
            result["render"] = args.render
        except Exception as exc:
            result["render_error"] = f"{type(exc).__name__}: {exc}"
        result["render_time_s"] = round(time.time() - t1, 3)
        result["stage"] = "done"
        write_result(args.result, result)


if __name__ == "__main__":
    main()
