// SketchCanvas: draw with four brushes, erase, undo, clear, or drop an image. Exports a PNG for the API and a coarse
// silhouette mask that the centre stage uses for its dots and its blob.
const SIZE = 512;
const MAX_UPLOAD = 10 * 1024 * 1024;
// Dark colours only. The server thresholds the sketch (Otsu), so a pale stroke would vanish.
export const INKS = ["#161616", "#b01e6e", "#16807d", "#b4532f", "#1f2f5c"];
export const BRUSHES = [
  { id: "pen", label: "pen", hint: "Even round line" },
  { id: "marker", label: "marker", hint: "Flat nib, thick and thin like a chisel" },
  { id: "pencil", label: "pencil", hint: "Rough, grainy line" },
  { id: "brush", label: "brush", hint: "Fat when slow, thin when fast" },
];
// Pixel widths on the 512 px canvas. Index 1 matches the old default of 6.
export const WEIGHTS = [3, 6, 11, 18];

// Each brush draws one segment from a to b. `st` carries state between segments of one stroke.
// Every brush stays dark and mostly opaque, because the server thresholds the sketch (Otsu).
const DRAW = {
  pen(ctx, a, b, w) { line(ctx, a, b, w); },
  marker(ctx, a, b, w) {
    const d = [Math.cos(-Math.PI / 4) * w * 0.8, Math.sin(-Math.PI / 4) * w * 0.8];
    ctx.beginPath();
    ctx.moveTo(a[0] + d[0], a[1] + d[1]); ctx.lineTo(b[0] + d[0], b[1] + d[1]);
    ctx.lineTo(b[0] - d[0], b[1] - d[1]); ctx.lineTo(a[0] - d[0], a[1] - d[1]); ctx.closePath();
    ctx.fill(); ctx.lineWidth = 1; ctx.stroke();
  },
  pencil(ctx, a, b, w) {
    ctx.globalAlpha = 0.85;
    for (let k = 0; k < 3; k++) {
      const j = () => (Math.random() - 0.5) * w * 0.7;
      line(ctx, [a[0] + j(), a[1] + j()], [b[0] + j(), b[1] + j()], Math.max(1, w * 0.45));
    }
    ctx.globalAlpha = 1;
  },
  brush(ctx, a, b, w, st) {
    const speed = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const target = w * Math.min(1.5, Math.max(0.35, 1.5 - speed / 18));
    st.w = st.w == null ? target : st.w * 0.7 + target * 0.3;
    line(ctx, a, b, st.w);
  },
};
function line(ctx, a, b, w) {
  ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
}

export function createSketch(canvas, { onChange, onError }) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const history = [];
  // `tool` is a brush id, or "eraser".
  let tool = "pen", lastBrush = "pen", ink = INKS[0], width = WEIGHTS[1], drawing = false, dirty = false, last = null, st = {};

  const blank = () => { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, SIZE, SIZE); };
  const snap = () => { history.push(ctx.getImageData(0, 0, SIZE, SIZE)); if (history.length > 30) history.shift(); };
  const pos = (e) => { const r = canvas.getBoundingClientRect(); return [((e.clientX - r.left) * SIZE) / r.width, ((e.clientY - r.top) * SIZE) / r.height]; };
  const touch = () => { dirty = true; onChange(); };
  blank();

  const stroke = (a, b) => {
    if (tool === "eraser") { ctx.globalAlpha = 1; line(ctx, a, b, width * 4); return; }
    DRAW[tool](ctx, a, b, width, st);
  };
  canvas.addEventListener("pointerdown", (e) => {
    snap(); drawing = true; canvas.setPointerCapture(e.pointerId);
    ctx.lineCap = ctx.lineJoin = "round";
    ctx.strokeStyle = ctx.fillStyle = tool === "eraser" ? "#fff" : ink;
    st = {}; last = pos(e);
    stroke(last, [last[0] + 0.01, last[1]]);
    touch();
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drawing) return;
    // Coalesced events keep fast strokes smooth on browsers that batch pointer moves.
    for (const ev of e.getCoalescedEvents?.().length ? e.getCoalescedEvents() : [e]) {
      const p = pos(ev); stroke(last, p); last = p;
    }
  });
  for (const ev of ["pointerup", "pointercancel"]) canvas.addEventListener(ev, () => { drawing = false; });

  async function loadFile(file) {
    if (!file) return;
    if (!/^image\/(png|jpeg|webp)$/.test(file.type)) return onError("Use a PNG, JPG or WebP image.");
    if (file.size > MAX_UPLOAD) return onError("That file is over 10 MB. Pick a smaller one.");
    const img = new Image();
    img.src = URL.createObjectURL(file);
    try { await img.decode(); } catch { return onError("That image would not open."); }
    snap(); blank();
    const k = Math.min(SIZE / img.width, SIZE / img.height);
    ctx.drawImage(img, (SIZE - img.width * k) / 2, (SIZE - img.height * k) / 2, img.width * k, img.height * k);
    URL.revokeObjectURL(img.src);
    touch();
  }

  canvas.parentElement.addEventListener("dragover", (e) => { e.preventDefault(); canvas.parentElement.classList.add("drop"); });
  canvas.parentElement.addEventListener("dragleave", () => canvas.parentElement.classList.remove("drop"));
  canvas.parentElement.addEventListener("drop", (e) => {
    e.preventDefault(); canvas.parentElement.classList.remove("drop");
    loadFile(e.dataTransfer.files[0]);
  });

  return {
    setTool(t) { tool = t; if (t !== "eraser") lastBrush = t; },
    setInk(c) { ink = c; tool = lastBrush; },
    setWidth(w) { width = w; },
    undo() { const s = history.pop(); if (s) ctx.putImageData(s, 0, 0); dirty = history.length > 0; onChange(); },
    clear() { snap(); blank(); dirty = false; onChange(); },
    loadFile,
    get dirty() { return dirty; },
    get tool() { return tool; },
    toBlob: () => new Promise((res) => canvas.toBlob(res, "image/png")),
    // Dark-pixel mask on a coarse grid, rows top to bottom. `fill` lists pixels that are ink.
    mask(grid = 96) {
      const small = document.createElement("canvas");
      small.width = small.height = grid;
      const c = small.getContext("2d", { willReadFrequently: true });
      c.drawImage(canvas, 0, 0, grid, grid);
      const d = c.getImageData(0, 0, grid, grid).data;
      const on = new Uint8Array(grid * grid);
      for (let i = 0; i < grid * grid; i++) on[i] = d[i * 4] + d[i * 4 + 1] + d[i * 4 + 2] < 600 ? 1 : 0;
      return { grid, on };
    },
  };
}
