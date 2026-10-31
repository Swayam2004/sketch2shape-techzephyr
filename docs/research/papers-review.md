# Papers review

Review date 31 Oct 2026. 27 PDFs from `papers/` (gitignored, never commit them). Scores follow the handoff rubric. Weighted total is Actionable x3 + Expected gain x3 + Relevance x2 + Evidence + Report value, out of 50. Tier A is 35 or more, B is 25 to 34, C is below 25.

How deep each paper was read

- Read in depth: TripoSR, the four conditioning papers, the seven sketch-to-3D papers and the four application papers. Page numbers are the printed page numbers in the PDFs.
- Abstract and first page only: Tailor3D, SilNet, Learning view priors, Hunyuan3D 1.0, Direct3D, MapAnything, LAS-Diffusion and the four 3D generation surveys. Their scores are triage scores, and numbers from them are marked reported. Two review subagents stalled on these groups, and the session was cut short to save tokens.
- Nothing here was run on our machines.

## Scoring table

| Tier | Total | Paper | Takeaway |
| --- | --- | --- | --- |
| A | 39 | TripoSR (2403.02151) | Our reconstruction model. Guesses the camera, so silhouette IoU needs a fixed or searched view. |
| A | 39 | ControlNet (ICCV 2023) | Our SD stage. Empty prompts and CFG interact, so the prompt fallback needs a sweep. |
| B | 34 | Sketch2Model (CVPR 2021) | Defines silhouette IoU on hand sketches. View is two Euler angles. |
| B | 32 | Sketch2Prototype (DESIGN 2024) | Closest product. ControlNet raises fidelity and lowers diversity. No mesh metric. |
| B | 28 | Doodle Your 3D (CVPR 2024) | Tests abstraction by redrawing with 8 to 32 strokes. Template for a stress test. |
| B | 27 | Sketch-based interaction and modeling, where do we stand | Survey. Source for ambiguity and interoperability arguments. |
| B | 26 | SKED (ICCV 2023) | Intersection-over-Sketch. Supports a fidelity check inside the loop. |
| B | 26 | AI-assisted game development case study | Target formats and a 40,000 triangle budget. Anecdotal. |
| C | 24 | Ctrl-X (NeurIPS 2024) | Training-free control. SDXL, 11.51 GiB, too heavy. |
| C | 23 | Control3D (ACM MM 2023) | Optimisation-based. Related work only. |
| C | 23 | Tailor3D (2407.06191) | Back view plus dual-sided LRM. Needs a model we do not have. |
| C | 22 | LAS-Diffusion (ACM TOG 2023) | Sketch-conditioned SDF diffusion. Trained on categories. Related work. |
| C | 19 | FreeControl (CVPR 2024) | 176 s per image on an A6000. Out. |
| C | 19 | SketchDream (ACM TOG 2024) | 1.0 to 1.3 h per example on an A100. Related work. |
| C | 19 | Deep learning for free-hand sketch, a survey (TPAMI 2023) | Taxonomy and the "scrawled sketch" claim. |
| C | 18 | Hunyuan3D 1.0 (2411.02293) | Ruled out by D18. Multi-view diffusion plus reconstruction. |
| C | 18 | Direct3D (NeurIPS 2024) | Native 3D latent diffusion. Too heavy. |
| C | 18 | Rapid 3D from intuitive 3D input (CVPR 2024) | VR sketch input. Gives a user study design. |
| C | 17 | SilNet (2017) | Silhouette prediction as a training proxy. Not usable now. |
| C | 15 | Learning view priors (CVPR 2019) | Train-time discriminator. Not usable now. |
| C | 14 | OmniControlNet (CVPRW 2024) | Needs extra models. Out. |
| C | 8 | Generative AI meets 3D, text-to-3D survey (2305.06131) | Survey. Citable. |
| C | 8 | A comprehensive survey on 3D content generation (2402.01166) | Taxonomy with three families. Citable. |
| C | 8 | A survey on text-to-3D contents generation in the wild (2405.09431) | Survey. Citable. |
| C | 8 | Text-to-3D shape generation (CGF 2024) | State of the art report. Citable. |
| C | 6 | MapAnything (3DV 2026) | Multi-view scene reconstruction. Out of scope. |
| C | 2 | CymbaDiff (NeurIPS 2025) | Urban scene generation. Out of scope. |

## Tier A notes

### TripoSR (2403.02151v1.pdf)

R5 A4 G3 E3 Rep5. Total 39, tier A.

It is a feed-forward image-to-triplane transformer built on LRM. It reconstructs a mesh from one image. The reported time is about 0.5 s on an A100 (p. 1, p. 4, reported, no CPU or 4 GB figure).

What the paper says that matters to us

- The input is one 512 x 512 RGB image. The image tokenizer is a DINO ViT with patch size 16 (Table 1, p. 3, verified).
- The model guesses camera extrinsics and intrinsics instead of taking them as input, to cope with in-the-wild images (p. 2, verified).
- A mask loss (BCE, weight 0.05) is said to reduce floaters (p. 3, reported, no ablation in the paper).
- Training used a curated Objaverse subset with rendering that imitates real photos (p. 2, verified).
- Shape metrics (Chamfer distance, F-score) were computed after a brute-force rotation search plus ICP to align predictions to ground truth (p. 4, verified).
- The paper does not state a foreground ratio, a background rule or anything about sketches (verified absence). The 0.85 frame fill is in `run.py`, per `model-quality.md`.

Idea we can use. Silhouette IoU needs a camera, and TripoSR does not return one. Report raw IoU at a fixed canonical view, IoU after bounding box alignment, and the best IoU over a small view grid. The paper's own rotation search is the precedent. Owner Udit for `eval`, Swayam for the renderer. About 2 h. Backlog idea 2.

Idea we can use. Floaters are a known artifact class. Keep the largest connected component in cleanup and log the dropped face share. Owner Swayam. 0.5 h. Backlog idea 9. The paper does not recommend this, it only confirms floaters exist.

Why it may not work for us. The benchmarks are GSO and OmniObject3D, which are clean photos or scans of objects, not sketches. The back side is a model guess.

Citation. Dmitry Tochilkin, David Pankratz, Zexiang Liu, Zixuan Huang, Adam Letts, Yangguang Li, Ding Liang, Christian Laforte, Varun Jampani, Yan-Pei Cao. "TripoSR: Fast 3D Object Reconstruction from a Single Image". arXiv:2403.02151, 2024.

### ControlNet (Adding_Conditional_Control_to_Text-to-Image_Diffusion_Models.pdf)

R5 A4 G3 E3 Rep5. Total 39, tier A.

It adds a trainable copy of the SD encoder blocks that reads a condition image, joined by zero-initialised convolutions.

- Training replaced 50% of prompts with empty strings so the model reads the condition alone (p. 3817, verified).
- With no prompt, adding the control signal to both CFG branches removes classifier-free guidance. Adding it to the conditional branch only gives very strong guidance. The paper proposes CFG resolution weighting (Section 3.4, p. 3817 to 3818, verified, formula ambiguous as printed).
- The sketch user study used 20 unseen hand-drawn sketches and 12 users. ControlNet scored 4.22 for quality and 4.28 for condition fidelity (Table 1, p. 3818, verified).
- A trained ControlNet transferred to three community SD 1.5 checkpoints without retraining (Figure 12, p. 3820, verified, qualitative).
- The paper does not use the term "guess mode", and it does not report a conditioning scale, CFG value or negative prompts in the main text (verified absence).

Idea we can use. Sweep the prompt fallback (empty, the paper's default prompt, our own object template), run an empty-prompt CFG A/B, and sweep the control guidance end. Owner Udit. About 4 h in total. Backlog ideas 3 and 6.

Why it may not work for us. Whether SD 1.5 plus ControlNet fits a 4 GB GPU in fp16 is not in the paper. Measure it. The paper says nothing about object-centred or plain-background images for TripoSR.

Citation. Lvmin Zhang, Anyi Rao, Maneesh Agrawala. "Adding Conditional Control to Text-to-Image Diffusion Models". IEEE/CVF International Conference on Computer Vision (ICCV), pp. 3813 to 3824, 2023.

## Tier B notes

### Sketch2Model (Sketch2Model_View-Aware_3D_Modeling_from_Single_Free-Hand_Sketches.pdf)

R4 A3 G3 E3 Rep5. Total 34, tier B.

It splits the image feature into a view code and a shape code, so the mesh matches the sketch silhouette from a chosen view.

- 2D silhouette IoU is the mesh projected to the ground-truth view against the ground-truth silhouette. The mean is 0.716 for a SoftRas baseline, 0.745 with a predicted view and 0.754 with the true view (Table 4, p. 6015, verified).
- The data is 1,300 hand-drawn sketches over 13 ShapeNet classes (p. 6012, verified).
- The view is two Euler angles, elevation and azimuth, at a fixed camera distance (pp. 6011 to 6012, verified).
- Silhouette normalisation and evaluation resolution are not stated in the main text (unknown).
- The true view instead of the predicted view moves voxel IoU on synthetic sketches from 0.584 to 0.601 (Table 1, p. 6013, verified).

Idea we can use. The three number silhouette report. A raw IoU far below the aligned IoU points to a scale or framing bug in cutout or export. An aligned IoU far below the best-over-grid IoU means TripoSR's camera guess differs from the sketch view. Backlog idea 2.

Why it may not work for us. The network is trained per class. We copy the metric, not the model.

Citation. Song-Hai Zhang, Yuan-Chen Guo, Qing-Wen Gu. "Sketch2Model: View-Aware 3D Modeling from Single Free-Hand Sketches". CVPR, pp. 6008 to 6017, 2021.

### Sketch2Prototype (sketch2prototype-rapid-conceptual-design-exploration-and-prototyping-with-generative-ai.pdf)

R4 A3 G3 E2 Rep4. Total 32, tier B.

It goes sketch to text (GPT-4V), text to image (DALL-E 3), image to 3D (One-2-3-45, DreamGaussian, Shap-E). It compares against raw sketch into Shap-E and ControlNet into Shap-E by eye on two designs and reports no mesh metric (pp. 1992 to 1993, verified).

- ControlNet outputs are "too similar to the users' sketch", which lowers diversity. Image-to-3D meshes are non-smooth, fragmented and sometimes non-manufacturable (pp. 1991, 1996, verified).
- Six prototypes came from four sketches, printed on FDM and SLA machines (pp. 1993 to 1996, verified).

Idea we can use. A ControlNet scale sweep that reports best-of-N IoU and the mean pairwise IoU between candidates as a diversity number. Owner Udit. 3 to 4 h. Backlog idea 4. A mesh readiness report is backlog idea 8.

Why it may not work for us. Its pipeline uses a paid image model and closed GPT-4V. Only the framing and the evaluation gaps carry over.

Citation. Kristen M. Edwards, Brandon Man, Faez Ahmed. "Sketch2Prototype: rapid conceptual design exploration and prototyping with generative AI". International Design Conference DESIGN 2024, Cambridge University Press, 2024. doi 10.1017/pds.2024.201.

### Doodle Your 3D (Doodle_Your_3D_from_Abstract_Freehand_Sketches_to_Precise_3D_Shapes.pdf)

R3 A3 G2 E3 Rep4. Total 28, tier B.

It turns abstract sketches into 3D shapes. It is trained on chairs only (6,755 shapes) and needs 39 to 44 h per stage on an RTX 3060 Ti (pp. 9800, 9802, verified). Abstraction was tested by redrawing renders with 8 to 32 strokes. Over that range the Chamfer distance of a competing method rose from 0.0078 to 0.0241 and Doodle's from 0.0084 to 0.0130 (verified).

Idea we can use. An abstraction ladder stress test. Drop 25, 50 and 75 percent of strokes from our 12 sketches and plot IoU and failure rate against level. Owner Udit. 2 h. Backlog idea 5. It feeds the failure recovery story.

Why it may not work for us. Training is per category, so it cannot run as a stage.

Citation. Hmrishav Bandyopadhyay, Subhadeep Koley, Ayan Das, Ayan Kumar Bhunia, Aneeshan Sain, Pinaki Nath Chowdhury, Tao Xiang, Yi-Zhe Song. "Doodle Your 3D: From Abstract Freehand Sketches to Precise 3D Shapes". CVPR, pp. 9795 to 9805, 2024.

### Sketch-based interaction and modeling, where do we stand (sketch-based-interaction-and-modeling-where-do-we-stand.pdf)

R3 A3 G2 E2 Rep4. Total 27, tier B. Survey.

- "A 2D drawing may have several 3D inflations", and people draw only the visible part, so hidden geometry is inferred (p. 374, verified).
- Industry has a gulf between 2D sketching and 3D modelling, and CAD has a steep learning curve for novices (pp. 371, 381, verified).
- Full tool interoperability needs a file interchange format (p. 382, verified).

Idea we can use. Preprocess robustness test with synthetic paper noise (backlog idea 7). Report material for the problem statement and application sections.

Citation. Alexandra Bonnici, Alican Akman, Gabriel Calleja, Kenneth P. Camilleri, Patrick Fehling, Alfredo Ferreira, Florian Hermuth, Johann Habakuk Israel, Tom Landwehr, Juncheng Liu, Natasha M. J. Padfield, T. Metin Sezgin, Paul L. Rosin. "Sketch-based interaction and modeling: where do we stand?". Journal title and volume are on the first page of the PDF. Check them before the final report.

### SKED (SKED_Sketch-guided_Text-based_3D_Editing.pdf)

R2 A4 G2 E2 Rep2. Total 26, tier B.

It edits a NeRF using multi-view sketches and a text prompt. It defines Intersection-over-Sketch, the share of the sketched region that the generated mask covers. On five samples the mean is 0.8220 with its silhouette loss and 0.0211 without (Table 2, p. 14568, verified). Optimisation takes 30 to 40 minutes on an RTX 3090 (reported in implementation details).

Idea we can use. Enforce sketch fidelity with a mask comparison in the loop. Our version is best-of-N by 2D mask IoU (backlog idea 1).

Why it may not work for us. Optimisation based and needs a NeRF.

Citation. Aryan Mikaeili, Or Perel, Mehdi Safaee, Daniel Cohen-Or, Ali Mahdavi-Amiri. "SKED: Sketch-guided Text-based 3D Editing". ICCV, pp. 14561 to 14570, 2023.

### AI-assisted game development case study (Empirical insights into AI-assisted game development_ A case stud.pdf)

R3 A3 G2 E1 Rep4. Total 26, tier B.

It reports that AI-generated meshes had excessive polygon counts and poor topology and needed retopology. Optimised game models are about 20,000 polygons or 40,000 triangles. Target formats are OBJ, GLTF and GLB (pp. 2, 5, 12 to 13, verified). The study is anecdotal: four subjects and no statistics (pp. 5, 9).

Idea we can use. Export a mesh readiness report (triangle count, components, watertight) and test a 40,000 triangle decimation (backlog idea 8).

Citation. Andrew Begemann, James Hutson. "Empirical insights into AI-assisted game development: A case study on the integration of generative AI tools in creative pipelines". Metaverse 5(2), 2568, 2024. doi 10.54517/m.v5i2.2568.

## Tier C notes

Conditioning

- Ctrl-X (24). Training-free structure and appearance control with SDXL. 10.91 s and 11.51 GiB peak on an H100 (Table 1, p. 8). Its control schedule (tau_s 0.3 to 0.5 for sparse conditions, p. 14 to 16) is the motivation for backlog idea 6. Lin, Mo, Klingher, Mu, Zhou. NeurIPS 2024. arXiv id is not on the first page.
- FreeControl (19). Training-free, 176.31 s per image on an A6000 (Table 2, p. 7472). Breaks the 100 s limit. Mo, Mu, Lin, Liu, Guan, Li, Zhou. CVPR 2024, pp. 7465 onward.
- OmniControlNet (14). Dual-stage integration with extra models. Scribble binarised at 127 (p. 7438, reported). Wang, Xu, Zhang, Chen, Sha, Wang, Tu. CVPR Workshops 2024, pp. 7436 to 7443.

Sketch to 3D

- SketchDream (19). Sketch-based text-to-3D and editing, 1.0 to 1.3 h per example on an A100 (p. 44:8). It says ControlNet plus image-to-3D gives distorted unseen views and fuzzy back textures (p. 44:2). That is our known weakness. Liu, Fu, Lai, Gao. ACM TOG 43(4), Article 44, 2024.
- Control3D (23). Sketch-controlled text-to-3D by optimisation. Chen, Pan, Li, Yao, Mei. ACM MM 2023, pp. 1148 onward.
- Rapid 3D from intuitive 3D input (18). VR sketch input. Three designers modelled nine shapes in 869.2 s with CAD and 89.4 s with the tool, including 7.3 s of inference on an A100 (Table 5, pp. 12560 to 12561). Gives a timing and rating study design (backlog idea 10). Zhang, Ding, Chen, Yu, Zang, Li, Peng, Sun. CVPR 2024, pp. 12554 onward.
- LAS-Diffusion (22, abstract only). Two stage occupancy then SDF diffusion with view-aware local attention. Accepts freehand sketches and category conditions. Zheng, Pan, Wang, Tong, Liu, Shum. ACM TOG, Article 91, August 2023, doi 10.1145/3592103.
- CymbaDiff (2). Urban scene generation. Out of scope. Liang, Miao, Wang, Akhtar, Vice, Mian. NeurIPS 2025.

Image to 3D (abstract only)

- Tailor3D (23). Edits the front view, generates the back view with multi-view diffusion, then fuses both with a dual-sided LRM. Each step is "just 5 seconds" (reported, hardware not captured). Tempting for the hidden side, but it needs a multi-view diffusion model and its own LRM weights. Its licence and CPU path are unknown. A cheaper test is a second SD sample as a pseudo back view, which TripoSR cannot consume. Not tried. Qi, Yang, Zhang, Xing, Wu, Wu, Lin, Liu, Wang, Zhao. arXiv:2407.06191, 2024.
- Hunyuan3D 1.0 (18). Multi-view diffusion in about 4 s, then reconstruction in about 7 s. The lite model takes about 10 s and the standard about 25 s, plus about 15 s for texture baking (reported, hardware not captured). It admits a flat top when the 0-elevation orbit lacks top-view information (reported). Ruled out by D18. Tencent Hunyuan3D team. arXiv:2411.02293, 2024.
- Direct3D (18). Native 3D latent diffusion with a triplane VAE and a diffusion transformer. Wu, Lin, Zeng, Zhang, Xu, Torr, Cao, Yao. NeurIPS 2024.
- SilNet (17). Learns 3D shape from a silhouette prediction proxy task, evaluated on ShapeNet silhouettes in new viewpoints. Wiles, Zisserman. arXiv:1711.07888, 2017.
- Learning view priors (15). Trains a discriminator on observed against unobserved views to fix unseen-view shapes. Training-time only. Kato, Harada. CVPR 2019.
- MapAnything (6). Multi-view metric scene reconstruction. Keetha et al. 3DV 2026.

Surveys

- Li et al., "Generative AI meets 3D: A Survey on Text-to-3D in AIGC Era", arXiv:2305.06131 (v4, Oct 2024). Covers fidelity, efficiency, consistency, controllability, diversity and applicability.
- Liu et al., "A Comprehensive Survey on 3D Content Generation", arXiv:2402.01166, 2024. Three families: 3D native, 2D prior-based and hybrid generative methods. About 60 papers. Our pipeline is a 2D prior feeding a 3D native feed-forward model, so it is a hybrid.
- Jiang, "A Survey On Text-to-3D Contents Generation In The Wild", arXiv:2405.09431, 2024. Covers datasets, metrics, feed-forward against optimisation-based generation.
- Lee, Savva, Chang, "Text-to-3D Shape Generation", Computer Graphics Forum 43(2), Eurographics 2024 STAR. Three families by data use: paired text, unpaired text and no 3D data. The text extracts poorly, so it was read from OCR of page 1 only.
- Xu, Hospedales, Yin, Song, Xiang, Wang, "Deep Learning for Free-Hand Sketch: A Survey", IEEE TPAMI 45(1), 2023. Sketches are abstract, sparse and varied in style, and sketch-to-3D is "relatively under-studied" (pp. 287, 300). There is no accepted automatic metric for sketch simplification (p. 295).
