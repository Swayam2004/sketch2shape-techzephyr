# Shared dev GPU on RunPod

Owner. Udit (his card pays). Everyone else connects over SSH. Prices below come from the research pass (`docs/research/cloud-gpu-options.md`) and may have moved, so read the console before you click Deploy.

## Why this setup

- Network volumes only work on Secure Cloud pods, and they survive pod termination. Weights and the repo checkout live there, so a lost pod costs minutes, not an hour.
- L4 24 GB (about $0.59 per hour on Secure Cloud) fits SD 1.5 plus ControlNet plus TripoSR with room to spare, and 24 hours costs about 1,300 INR. An RTX 4090 (about $0.89 per hour) is faster and costs about 1,900 INR for 24 hours. Start on L4. Switch only if benchmarks say speed matters.
- Billing is per second while the pod runs. Stop the pod when nobody needs it.

## Steps for Udit

1. Sign up at runpod.io and add credit under Billing. Start with $25. A Visa or Mastercard with international payments enabled is the safe choice. Turn auto top-up off.
2. Each person makes an SSH key on their own laptop and sends Udit the public half only.

   ```
   ssh-keygen -t ed25519 -C "s2s-<name>"
   ```

   Windows PowerShell has `ssh-keygen` built in. The public file is `id_ed25519.pub`. Never send the file without `.pub`.
3. In the console open Settings, find the SSH public keys box (the docs call the page Credentials), and paste all three public keys, one per line, each starting with `ssh-ed25519`. Paste the file contents, not a fingerprint that starts with `SHA256:`.
4. Storage, New Network Volume. Pick a data center that lists L4 or 4090 stock, name it `s2s-vol`, size 50 GB, Standard tier. It costs about $0.07 per GB per month.
5. Pods, Deploy. Choose Secure Cloud, the same data center, an L4 (or 4090), the official RunPod PyTorch template, and attach `s2s-vol`. It mounts at `/workspace`. In Edit Template add `7860` to Expose HTTP Ports. Name the pod `s2s-dev`.
6. Wait for Running, then check the Telemetry tab. Open Connect and copy the "SSH over exposed TCP" command. It looks like

   ```
   ssh root@<POD_IP> -p <PORT> -i ~/.ssh/id_ed25519
   ```

   Send that line (IP and port, no secrets) to Swayam and Disha. The IP and port change if the pod is recreated.
7. First login, on the pod. The repo is private, so the pod needs a read-only deploy key. Copy `infra/runpod/bootstrap.sh` to the pod (paste it into a file, or `scp` it) and run it. It prints a public key if GitHub does not accept the pod yet. Swayam adds that key under the repo's Settings, Deploy keys, without write access. Rerun the script and it clones the repo into `/workspace/sketch2shape`, sets cache folders on the volume and runs `uv sync`.

## Rules of the shared box

- Code changes flow laptop to GitHub to pod (`git pull`). Do not edit files only on the pod.
- Put every model weight under `/workspace/.cache`. The bootstrap script sets the cache variables for you.
- The pod's public URL `https://<POD_ID>-7860.proxy.runpod.net` is open to anyone who has it. The app must have the access code on.
- Cloudflare cuts HTTP requests at 100 seconds with a 524 error. Our API must answer in under 100 seconds or use job polling. Do not hold one HTTP call open for a slow generation.
- Bind servers to `0.0.0.0`, not `localhost`, or the proxy cannot reach them.
- Say in `STATUS.md` when you start a long job so nobody stops the pod under you.

## Sources

- [SSH on RunPod](https://docs.runpod.io/pods/configuration/use-ssh)
- [Network volumes](https://docs.runpod.io/pods/storage/create-network-volumes)
- [Expose ports](https://docs.runpod.io/pods/configuration/expose-ports)
