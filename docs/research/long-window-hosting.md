# Long window hosting

Research date 31 Oct 2026. Question. How do we keep a public demo link usable for 7 to 10 days after the 1 Nov deadline, with no always-on GPU and about 1,500 to 2,000 INR of extra cash. Nothing here was signed up for or run. INR figures use 90 INR per USD.

This file builds on `cloud-gpu-options.md` and `aws-gpu-optional.md`. It does not repeat them.

## Labels

- **verified** means I read it on an official docs or pricing page today.
- **reported** means a forum post, a search summary or a third party said it.
- **unknown** means I found no primary source. Any number next to it is an estimate.

## Findings that change the plan

1. A free Hugging Face account cannot create a Gradio or Docker Space on CPU. Only Static Spaces are free to everyone. Free accounts get one exception, up to 2 ZeroGPU Spaces. Verified. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview)
2. ZeroGPU quota belongs to the visitor, not to us. Anonymous visitors get 2 GPU minutes a day. Free accounts get 5. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu) A judge who runs 5 to 20 generations will hit that wall on the first visit.
3. ZeroGPU lists Python 3.10.13 and 3.12.12 only. Our decision D8 pins 3.11. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
4. Modal can run a Gradio UI on a cheap CPU container and call a separate GPU function. Both scale to zero. Verified. [Gradio on Modal](https://www.gradio.app/guides/deploying-gradio-with-modal)
5. AWS credits are per account. One g4dn.xlarge running 10 days costs more than one account's $100.

## 1. Hugging Face ZeroGPU Spaces

- Free personal accounts in good standing can host up to 2 ZeroGPU Spaces. Good standing means a verified email and an account older than 30 days. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
- PRO is not required to host one. PRO lifts the cap to 10 Spaces and costs $9 a month. Verified. [pricing](https://huggingface.co/pricing)
- A teammate who signs up today fails the 30 day rule. Use an older account. Check this in the first 10 minutes.
- Hardware is half an RTX Pro 6000 Blackwell with 48 GB VRAM by default. `size="xlarge"` gives 96 GB and costs 2x quota. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
- Daily quota by visitor type. Anonymous 2 min, free account 5 min, PRO 40 min. It resets 24 hours after first GPU use. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
- At 30 to 90 s per generation, that is 1 to 4 runs a day anonymous and 3 to 10 runs a day for a free login.
- A separate cap of 3 runs a day for free users was reported by a forum contributor in April 2026. It is not in the docs. Reported. [forum thread](https://discuss.huggingface.co/t/what-is-the-free-zerogpu-quota-for-1-space/178610)
- The default call length is 60 s. `@spaces.GPU(duration=120)` is the documented way to raise it. The docs name no maximum. A forum user says 120 s is the official maximum and 240 s sometimes works. Reported. [forum thread](https://discuss.huggingface.co/t/zerogpu-illegal-duration-the-requested-gpu-duration-300s-is-larger-than-the-maximum-allowed/140849)
- Supported versions. Gradio 4 and up, PyTorch 2.8.0 to 2.13.0, Python 3.10.13 or 3.12.12. Gradio SDK only. `torch.compile` is not supported. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
- Decorator usage. Import `spaces`, load models with `.to("cuda")` at module level, and decorate only the GPU function with `@spaces.GPU`. The decorator does nothing outside ZeroGPU, so the same file runs locally. Dynamic duration takes a callable with the same arguments. Verified. [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)
- Custom CUDA extension builds. Unknown. The docs say compatibility is "limited" and nothing on the build environment. A search found one report that TRELLIS.2 setup scripts fail without a visible GPU. Reported. [HN thread](https://hn.nuxt.dev/item/47828896) Stay with pure Python or prebuilt wheels. D9 already drops `torchmcubes`. Hunyuan3D-2mini texture needs compiled kernels, so skip texture there.
- Dependencies come from `requirements.txt`, `packages.txt` and `pre-requirements.txt`. Verified. [dependencies](https://huggingface.co/docs/hub/spaces-dependencies)
- Weights. `preload_from_hub` in the README front matter downloads Hub files at build time. Verified. [config reference](https://huggingface.co/docs/hub/spaces-config-reference) Disk is ephemeral and the persistent storage feature is gone. Verified. [storage](https://huggingface.co/docs/hub/spaces-storage) Mirror weights to a Hub model repo we own, or use the upstream repos directly.
- Size limits. No per-repo cap. Files under 200 GB recommended, 500 GB hard. Free public storage is "best effort", with a request to be responsible beyond a few GB. Verified. [storage limits](https://huggingface.co/docs/hub/storage-limits) Our weights are under 10 GB.
- Deploy from GitHub with `huggingface/hub-sync@v0.3.0` and an `HF_TOKEN` secret. It mirrors files with `hf upload` and skips `.github/`. Verified. [GitHub Actions](https://huggingface.co/docs/hub/spaces-github-actions) The Space README needs YAML front matter (`sdk: gradio`, `app_file`, `python_version`). Keep a `space/` folder with its own README and `app.py`, and upload only that folder.
- ZeroGPU hardware is picked in the Space settings. `suggested_hardware` does not assign it. Verified. [config reference](https://huggingface.co/docs/hub/spaces-config-reference)
- Sleep. Free hardware Spaces are suspended after about two days unused and restart when a visitor arrives. Verified for CPU Basic. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus) Whether ZeroGPU follows the same rule and how long the restart takes is unknown.
- `gr.Model3D` accepts `.glb`. Verified. [Model3D docs](https://www.gradio.app/docs/gradio/model3d) Public ZeroGPU Spaces that output a GLB into `gr.Model3D` exist. Reported. [example app](https://huggingface.co/CreadtoML2/text-to-3d/raw/main/app.py)
- Cost for 10 days. 0 INR. 810 INR if we want PRO for the 40 minute quota.

## 2. Hugging Face free CPU Spaces as a lite tier

- CPU Basic is 2 vCPU, 16 GB RAM, 50 GB ephemeral disk, free to run. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus)
- Creating a Gradio or Docker Space on it needs PRO, $9 a month. Verified. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview) So a free CPU Gradio lite tier costs 810 INR, not 0.
- A Static Space is free for everyone. Verified. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview) It can serve HTML and JavaScript with pre-made `.glb` samples in a viewer, plus links to the live paths. That is our zero cost "there is always a link" page.
- Free hardware sleeps after about 48 hours of no visits and wakes on the next visit. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus) Wake time is unknown. Estimate 1 to 3 minutes for a torch app.
- Real pipeline on 2 vCPU. Unknown. Estimate several minutes per model with SD skipped. Fine as a "lite mode" proof, bad as a judge experience.

## 3. Hugging Face paid GPU Spaces with a sleep time

- Prices per hour. T4 small $0.40, T4 medium $0.60, L4 $0.80, A10G small $1.00. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus)
- Creating the Space needs PRO ($9). Verified. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview)
- Billing is by the minute while the Space is `Starting` or `Running`, used or not. Not billed while building, asleep or paused. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus)
- A sleep time stops the Space when idle. A new visitor restarts it. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus) The visitor sees the Space's starting page while it boots. Boot plus model load time is unknown. Estimate 2 to 5 minutes.
- 30 active hours on T4 small is $12 (1,080 INR). On L4 it is $24 (2,160 INR). Add PRO $9 (810 INR). Totals are 1,890 INR and 2,970 INR.
- Community GPU grants exist and can be requested from Space settings. No approval promise or time. Verified. [GPU docs](https://huggingface.co/docs/hub/spaces-gpus)
- This is plain Gradio on a normal GPU, so Python 3.11, any torch and compiled extensions work. It is the most code-compatible host.

## 4. Modal

- Starter plan has $30 of free compute credit a month, 100 containers, 10 GPU concurrency, and limited web functions. Verified. [pricing](https://modal.com/pricing)
- Card. Modal's billing page says a payment method must be on file to use Modal. Verified. [billing](https://modal.com/docs/guide/billing) Two third-party pages say no card is needed. One says it is required. Reported. [search results](https://aicreditmart.com/ai-credits-providers/modal-free-tier-how-to-get-30-month-in-compute-credits-2026/) Plan on using the Visa or Mastercard.
- Prices per second. T4 $0.000164, L4 $0.000222, A10 $0.000306, L40S $0.000542. CPU $0.0000131 per core and memory $0.00000222 per GiB. Verified. [pricing](https://modal.com/pricing)
- Scale to zero is the default. `scaledown_window` defaults to 60 s and ranges from 2 s to 20 min. `min_containers` sets a floor. Verified. [cold start guide](https://modal.com/docs/guide/cold-start)
- Cold start. Containers boot in about 1 s. Loading weights is the real delay. Keep weights in a Volume or the image. Verified. [cold start guide](https://modal.com/docs/guide/cold-start) CPU memory snapshots start 3 to 10x faster for import-heavy code and need `modal deploy`. GPU snapshots are alpha and do not speed weight loading. Verified. [memory snapshots](https://modal.com/docs/guide/memory-snapshot) Our cold start with SD1.5, ControlNet and TripoSR from a Volume is unknown. Estimate 30 to 60 s.
- Gradio hosting. Return `mount_gradio_app(app=FastAPI(), blocks=demo, path="/")` from an `@modal.asgi_app()` function. Set `max_containers=1` and `@modal.concurrent(max_inputs=100)` because Gradio needs sticky sessions. Put GPU work in a separate Modal function so it scales on its own while the UI sits on a CPU container. Verified. [Gradio guide](https://www.gradio.app/guides/deploying-gradio-with-modal)
- Web endpoints cut a request at 150 s with a 303 redirect to a result URL. The redirect fails for CORS requests. Longer jobs should use a spawn and poll pattern. Verified. [web endpoint timeouts](https://modal.com/docs/guide/webhook-timeouts) WebSockets work on ASGI apps. Verified. [webhooks](https://modal.com/docs/guide/webhooks)
- `modal deploy` makes a persistent app. `modal serve` is temporary. Verified. [webhooks](https://modal.com/docs/guide/webhooks)
- Budgets exist at workspace and environment level. Hard or soft behaviour is unknown. Verified existence. [billing](https://modal.com/docs/guide/billing)
- Cost of 200 generations on L4. GPU time is 6,000 s to 18,000 s, so $1.33 to $4.00. Add cold starts and idle tail for 60 sessions at 120 s each, $1.60. Total about $3 to $5.60, or 270 to 500 INR. On T4 it is about $2.2 to $4.1. All inside the $30 credit.
- Holding one L4 warm for the 30 judging hours costs $24 (2,160 INR of credit). Possible, but it eats most of the month's credit.
- Holding one L4 warm for all 10 days costs $192. Do not.

## 5. RunPod Serverless versus pods

- Flex workers scale to zero and bill per second, rounded up, from worker start to full stop, including cold start. Default idle timeout 5 s. Verified. [serverless pricing](https://docs.runpod.io/serverless/pricing)
- Listed serverless rates per hour. 16 GB tier $0.58, 24 GB tier (L4, A5000, 3090) $0.75, RTX 4090 $1.34, 48 GB tier $1.75. The page does not say whether these are flex or active rates. Verified list, unknown mode. [RunPod pricing](https://www.runpod.io/pricing)
- Pod rates per hour. L4 $0.44 community, $0.59 secure. Verified. [RunPod pricing](https://www.runpod.io/pricing) Stopped pod volume disk is $0.20 per GB a month. Verified. [RunPod pricing](https://www.runpod.io/pricing)
- Queue-based endpoints are API only. Clients call `/run`, `/runsync` and `/status` against a handler function. Verified. [serverless overview](https://docs.runpod.io/serverless/overview)
- Load balancing endpoints accept FastAPI or Flask apps with custom paths. Processing timeout 5.5 min, 30 MB payload, health check on `/ping`, "no workers available" errors during cold start. WebSockets and Gradio are not mentioned. Verified for limits, unknown for Gradio. [load balancing](https://docs.runpod.io/serverless/load-balancing/overview)
- Cold start time is unknown. FlashBoot and model caching are named as fixes with no numbers. Verified. [serverless overview](https://docs.runpod.io/serverless/overview)
- Verdict. Serverless is an API, not a UI host. It needs a separate frontend, and its API key must stay server side.
- 200 generations on the 24 GB tier. About $2.75 to $5.25, or 250 to 470 INR. The $10 minimum prepaid deposit (900 INR) is the cash needed. No free credit found.
- A pod running 24/7 for 10 days. L4 secure $141.60 (12,740 INR), community $105.60 (9,500 INR). A stopped pod does not serve a link. 30 hours on secure L4 plus 50 GB volume is about $21 (1,890 INR), but judges arrive at unknown times.

## 6. AWS g4dn or g5 on credits

- g4dn.xlarge is 1 T4, 4 vCPU, 16 GiB. Verified. [AWS G4](https://aws.amazon.com/ec2/instance-types/g4/)
- AWS pages do not list the hourly price. A third-party table shows $0.526 an hour. Reported, region not stated. [Vantage](https://instances.vantage.sh/aws/ec2/g4dn.xlarge?region=ap-south-1) Mumbai price and g5 price are unknown.
- Always on for 10 days is 240 h x $0.526 = $126, plus disk and public IPv4. About $131, or 11,800 INR.
- One account's $100 covers about 190 hours, or 7.9 days. It does not cover 10 days.
- Three accounts hold $300 on paper. Credits do not move between accounts. The instance runs in one account. Moving it to a second account midway means copying an AMI and redoing the IP and URL. Not worth it.
- On for 6 hours a day for 10 days is 60 h x $0.526 = $32, plus disk, about $35 (3,150 INR). One account covers it.
- A schedule needs someone or a scheduled job (EventBridge Scheduler or a cron on a laptop) to start and stop it. Judges outside the window see a dead link.
- Blockers from the earlier guides stand. G and VT quota starts at 0, the Free plan needs a Paid upgrade, and AWS publishes no approval time. Verified. [EC2 quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html)
- Verdict. Credits make it cash-free, not risk-free. It is a bad first-two-hours bet and a good "free tier" if the quota arrives. Start the request now in parallel and ignore it if it stalls.

## 7. Other options with a public price

- Lightning AI. Free plan gives 30 credits to start (5 on signup, 25 with a card). T4 $0.55 an hour, L4 $0.79. No card needed, phone required. Free Studios must restart every 4 hours. Public ports on free Studios are not stated. Verified. [pricing](https://lightning.ai/pricing) Not suitable for a 10 day link.
- Koyeb. L4 $0.70 an hour, L40S $1.20, scale to zero. Pro plan $29 a month includes $10 of compute. Card, GPU gating and India region not stated. Verified prices. [pricing](https://www.koyeb.com/pricing) Estimate $32 for the window, 2,900 INR. Over budget.
- Beam. RTX 4090 serverless at $0.000192 per s. Developer plan $20 a month with $20 credits. No free tier listed, Gradio not mentioned. Verified prices. [pricing](https://www.beam.cloud/pricing) Estimate 2,100 INR for the window.
- Cerebrium. The page lists T4, L4 and A10 prices identical to Modal's, Hobby plan free plus compute, credit amount and web endpoints not stated. Verified page, suspicious numbers. [pricing](https://www.cerebrium.ai/pricing) Skip.
- Fly.io. Says it is "scaling back our GPU ambitions". Existing machines keep running. Verified. [Fly blog](https://fly.io/blog/wrong-about-gpu/) Skip.

## 8. Hybrid design

The idea. A free always-up lite page plus an on-demand GPU path behind a button.

What I found.

- The lite page can be a free Static Space. A CPU Gradio lite costs 810 INR for PRO.
- A static page can show 12 pre-made `.glb` samples and link out to the GPU path. A link is realistic in a day.
- A button that calls the GPU from the static page needs CORS, an exposed access code in JavaScript and polling in JS. That is extra work for no gain over a link.
- Modal already behaves like a lite page. The UI runs on a CPU container that boots in seconds. The GPU spins up only when a judge presses Generate. So Modal alone is a hybrid.
- ZeroGPU is the free GPU path. Its quota is the weak spot. A PRO owner's token passed to the Space through `gradio_client` might bill the owner's 40 minutes instead of the visitor's. I found no primary source on that. Unknown. Do not count on it.

Effort in a 24 hour hackathon.

- Static sample page. 1 hour.
- Modal deploy of the existing pipeline with a polling job API. 4 to 6 hours once the pipeline works locally.
- ZeroGPU port. 2 to 4 hours. Decorator, Python 3.12, torch 2.8 or newer, no compiled kernels.
- Do the ZeroGPU port only after the core path is green and Modal is up.

## Decision table

Costs are for the 10 day window, at 90 INR per USD. Setup hours and first-two-hours risk are my estimates.

| Option | 10 day cost (INR) | Cash up front (INR) | Setup (h) | Risk in first 2 h | Judge friction |
| --- | --- | --- | --- | --- | --- |
| Modal Gradio, UI on CPU, GPU function on L4 | 270 to 500, covered by $30 credit | 0 plus card on file | 4 to 6 | Medium. Card, sticky sessions, 150 s limit | Low. Access code, first run 30 to 90 s slower |
| HF ZeroGPU Space (free host) | 0 | 0 | 3 to 5 | Medium. 30 day account rule, Python 3.10 or 3.12, torch 2.8+ | High. 2 or 5 GPU min a day per visitor |
| HF Static Space samples page | 0 | 0 | 1 | Very low | Low. No live generation |
| HF CPU Gradio lite (PRO) | 810 | 810 | 2 | Low | Medium. Slow CPU run |
| HF T4 small, sleep time, 30 active h (PRO) | 1,890 | 1,890 | 3 | Low to medium. Card, build 10 to 30 min | Medium. 2 to 5 min wake from sleep |
| HF L4, sleep time, 30 active h (PRO) | 2,970 | 2,970 | 3 | Low to medium | Medium. Same wake time |
| RunPod Serverless plus separate frontend | 250 to 470 | 900 | 5 to 7 | Medium to high. Needs a frontend host | Low once built |
| RunPod pod L4 secure, 30 scheduled h | 1,890 | 1,890 | 2 | Medium. Stop and start, URL | High. Dead outside windows |
| RunPod pod L4 secure, 24/7 | 12,740 | 12,740 | 2 | Medium | Low, but unaffordable |
| AWS g4dn.xlarge, 24/7 | 11,800 in credits, over one account | 0 | 3 to 6 plus quota wait | Very high. Quota 0, plan upgrade | Low if it works |
| AWS g4dn.xlarge, 6 h a day | 3,150 in credits | 0 | 3 to 6 plus quota wait | Very high | High. Dead off schedule |
| Koyeb or Beam L4 or 4090 | 2,100 to 2,900 | 2,100 to 2,900 | 4 to 6 | Medium. Unknowns on card and GPU access | Low |

## What to build in the app

1. Job API with polling. Submit returns a job id, a poll call returns status and the `.glb` path. Modal cuts requests at 150 s and RunPod's proxy at 100 s. Use `.spawn()` on Modal.
2. Access code. One throwaway code in an env var, checked server side before any GPU call. Never commit a cloud key.
3. Queue and caps. `max_containers` of 1 or 2, a Gradio queue with a visible position, a per-code daily cap such as 60 generations, and a Modal workspace budget. This protects the $30 credit.
4. Warm-up ping. When the page loads, fire a non-blocking call that starts the GPU container and loads models while the judge draws. Show "GPU waking, up to 60 s".
5. Daily keep-alive. A GitHub Actions cron that does one GET on the Space URL every 24 hours, so a free Space does not hit the 48 hour sleep. Skip if the Space is on Modal.
6. Static fallback page. 12 sample sketches, their `.glb` files and links to every live path. This page stays up with no GPU.
7. Backend switch. The `S2S_BACKEND=remote` setting from `PLAN.md` picks Modal or local. Wrap `@spaces.GPU` so the same `app.py` runs on ZeroGPU and elsewhere.
8. Shutdown banner. A `SHUTDOWN_DATE` env var shown on the page, extendable without a redeploy.
9. Timing log. Write per-stage time and VRAM to a file for the README.

## Recommendation

1. Primary host is Modal. Gradio UI on a CPU container, SD1.5 plus TripoSR on a separate L4 function, scale to zero, access code, workspace budget. About 270 to 500 INR of usage, inside the free credit.
2. Backup is a free ZeroGPU Space from an HF account older than 30 days, plus a free Static Space page with sample `.glb` files and every link. Check the account age in the first 10 minutes.
3. If both stall and Udit's card works, buy PRO and run an HF T4 Space with a sleep time for about 1,890 INR. That uses the whole cash cap.
4. Skip AWS as a host, skip a RunPod pod as a host and use RunPod serverless only if Modal's card fails. Start the AWS quota request anyway and drop it if it stalls.
5. Build the job API, access code, queue caps and warm-up ping first. The static fallback page comes second and takes an hour.
6. Put all three links in the submission, label which one is primary, and state the quota limits of the ZeroGPU link.
