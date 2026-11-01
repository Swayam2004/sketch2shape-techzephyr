// DoodleLayer: hand-drawn SVG marks that draw themselves in, the boil-line wobble,
// the user's floating scribbles, background collage scraps and the eye-head silhouette.
import { reducedMotion } from "./store.js";
import { pop } from "./audio.js";

const NS = "http://www.w3.org/2000/svg";
export const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  parent?.appendChild(e);
  return e;
};
const rnd = (a, b) => a + Math.random() * (b - a);
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

// Boil line: re-seed the displacement noise 8 times a second so every stroke jitters between 2 or 3 frames.
export function startBoil() {
  if (reducedMotion) return;
  const turb = document.querySelector("#boil feTurbulence");
  let seed = 1;
  setInterval(() => turb?.setAttribute("seed", String((seed = (seed % 3) + 1))), 130);
}

function starburst(cx, cy, r1, r2, n = 14) {
  const pts = [];
  for (let i = 0; i < n * 2; i++) {
    const a = (i / (n * 2)) * Math.PI * 2, r = (i % 2 ? r1 : r2) * rnd(0.85, 1.1);
    pts.push(`${(cx + Math.cos(a) * r).toFixed(1)},${(cy + Math.sin(a) * r).toFixed(1)}`);
  }
  return pts.join(" ");
}

function lettering(parent, text, x, y, size) {
  const base = { x, y, "text-anchor": "middle", "font-size": size, "class": "letters" };
  // Outline first, fill on top, so the letters read like white marker with a black edge.
  const back = el("text", { ...base, class: "letters back", pathLength: 1 }, parent); back.textContent = text;
  const front = el("text", { ...base, class: "letters front", pathLength: 1 }, parent); front.textContent = text;
}

// A starburst with lettering that scribbles in, holds, then fades. `host` must be position:relative or absolute.
export function boom(host, x, y, word = pick(["BOOM!", "WOW!", "ooh!", "POP!", "ta-da!"])) {
  const size = 200;
  const svg = el("svg", { viewBox: "0 0 200 200", class: "doodle boom", width: size, height: size });
  svg.style.left = `${x - size / 2}px`; svg.style.top = `${y - size / 2}px`;
  svg.style.setProperty("--tilt", `${rnd(-12, 12)}deg`);
  el("polygon", { points: starburst(100, 100, 52, 92), class: "burst" }, svg);
  for (let i = 0; i < 6; i++) {
    const a = rnd(0, Math.PI * 2);
    el("path", { d: `M${100 + Math.cos(a) * 96} ${100 + Math.sin(a) * 96} l${Math.cos(a) * 14} ${Math.sin(a) * 14}`, class: "stroke draw", pathLength: 1 }, svg);
  }
  lettering(svg, word, 100, 112, 38);
  host.appendChild(svg);
  setTimeout(() => svg.remove(), reducedMotion ? 900 : 1700);
}

const STICKERS = [
  (s) => el("polygon", { points: starburst(30, 30, 12, 26, 5), class: "fillY stroke draw", pathLength: 1 }, s),
  (s) => el("path", { d: "M30 50 C5 32 8 10 22 12 C28 13 30 20 30 20 C30 20 32 13 38 12 C52 10 55 32 30 50Z", class: "fillM stroke draw", pathLength: 1 }, s),
  (s) => el("path", { d: "M30 30 m0 0 c4 -4 10 -2 10 4 c0 8 -14 10 -18 2 c-6 -12 8 -24 22 -18 c16 8 8 30 -10 32", class: "stroke draw", pathLength: 1 }, s),
  (s) => el("path", { d: "M6 40 q8 -22 14 -2 t14 -2 t14 -2 M44 20 l10 -8 m-10 8 l12 4", class: "stroke draw", pathLength: 1 }, s),
  (s) => el("path", { d: "M8 48 C20 10 40 10 50 12 M50 12 l-12 -4 M50 12 l-6 12", class: "stroke draw", pathLength: 1 }, s),
];

export function sticker(host, x, y) {
  const svg = el("svg", { viewBox: "0 0 60 60", class: "doodle sticker", width: 56, height: 56 });
  svg.style.left = `${x - 28}px`; svg.style.top = `${y - 28}px`;
  svg.style.setProperty("--tilt", `${rnd(-18, 18)}deg`);
  pick(STICKERS)(svg);
  host.appendChild(svg);
  pop(rnd(0.9, 1.5));
}

// Scribbles the user draws while the job runs. They float and bob, so the sketch panel stays busy.
export function createScribbleLayer(host) {
  const svg = el("svg", { class: "scribbles" });
  host.appendChild(svg);
  let path = null, pts = [], enabled = false;
  const at = (e) => { const r = svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  svg.addEventListener("pointerdown", (e) => {
    if (!enabled) return;
    svg.setPointerCapture(e.pointerId);
    pts = [at(e)];
    const g = el("g", { class: "scribble" }, svg);
    g.style.setProperty("--dx", `${rnd(-14, 14)}px`); g.style.setProperty("--dy", `${rnd(-14, 14)}px`);
    g.style.animationDelay = `${rnd(0, 1.5)}s`;
    const dark = el("path", { class: "sc-dark", fill: "none" }, g);
    const light = el("path", { class: "sc-light", fill: "none" }, g);
    path = [dark, light];
  });
  svg.addEventListener("pointermove", (e) => {
    if (!path) return;
    pts.push(at(e));
    const d = "M" + pts.map((p) => p.map((n) => n.toFixed(1)).join(" ")).join(" L");
    path.forEach((p) => p.setAttribute("d", d));
  });
  const end = () => { path = null; };
  svg.addEventListener("pointerup", end);
  svg.addEventListener("pointercancel", end);
  return {
    setEnabled(v) { enabled = v; svg.classList.toggle("on", v); },
    clear() { svg.querySelectorAll(".scribble").forEach((n) => n.remove()); },
  };
}

// ---- background collage scraps --------------------------------------------------------------

const SCRAPS = {
  moon: () => `<circle cx="50" cy="50" r="44" fill="var(--sand)" stroke="var(--ink)" stroke-width="2"/><circle cx="50" cy="50" r="44" fill="url(#ht)" opacity=".5"/><circle cx="34" cy="36" r="8" fill="var(--ink)" opacity=".25"/><circle cx="62" cy="62" r="11" fill="var(--ink)" opacity=".25"/><circle cx="64" cy="30" r="5" fill="var(--ink)" opacity=".25"/>`,
  sun: () => `<polygon points="${starburst(50, 50, 28, 46, 12)}" fill="var(--mustard)" stroke="var(--ink)" stroke-width="2"/><circle cx="50" cy="50" r="22" fill="var(--mustard)" stroke="var(--ink)" stroke-width="2"/><circle cx="50" cy="50" r="22" fill="url(#ht)" opacity=".35"/>`,
  butterfly: () => `<path d="M50 50 C20 5 0 30 18 52 C4 70 26 90 50 58 C74 90 96 70 82 52 C100 30 80 5 50 50Z" fill="var(--sage)" stroke="var(--ink)" stroke-width="2"/><path d="M50 50 C20 5 0 30 18 52" fill="url(#ht)" opacity=".6"/><circle cx="26" cy="40" r="6" fill="var(--mustard)"/><circle cx="74" cy="40" r="6" fill="var(--mustard)"/><rect x="48" y="36" width="4" height="34" rx="2" fill="var(--ink)"/>`,
  flower: () => `${[0, 60, 120, 180, 240, 300].map((a) => `<ellipse cx="50" cy="24" rx="14" ry="24" transform="rotate(${a} 50 50)" fill="var(--c)" stroke="var(--ink)" stroke-width="2"/>`).join("")}<circle cx="50" cy="50" r="11" fill="var(--mustard)" stroke="var(--ink)" stroke-width="2"/>`,
  star: () => `<polygon points="${starburst(50, 52, 20, 46, 5)}" fill="var(--c)" stroke="var(--ink)" stroke-width="2"/>`,
  scroll: () => `<rect x="14" y="26" width="72" height="48" rx="6" fill="var(--sand)" stroke="var(--ink)" stroke-width="2"/><ellipse cx="14" cy="50" rx="8" ry="24" fill="var(--terra)" stroke="var(--ink)" stroke-width="2"/><path d="M28 40h46M28 50h40M28 60h44" stroke="var(--ink)" stroke-width="2" stroke-linecap="round"/>`,
  clock: () => `<path d="M50 8 C80 8 90 34 80 56 C78 70 84 86 76 92 C70 96 66 84 60 84 C52 84 54 98 44 96 C34 94 38 80 30 72 C12 62 10 8 50 8Z" fill="var(--cream)" stroke="var(--ink)" stroke-width="2"/><path d="M50 22v26l16 10" stroke="var(--ink)" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M50 8 C80 8 90 34 80 56" fill="url(#ht)" opacity=".4"/>`,
  eye: () => `<path d="M4 50 C26 14 74 14 96 50 C74 86 26 86 4 50Z" fill="var(--cream)" stroke="var(--ink)" stroke-width="2"/><circle cx="50" cy="50" r="22" fill="var(--teal)" stroke="var(--ink)" stroke-width="2"/><path d="M50 50 m0 0 a4 4 0 1 1 6 4 a10 10 0 1 1 -14 -8 a16 16 0 1 1 22 18" fill="none" stroke="var(--cream)" stroke-width="2.5"/>`,
  heart: () => `<path d="M50 88 C8 56 14 18 36 20 C44 21 50 30 50 30 C50 30 56 21 64 20 C86 18 92 56 50 88Z" fill="var(--c)" stroke="var(--ink)" stroke-width="2"/>`,
  mushroom: () => `<path d="M8 52 C8 20 92 20 92 52Z" fill="var(--terra)" stroke="var(--ink)" stroke-width="2"/><circle cx="30" cy="40" r="6" fill="var(--cream)"/><circle cx="58" cy="34" r="5" fill="var(--cream)"/><circle cx="72" cy="46" r="4" fill="var(--cream)"/><path d="M38 52h24v34a12 6 0 0 1 -24 0Z" fill="var(--cream)" stroke="var(--ink)" stroke-width="2"/>`,
  stairs: () => `<path d="M6 92V76h18V60h18V44h18V28h18V12h16v80Z" fill="var(--sky)" stroke="var(--ink)" stroke-width="2"/><path d="M6 92V76h18V60h18V44h18V28h18V12h16v80Z" fill="url(#ht)" opacity=".35"/>`,
  ear: () => `<path d="M30 90 C10 70 14 20 50 12 C86 6 92 52 64 62 C54 66 56 78 50 84 C44 92 36 94 30 90Z" fill="var(--sand)" stroke="var(--ink)" stroke-width="2"/><path d="M42 30 C62 24 70 44 54 52 C48 56 46 62 50 70" fill="none" stroke="var(--ink)" stroke-width="2"/>`,
  swirl: () => `<circle cx="50" cy="50" r="44" fill="var(--sky)" stroke="var(--ink)" stroke-width="2"/><path d="M50 50 m0 0 a5 5 0 1 1 8 3 a11 11 0 1 1 -17 -10 a18 18 0 1 1 28 14 a26 26 0 1 1 -40 -22" fill="none" stroke="var(--cream)" stroke-width="3.5" stroke-linecap="round"/>`,
  news: () => `<path d="M4 10 L30 4 L58 12 L90 6 L96 40 L90 66 L96 94 L60 88 L30 96 L6 90 L12 56 L4 36Z" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.5"/><rect x="14" y="16" width="36" height="8" fill="var(--ink)"/>${[34, 42, 50, 58, 66, 74].map((y) => `<path d="M14 ${y}h30M54 ${y}h32" stroke="var(--ink)" stroke-width="2" opacity=".55"/>`).join("")}<rect x="56" y="16" width="30" height="14" fill="url(#ht)"/>`,
};

const COLOURS = ["var(--magenta)", "var(--teal)", "var(--sky)", "var(--mustard)", "var(--terra)", "var(--sage)"];

export function buildScraps(host, count) {
  const kinds = Object.keys(SCRAPS);
  const n = Math.min(count, kinds.length + 4);
  for (let i = 0; i < n; i++) {
    const kind = kinds[i % kinds.length];
    const d = document.createElement("div");
    const depth = rnd(8, 46);
    const size = rnd(70, 150);
    d.className = "scrap";
    d.style.cssText = `left:${rnd(-2, 94)}%;top:${rnd(-2, 92)}%;width:${size}px;--d:${depth};--r:${rnd(-24, 24)}deg;--c:${pick(COLOURS)};animation-delay:${-rnd(0, 8)}s`;
    d.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true">${SCRAPS[kind]()}</svg>`;
    host.appendChild(d);
  }
  const set = (x, y) => { host.style.setProperty("--px", x.toFixed(3)); host.style.setProperty("--py", y.toFixed(3)); };
  addEventListener("pointermove", (e) => set((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1), { passive: true });
  addEventListener("deviceorientation", (e) => {
    if (e.gamma == null) return;
    set(Math.max(-1, Math.min(1, e.gamma / 30)), Math.max(-1, Math.min(1, (e.beta - 40) / 30)));
  }, { passive: true });
}

// ---- eye-head silhouette --------------------------------------------------------------------

export function buildHead(host) {
  host.innerHTML = `
  <svg viewBox="0 0 220 280" role="img" aria-label="A head made of a flower, a moon and a butterfly. Click it and the eyes blink.">
    <path d="M10 280 C10 220 50 200 80 196 L80 170 C60 160 50 130 54 100 C58 60 90 44 116 46 C146 48 168 74 164 108 C162 130 156 152 140 168 L140 196 C176 204 210 224 210 280Z" fill="var(--ink)"/>
    <path d="M10 280 C10 220 50 200 80 196 L80 170 C60 160 50 130 54 100 C58 60 90 44 116 46 C146 48 168 74 164 108 C162 130 156 152 140 168 L140 196 C176 204 210 224 210 280Z" fill="url(#ht)" opacity=".55"/>
    <g class="sprout">
      <circle cx="70" cy="40" r="26" fill="var(--sand)" stroke="var(--ink)" stroke-width="2"/><circle cx="62" cy="34" r="6" fill="var(--ink)" opacity=".25"/>
      <g transform="translate(112 6) scale(.52)">${[0, 72, 144, 216, 288].map((a) => `<ellipse cx="50" cy="24" rx="15" ry="26" transform="rotate(${a} 50 50)" fill="var(--magenta)" stroke="var(--cream)" stroke-width="3"/>`).join("")}<circle cx="50" cy="50" r="12" fill="var(--mustard)"/></g>
      <g transform="translate(138 20) scale(.5)">${SCRAPS.butterfly()}</g>
    </g>
    <g class="eyes">
      ${[88, 134].map((x) => `<g class="eye" data-cx="${x}" data-cy="104"><ellipse cx="${x}" cy="104" rx="15" ry="11" fill="var(--cream)"/><circle class="iris" cx="${x}" cy="104" r="6.5" fill="var(--magenta)"/><circle class="pupil" cx="${x}" cy="104" r="2.6" fill="var(--ink)"/><ellipse class="lid" cx="${x}" cy="104" rx="16" ry="12" fill="var(--ink)"/></g>`).join("")}
    </g>
  </svg>`;
  const eyes = [...host.querySelectorAll(".eye")];
  const svg = host.querySelector("svg");
  addEventListener("pointermove", (e) => {
    const r = svg.getBoundingClientRect(), k = r.width / 220;
    for (const eye of eyes) {
      const cx = r.left + +eye.dataset.cx * k, cy = r.top + +eye.dataset.cy * k;
      const dx = e.clientX - cx, dy = e.clientY - cy, d = Math.hypot(dx, dy) || 1, m = Math.min(5, d / 40);
      eye.querySelectorAll(".iris,.pupil").forEach((n) => { n.style.transform = `translate(${(dx / d) * m}px,${(dy / d) * m}px)`; });
    }
  }, { passive: true });
  host.addEventListener("click", () => {
    host.classList.remove("blink"); void host.offsetWidth; host.classList.add("blink");
    pop(1.3);
  });
}
