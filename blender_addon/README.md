# Blender add-on

Imports the `.glb` or `.obj` the pipeline writes, with its vertex colours. It can also send a sketch to the local server and import the result.

## Install

1. Run `uv run python scripts/package_blender_addon.py`. It writes `outputs/sketch2shape_blender_addon.zip`.
2. In Blender, open Edit, Preferences, Add-ons, Install from Disk, pick the zip and tick Sketch2Shape.
3. Press N in the 3D viewport and open the Sketch2Shape tab. Pick a mesh file and press Import.

## Generate from a sketch

Start the server with `uv run sketch2shape serve` (port 7860). In the panel, pick a sketch, type a prompt, and press Generate from sketch. Enter the access code if the server has `S2S_ACCESS_CODE` set. The panel shows the stage and any warnings, and imports the mesh when the job is done. CPU runs take minutes.

## What was checked

- `tests/test_blender_client.py` runs the HTTP client against a fake server. It covers the multipart upload, the access code header, the poll schedule (1 s for 10 s, then 3 s, stop at 15 minutes) and error messages.
- A headless run on Blender 5.0.1 (the `bpy` wheel on Windows) imported a vertex-coloured `.glb` and `.obj` and found the colour attribute and a Vertex Color node in the material.
- Not checked in the Blender window. The Generate button (worker thread plus timer), the panel layout, and Blender versions other than 5.0.1. The manifest says 3.6 or newer, which is untested.
