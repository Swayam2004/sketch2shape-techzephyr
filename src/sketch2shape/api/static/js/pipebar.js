// PipelineBar: a glossy pipe with five spheres, one per stage. The pipe fills as the job runs,
// a ball rides the fill front and a doodle cat hops along it. Click a sphere or the cat to play.
import { STAGES, reducedMotion } from "./store.js";
import { el, boom } from "./doodles.js";
import { pop } from "./audio.js";

const W = 600, H = 120, X0 = 38, X1 = 562, Y = 76, PIPE = 18;
const COLS = ["--sky", "--sage", "--mustard", "--terra", "--magenta"];
// Node k sits where stage k ends, so the fill reaches it exactly when that stage completes.
const nodeX = (k) => X0 + ((k + 1) / STAGES.length) * (X1 - X0);
const uToX = (u) => X0 + u * (X1 - X0);

export function createPipebar(host) {
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "pipe-svg", role: "img", "aria-label": "Pipeline progress. Five spheres fill as each stage finishes." }, host);
  const defs = el("defs", {}, svg);

  // Cylinder shading for the pipe: light on top, dark underneath.
  const tube = el("linearGradient", { id: "pipeTube", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  [[0, "#ffffff", 0.75], [0.35, "#ffffff", 0.05], [0.75, "#000000", 0.12], [1, "#000000", 0.35]].forEach(([o, c, a]) => el("stop", { offset: o, "stop-color": c, "stop-opacity": a }, tube));
  const fillG = el("linearGradient", { id: "pipeFill", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
  COLS.forEach((c, i) => el("stop", { offset: i / (COLS.length - 1), style: `stop-color:var(${c})` }, fillG));
  // A sphere is a radial gradient with the highlight off centre.
  const sphere = (id, colour) => {
    const g = el("radialGradient", { id, cx: 0.35, cy: 0.3, r: 0.8 }, defs);
    el("stop", { offset: 0, "stop-color": "#fff", "stop-opacity": 0.95 }, g);
    el("stop", { offset: 0.28, style: `stop-color:${colour}` }, g);
    el("stop", { offset: 1, style: `stop-color:color-mix(in srgb, ${colour} 55%, #000)` }, g);
  };
  sphere("sphEmpty", "var(--cream)");
  STAGES.forEach((_, k) => sphere(`sph${k}`, `var(${COLS[k]})`));
  sphere("sphBall", "var(--mustard)");
  const clip = el("clipPath", { id: "pipeClip" }, defs);
  el("rect", { x: X0, y: Y - PIPE / 2, width: X1 - X0, height: PIPE, rx: PIPE / 2 }, clip);

  // pipe body
  const body = el("g", { class: "pipe-body" }, svg);
  el("rect", { x: X0, y: Y - PIPE / 2, width: X1 - X0, height: PIPE, rx: PIPE / 2, fill: "var(--cream)" }, body);
  const fillWrap = el("g", { "clip-path": "url(#pipeClip)" }, body);
  const fill = el("rect", { x: X0, y: Y - PIPE / 2, width: X1 - X0, height: PIPE, fill: "url(#pipeFill)", class: "pipe-fill" }, fillWrap);
  el("rect", { x: X0, y: Y - PIPE / 2, width: X1 - X0, height: PIPE, rx: PIPE / 2, fill: "url(#pipeTube)" }, body);
  el("rect", { x: X0, y: Y - PIPE / 2, width: X1 - X0, height: PIPE, rx: PIPE / 2, class: "pipe-edge" }, body);

  // start spigot
  el("ellipse", { cx: X0 - 4, cy: Y, rx: 9, ry: 15, class: "cap" }, svg);

  // nodes
  const nodes = STAGES.map((s, k) => {
    const g = el("g", { class: "node", tabindex: 0, role: "button", "aria-label": `${s.label}. Click to play.`, transform: `translate(${nodeX(k)} ${Y})` }, svg);
    el("ellipse", { cx: 3, cy: 22, rx: 17, ry: 4.5, class: "shadow" }, g);
    const inner = el("g", { class: "node-in" }, g);
    el("circle", { r: 17, class: "orb", fill: "url(#sphEmpty)" }, inner);
    const t = el("text", { y: 36, "text-anchor": "middle", class: "node-label" }, g); t.textContent = s.short;
    const tick = el("path", { d: "M-7 0 l5 6 l10 -12", class: "node-tick", pathLength: 1 }, inner);
    const act = (e) => { e?.stopPropagation(); pop(1 + k * 0.12); wobble(g); bubble(nodeX(k), `${s.label}`); hopTo(nodeX(k), true); };
    g.addEventListener("click", act);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(); } });
    return { g, inner, orb: inner.firstChild, tick, done: false };
  });

  // ball and cat ride the fill front
  const rider = el("g", { class: "rider" }, svg);
  el("circle", { cx: 0, cy: Y, r: 11, fill: "url(#sphBall)", class: "ball" }, rider);
  const catHop = el("g", { class: "cat-hop" }, rider);
  const cat = el("g", { class: "cat", tabindex: 0, role: "button", "aria-label": "Cat. Click to hear it.", transform: `translate(0 ${Y - 10})` }, catHop);
  cat.innerHTML = `
    <path class="tail" d="M-12 -12 C-26 -14 -26 -32 -16 -30" fill="none"/>
    <ellipse cx="0" cy="-12" rx="14" ry="10" fill="var(--terra)"/>
    <ellipse cx="2" cy="-8" rx="8" ry="5" fill="var(--cream)" stroke="none"/>
    <path d="M-8 -4 v6 M7 -4 v6" fill="none"/>
    <circle cx="9" cy="-26" r="10" fill="var(--terra)"/>
    <path d="M1 -32 L2 -42 L8 -35 M12 -35 L17 -42 L18 -31" fill="var(--terra)"/>
    <circle cx="6" cy="-27" r="1.6" fill="var(--ink)" stroke="none"/><circle cx="13" cy="-27" r="1.6" fill="var(--ink)" stroke="none"/>
    <path d="M9 -24 l-1.5 2 h3z" fill="var(--magenta)" stroke="none"/>
    <path d="M17 -24 l8 -2 M17 -22 l8 1 M1 -24 l-8 -2 M1 -22 l-8 1" fill="none" stroke-width="1.4"/>`;
  cat.addEventListener("click", (e) => { e.stopPropagation(); pop(1.4); bubble(parseFloat(rider.dataset.x || X0), "meow!"); hop(); });
  cat.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); cat.dispatchEvent(new Event("click")); } });

  // helpers --------------------------------------------------------------
  const toHost = (x) => (x / W) * host.clientWidth; // user units to px for doodles
  function bubble(x, word) {
    const r = svg.getBoundingClientRect(), hr = host.getBoundingClientRect();
    boom(host, toHost(x) , (Y / H) * r.height - 20 + (r.top - hr.top), word);
  }
  function wobble(g) { g.classList.remove("wob"); void g.getBoundingClientRect(); g.classList.add("wob"); }
  function hop() {
    if (reducedMotion) return;
    catHop.classList.remove("hop"); void catHop.getBoundingClientRect(); catHop.classList.add("hop");
  }
  let homeX = X0;
  // Hop to a node and come back, so the cat does not lose its place in the line.
  function hopTo(x, back) {
    const prev = homeX; place(x); hop();
    if (back) setTimeout(() => place(prev), 900);
  }
  function place(x) {
    rider.style.transform = `translateX(${x}px)`; rider.dataset.x = x;
  }
  place(X0);

  let lastShown = -1, lastBucket = -1, hopTimer = null;
  const api = {
    // shown: stage index being displayed, within: 0 to 1 progress inside it, state: idle | running | done
    set({ shown, within = 0, state }) {
      const u = state === "done" ? 1 : state === "idle" ? 0 : Math.min(1, (Math.max(0, shown) + within) / STAGES.length);
      fill.style.transform = `scaleX(${u})`;
      homeX = uToX(u);
      place(homeX);
      nodes.forEach((n, k) => {
        const done = state === "done" || (state === "running" && k < shown);
        n.g.classList.toggle("full", done);
        n.orb.setAttribute("fill", done ? `url(#sph${k})` : "url(#sphEmpty)");
        n.tick.classList.toggle("draw", done);
        if (done && !n.done) { wobble(n.g); pop(1 + k * 0.1); }
        n.done = done;
      });
      svg.classList.toggle("running", state === "running");
      // A hop for every stage change and every quarter of a stage, so the cat keeps moving.
      const bucket = Math.floor(within * 4);
      if (state === "running" && (shown !== lastShown || bucket !== lastBucket)) hop();
      if (state === "done" && lastShown !== -2) { hop(); setTimeout(hop, 500); }
      lastShown = state === "done" ? -2 : shown; lastBucket = bucket;
    },
    reset() { lastShown = -1; lastBucket = -1; api.set({ shown: 0, state: "idle" }); },
  };
  api.reset();
  return api;
}
