# Udit. Pod, preprocessing, SD stage, evaluation

Machine. Windows, Ryzen 7 PRO 7840U, 16 GB RAM, no usable GPU for PyTorch. Native Windows with uv is the judge's view of the project. The shared GPU pod does the heavy runs.

You own `src/sketch2shape/preprocess/`, `generate/`, `eval/`, `scripts/` (except `download_weights.py`), the RunPod account, and from about 00:00 `blender_addon/`.

Read `docs/tasks/README.md` first and follow the sync routine.

## U0. RunPod pod. Target 16:45. Do this first

Follow `docs/guides/runpod-dev-gpu.md` step by step. Disha's and Swayam's SSH public keys come from `docs/guides/ssh-key.md`. Collect all three keys, add them in the RunPod console, create the network volume and the L4 pod, post the pod address in `STATUS.md` under Shared resources.

Spend rule. Start with $25 of credit. Stop the pod when nobody needs it. If anything blocks you for more than 20 minutes, tell Swayam.

## U1. Windows check. Target 17:00, ten minutes

`scripts/setup.ps1` already ran for you. Note any rough edge in `STATUS.md`. WSL2 is optional and low priority.

## U2. Sketch preprocessing. Target 17:30

Goal. `preprocess.prepare_sketch(image: PIL.Image) -> PreparedSketch` (see `src/sketch2shape/types.py`). CPU only, numpy and OpenCV, no models.

It must handle
- RGBA input with a transparent background (canvas exports). Composite on white.
- White strokes on a dark background (detect and invert).
- Phone photos of paper (uneven lighting, grey paper). Use adaptive thresholding.
- Thin or faint pencil lines, small specks of noise.

Steps. Convert to grey, normalise contrast, threshold to strokes, remove specks, crop to the strokes' bounding box, pad to a square with margin, resize to 512. Build `mask` by closing small gaps (morphological dilation), flood filling the outside from the border, and inverting, so the interior is filled. If the shape never closes, fall back to the convex hull and add a warning to the result. Build `scribble` as white lines on black, about 2 to 4 px wide.

Tests, using synthetic images made in the test (circle, open arc, rectangle, noisy circle, inverted colours, transparent background). Check output sizes, dtypes, that the mask area of a drawn circle matches within a few percent, and that a blank image raises a clear error.

Done when. All tests pass on Windows, and Disha's 12 sketches (when they land) produce sensible masks. Save a contact sheet of input, mask and scribble to `outputs/preprocess_check.png` and look at it yourself.

## U3. Sketch to image. Target 19:00

Goal. `generate.sketch_to_image(sketch: PreparedSketch, prompt: str | None, seed: int, device: Device) -> PIL.Image` (512 RGB).

- Models. `stable-diffusion-v1-5/stable-diffusion-v1-5` with `lllyasviel/control_v11p_sd15_scribble`, loaded by `scripts/download_weights.py` into `weights/` (Swayam writes that script, run it on the pod). Do not use the HED annotator, its licence is unclear. The sketch already is a scribble.
- Prompt template. `"{prompt}, product design render, single object, centred, plain white background, soft studio lighting"`. When the user gives no prompt, use `"a single object"` plus the template. Negative prompt for clutter, text, multiple objects, cropped, background scenery. Start values, tune them.
- Settings. 20 steps, UniPC scheduler, guidance 7.5, ControlNet conditioning scale 1.0 (test 0.7 to 1.2), seed passed through a `torch.Generator`.
- Devices. CUDA uses fp16. Check for black or NaN output and fall back to fp32 (GTX 16xx cards are known to do this). CPU uses fp32 and attention slicing. Return a clear error if the model files are missing.
- Test LCM-LoRA with 4 steps as the CPU speed-up. Only keep it if the images keep the sketch structure. Log the comparison in `EXPERIMENTS.md`, with seconds and silhouette IoU when the harness exists. The default must be identical on every device, so if LCM wins it wins everywhere.

Done when. On the pod, 3 test sketches give clean single-object images that follow the sketch outline. Save examples to `samples/results/` after Swayam's cutout is in.

## U4. Evaluation harness. Target 21:00

Goal. `eval.silhouette_iou(mesh: trimesh.Trimesh, mask: np.ndarray) -> float` and `scripts/eval_testset.py`.

- Render without OpenGL (it fails on headless pods and some Windows setups). Project the mesh orthographically along -Z onto XY (glTF convention from `types.py`), fit it to the same normalised frame as the sketch mask (use the mask's bounding box, since TripoSR rescales the object), rasterise triangles with OpenCV `fillPoly` into a 512 by 512 mask, compute IoU against the sketch mask.
- Tests. A unit cube against a square mask gives near 1.0. A shifted or scaled mesh gives a lower value.
- `scripts/eval_testset.py` runs every sketch in `samples/sketches/` (with `prompts.json`) through `pipeline.run`, writes `outputs/eval/results.csv` and a Markdown table of IoU, seconds and any failures. You paste the table into `EXPERIMENTS.md`. Fixed seed 0.

## U5. CPU and Windows run. After Swayam's CLI lands (about 20:00)

Run the whole pipeline on your laptop on CPU, native Windows. Record seconds per stage and peak RAM. Report anything that fails or is unusably slow in `STATUS.md` right away. The README needs this number ("time on a CPU laptop").

## U6. Blender add-on. From about 00:00, if the core is green

Goal. A panel in Blender that sends a sketch to the API (`docs/api.md`), polls, and imports the returned `.glb`.

- Use only the standard library inside Blender (`urllib`, `json`, `threading` or `bpy.app.timers`), so there are no pip installs.
- Two inputs. An image file chosen on disk, and the current Grease Pencil drawing rendered to PNG. Image file first.
- Settings. API URL, access code, prompt, seed. Import the `.glb` with `bpy.ops.import_scene.gltf`. Show progress and errors in the panel.
- Disha tests it on her Mac and writes the install steps for the README.

## Kickoff prompt

> Read AGENTS.md, CONTEXT.md, STATUS.md, PLAN.md, docs/tasks/README.md and docs/tasks/udit.md. Run the sync routine. Do U0 with me, then U2. Tell me your plan in five lines, then go.
