# Experiments

One row per run, including the ones that failed. Metric is silhouette IoU against the cleaned sketch mask on the fixed test set (`samples/sketches/`), plus seconds and peak VRAM. Add a row before moving on.

| # | Time | Change | IoU (mean) | Seconds | Peak VRAM | Kept | What we learned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 12:00 | Repo created | - | - | - | - | Hardware is a GTX 1650 Ti with 4 GB. Most candidate models quote 5 to 6 GB or more. |
