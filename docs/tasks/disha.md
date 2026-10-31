# Disha. Test sketches, UI, documentation

Machine. MacBook Air M2, 16 GB. You do not need a GPU for any of this.

You own `src/sketch2shape/app/`, `README.md`, `REPORT.md`, `docs/` (except the research and task files), `AI_USAGE.md` audits, `samples/sketches/`, slides and the demo video.

Read `docs/tasks/README.md` first and follow the sync routine.

## D0. SSH key. Target 16:15, ten minutes

Follow `docs/guides/ssh-key.md` and send Udit your public key. You only need the pod to check the hosted run later.

## D1. Twelve test sketches. Target 17:30

These are the fixed inputs for every comparison, so quality matters more than speed.

Put them in `samples/sketches/` as PNG, at least 768 px on the long side, dark strokes on a white background, named `01_chair.png` to `12_<name>.png`. Draw digitally with any app. Make three of them phone photos of real paper sketches (`photo_` prefix) so we test uploads.

| # | Content | Why |
| --- | --- | --- |
| 1 | Chair, three-quarter view | Classic furniture |
| 2 | Mug with a handle, side view | Simple closed shape with a hole |
| 3 | Table lamp | Thin parts and a shade |
| 4 | Car, side view | Wheels, long flat shape |
| 5 | Small house with a roof and door | Architecture |
| 6 | Toy robot, front view | Many small parts |
| 7 | Sneaker, side view | Organic shape |
| 8 | Potted plant | Thin leaves, hard case |
| 9 | Guitar, front view | Long and symmetrical |
| 10 | Aeroplane, top view | Flat shape seen from above |
| 11 | Very rough three-stroke vase | Minimal input |
| 12 | Messy overlapping scribble of a bottle | Noise and overlapping strokes |

Write `samples/sketches/prompts.json` mapping file name to a prompt, for six of them (for example `"01_chair.png": "wooden dining chair, oak"`) and leave the other six empty. Add `samples/sketches/README.md` listing each sketch, what it tests, and that you drew them during the event (this supports the "original work" rule).

Done when. Udit's `prepare_sketch` runs on all twelve without errors.

## D2. Gradio UI on a stub client. Target 19:00

Goal. A UI that works end to end against `StubClient` today and the real API later (`docs/api.md`).

Files in `src/sketch2shape/app/`
- `client.py`. The `GenerationClient` interface with `HttpClient` and `StubClient`. `S2S_API_URL` unset means stub. The stub waits a few seconds, then returns a sample `.glb`. Make that sample with `scripts/make_stub_glb.py` (a coloured trimesh shape, committed under `samples/results/stub.glb`).
- `ui.py`. Gradio Blocks. Run with `uv run python -m sketch2shape.app`.

UI requirements (from the problem statement)
- Drawing canvas with brush, eraser and clear (`gr.Sketchpad` or `gr.ImageEditor`).
- Image upload as a second tab.
- Optional prompt box. Generation must work without it.
- Seed box in an "Advanced" section.
- Generate button, a progress line that shows the stage name and elapsed time while polling.
- 3D viewer (`gr.Model3D`) with the result, download buttons for `.glb` and `.obj`.
- Info panel. Device, seconds, validation result, silhouette IoU if present, and a visible warning banner for any `warnings` from the API (a CPU warning must show).
- Access code field, shown only when the server asks for one.
- Examples gallery from `samples/sketches/`.
- Clear error messages. No stack traces for users.

Keep it simple and clean. A polished UI does not score on its own, but a confusing one loses points on "end-to-end validity".

Done when. You can draw a sketch, press Generate, watch the progress and see the stub model in the viewer on your Mac. Tests cover the client with a mocked server.

## D3. README and report facts. Target 21:00 first pass, then keep going

- `README.md`. Fill the skeleton as the work lands. Objective, architecture diagram, requirements, install per OS (use what Udit and you actually ran), run commands, inputs and outputs, models and licences table (from `docs/research/model-options.md`, TripoSR, SD 1.5, ControlNet scribble, rembg isnet, all open or OpenRAIL), time per model per device (numbers come from `EXPERIMENTS.md`), hardware used, limitations, troubleshooting (collect real errors your teammates hit), and the hosted link and access code once they exist.
- `REPORT.md`. Agents append facts. Read them once in a while and note gaps in `STATUS.md`. Your final pass comes after 08:00. Rewrite in plain, direct language in your own voice. Keep real numbers and real failures.
- `AI_USAGE.md`. Check every session left a row. Ask the owner to fix gaps.

## D4. Later

- 23:00 to 04:00. Run your Mac through the CPU path and log seconds. Test the Blender add-on when Udit has v0.
- 08:00 after freeze. Slides (6 to 8, problem, approach, results, what failed, real-world use), demo video (screen recording, 2 to 3 minutes, draw a sketch live, show the 3D result, open it in Blender), the final `REPORT.md` pass.
- 09:30. Fresh clone on your Mac, follow the README only, time it, write down every stumble. Fix the README.

## Kickoff prompt

> Read AGENTS.md, CONTEXT.md, STATUS.md, PLAN.md, docs/tasks/README.md and docs/tasks/disha.md. Run the sync routine. Help me with D0 and D1 first, then D2. Tell me your plan in five lines, then go.
