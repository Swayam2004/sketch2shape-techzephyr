"""Sketch2Shape panel for Blender. Imports the .glb or .obj the pipeline writes, and can send a
sketch to the local server and import the result.

Uses only the standard library plus bpy. The HTTP code is in client.py.
"""

from __future__ import annotations

bl_info = {
    "name": "Sketch2Shape",
    "author": "Sketch2Shape team",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Sketch2Shape",
    "description": "Import Sketch2Shape meshes with vertex colours, or generate one from a sketch",
    "category": "Import-Export",
}

import tempfile
import threading
from pathlib import Path

import bpy
from bpy.props import IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from . import client

# One generate job at a time. The worker thread writes here, the timer on the main thread reads.
_job: dict = {}


class S2SSettings(PropertyGroup):
    mesh_path: StringProperty(name="Mesh", subtype="FILE_PATH", description=".glb or .obj file")
    sketch_path: StringProperty(name="Sketch", subtype="FILE_PATH", description="PNG, JPG or WebP")
    prompt: StringProperty(name="Prompt", maxlen=300)
    seed: IntProperty(name="Seed", default=0, min=0)
    server_url: StringProperty(name="Server", default=client.DEFAULT_URL)
    access_code: StringProperty(name="Access code", subtype="PASSWORD")
    status: StringProperty(name="Status", default="")


def _show_vertex_colours(obj: bpy.types.Object) -> None:
    """Link the mesh colour attribute to Base Color so the colours show in Material Preview.

    The glTF importer keeps the colours as a mesh attribute but does not always wire them into the
    material, and the OBJ importer does not touch the material at all.
    """
    mesh = obj.data
    attributes = getattr(mesh, "color_attributes", None)
    if not attributes or len(attributes) == 0:
        return
    layer = (attributes.active_color or attributes[0]).name

    if not mesh.materials:
        mesh.materials.append(bpy.data.materials.new(f"{obj.name}_vertex_colour"))
    for material in mesh.materials:
        if material is None:
            continue
        material.use_nodes = True
        tree = material.node_tree
        bsdf = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or bsdf.inputs["Base Color"].is_linked:
            continue
        colour = tree.nodes.new("ShaderNodeVertexColor")
        colour.layer_name = layer
        tree.links.new(colour.outputs["Color"], bsdf.inputs["Base Color"])


def import_mesh_file(path: Path) -> list[bpy.types.Object]:
    """Import a .glb, .gltf or .obj and return the new objects. Raises ValueError for other types."""
    if not path.is_file():
        raise ValueError(f"File not found: {path}")
    suffix = path.suffix.lower()
    before = set(bpy.data.objects)
    if suffix in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix == ".obj":
        # Blender 3.6 and older only have the Python importer, 4.x has the C++ one.
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(filepath=str(path))
        else:
            bpy.ops.import_scene.obj(filepath=str(path))
    else:
        raise ValueError(f"Unsupported file type {suffix!r}. Use .glb or .obj.")

    new_objects = [o for o in bpy.data.objects if o not in before]
    for obj in new_objects:
        if obj.type == "MESH":
            _show_vertex_colours(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in new_objects:
        obj.select_set(True)
    if new_objects:
        bpy.context.view_layer.objects.active = new_objects[0]
    return new_objects


class S2S_OT_import(Operator):
    bl_idname = "sketch2shape.import_mesh"
    bl_label = "Import"
    bl_description = "Import the mesh file and show its vertex colours"

    def execute(self, context):
        settings = context.scene.s2s
        try:
            objects = import_mesh_file(Path(bpy.path.abspath(settings.mesh_path)))
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings.status = f"Imported {len(objects)} object(s)."
        return {"FINISHED"}


def _run_job(url: str, sketch: Path, prompt: str, seed: int, code: str) -> None:
    """Worker thread. Never touches bpy, only the shared _job dict."""
    try:
        job_id = client.submit_job(url, sketch, prompt, seed, code)

        def progress(job: dict) -> None:
            stage = job.get("stage") or job["status"]
            _job["message"] = f"{job['status']}: {stage}"

        job = client.wait_for_job(url, job_id, code, on_update=progress)
        _job["warnings"] = job.get("warnings") or []
        out_dir = Path(tempfile.gettempdir()) / "sketch2shape"
        _job["path"] = client.download_result(url, job_id, out_dir, "result.glb", code)
    except (client.ClientError, OSError, KeyError, ValueError) as exc:
        _job["error"] = str(exc)
    finally:
        _job["finished"] = True


def _tick() -> float | None:
    """Timer on the main thread. Imports the result when the worker finishes."""
    scene = bpy.data.scenes.get(_job.get("scene", ""))
    if scene is None:
        _job.clear()
        return None
    settings = scene.s2s
    if not _job.get("finished"):
        settings.status = _job.get("message", "Working...")
    elif _job.get("error"):
        settings.status = f"Failed. {_job['error']}"
    else:
        try:
            import_mesh_file(_job["path"])
            note = " ".join(_job.get("warnings", []))
            settings.status = f"Done. {note}".strip()
        except (ValueError, RuntimeError) as exc:
            settings.status = f"Downloaded but the import failed. {exc}"
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    if _job.get("finished"):
        _job.clear()
        return None
    return 0.5


class S2S_OT_generate(Operator):
    bl_idname = "sketch2shape.generate"
    bl_label = "Generate from sketch"
    bl_description = "Send the sketch to the local server and import the mesh it returns"

    def execute(self, context):
        settings = context.scene.s2s
        sketch = Path(bpy.path.abspath(settings.sketch_path))
        if not sketch.is_file():
            self.report({"ERROR"}, f"Sketch not found: {sketch}")
            return {"CANCELLED"}
        if _job:
            self.report({"WARNING"}, "A job is already running.")
            return {"CANCELLED"}
        _job.update(scene=context.scene.name, message="Submitting...", finished=False)
        threading.Thread(
            target=_run_job,
            args=(
                settings.server_url,
                sketch,
                settings.prompt,
                settings.seed,
                settings.access_code,
            ),
            daemon=True,
        ).start()
        bpy.app.timers.register(_tick, first_interval=0.5)
        return {"FINISHED"}


class S2S_PT_panel(Panel):
    bl_label = "Sketch2Shape"
    bl_idname = "S2S_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketch2Shape"

    def draw(self, context):
        settings = context.scene.s2s
        layout = self.layout

        box = layout.box()
        box.label(text="Import a mesh")
        box.prop(settings, "mesh_path")
        box.operator("sketch2shape.import_mesh", icon="IMPORT")

        box = layout.box()
        box.label(text="Generate from a sketch")
        box.prop(settings, "sketch_path")
        box.prop(settings, "prompt")
        box.prop(settings, "seed")
        box.prop(settings, "server_url")
        box.prop(settings, "access_code")
        row = box.row()
        row.enabled = not _job
        row.operator("sketch2shape.generate", icon="MESH_MONKEY")

        if settings.status:
            layout.label(text=settings.status)


_classes = (S2SSettings, S2S_OT_import, S2S_OT_generate, S2S_PT_panel)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.s2s = PointerProperty(type=S2SSettings)


def unregister() -> None:
    del bpy.types.Scene.s2s
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
