// Wires the components together: SketchCanvas, CenterStage, PipelineTracker, StatusTicker,
// DoodleLayer and the result viewer controls. The only backend call goes through api.js.
import { store, STAGES, reducedMotion, isMobile } from "./store.js";
import { detectBackend, runPipeline, createEstimator, PipelineError, Cancelled } from "./api.js";
import { createSketch, INKS } from "./sketch.js";
import { createStage } from "./stage.js";
import { startBoil, boom, sticker, createScribbleLayer, buildScraps, buildHead, el } from "./doodles.js";
import { createPipebar } from "./pipebar.js";
import { rustle, pop } from "./audio.js";

const $ = (id) => document.getElementById(id);
const rnd = (a, b) => a + Math.random() * (b - a);

// ---------------------------------------------------------------- torn paper edges
function tornEdge(node, seed) {
  const w = node.offsetWidth, h = node.offsetHeight;
  if (!w || !h) return;
  let s = seed * 7919;
  const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const step = 24, j = 6, pts = [];
  for (let x = 0; x <= w; x += step) pts.push([x, r() * j]);
  for (let y = 0; y <= h; y += step) pts.push([w - r() * j, y]);
  for (let x = w; x >= 0; x -= step) pts.push([x, h - r() * j]);
  for (let y = h; y >= 0; y -= step) pts.push([r() * j, y]);
  node.style.clipPath = `polygon(${pts.map((p) => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(",")})`;
}
document.querySelectorAll(".panel").forEach((p, i) => {
  new ResizeObserver(() => tornEdge(p, i + 3)).observe(p);
});

// ---------------------------------------------------------------- background and decor
startBoil();
buildScraps($("scraps"), isMobile ? 7 : 14);
buildHead($("head"));

// ---------------------------------------------------------------- sketch
const msg = (t) => { $("msg").textContent = t; };
const sketch = createSketch($("pad"), {
  onChange() {
    $("canvasWrap").classList.toggle("used", sketch.dirty);
    updateGo();
  },
  onError: msg,
});
const scribbles = createScribbleLayer($("canvasWrap"));

const inks = $("inks");
INKS.forEach((c, i) => {
  const b = document.createElement("button");
  b.type = "button"; b.style.background = c; b.setAttribute("aria-label", `Ink ${i + 1}`); b.setAttribute("aria-pressed", String(i === 0));
  b.onclick = () => { sketch.setInk(c); setTool("pen"); [...inks.children].forEach((x) => x.setAttribute("aria-pressed", String(x === b))); };
  inks.appendChild(b);
});
function setTool(t) {
  sketch.setTool(t);
  for (const id of ["pen", "eraser"]) { $(id).classList.toggle("on", id === t); $(id).setAttribute("aria-pressed", String(id === t)); }
}
$("pen").onclick = () => setTool("pen");
$("eraser").onclick = () => setTool("eraser");
$("size").oninput = (e) => sketch.setWidth(+e.target.value);
$("undo").onclick = () => sketch.undo();
$("clear").onclick = () => sketch.clear();
$("file").onchange = (e) => { sketch.loadFile(e.target.files[0]); e.target.value = ""; };
document.querySelector("label.upload").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("file").click(); } });

function updateGo() {
  const running = store.get().phase === "running";
  $("go").disabled = !sketch.dirty || running;
}

// ---------------------------------------------------------------- stage
const host = $("doodleHost");
const stage = createStage({
  canvas: $("gl"),
  getMask: (g) => sketch.mask(g),
  onBoom: (x, y, word) => boom(host, x, y, word),
  onSticker: (x, y) => sticker(host, x, y),
  onStars: (n) => { store.set({ stars: n }); $("starsN").textContent = n; },
});

// ---------------------------------------------------------------- tracker (stair-step path and paper doll)
const STEP_COLS = ["--sky", "--sage", "--mustard", "--terra", "--magenta"];
function buildTracker() {
  const box = $("stairs");
  const svg = el("svg", { viewBox: "0 0 270 250", role: "img", "aria-label": "Five stairs. A paper doll climbs one stair per finished stage." });
  box.appendChild(svg);
  const stepX = (i) => 6 + i * 50, stepY = (i) => 196 - i * 40;
  STAGES.forEach((s, i) => {
    const x = stepX(i), y = stepY(i);
    el("path", { d: `M${x} ${y + 2} L${x + 46} ${y + 2 + rnd(-2, 2)} L${x + 46} 244 L${x} 244 Z`, class: "step-rect", style: `fill:var(${STEP_COLS[i]})` }, svg);
    el("path", { d: `M${x} ${y + 2} l46 0 l0 242 l-46 0Z`, fill: "url(#ht)", opacity: ".25" }, svg);
    const t = el("text", { x: x + 4, y: y + 18, class: "step-label" }, svg); t.textContent = s.short;
    const g = el("g", { id: `tick${i}`, opacity: "0" }, svg);
    el("path", { d: `M${x + 12} ${y + 30} l8 9 l16 -20`, class: "tick", pathLength: 1 }, g);
  });
  el("path", { d: `M${stepX(4) + 6} ${stepY(4) - 6} l0 -26`, class: "stroke", style: "stroke:var(--ink);stroke-width:3" }, svg);
  el("polygon", { points: `${stepX(4) + 6},${stepY(4) - 32} ${stepX(4) + 32},${stepY(4) - 24} ${stepX(4) + 6},${stepY(4) - 16}`, style: "fill:var(--magenta);stroke:var(--ink);stroke-width:2.5" }, svg);
  const doll = el("g", { class: "doll still", id: "doll" }, svg);
  const bob = el("g", { class: "bob" }, doll);
  el("circle", { cx: 0, cy: -36, r: 8, fill: "var(--cream)" }, bob);
  el("path", { d: "M0 -28 L0 -12 M-9 -22 L9 -18 M0 -12 L-7 0 M0 -12 L7 0", fill: "none" }, bob);
  el("path", { d: "M-6 -43 q6 -9 12 0", fill: "var(--ink)" }, bob);
  const place = (i) => {
    const x = i < 0 ? -2 : i >= STAGES.length ? stepX(4) + 22 : stepX(i) + 24;
    const y = i < 0 ? 244 : i >= STAGES.length ? stepY(4) - 2 : stepY(i) + 2;
    doll.style.transform = `translate(${x}px, ${y}px)`;
  };
  place(-1);
  const list = $("stageList");
  list.innerHTML = STAGES.map((s, i) => `<li data-i="${i}">${i + 1}. ${s.label}</li>`).join("");
  return {
    set(shown, running) {
      place(shown);
      doll.classList.toggle("still", !running);
      STAGES.forEach((_, i) => {
        const g = $(`tick${i}`), done = i < shown;
        if (done && g.getAttribute("opacity") === "0") { g.setAttribute("opacity", "1"); g.firstChild.classList.add("draw"); }
        if (!done) { g.setAttribute("opacity", "0"); g.firstChild.classList.remove("draw"); }
      });
      list.querySelectorAll("li").forEach((li, i) => { li.classList.toggle("done", i < shown); li.classList.toggle("active", running && i === shown); });
    },
  };
}
const tracker = buildTracker();
const pipe = createPipebar($("pipebar"));

// ---------------------------------------------------------------- status ticker (typewriter phrases)
const PHRASES = ["working", "in progress", "creating", "bringing ideas to life", "sketching the invisible", "folding space", "teaching clay to dream", "almost there", "adding sparkle", "melting the clock"];
let phraseTimer = null, typeTimer = null, phraseIdx = 0;
function typePhrase(text) {
  clearInterval(typeTimer);
  const out = $("phrase");
  if (reducedMotion) { out.textContent = text; return; }
  let i = 0; out.textContent = "";
  typeTimer = setInterval(() => { out.textContent = text.slice(0, ++i); if (i >= text.length) clearInterval(typeTimer); }, 38);
}
function startTicker() {
  $("ticker").hidden = false;
  phraseIdx = Math.floor(Math.random() * PHRASES.length);
  typePhrase(PHRASES[phraseIdx]);
  clearInterval(phraseTimer);
  phraseTimer = setInterval(() => typePhrase(PHRASES[(phraseIdx = (phraseIdx + 1) % PHRASES.length)]), 1600);
}
function stopTicker() { clearInterval(phraseTimer); clearInterval(typeTimer); $("ticker").hidden = true; }
function setProgress(p) { $("ringFill").style.strokeDashoffset = String(1 - p); $("pct").textContent = `${Math.round(p * 100)}%`; }

// ---------------------------------------------------------------- run
let backend = { mock: true }, abort = null, shown = 0, target = 0, stageSince = 0, est = null, uiTimer = null, dwellTimer = null;
const DWELL = [1700, 1700, 900, 900, 900]; // minimum time on each stage so fast GPU runs still show every experience
const wrap = $("stageWrap");

function applyShown(i) {
  shown = i; stageSince = performance.now();
  stage.setStage(i);
  tracker.set(i, store.get().phase === "running");
  if (store.get().phase === "running") pipe.set({ shown: i, within: est?.within() || 0, state: "running" });
  $("canvasWrap").classList.toggle("scanning", store.get().phase === "running" && i <= 1);
  $("refine").hidden = !(store.get().phase === "running" && i === 3);
  $("stickerHint").hidden = $("refine").hidden;
  $("starsBox").hidden = !(store.get().phase === "running" && (i === 2 || i === 3));
  $("live").textContent = i < STAGES.length ? `Stage ${i + 1} of ${STAGES.length}: ${STAGES[i].label}` : "Finished";
  if (i === 1 || i === 2) rustle(0.3);
}
function pace() {
  clearTimeout(dwellTimer);
  if (shown >= Math.min(target, STAGES.length)) return;
  const wait = Math.max(0, DWELL[shown] - (performance.now() - stageSince));
  dwellTimer = setTimeout(() => { applyShown(shown + 1); pace(); }, wait);
}
const waitForShown = (i) => new Promise((res) => { const t = setInterval(() => { if (shown >= i) { clearInterval(t); res(); } }, 100); });

function resetUI() {
  clearTimeout(dwellTimer); clearInterval(uiTimer); stopTicker();
  wrap.classList.remove("busy", "done", "error");
  for (const id of ["oops", "resultBar", "banner", "refine", "stickerHint", "starsBox"]) $(id).hidden = true;
  $("tearImg").hidden = true; $("canvasWrap").classList.remove("scanning");
  $("go").hidden = false; $("cancel").hidden = true;
  scribbles.setEnabled(false);
  shown = 0; target = 0; tracker.set(-1, false); pipe.reset();
  host.replaceChildren();
}

function showBanner(list) {
  const b = $("banner");
  b.textContent = list.join(" ");
  b.hidden = list.length === 0;
}

async function start() {
  const blob = await sketch.toBlob();
  stage.reset(); resetUI(); scribbles.clear();
  const health = backend.health;
  store.set({ phase: "running", stage: 0, progress: 0.02, error: null, result: null, warnings: [], stars: 0 });
  wrap.classList.add("busy");
  $("go").hidden = true; $("cancel").hidden = false; $("cancel").focus();
  scribbles.setEnabled(true);
  msg("Doodle on the sketch while you wait. The server keeps working.");
  startTicker();
  est = createEstimator(backend.mock ? "mock" : health?.device || "cpu");
  applyShown(0);
  const cpuWarn = !backend.mock && health?.device === "cpu" ? ["Running on CPU. Results may be slow."] : [];
  showBanner(cpuWarn);

  stage.setMorph(0.1);
  uiTimer = setInterval(() => {
    const p = est.update(shown);
    setProgress(p); store.set({ progress: p });
    pipe.set({ shown, within: est.within(), state: "running" });
    if (shown === 2) stage.setMorph(0.12 + 0.88 * (1 - Math.exp(-(performance.now() - stageSince) / 20000)));
    if (shown >= 3) stage.setMorph(1);
    if (shown === 3 && stage.lodAuto) { const v = 0.5 + 0.5 * Math.sin(performance.now() / 1100); stage.setLod(v, false); $("lod").value = Math.round(v * 100); }
  }, 120);

  abort = new AbortController();
  try {
    const result = await runPipeline({
      blob, prompt: $("prompt").value.trim(), seed: +$("seed").value || 0, code: $("code").value, mock: backend.mock, signal: abort.signal,
      onUpdate: (u) => {
        target = u.index; pace();
        if (u.device && u.device !== "mock" && u.device !== health?.device) est = createEstimator(u.device);
        store.set({ queuePosition: u.queuePosition, elapsed: u.elapsed, device: u.device });
        showBanner([...new Set([...cpuWarn, ...u.warnings])]);
      },
    });
    target = STAGES.length; pace();
    await waitForShown(STAGES.length - 1);
    await new Promise((r) => setTimeout(r, Math.max(0, DWELL[4] - (performance.now() - stageSince))));
    await finish(result);
  } catch (e) {
    if (e instanceof Cancelled) { resetUI(); store.set({ phase: "idle" }); stage.reset(); msg("Stopped. The server may still finish that job."); updateGo(); return; }
    fail(e instanceof PipelineError ? e.message : `Something broke: ${e.message}`);
  }
}

function tearWipe(snapshot) {
  return new Promise((res) => {
    const img = $("tearImg");
    img.src = snapshot; img.hidden = false;
    if (reducedMotion) { setTimeout(() => { img.hidden = true; res(); }, 300); return; }
    const jag = Array.from({ length: 29 }, () => Math.random() * 7 - 3.5);
    const t0 = performance.now(), dur = 1500;
    rustle(0.6);
    const f = (now) => {
      const k = Math.min(1, (now - t0) / dur), e = k * k * (3 - 2 * k), y = (1 - e) * 112 - 6;
      const pts = ["0% 0%", "100% 0%"];
      for (let i = 0; i <= 28; i++) pts.push(`${(100 - (i * 100) / 28).toFixed(2)}% ${(y + jag[i]).toFixed(2)}%`);
      img.style.clipPath = `polygon(${pts.join(",")})`;
      if (k < 1) requestAnimationFrame(f); else { img.hidden = true; img.style.clipPath = ""; res(); }
    };
    requestAnimationFrame(f);
  });
}

let current = null;
async function finish(result) {
  current = result;
  clearInterval(uiTimer); setProgress(1);
  await stage.showResult(result, tearWipe);
  stopTicker();
  store.set({ phase: "done", result });
  wrap.classList.remove("busy"); wrap.classList.add("done");
  $("canvasWrap").classList.remove("scanning"); scribbles.setEnabled(false);
  tracker.set(STAGES.length, false);
  pipe.set({ shown: STAGES.length, state: "done" });
  $("refine").hidden = true; $("stickerHint").hidden = true; $("starsBox").hidden = true;
  $("resultBar").hidden = false;
  $("dlObj").disabled = result.kind === "files" && !result.obj;
  const secs = (result.timings || []).reduce((a, t) => a + t.seconds, 0);
  $("info").textContent = [
    result.device ? `device ${result.device}` : "", secs ? `${secs.toFixed(1)} s in the pipeline` : "",
    result.iou != null ? `silhouette IoU ${result.iou.toFixed(3)}` : "", result.kind === "procedural" ? "mock shape, built in the browser" : "",
  ].filter(Boolean).join(" · ");
  showBanner(result.warnings || []);
  const r = host.getBoundingClientRect();
  boom(host, r.width / 2, r.height * 0.3, "BOOM!");
  $("go").hidden = false; $("cancel").hidden = true; updateGo();
  msg("Done. Orbit it, switch the look, download it.");
}

function fail(text) {
  clearInterval(uiTimer); clearTimeout(dwellTimer); stopTicker(); scribbles.setEnabled(false);
  store.set({ phase: "error", error: text });
  wrap.classList.remove("busy"); wrap.classList.add("error");
  $("canvasWrap").classList.remove("scanning");
  $("oopsMsg").textContent = text;
  $("oops").hidden = false;
  $("go").hidden = false; $("cancel").hidden = true; updateGo();
  $("retry").focus();
}

$("go").onclick = start;
$("retry").onclick = () => { $("oops").hidden = true; wrap.classList.remove("error"); start(); };
$("cancel").onclick = () => abort?.abort();
$("again").onclick = () => { stage.reset(); resetUI(); store.set({ phase: "idle" }); scribbles.clear(); updateGo(); msg("Draw another one."); };
$("lod").oninput = (e) => stage.setLod(+e.target.value / 100, true);
$("prompt").addEventListener("keydown", (e) => { if (e.key === "Enter" && !$("go").disabled) start(); });

// result view modes and downloads
document.querySelectorAll("[data-view]").forEach((b) => {
  b.onclick = () => {
    stage.setViewMode(b.dataset.view);
    document.querySelectorAll("[data-view]").forEach((x) => x.classList.toggle("on", x === b));
    pop(1.1);
  };
});
function save(blobOrUrl, name) {
  const a = document.createElement("a");
  a.href = typeof blobOrUrl === "string" ? blobOrUrl : URL.createObjectURL(blobOrUrl);
  a.download = name; document.body.appendChild(a); a.click(); a.remove();
}
async function download(fmt) {
  try {
    // Real results come from the server. The browser exports only the formats the server does not make, and the mock shape.
    if (current?.kind === "files" && fmt !== "stl") { const u = current[fmt]; if (u) return save(u, `sketch2shape.${fmt}`); }
    save(await stage.exportAs(fmt), `sketch2shape.${fmt}`);
  } catch (e) { msg(`Export failed: ${e.message}`); }
}
$("dlGlb").onclick = () => download("glb");
$("dlObj").onclick = () => download("obj");
$("dlStl").onclick = () => download("stl");

// ---------------------------------------------------------------- vibe, sound, health
const THEMES = ["cream", "tan", "navy", "magenta"];
$("vibe").onclick = () => {
  const next = THEMES[(THEMES.indexOf(document.body.dataset.theme) + 1) % THEMES.length];
  document.body.dataset.theme = next; store.set({ theme: next });
  setTimeout(() => stage.rethemed(), 60);
  rustle(0.3);
};
$("sound").onclick = () => {
  const on = !store.get().sound;
  store.set({ sound: on });
  $("sound").textContent = on ? "sound on" : "sound off"; $("sound").setAttribute("aria-pressed", String(on));
  if (on) pop();
};

async function refreshHealth() {
  if (backend.mock) { $("health").textContent = "mock mode, no server found"; return; }
  try {
    const h = await (await fetch("/v1/health")).json();
    backend.health = h;
    $("health").textContent = `${h.device}${h.gpu_name ? " · " + h.gpu_name : ""} · queue ${h.queue_length}${h.ready === false ? " · loading models, the first job waits" : ""}`;
  } catch { $("health").textContent = "server unreachable"; }
}
(async () => { backend = await detectBackend(); store.set({ mock: backend.mock }); refreshHealth(); setInterval(refreshHealth, 5000); })();

// stop drawing when the page is hidden so a background tab does not burn the GPU
document.addEventListener("visibilitychange", () => stage.pause(document.hidden));

// Handy in the browser console, for example s2s.stage.debug().
window.s2s = { stage, store };
