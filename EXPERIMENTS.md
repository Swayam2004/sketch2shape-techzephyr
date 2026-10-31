# Experiments

One row per run, including the ones that failed. Metric is silhouette IoU against the cleaned sketch mask on the fixed test set (`samples/sketches/`), plus seconds and peak VRAM. Add a row before moving on.

| # | Time | Change | IoU (mean) | Seconds | Peak VRAM | Kept | What we learned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 12:00 | Repo created | - | - | - | - | Hardware is a GTX 1650 Ti with 4 GB. Most candidate models quote 5 to 6 GB or more. |
| 1 | 16:35 | TripoSR on CPU (M2 MacBook Air, 4 torch threads), `chair.png` from the upstream examples, mc-resolution 192, seed 1 | - | 7.1 load, 32.9 reconstruct | 5.6 GB RAM, no GPU | Yes, the CPU default | 22,779 vertices and 45,556 faces. GLB is 0.9 MB, loads in trimesh with vertex colours, not watertight. First attempt failed to load the checkpoint (see REPORT.md). |
| 2 | 16:40 | Same input, mc-resolution 256 on CPU | - | 6.8 load, 112.1 reconstruct | 8.6 GB RAM, no GPU | No | 40,792 vertices and 81,584 faces, watertight. 3.4 times slower and 3 GB more RAM than 192. Supports 192 as the CPU default. The GPU number at 256 is still to measure on the pod. |
| 3 | 22:31 | TripoSR on Swayam's Linux CPU, same chair, mc-resolution 192, seed 1 | - | 10.1 load, 22.5 reconstruct | not measured | Yes | Same 22,779 vertices and 45,556 faces as the Mac run, so the CPU path is deterministic across machines. Faster than the M2 (32.9 s). |
| 4 | 23:31 | TripoSR on GTX 1650 Ti (4 GB), same chair, mc-resolution 256, chunk 8192 | - | 6.6 load, 5.4 reconstruct | 2370 MB | Yes, the GPU default | 40,792 vertices, 81,584 faces, watertight. Fits in 4 GB, so no fp16 or CPU/GPU split needed. Chunk 2048 gave the same peak and 6.7 s, so 8192 stays. |
| 5 | 00:09 | Full pipeline CLI on GPU, `chair.png` through our rembg cutout, stub for preprocess and generate, seed 1 | - | 0.1 preprocess, 2.1 cutout, 11.3 reconstruct (6.7 model load, 4.6 run), 0.5 export | 2370 MB | Yes | 41,930 vertices and 83,864 faces after cleanup, watertight, vertex colours. The largest-component step dropped a 24 face fragment. About 14 s end to end including the one-time model load. |
| 6 | 00:55 | API server on GTX 1650 Ti, model warmed at startup, one job (chair, stub stages) over HTTP with curl | - | 6.6 submit to done | 2370 MB | Yes | The warm-up moves the 6.7 s TripoSR load out of the first request. Job time drops from about 14 s (CLI, cold) to 6.6 s. |
