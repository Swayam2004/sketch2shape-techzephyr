# Demo video script

Target 2:45. Record the screen with voice. Never show `.env`, tokens or terminal history that holds keys. Say on screen which device made each result.

| Time | Screen | Say |
| --- | --- | --- |
| 0:00 to 0:20 | Title card, then a hand sketch of a chair | "A modeller needs hours to turn a rough drawing into a 3D asset. Sketch2Shape does it from a drawing and an optional short prompt." |
| 0:20 to 1:00 | Pipeline diagram from `README.md` | "Preprocess cleans the sketch. Stable Diffusion 1.5 with a ControlNet scribble model makes an object image that keeps the outline. rembg removes the background. TripoSR builds a triplane, and marching cubes turns it into a mesh. We fix the axes, keep the largest piece and export a .glb and an .obj. The same models run on an NVIDIA GPU or on CPU." |
| 1:00 to 2:00 | Browser on localhost:7860. Draw, type "a wooden chair", press Generate. Show the stage bar, the timings and the warning banner if on CPU. Orbit the mesh, click the .glb download | "I draw a chair, add a prompt and press Generate. The bar shows each stage. This run used [device]. Here is the mesh, I can orbit it, and download the .glb." |
| 2:00 to 2:30 | Blender, import the .glb. Switch to Vertex Color shading, then wireframe | "It opens in Blender as real geometry. These are vertex colours, and the wireframe shows a full mesh, not a flat plane." |
| 2:30 to 3:00 | Results table from `REPORT.md` | "TripoSR takes 5.4 seconds on a 4 GB laptop GPU and 22 to 33 seconds on CPU. Silhouette IoU is [number]. The back of the object is a model guess, and the generate stage needs more than 4 GB. Designers and teachers can use it to block out props from a sketch." |

## Before you record

- Fill the bracketed numbers from `EXPERIMENTS.md`.
- Pick the device. Use the CPU path only if a run finishes in time on screen, otherwise cut to a pre-generated result and say which machine made it.
- Upload as unlisted and put the link in `README.md`.
