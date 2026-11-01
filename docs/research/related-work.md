# Related work

Draft notes for the report, 31 Oct 2026. Each citation was checked against the first page of the PDF. Papers marked "abstract only" were not read past the first page, so no numbers from them are used. Page numbers are in `papers-review.md`.

## Feed-forward image-to-3D

Early image-to-3D work used score distillation, which optimises a 3D model against a 2D diffusion model and takes a long time per object. Feed-forward reconstruction models skip that loop. TripoSR [1] builds on the Large Reconstruction Model and maps one image to a triplane neural radiance field with a transformer. It takes about 0.5 s on an A100, according to its authors, and is released under the MIT licence. It guesses the camera instead of taking it as input, and it trains on a curated Objaverse subset. The paper evaluates on GSO and OmniObject3D, two sets of clean object images, and does not test sketches. Other systems first generate several views with a diffusion model and then reconstruct. Hunyuan3D 1.0 [2] follows that route and reports 10 to 25 s per mesh. Direct3D [3] instead trains a diffusion transformer directly on 3D latents. We use TripoSR because it is open, ungated and the only candidate with a believable CPU path.

## Sketch-conditioned 3D generation

Sketch2Model [4] reconstructs meshes from free-hand sketches and handles the view ambiguity with a separate view code. It measures sketch fidelity as the silhouette IoU between the projected mesh and the sketch silhouette, and we use the same idea. Doodle Your 3D [5] targets abstract sketches and tests robustness by redrawing shapes with fewer strokes. LAS-Diffusion [6] generates signed distance fields from sketches. These systems train on one or a few categories. SKED [7], SketchDream [8] and Control3D [9] steer NeRF-based text-to-3D generation with sketches and take from 30 minutes to over an hour per object. Rapid 3D [10] reconstructs from VR sketches. Our approach avoids per-category training and per-object optimisation by combining a 2D sketch-conditioned image model with a feed-forward reconstruction model. SketchDream's authors note the weakness of that combination: images lifted from ControlNet output give distorted geometry in unseen views and fuzzy back textures [8].

## Conditioning image diffusion on sketches

ControlNet [11] adds a trainable copy of the Stable Diffusion encoder that reads a condition image such as a scribble. It was trained with half of the prompts empty, so it works without text. In its user study, 12 users rated results from 20 unseen hand-drawn sketches at 4.22 for quality and 4.28 for condition fidelity on a 5 point scale. Training-free alternatives such as Ctrl-X [12] and FreeControl [13] avoid training but use far more compute. FreeControl needs 176.31 s per image on an A6000. OmniControlNet [14] combines several conditions with extra models. We use ControlNet because the training-free methods break the 100 s hosted limit.

## Sketch-to-prototype systems and application

Sketch2Prototype [15] is the closest product. It converts a sketch to text, to an image and then to 3D, and prints the result. The authors report no mesh metric and note that ControlNet outputs are very close to the sketch and that image-to-3D meshes are often fragmented. Surveys describe the same gap. A 2D drawing may have several 3D inflations, people draw only the visible side [16], and sketches are abstract and sparse with no accepted automatic simplification metric [17]. A case study on game development reports that AI meshes arrived with high polygon counts and poor topology, against about 40,000 triangles for optimised game models [18]. We therefore export `.glb` and `.obj` and report a mesh validity check.

## Surveys

Surveys on text-to-3D and 3D content generation [19, 20, 21, 22] organise the field into 3D native, 2D prior-based and hybrid methods, or into families by how much 3D and paired text data they use. In the taxonomy of [20], our pipeline is a hybrid. A 2D image model supplies the prior and a 3D native feed-forward model reconstructs the object.

## References

[1] Dmitry Tochilkin, David Pankratz, Zexiang Liu, Zixuan Huang, Adam Letts, Yangguang Li, Ding Liang, Christian Laforte, Varun Jampani, Yan-Pei Cao. TripoSR: Fast 3D Object Reconstruction from a Single Image. arXiv:2403.02151, 2024.

[2] Tencent Hunyuan3D team. Hunyuan3D 1.0: A Unified Framework for Text-to-3D and Image-to-3D Generation. arXiv:2411.02293, 2024. Abstract only.

[3] Shuang Wu, Youtian Lin, Yifei Zeng, Feihu Zhang, Jingxi Xu, Philip Torr, Xun Cao, Yao Yao. Direct3D: Scalable Image-to-3D Generation via 3D Latent Diffusion Transformer. NeurIPS 2024. Abstract only.

[4] Song-Hai Zhang, Yuan-Chen Guo, Qing-Wen Gu. Sketch2Model: View-Aware 3D Modeling from Single Free-Hand Sketches. CVPR 2021, pp. 6008 to 6017.

[5] Hmrishav Bandyopadhyay, Subhadeep Koley, Ayan Das, Ayan Kumar Bhunia, Aneeshan Sain, Pinaki Nath Chowdhury, Tao Xiang, Yi-Zhe Song. Doodle Your 3D: From Abstract Freehand Sketches to Precise 3D Shapes. CVPR 2024, pp. 9795 to 9805.

[6] Xin-Yang Zheng, Hao Pan, Peng-Shuai Wang, Xin Tong, Yang Liu, Heung-Yeung Shum. Locally Attentional SDF Diffusion for Controllable 3D Shape Generation. ACM Transactions on Graphics, Article 91, August 2023. doi 10.1145/3592103. Abstract only.

[7] Aryan Mikaeili, Or Perel, Mehdi Safaee, Daniel Cohen-Or, Ali Mahdavi-Amiri. SKED: Sketch-guided Text-based 3D Editing. ICCV 2023, pp. 14561 to 14570.

[8] Feng-Lin Liu, Hongbo Fu, Yu-Kun Lai, Lin Gao. SketchDream: Sketch-based Text-to-3D Generation and Editing. ACM Transactions on Graphics 43(4), Article 44, 2024.

[9] Yang Chen, Yingwei Pan, Yehao Li, Ting Yao, Tao Mei. Control3D: Towards Controllable Text-to-3D Generation. ACM Multimedia 2023, pp. 1148 onward. doi 10.1145/3581783.3612489.

[10] Shangzhan Zhang, Chaotao Ding, Tianrun Chen, Chunan Yu, Ying Zang, Zejian Li, Sida Peng, Lingyun Sun. Rapid 3D Model Generation with Intuitive 3D Input. CVPR 2024, pp. 12554 onward.

[11] Lvmin Zhang, Anyi Rao, Maneesh Agrawala. Adding Conditional Control to Text-to-Image Diffusion Models. ICCV 2023, pp. 3813 to 3824.

[12] Kuan Heng Lin, Sicheng Mo, Ben Klingher, Fangzhou Mu, Bolei Zhou. Ctrl-X: Controlling Structure and Appearance for Text-To-Image Generation Without Guidance. NeurIPS 2024.

[13] Sicheng Mo, Fangzhou Mu, Kuan Heng Lin, Yanli Liu, Bochen Guan, Yin Li, Bolei Zhou. FreeControl: Training-Free Spatial Control of Any Text-to-Image Diffusion Model with Any Condition. CVPR 2024, pp. 7465 onward.

[14] Yilin Wang, Haiyang Xu, Xiang Zhang, Zeyuan Chen, Zhizhou Sha, Zirui Wang, Zhuowen Tu. OmniControlNet: Dual-stage Integration for Conditional Image Generation. CVPR Workshops 2024, pp. 7436 to 7443.

[15] Kristen M. Edwards, Brandon Man, Faez Ahmed. Sketch2Prototype: rapid conceptual design exploration and prototyping with generative AI. International Design Conference DESIGN 2024. doi 10.1017/pds.2024.201.

[16] Alexandra Bonnici, Alican Akman, Gabriel Calleja, Kenneth P. Camilleri, Patrick Fehling, Alfredo Ferreira, Florian Hermuth, Johann Habakuk Israel, Tom Landwehr, Juncheng Liu, Natasha M. J. Padfield, T. Metin Sezgin, Paul L. Rosin. Sketch-based interaction and modeling: where do we stand? Journal and volume to be filled from the PDF before the final report.

[17] Peng Xu, Timothy M. Hospedales, Qiyue Yin, Yi-Zhe Song, Tao Xiang, Liang Wang. Deep Learning for Free-Hand Sketch: A Survey. IEEE TPAMI 45(1), 2023. doi 10.1109/TPAMI.2022.3148853.

[18] Andrew Begemann, James Hutson. Empirical insights into AI-assisted game development: A case study on the integration of generative AI tools in creative pipelines. Metaverse 5(2), 2568, 2024. doi 10.54517/m.v5i2.2568.

[19] Chenghao Li, Chaoning Zhang, Joseph Cho, Atish Waghwase, Lik-Hang Lee, Francois Rameau, Yang Yang, Sung-Ho Bae, Choong Seon Hong. Generative AI meets 3D: A Survey on Text-to-3D in AIGC Era. arXiv:2305.06131, 2024. Abstract only.

[20] Jian Liu, Xiaoshui Huang, Tianyu Huang, Lu Chen, Yuenan Hou, Shixiang Tang, Ziwei Liu, Wanli Ouyang, Wangmeng Zuo, Junjun Jiang, Xianming Liu. A Comprehensive Survey on 3D Content Generation. arXiv:2402.01166, 2024. Abstract only.

[21] Chenhan Jiang. A Survey On Text-to-3D Contents Generation In The Wild. arXiv:2405.09431, 2024. Abstract only.

[22] H. Lee, M. Savva, A. X. Chang. Text-to-3D Shape Generation. Computer Graphics Forum 43(2), Eurographics 2024 State of the Art Report. First page only.
