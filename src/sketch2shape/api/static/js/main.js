// Wires the components together: SketchCanvas, CenterStage, History, StatusTicker,
// DoodleLayer and the result viewer controls. The only backend call goes through api.js.
import { store, STAGES, reducedMotion, isMobile } from "./store.js";
import { detectBackend, runPipeline, createEstimator, PipelineError, Cancelled } from "./api.js";
import { createSketch, INKS, BRUSHES, WEIGHTS } from "./sketch.js";
import { history, toResult } from "./history.js";
import { createStage } from "./stage.js";
import { startBoil, boom, sticker, createScribbleLayer, buildScraps, buildHead } from "./doodles.js";
import { createPipebar } from "./pipebar.js";
import { rustle, pop } from "./audio.js";

const $ = (id) => document.getElementById(id);

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

const press = (group, active) => [...group.children].forEach((x) => { x.setAttribute("aria-pressed", String(x === active)); x.classList.toggle("on", x === active); });
const inks = $("inks");
INKS.forEach((c, i) => {
  const b = document.createElement("button");
  b.type = "button"; b.style.background = c; b.setAttribute("aria-label", `Ink ${i + 1}`); b.setAttribute("aria-pressed", String(i === 0));
  b.onclick = () => { sketch.setInk(c); showTool(sketch.tool); press(inks, b); };
  inks.appendChild(b);
});
// Four brush types and four weights. The eraser is a tool of its own and uses the same weight times four.
const brushes = $("brushes");
BRUSHES.forEach((br, i) => {
  const b = document.createElement("button");
  b.type = "button"; b.className = "tool"; b.textContent = br.label; b.title = br.hint; b.dataset.brush = br.id;
  b.onclick = () => { sketch.setTool(br.id); showTool(br.id); };
  brushes.appendChild(b);
});
const weights = $("weights");
WEIGHTS.forEach((w, i) => {
  const b = document.createElement("button");
  b.type = "button"; b.setAttribute("aria-label", `Stroke weight ${i + 1} of ${WEIGHTS.length}`); b.title = `${w} px`;
  b.innerHTML = `<i style="width:${4 + w * 0.7}px;height:${4 + w * 0.7}px"></i>`;
  b.onclick = () => { sketch.setWidth(w); press(weights, b); };
  weights.appendChild(b);
});
press(weights, weights.children[1]);
function showTool(t) {
  for (const b of brushes.children) { const on = b.dataset.brush === t; b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); }
  $("eraser").classList.toggle("on", t === "eraser"); $("eraser").setAttribute("aria-pressed", String(t === "eraser"));
}
showTool("pen");
$("eraser").onclick = () => { sketch.setTool("eraser"); showTool("eraser"); };
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
  shown = 0; target = 0; pipe.reset();
  host.replaceChildren();
}

function showBanner(list) {
  const b = $("banner");
  b.textContent = list.join(" ");
  b.hidden = list.length === 0;
}

async function start() {
  const blob = await sketch.toBlob();
  lastSketch = Promise.resolve(blob);
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

let current = null, lastSketch = null;
// `saved` is true when the design comes from history, so it is not stored a second time.
async function finish(result, { saved = false } = {}) {
  current = result;
  clearInterval(uiTimer); setProgress(1);
  await stage.showResult(result, tearWipe);
  stopTicker();
  store.set({ phase: "done", result });
  wrap.classList.remove("busy"); wrap.classList.add("done");
  $("canvasWrap").classList.remove("scanning"); scribbles.setEnabled(false);
  pipe.set({ shown: STAGES.length, state: "done" });
  $("refine").hidden = true; $("stickerHint").hidden = true; $("starsBox").hidden = true;
  $("resultBar").hidden = false;
  $("dlObj").disabled = result.kind === "files" && !result.obj;
  $("dlPng").disabled = false;
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
  if (!saved && result.kind === "files") remember(result);
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
    if (fmt === "png") return save(await stage.snapshot(), "sketch2shape.png");
    // Real results come from the server. The browser exports only the mock shape.
    if (current?.kind === "files") { const u = current[fmt]; if (u) return save(u, `sketch2shape.${fmt}`); }
    save(await stage.exportAs(fmt), `sketch2shape.${fmt}`);
  } catch (e) { msg(`Export failed: ${e.message}`); }
}
$("dlGlb").onclick = () => download("glb");
$("dlObj").onclick = () => download("obj");
$("dlPng").onclick = () => download("png");

// ---------------------------------------------------------------- history (right panel)
const ago = (t) => {
  const m = Math.round((Date.now() - t) / 60000);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
};
let historyOk = true;
const thumbUrls = [];
async function renderHistory() {
  const list = $("histList");
  let items = [];
  try { items = await history.list(); } catch { historyOk = false; }
  thumbUrls.splice(0).forEach(URL.revokeObjectURL);
  list.replaceChildren();
  $("histClear").hidden = items.length === 0;
  $("histNote").textContent = !historyOk ? "This browser blocks local storage, so designs are not kept."
    : items.length ? "Kept in this browser only. Click one to open it." : "Nothing yet. Designs you make are kept in this browser only.";
  for (const it of items) {
    const li = document.createElement("li");
    const open = document.createElement("button");
    open.type = "button"; open.className = "hist-open";
    const url = URL.createObjectURL(it.thumb || it.sketch); thumbUrls.push(url);
    open.innerHTML = `<img alt="" src="${url}"><span class="hand"></span><small class="type"></small>`;
    open.querySelector("span").textContent = it.prompt || "no prompt";
    open.querySelector("small").textContent = ago(it.createdAt);
    open.setAttribute("aria-label", `Open design ${it.prompt || "with no prompt"}, ${ago(it.createdAt)}`);
    open.onclick = () => openDesign(it);
    const del = document.createElement("button");
    del.type = "button"; del.className = "hist-del"; del.textContent = "x"; del.setAttribute("aria-label", "Delete this design");
    del.onclick = async () => { await history.remove(it.id); renderHistory(); };
    li.append(open, del);
    list.appendChild(li);
  }
}
// Store the finished design with a small picture of the model. A failed save must not break the result screen.
async function remember(result) {
  try {
    const [sketchBlob, thumb] = await Promise.all([lastSketch, stage.snapshot(220)]);
    await history.add({ result, sketch: sketchBlob, thumb, prompt: $("prompt").value.trim(), seed: +$("seed").value || 0 });
  } catch (e) { console.warn("history save failed", e); historyOk = false; }
  renderHistory();
}
async function openDesign(it) {
  if (store.get().phase === "running") { msg("Wait for the current job, or stop it first."); return; }
  stage.reset(); resetUI(); scribbles.clear();
  await sketch.loadFile(it.sketch);
  $("prompt").value = it.prompt || ""; $("seed").value = it.seed ?? 0;
  store.set({ phase: "running" }); // finish() expects a run in progress
  await finish(toResult(it), { saved: true });
  msg("Opened from history. Press make it 3D to run it again.");
}
$("histClear").onclick = async () => { if (confirm("Delete every saved design from this browser?")) { await history.clear(); renderHistory(); } };
renderHistory();

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
