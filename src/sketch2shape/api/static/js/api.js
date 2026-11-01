// Pipeline adapter. `runPipeline` is the one place that talks to the sketch2shape backend
// (contract in docs/api.md). Without a reachable server it falls back to a timed mock so the UI
// works on its own. Force the mock with ?mock=1 in the URL.
import { STAGES, stageIndexFor } from "./store.js";

const POLL_LIMIT_MS = 15 * 60 * 1000;

export class PipelineError extends Error {}
export class Cancelled extends Error {}

export async function detectBackend() {
  if (new URLSearchParams(location.search).has("mock")) return { mock: true };
  try {
    const r = await fetch("/v1/health", { signal: AbortSignal.timeout(2500) });
    if (!r.ok) return { mock: true };
    return { mock: false, health: await r.json() };
  } catch {
    return { mock: true };
  }
}

function explain(status, body, retryAfter) {
  if (status === 401) return "The access code is missing or wrong.";
  if (status === 429) return `The server is busy or rate limited.${retryAfter ? ` Try again in ${retryAfter} s.` : ""}`;
  if (status === 413) return "That sketch is over 10 MB.";
  return `${status}: ${body.detail || "request failed"}`;
}

// Expected seconds per UI stage, used only for the smooth progress estimate. The server sends no percentage.
const EXPECTED = {
  cuda: [1, 2, 12, 12, 3],
  cpu: [1, 3, 240, 70, 3],
  mock: [1.5, 4, 8, 7, 3],
};

export function createEstimator(device) {
  const exp = EXPECTED[device] || EXPECTED.cpu;
  let stage = 0;
  let stageStart = performance.now();
  const total = exp.reduce((a, b) => a + b, 0);
  let lastWithin = 0;
  return {
    update(idx) {
      if (idx !== stage) { stage = idx; stageStart = performance.now(); }
      if (idx >= STAGES.length) return 1;
      const within = 1 - Math.exp(-((performance.now() - stageStart) / 1000) / exp[idx]);
      lastWithin = within;
      const before = exp.slice(0, idx).reduce((a, b) => a + b, 0);
      return Math.min(0.97, (before + within * exp[idx]) / total);
    },
    // Fraction of the current stage, for the pipe bar.
    within: () => lastWithin,
  };
}

export async function runPipeline({ blob, prompt, seed, code, mock, signal, onUpdate }) {
  return mock ? runMock({ signal, onUpdate }) : runReal({ blob, prompt, seed, code, signal, onUpdate });
}

async function runReal({ blob, prompt, seed, code, signal, onUpdate }) {
  const headers = code ? { "X-Access-Code": code } : {};
  const form = new FormData();
  form.append("sketch", blob, "sketch.png");
  if (prompt) form.append("prompt", prompt);
  form.append("seed", String(seed || 0));
  let r;
  try { r = await fetch("/v1/jobs", { method: "POST", body: form, headers, signal }); }
  catch (e) { if (signal.aborted) throw new Cancelled(); throw new PipelineError("Cannot reach the server."); }
  if (!r.ok) throw new PipelineError(explain(r.status, await r.json().catch(() => ({})), r.headers.get("Retry-After")));
  const { job_id } = await r.json();

  const t0 = Date.now();
  for (;;) {
    if (signal.aborted) throw new Cancelled();
    const age = Date.now() - t0;
    if (age > POLL_LIMIT_MS) throw new PipelineError("Timed out after 15 minutes. The job may still finish on the server.");
    let j;
    try {
      const pr = await fetch(`/v1/jobs/${job_id}`, { headers, signal });
      if (!pr.ok) throw new PipelineError(explain(pr.status, await pr.json().catch(() => ({})), pr.headers.get("Retry-After")));
      j = await pr.json();
    } catch (e) {
      if (signal.aborted) throw new Cancelled();
      if (e instanceof PipelineError) throw e;
      j = null; // transient network error, keep polling
    }
    if (j) {
      onUpdate({ index: stageIndexFor(j.stage, j.status), status: j.status, queuePosition: j.queue_position || 0, elapsed: j.elapsed_seconds || 0, device: j.device, warnings: j.warnings || [] });
      if (j.status === "failed") throw new PipelineError(j.error || "The job failed without a reason.");
      if (j.status === "done") return collect(j, headers, signal);
    }
    // docs/api.md client rules: 1 s for the first 10 s, then 3 s.
    await sleep(age < 10000 ? 1000 : 3000, signal);
  }
}

async function collect(j, headers, signal) {
  const base = `/v1/jobs/${j.job_id}`;
  const grab = async (name) => {
    const r = await fetch(`${base}/${name}`, { headers, signal });
    return r.ok ? URL.createObjectURL(await r.blob()) : null;
  };
  const [glb, obj, img] = await Promise.all([grab("result.glb"), grab("result.obj"), grab("generated.png")]);
  if (!glb) throw new PipelineError("The job finished but the mesh file is missing.");
  return { kind: "files", glb, obj, image: img, iou: j.silhouette_iou, warnings: j.warnings || [], device: j.device, timings: j.timings || [] };
}

async function runMock({ signal, onUpdate }) {
  const dur = [1.6, 4, 8, 7, 3];
  const t0 = performance.now();
  for (let i = 0; i < STAGES.length; i++) {
    const end = performance.now() + dur[i] * 1000;
    while (performance.now() < end) {
      if (signal.aborted) throw new Cancelled();
      onUpdate({ index: i, status: "running", queuePosition: i === 0 ? 1 : 0, elapsed: (performance.now() - t0) / 1000, device: "mock", warnings: ["Mock mode. No server was found, so this shape is built in the browser."] });
      await sleep(250, signal);
    }
  }
  return { kind: "procedural", iou: null, warnings: ["Mock mode. No server was found, so this shape is built in the browser."], device: "mock", timings: [] };
}

function sleep(ms, signal) {
  return new Promise((res, rej) => {
    const t = setTimeout(res, ms);
    signal?.addEventListener("abort", () => { clearTimeout(t); rej(new Cancelled()); }, { once: true });
  });
}
