# Experiments

One row per run, including the ones that failed. Metric is silhouette IoU against the cleaned sketch mask on the fixed test set (`samples/sketches/`), plus seconds and peak VRAM. Add a row before moving on.

| # | Time | Change | IoU (mean) | Seconds | Peak VRAM | Kept | What we learned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 12:00 | Repo created | - | - | - | - | Hardware is a GTX 1650 Ti with 4 GB. Most candidate models quote 5 to 6 GB or more. |
| 1 | 16:35 | TripoSR on CPU (M2 MacBook Air, 4 torch threads), `chair.png` from the upstream examples, mc-resolution 192, seed 1 | - | 7.1 load, 32.9 reconstruct | 5.6 GB RAM, no GPU | Yes, the CPU default | 22,779 vertices and 45,556 faces. GLB is 0.9 MB, loads in trimesh with vertex colours, not watertight. First attempt failed to load the checkpoint (see REPORT.md). |
| 2 | 16:40 | Same input, mc-resolution 256 on CPU | - | 6.8 load, 112.1 reconstruct | 8.6 GB RAM, no GPU | No | 40,792 vertices and 81,584 faces, watertight. 3.4 times slower and 3 GB more RAM than 192. Supports 192 as the CPU default. The GPU number at 256 is still to measure on the pod. |
