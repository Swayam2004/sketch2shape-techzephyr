# Cloud GPU options

> Status note, 31 Oct 15:30. Judging is expected to last 5 to 6 days, which changed the demo plan. `docs/research/long-window-hosting.md` and `CONTEXT.md` D15 now set the hosting order. The dev GPU advice here still holds.

Research date 31 Oct 2026, during the hackathon. Scope is a shared dev GPU, a judge demo endpoint and a cheap fallback for the pipeline in `docs/PLAN.md`. Nothing here was signed up for or run. INR figures use an assumed 90 INR per USD. Check the live rate.

## How to read the labels

- **verified** means I read it on an official pricing, docs or quota page today.
- **reported** means a search summary of an official page, a forum post or a third party said it. I did not read the primary page in full.
- **unknown** means no primary source found. Any number next to it is an estimate.

Pages that failed to load for me were the Oracle free tier page (403), the AWS Knowledge Center quota article (403) and the Kaggle docs (title only). Kaggle, Oracle and Colab pricing therefore rest on weaker evidence.

## Findings that change the plan

1. AWS gives new accounts 0 vCPUs for G and VT instances, on demand and spot ([quota page](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html), verified). Standard instances get 5. A g4dn.xlarge has 4 vCPUs ([AWS](https://aws.amazon.com/ec2/instance-types/g4/), verified), so you must request at least 4. AWS publishes no approval time ([builder.aws.com guide](https://builder.aws.com/content/2vYKRds70ZRnfgrW7Jk9Nomar7U/getting-started-with-gpu-infrastructure-on-aws-practical-tips-for-obtaining-gpu-instances), verified absence). AWS is a bad first-hour bet.
2. GCP blocks GPUs on the $300 free trial. You must upgrade to a paid billing account, which ends the trial ([GCP free features](https://docs.cloud.google.com/free/docs/free-cloud-features), verified). GPU quota on the upgraded account is still a separate request. I found no primary figure for its default or approval time (unknown).
3. Colab's FAQ bars SSH and "bypassing the notebook UI to interact primarily via a web UI" on free runtimes, and bars "connecting to remote proxies" on all managed runtimes ([FAQ](https://research.google.com/colaboratory/faq.html), verified). Do not serve Gradio from Colab, free or Pro.
4. The GitHub Student Developer Pack today lists $100 Azure credit, a Camber plan with 5 GPU hours a month and Heroku credit. It does not list DigitalOcean ([pack page](https://education.github.com/pack), verified). GitHub states no verification time. Community threads report 72 hours to 2 weeks ([search summary](https://github.com/orgs/community/discussions/180773), reported). Do not plan on it for this event.
5. Modal gives $30 of free compute a month on Starter and bills L4 at $0.000222 per second ([pricing](https://modal.com/pricing), verified). Idle containers scale to zero, so a 3 day demo costs almost nothing.
6. Creating a new Gradio or Docker Space that runs on compute needs a paid Hugging Face plan ([Spaces GPU docs](https://huggingface.co/docs/hub/spaces-gpus), verified). This conflicts with the free ZeroGPU hosting note in `backend-feasibility.md`. Treat HF hosting as paid until proven otherwise.
7. Upgraded HF Spaces never sleep by default and bill by the minute while `Running`, used or not ([Spaces GPU docs](https://huggingface.co/docs/hub/spaces-gpus), verified). Set a sleep time or the demo costs round the clock.

## Comparison

| Option | GPU and VRAM | USD per hour (approx INR) | Free credit or quota | Signup friction and India payment | Time to first GPU shell | Public URL | Persistence | First-hour failure risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AWS EC2 g4dn, g5, g6 | T4 16 GB, A10G 24 GB, L4 24 GB (reported) | unknown, not on fetched pages. Check the pricing calculator. | Free plan up to $200 over 6 months (verified). GPU eligibility unknown. Free plan EC2 types seen are non-GPU (reported). | Quota 0 for G and VT (verified). Cards incl. RuPay, net banking and UPI listed for AWS India (reported). | Unknown. Hours to days. | Yes, with a public IP and security group | EBS persists. Billed while stopped. | Very high |
| AWS credits (Builder, ML Challenge, Activate) | n/a | n/a | $200 for ML Challenge per a community guide (reported). Official terms not found. Activate lists Capacity Blocks for H100 (reported). | Same quota wall | n/a | n/a | n/a | Credits do not remove the quota wall |
| SageMaker Studio Lab | Not checked | Free per memory | Unknown | Not checked | Unknown | No | Unknown | Unknown, skip |
| GCP Compute Engine T4, L4 | T4 16 GB, L4 24 GB. Both in asia-south1-a and b (verified). | unknown, not fetched | $300 trial, but GPUs blocked until paid upgrade (verified) | Visa, Mastercard, Amex, debit with Visa or Mastercard logo. RuPay not listed. Prepaid and 2FA-only debit refused. UPI only for qualified orgs (verified). | Unknown. Needs upgrade plus GPU quota request. | Yes | Disk persists | Very high |
| Azure for Students | NC-series not mentioned on the page | unknown | $100 for 12 months, no card (verified). Pack also lists $100 (verified). | School email. India eligibility not stated on page. | Unknown. GPU quota likely 0, unconfirmed. | Yes if a GPU VM is allowed | Disk persists | High |
| Oracle Cloud | Free tier has no GPU (verified) | unknown | $300 trial credit (verified). Trial GPU access unknown. | Unknown | Unknown | Yes | Unknown | High |
| Lightning AI free | T4 and L4, single GPU (reported) | Free credit. About 75 T4 hours or 31 L4 hours to start (reported). | 30 credits to start. Card adds 25 (reported). | Phone number needed. Card optional. | About 10 min (estimate) | Not confirmed on the free plan | Persistent storage. Free studio restarts every 4 hours (reported). | Medium |
| Kaggle notebooks | T4 x2 (16 GB each) or P100 (reported). A forum thread claims P100 retired 15 Sep 2026 (unverified). | Free | About 30 GPU hours a week, floating. Session up to 12 hours (reported). | Kaggle login. Phone verification and internet toggle not confirmed. | About 5 to 10 min (estimate) | Only via a tunnel such as cloudflared. Not documented by Kaggle. A thread says LLM-server notebooks are straining GPU supply (reported). | Session files only. Save outputs as a notebook version. | Medium |
| Colab free | T4 usually, varies (verified) | Free | Not published (verified) | Google account | About 2 min | No. FAQ bars web UI use and proxies. | Session only | Low to start, high for serving |
| Colab Pro | Premium GPUs subject to availability (verified) | About $9.99 a month for 100 compute units via Workspace pricing (reported). India price unknown. | None | Card | About 2 min | No. Proxies barred on all runtimes (verified). | Session only | High for serving |
| Modal | T4, L4, A10, L40S, A100, H100 and more (verified) | T4 $0.59 (53), L4 $0.80 (72), A10 $1.10 (99), L40S $1.95 (176) (verified, hourly derived from per-second) | $30 free compute a month (verified) | "A payment method on file" is required to use Modal (verified). Card type for India unknown. | About 15 min (estimate) | Yes. `modal.run` URLs via `@modal.asgi_app()`. Gradio not on the page (verified for ASGI, unknown for Gradio). | Deploy persists. Weights need a Volume. Idle scale-to-zero after 60 s by default (verified). | Medium, mostly the card and cold start |
| RunPod | RTX 4090 24 GB, L4 24 GB, L40S 48 GB, A40 48 GB | 4090 $0.34 community or $0.89 secure (31 or 80). L4 $0.44 or $0.59 (40 or 53). L40S $0.79 or $1.09 (71 or 98). (verified) | None found | Prepaid credit, $10 minimum, Stripe cards, crypto. Prepaid cards need a $100 deposit (verified). RuPay and UPI not mentioned. | About 10 min (estimate) | Likely via proxy URL. Not read, so unknown. | Network volume $0.07 per GB a month (verified). Pod without volume is deleted at zero balance (verified). | Medium, card and GPU stock |
| Vast.ai | Marketplace GPUs | unknown, price grid did not render | Unknown | Unknown | Unknown | Unknown | Unknown | Medium to high, unverified hosts |
| Lambda | A10 24 GB, A6000 48 GB, A100, H100 | A10 $1.29 (116), A6000 $1.09 (98), A100 40 GB $1.99 (179) (verified) | None found | Payment methods not on page | Unknown | Yes | Unknown | Medium, capacity unknown |
| HF Spaces paid GPU | T4 small and medium 16 GB, L4 24 GB, A10G 24 GB | T4 small $0.40 (36), T4 medium $0.60 (54), L4 $0.80 (72), A10G small $1.00 (90), A10G large $1.50 (135) (verified) | Community GPU grants on request (verified) | Paid plan needed to create a compute Space (verified). Card type unknown. | Build time 10 to 30 min (estimate) | Yes, native, with a stable `hf.space` URL | Repo persists. Disk is ephemeral. | Medium |
| Replicate | T4 16 GB, L40S 48 GB, A100 80 GB | T4 $0.81 (73), L40S $3.51 (316) (verified) | None found | Deploying your own model needs Cog (verified) | Unknown | API only | Unknown | High, packaging overhead |
| fal.ai | H100, H200 and similar only | H100 $2.49 to $4.50 (224 to 405) (verified) | None found | Prepaid credits | Unknown | Yes, serverless | Unknown | High, no small GPU, overkill |
| Paperspace (DigitalOcean) | RTX4000 8 GB, A4000 16 GB | RTX4000 $0.56 (50), A4000 $0.76 (68) (reported) | RTX4000 on Free plan (reported) | DigitalOcean account and card | Unknown | Unknown | Billing stops when powered off (reported) | Medium |
| GitHub Student Pack | Camber 5 GPU hours a month (verified) | n/a | Azure $100, Heroku $13 a month for 24 months (verified) | Review time 72 h to 2 weeks (reported) | Not within the hour | n/a | n/a | Very high for this event |

## Notes on payment in India

- Google lists Visa, Mastercard, Amex and debit cards with a Visa or Mastercard logo. It does not name RuPay. It refuses prepaid cards and debit cards that need two-factor authentication ([GCP payment methods](https://docs.cloud.google.com/billing/docs/how-to/payment-methods), verified).
- RBI rules may make a bank decline automatic charges above 15,000 INR. That matters for end-of-month bills, not for a 2,000 INR prepaid session ([same page](https://docs.cloud.google.com/billing/docs/how-to/payment-methods), verified).
- AWS India lists Visa, Mastercard, Amex and RuPay cards, net banking and UPI Scan and Pay for sign-up and payments ([AWS India payments](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/edit-aispl-payment-method.html), reported through a search summary). It is the friendliest payment setup, and the quota is still 0.
- Modal bills through Stripe and needs a payment method on file ([Modal billing](https://modal.com/docs/guide/billing), verified). RunPod accepts Stripe cards and crypto ([RunPod billing](https://docs.runpod.io/get-started/billing-information), verified). Neither page names RuPay, UPI or India. A Visa or Mastercard debit card with international transactions enabled is the safe bet (unknown, not tested).
- Azure for Students and Kaggle need no card. Lightning needs a phone number and takes an optional card.

## Serving a public URL after the event

- **Modal.** `modal deploy` makes a persistent web function. `modal serve` is temporary ([webhooks guide](https://modal.com/docs/guide/webhooks), verified). Containers boot in about one second, but loading large weights is the real delay ([cold start guide](https://modal.com/docs/guide/cold-start), verified). Bake weights into a Volume or image and use memory snapshots. Set `min_containers=1` only while judges are active.
- **HF Spaces.** Simplest to publish and stable to share. Costs the full hourly rate while running. Set a sleep time ([docs](https://huggingface.co/docs/hub/spaces-gpus), verified).
- **Pod on RunPod.** Cheap per hour, but a pod you leave running for 3 days costs 3 days of GPU. Stopping it risks losing the URL.
- **Kaggle or Lightning with a tunnel.** Free, but the URL dies with the session and the 4 hour or 12 hour limits apply. Use only as an emergency demo.
- **Cheapest honest option.** Record a video and keep the GLB outputs in the repo. The live link is then a bonus.

## Cost estimate

Assumptions are 90 INR per USD, one shared GPU, 24 h of dev and 72 h of demo.

| Item | Setup | USD | INR |
| --- | --- | --- | --- |
| Dev 24 h, RunPod RTX 4090 secure at $0.89 | Primary | 21.4 | about 1,920 |
| Dev 24 h, RunPod RTX 4090 community at $0.34 | Cheaper if stock exists | 8.2 | about 735 |
| 100 GB network volume for 6 days at $0.07 per GB a month | Weights and env | 1.4 | about 125 |
| Demo 72 h, Modal L4, 8 warm hours plus 4 cold hours | Primary demo | 9.6 | about 865, covered by the $30 free credit |
| Expected out of pocket, primary plan | | 22.8 | about 2,050 |
| Expected out of pocket, with community 4090 | | 9.6 | about 860 |
| Alternative demo, HF L4 always on 72 h | Do not do this | 57.6 | about 5,185 plus plan fee |
| Alternative demo, RunPod 4090 secure always on 72 h | Do not do this | 64.1 | about 5,770 |
| Fallback dev and demo, Kaggle plus tunnel | Backup | 0 | 0 |

Budget 3,000 INR to cover a retry and a 10 USD minimum deposit.

## Recommendation

1. Dev GPU for the 24 h session (phase a). Primary is one RunPod pod with an RTX 4090 or L4 (24 GB) and a network volume, shared over SSH or Jupyter. It costs about 2,050 INR and needs one Visa or Mastercard with international enabled. Everyone signs up with a card now, and one person tops up $25.
2. Demo endpoint for judges (phase b). Primary is Modal with `modal deploy` on an L4, weights in a Volume, scale to zero, and `min_containers=1` only during judging. It should fit inside the $30 monthly credit. Backup is an HF Space on L4 with a sleep time, if a team member already has the paid plan.
3. Cheap fallback if the card route fails (phase c). Use Kaggle T4 x2 for dev, with Lightning free studios as a second seat. Keep SD plus TripoSR on one T4 and defer Hunyuan3D. Serve the demo from a tunnel only for scheduled judge slots.
4. Skip AWS, GCP and Azure for this event. AWS and GCP gate GPUs behind quota or an upgrade with no published approval time. Azure for Students does not mention NC-series. Start an AWS quota request for 4 vCPUs in parallel only if someone has spare time.
5. Skip Colab for serving. Its FAQ bars web UI use and proxies. Use it only to run notebook cells.
6. Ask each teammate in the next 10 minutes whether they have a Visa or Mastercard with international use on, and whether the Builder credits are for AWS. If the answer to both is no, go straight to Kaggle and Lightning.
