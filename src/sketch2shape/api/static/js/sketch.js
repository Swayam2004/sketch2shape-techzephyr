// SketchCanvas: draw, erase, undo, clear, or drop an image. Exports a PNG for the API and a coarse
// silhouette mask that the centre stage uses for its dots and its blob.
const SIZE = 512;
const MAX_UPLOAD = 10 * 1024 * 1024;
// Dark colours only. The server thresholds the sketch (Otsu), so a pale stroke would vanish.
export const INKS = ["#161616", "#b01e6e", "#16807d", "#b4532f", "#1f2f5c"];

export function createSketch(canvas, { onChange, onError }) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const history = [];
  let tool = "pen", ink = INKS[0], width = 6, drawing = false, dirty = false;

  const blank = () => { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, SIZE, SIZE); };
  const snap = () => { history.push(ctx.getImageData(0, 0, SIZE, SIZE)); if (history.length > 30) history.shift(); };
  const pos = (e) => { const r = canvas.getBoundingClientRect(); return [((e.clientX - r.left) * SIZE) / r.width, ((e.clientY - r.top) * SIZE) / r.height]; };
  const touch = () => { dirty = true; onChange(); };
  blank();

  canvas.addEventListener("pointerdown", (e) => {
    snap(); drawing = true; canvas.setPointerCapture(e.pointerId);
    const [x, y] = pos(e);
    ctx.lineCap = ctx.lineJoin = "round";
    ctx.strokeStyle = tool === "pen" ? ink : "#fff";
    ctx.lineWidth = tool === "pen" ? width : width * 4;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 0.01, y); ctx.stroke();
    touch();
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drawing) return;
    const [x, y] = pos(e);
    ctx.lineTo(x, y); ctx.stroke();
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
    setTool(t) { tool = t; },
    setInk(c) { ink = c; tool = "pen"; },
    setWidth(w) { width = w; },
    undo() { const s = history.pop(); if (s) ctx.putImageData(s, 0, 0); dirty = history.length > 0; onChange(); },
    clear() { snap(); blank(); dirty = false; onChange(); },
    loadFile,
    get dirty() { return dirty; },
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
