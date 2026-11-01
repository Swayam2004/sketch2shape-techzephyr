// CenterStage: one WebGL renderer for everything in the middle of the screen. It cycles toy objects,
// runs the per-stage experiences (dots, blob, refine) and, at the end, shows the real result.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";
import { OBJExporter } from "three/addons/exporters/OBJExporter.js";
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";
import { TIME, DPR, CELL, palette, toon, outlineMaterial, dotMaterial, withOutline } from "./shaders.js";
import { OBJECT_NAMES, makeObject, makeStar } from "./objects.js";
import { reducedMotion, isMobile } from "./store.js";
import { pop, rustle, chime } from "./audio.js";

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const rnd = (a, b) => a + Math.random() * (b - a);

function dispose(obj) {
  obj.traverse((n) => {
    n.geometry?.dispose();
    for (const m of [].concat(n.material || [])) { m.map?.dispose(); m.dispose(); }
  });
}

// ---- silhouette helpers ---------------------------------------------------------------------

// Fill the sketch: whatever the outside cannot reach is inside. Returns a radius per angle bin, in world units.
function radialProfile({ grid, on }, worldWidth, bins = 128) {
  const outside = new Uint8Array(grid * grid);
  const stack = [];
  const push = (i) => { if (!on[i] && !outside[i]) { outside[i] = 1; stack.push(i); } };
  for (let k = 0; k < grid; k++) { push(k); push((grid - 1) * grid + k); push(k * grid); push(k * grid + grid - 1); }
  while (stack.length) {
    const i = stack.pop(), x = i % grid, y = (i / grid) | 0;
    if (x > 0) push(i - 1); if (x < grid - 1) push(i + 1); if (y > 0) push(i - grid); if (y < grid - 1) push(i + grid);
  }
  let sx = 0, sy = 0, n = 0;
  for (let i = 0; i < grid * grid; i++) if (!outside[i]) { sx += i % grid; sy += (i / grid) | 0; n++; }
  const k = worldWidth / grid;
  if (n < 12) return { r: new Float32Array(bins).fill(1.2), depth: 0.7, empty: true };
  const cx = sx / n, cy = sy / n, r = new Float32Array(bins);
  for (let i = 0; i < grid * grid; i++) {
    if (outside[i]) continue;
    const dx = (i % grid) - cx, dy = cy - ((i / grid) | 0); // y up
    const b = Math.floor(((Math.atan2(dy, dx) + Math.PI) / (Math.PI * 2)) * bins) % bins;
    r[b] = Math.max(r[b], Math.hypot(dx, dy) * k);
  }
  // Fill empty bins from neighbours, then smooth so the blob has no spikes.
  for (let pass = 0; pass < 3; pass++) for (let b = 0; b < bins; b++) if (!r[b]) r[b] = Math.max(r[(b + bins - 1) % bins], r[(b + 1) % bins]) * 0.98;
  const sm = new Float32Array(bins);
  for (let b = 0; b < bins; b++) { let s = 0; for (let j = -3; j <= 3; j++) s += r[(b + j + bins) % bins]; sm[b] = s / 7; }
  const avg = sm.reduce((a, b) => a + b, 0) / bins;
  return { r: sm, depth: avg * 0.55, empty: false };
}
const sample = (r, theta) => {
  const bins = r.length, f = ((theta + Math.PI) / (Math.PI * 2)) * bins, i = Math.floor(f) % bins, t = f - Math.floor(f);
  return r[i] * (1 - t) + r[(i + 1) % bins] * t;
};

// ---- stage ----------------------------------------------------------------------------------

export function createStage({ canvas, getMask, onBoom, onSticker, onStars }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  let pr = Math.min(devicePixelRatio, isMobile ? 1.5 : 2);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 50);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x887766, 1.4));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(2, 3, 4); scene.add(sun);
  const root = new THREE.Group(); scene.add(root);
  const extras = new THREE.Group(); scene.add(extras); // stars and confetti live here, outside the spinning root
  const controls = new OrbitControls(camera, canvas);
  controls.enabled = false; controls.enableDamping = true;

  let P = palette();
  const cb = { onBoom, onSticker, onStars };
  let content = null; // { kind, group, obj?, update?(t,dt), dispose? }
  let experience = "objects"; // objects | dots | blob | refine | result
  let spin = new THREE.Vector2(), spinTarget = 0;
  let lastInteract = 0, cycleAt = 0, cycleIdx = 0, queue = [], trans = null;
  let lod = 0.8, lodAuto = true, morph = 0.3, viewMode = "color";
  let result = null; // { group, hasColors }
  let paused = false;

  // pointer state in NDC and on the z = 0 plane
  const ptr = { ndc: new THREE.Vector2(0, 0), p: new THREE.Vector3(0, 0, 0), down: false, hit: null, id: null };
  const ray = new THREE.Raycaster();
  const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
  const updatePointer = () => { ray.setFromCamera(ptr.ndc, camera); ray.ray.intersectPlane(plane, ptr.p); };

  // ---- confetti: one instanced mesh, 160 scraps reused ----
  const CONF = 160;
  const confGeo = new THREE.PlaneGeometry(0.14, 0.09);
  const conf = new THREE.InstancedMesh(confGeo, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }), CONF);
  conf.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(CONF * 3), 3);
  conf.frustumCulled = false; extras.add(conf);
  const bits = Array.from({ length: CONF }, () => ({ life: 0, p: new THREE.Vector3(), v: new THREE.Vector3(), r: new THREE.Euler(), vr: new THREE.Vector3() }));
  const tmp = new THREE.Object3D();
  let confNext = 0;
  function burst(at, n = 44) {
    const cols = [P.magenta, P.teal, P.sky, P.mustard, P.terra, P.sage, P.cream];
    n = reducedMotion ? 10 : isMobile ? Math.min(n, 28) : n;
    for (let k = 0; k < n; k++) {
      const b = bits[confNext = (confNext + 1) % CONF];
      b.life = rnd(0.9, 1.7); b.p.copy(at);
      b.v.set(rnd(-2.4, 2.4), rnd(0.8, 3.6), rnd(-1, 1.6)); b.vr.set(rnd(-9, 9), rnd(-9, 9), rnd(-9, 9));
      conf.setColorAt(confNext, cols[(Math.random() * cols.length) | 0]);
    }
    conf.instanceColor.needsUpdate = true;
  }
  function updateConfetti(dt) {
    for (let i = 0; i < CONF; i++) {
      const b = bits[i];
      if (b.life > 0) { b.life -= dt; b.v.y -= 7 * dt; b.v.multiplyScalar(0.985); b.p.addScaledVector(b.v, dt); b.r.x += b.vr.x * dt; b.r.y += b.vr.y * dt; b.r.z += b.vr.z * dt; }
      tmp.position.copy(b.p); tmp.rotation.copy(b.r); tmp.scale.setScalar(b.life > 0 ? clamp(b.life * 2, 0, 1) : 0); tmp.updateMatrix();
      conf.setMatrixAt(i, tmp.matrix);
    }
    conf.instanceMatrix.needsUpdate = true;
  }

  // ---- content swapping with a pop transition ----
  // The root only ever holds the current content, so clear every child. Removing just `content.group`
  // once left a stale toy on screen after reset() dropped the reference.
  function clearRoot() {
    for (const c of [...root.children]) { root.remove(c); dispose(c); }
    content?.dispose?.(); content = null; result = null;
  }
  function place(next) {
    clearRoot();
    content = next;
    root.add(next.group);
    root.rotation.set(0, 0, 0); spin.set(0, 0); root.scale.setScalar(1);
    trans = { t: 0, dir: 1 }; // pop in
    next.group.scale.setScalar(0.001);
  }

  function objectContent(name) {
    if (name === "sketch blob") return blobContent("morph");
    const obj = makeObject(name, P);
    return { kind: "object", name, group: obj.group, obj };
  }

  // ---- dots (preprocess) ----
  function dotsContent() {
    const mask = getMask(96), grid = mask.grid, pts = [];
    for (let i = 0; i < grid * grid; i++) if (mask.on[i]) pts.push(i);
    const N = Math.min(isMobile ? 1400 : 2600, Math.max(pts.length, 0));
    const count = N < 40 ? 600 : N;
    const home = new Float32Array(count * 3), pos = new Float32Array(count * 3), vel = new Float32Array(count * 3), size = new Float32Array(count);
    const w = 3.4;
    for (let i = 0; i < count; i++) {
      if (N < 40) { const a = (i / count) * Math.PI * 2 * 3, r = 0.4 + (i / count) * 1.1; home.set([Math.cos(a) * r, Math.sin(a) * r, 0], i * 3); }
      else { const c = pts[(Math.random() * pts.length) | 0]; home.set([((c % grid) + Math.random() - 0.5) / grid * w - w / 2, w / 2 - (((c / grid) | 0) + Math.random() - 0.5) / grid * w, 0], i * 3); }
      const a = Math.random() * Math.PI * 2, r = 3 + Math.random() * 2;
      pos.set([Math.cos(a) * r, Math.sin(a) * r, rnd(-1, 1)], i * 3);
      size[i] = rnd(0.7, 1.4);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
    const points = new THREE.Points(geo, dotMaterial(P.ink));
    points.frustumCulled = false;
    const group = new THREE.Group(); group.add(points);
    let age = 0;
    return {
      kind: "dots", group,
      update(t, dt) {
        age += dt;
        const k = Math.min(1, age / 1.2) * 14 + 2, p = geo.attributes.position.array;
        for (let i = 0; i < count; i++) {
          const j = i * 3;
          let fx = (home[j] - p[j]) * k, fy = (home[j + 1] - p[j + 1]) * k, fz = (0 - p[j + 2]) * k;
          // The cursor shoves dots away, then they settle back into the outline.
          const dx = p[j] - ptr.p.x, dy = p[j + 1] - ptr.p.y, d2 = dx * dx + dy * dy;
          if (d2 < 0.5) { const f = (0.5 - d2) * 60 / Math.sqrt(d2 + 0.01); fx += dx * f; fy += dy * f; fz += (Math.random() - 0.5) * 8; }
          vel[j] = (vel[j] + fx * dt) * 0.9; vel[j + 1] = (vel[j + 1] + fy * dt) * 0.9; vel[j + 2] = (vel[j + 2] + fz * dt) * 0.9;
          p[j] += vel[j] * dt * 6; p[j + 1] += vel[j + 1] * dt * 6; p[j + 2] += vel[j + 2] * dt * 6;
        }
        geo.attributes.position.needsUpdate = true;
      },
    };
  }

  // ---- blob (shape forming, refine, and a toy in the cycler) ----
  const LODS = isMobile ? [3, 6, 10, 14] : [4, 8, 14, 20];
  function blobContent(mode) {
    const mask = getMask(96);
    const prof = radialProfile(mask, 3.4);
    const levels = LODS.map((d) => {
      // Drop uv and normal first, otherwise the seam vertices never merge and the surface cracks when it deforms.
      const raw = new THREE.IcosahedronGeometry(1, d);
      raw.deleteAttribute("uv"); raw.deleteAttribute("normal");
      const g = mergeVertices(raw);
      const base = Float32Array.from(g.attributes.position.array);
      const n = base.length / 3, target = new Float32Array(base.length);
      for (let i = 0; i < n; i++) {
        const x = base[i * 3], y = base[i * 3 + 1], z = base[i * 3 + 2];
        const R = sample(prof.r, Math.atan2(y, x));
        target.set([x * R, y * R, z * prof.depth], i * 3);
      }
      g.setAttribute("position", new THREE.BufferAttribute(Float32Array.from(base), 3).setUsage(THREE.DynamicDrawUsage));
      return { g, base, target, sculpt: new Float32Array(base.length), n };
    });
    const mat = toon(P.teal, P.ink, { amp: 0 });
    const group = new THREE.Group();
    const meshes = levels.map(({ g }) => {
      const s = new THREE.Mesh(g, mat), o = new THREE.Mesh(g, outlineMaterial(P.ink, 0.03));
      const w = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: P.ink, wireframe: true }));
      s.visible = o.visible = w.visible = false; group.add(s, o, w);
      return { s, o, w };
    });
    let age = 0;
    const hitSphere = new THREE.Sphere(new THREE.Vector3(), 2.2);
    return {
      kind: "blob", mode, group, levels,
      update(t, dt) {
        age += dt;
        const li = mode === "morph" ? 2 : Math.round(lod * 3);
        const showToon = mode === "morph" || lod > 0.3, showWire = mode !== "morph" && lod < 0.7;
        meshes.forEach((m, i) => { m.s.visible = m.o.visible = i === li && showToon; m.w.visible = i === li && showWire; });
        const L = levels[li], p = L.g.attributes.position.array;
        const e = mode === "morph" ? 0.5 - 0.5 * Math.cos((t * 0.8) % (Math.PI * 2)) : morph;
        const k = e * e * (3 - 2 * e);
        let hit = null;
        if (ptr.down && experience !== "objects") { ray.setFromCamera(ptr.ndc, camera); hit = ray.ray.intersectSphere(hitSphere, new THREE.Vector3()); }
        for (let i = 0; i < L.n; i++) {
          const j = i * 3, b = 1.05 + 0.07 * Math.sin(t * 2 + L.base[j] * 4 + L.base[j + 1] * 3 + L.base[j + 2] * 5);
          if (hit) {
            const dx = hit.x - p[j], dy = hit.y - p[j + 1], dz = hit.z - p[j + 2], d = Math.hypot(dx, dy, dz);
            if (d < 0.8) { const f = (1 - d / 0.8) * 0.09; L.sculpt[j] += dx * f; L.sculpt[j + 1] += dy * f; L.sculpt[j + 2] += dz * f; }
          }
          L.sculpt[j] *= 0.995; L.sculpt[j + 1] *= 0.995; L.sculpt[j + 2] *= 0.995;
          p[j] = L.base[j] * b * (1 - k) + L.target[j] * k + L.sculpt[j];
          p[j + 1] = L.base[j + 1] * b * (1 - k) + L.target[j + 1] * k + L.sculpt[j + 1];
          p[j + 2] = L.base[j + 2] * b * (1 - k) + L.target[j + 2] * k + L.sculpt[j + 2];
        }
        L.g.attributes.position.needsUpdate = true;
        L.g.computeVertexNormals();
        L.g.computeBoundingSphere();
        if (mode === "morph") group.rotation.y = Math.sin(t * 0.7) * 0.6;
      },
    };
  }

  // ---- stars for the pop game ----
  const stars = [];
  let starTimer = 0, starCount = 0;
  function spawnStar() {
    if (stars.length >= 3) return;
    const g = makeStar(P); g.scale.setScalar(0.32);
    const a = Math.random() * Math.PI * 2;
    g.position.set(Math.cos(a) * rnd(1.7, 2.3), Math.sin(a) * rnd(0.8, 1.4), rnd(0.2, 0.8));
    extras.add(g);
    stars.push({ g, v: new THREE.Vector3(rnd(-0.3, 0.3), rnd(-0.2, 0.2), 0), born: performance.now() });
  }
  function clearStars() { while (stars.length) { const s = stars.pop(); extras.remove(s.g); dispose(s.g); } }
  function updateStars(t, dt) {
    for (const s of stars) {
      s.g.position.addScaledVector(s.v, dt); s.g.rotation.y += dt * 2; s.g.rotation.z = Math.sin(t * 2 + s.born) * 0.3;
      if (Math.abs(s.g.position.x) > 2.6) s.v.x *= -1; if (Math.abs(s.g.position.y) > 1.7) s.v.y *= -1;
    }
    if ((starTimer -= dt) <= 0) { starTimer = 1.6; spawnStar(); }
  }

  // ---- interaction ----
  let downAt = 0, downXY = [0, 0], pinch = null;
  const touches = new Map();
  canvas.addEventListener("pointerdown", (e) => {
    touches.set(e.pointerId, [e.clientX, e.clientY]);
    canvas.setPointerCapture(e.pointerId);
    ptr.down = true; ptr.id = e.pointerId; lastInteract = performance.now();
    downAt = lastInteract; downXY = [e.clientX, e.clientY];
    if (touches.size === 2) { const [a, b] = [...touches.values()]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s: root.scale.x }; }
    setPtr(e);
  });
  canvas.addEventListener("pointermove", (e) => {
    const prev = touches.get(e.pointerId);
    setPtr(e);
    if (!prev) return;
    touches.set(e.pointerId, [e.clientX, e.clientY]);
    lastInteract = performance.now();
    if (pinch && touches.size === 2 && experience !== "result") { const [a, b] = [...touches.values()]; root.scale.setScalar(clamp(pinch.s * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch.d, 0.5, 2.2)); return; }
    // Drag to spin the toy. The blob stage keeps the drag for sculpting.
    if (ptr.down && (experience === "objects" || experience === "refine") && experience !== "result") { spin.x += (e.clientX - prev[0]) * 0.012; spin.y += (e.clientY - prev[1]) * 0.012; }
  });
  const up = (e) => {
    touches.delete(e.pointerId); pinch = null;
    if (touches.size === 0) ptr.down = false;
    const moved = Math.hypot(e.clientX - downXY[0], e.clientY - downXY[1]);
    if (moved < 7 && performance.now() - downAt < 450 && e.type === "pointerup") click(e);
  };
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", up);
  canvas.addEventListener("wheel", (e) => { if (experience !== "result") { e.preventDefault(); root.scale.setScalar(clamp(root.scale.x * (e.deltaY > 0 ? 0.94 : 1.06), 0.5, 2.2)); } }, { passive: false });
  canvas.addEventListener("pointerleave", () => { ptr.ndc.set(0, 0); });

  function setPtr(e) {
    const r = canvas.getBoundingClientRect();
    ptr.ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    updatePointer();
  }

  function click(e) {
    const r = canvas.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    ray.setFromCamera(ptr.ndc, camera);
    const starHit = stars.length ? ray.intersectObjects(stars.map((s) => s.g), true)[0] : null;
    if (starHit) {
      const s = stars.find((s) => s.g === starHit.object.parent || s.g.children.includes(starHit.object));
      if (s) { burst(s.g.position, 30); extras.remove(s.g); dispose(s.g); stars.splice(stars.indexOf(s), 1); starCount++; cb.onStars(starCount); pop(1 + starCount * 0.05); cb.onBoom(x, y, "pop!"); return; }
    }
    if (experience === "result") return;
    const hit = content ? ray.intersectObject(content.group, true)[0] : null;
    if (content?.kind === "object" && hit) { content.obj.click(); burst(hit.point); cb.onBoom(x, y); pop(); return; }
    if (content?.kind === "blob" && hit && content.mode === "morph") { burst(hit.point); cb.onBoom(x, y); pop(); return; }
    if (experience === "refine" && !hit) cb.onSticker(x, y);
  }

  // ---- cycling toys ----
  const nextDelay = () => (reducedMotion ? 2600 : 1200 + Math.random() * 800);
  function nextName() {
    if (!queue.length) queue = [...OBJECT_NAMES, "sketch blob"].sort(() => Math.random() - 0.5);
    return queue.pop();
  }
  function cycle(now) {
    if (now < cycleAt) return;
    // Do not swap an object out from under a finger.
    if (ptr.down) { cycleAt = now + 400; return; }
    place(objectContent(nextName()));
    cycleAt = now + nextDelay();
  }

  // ---- result viewer ----
  function applyViewMode() {
    if (!result) return;
    result.group.traverse((n) => {
      if (!n.isMesh || n.userData.isOutline) return;
      n.userData.orig ??= n.material;
      const outline = n.userData.outline;
      if (outline) outline.visible = false;
      if (viewMode === "color") n.material = n.userData.orig;
      else if (viewMode === "clay") n.material = (n.userData.clay ??= new THREE.MeshStandardMaterial({ color: P.sand, roughness: 1, flatShading: false }));
      else if (viewMode === "wire") n.material = (n.userData.wire ??= new THREE.MeshBasicMaterial({ color: P.ink, wireframe: true }));
      else { n.material = (n.userData.half ??= toon(P.cream, P.ink)); if (outline) outline.visible = true; }
    });
  }

  async function loadResult(res) {
    let group;
    if (res.kind === "files") {
      const gltf = await new GLTFLoader().loadAsync(res.glb);
      group = gltf.scene;
    } else {
      // Mock mode: the final blob, coloured by height, stands in for a mesh from the server.
      const src = content?.levels ? content : blobContent("morph");
      const L = src.levels[3];
      const g = L.g.clone();
      g.setAttribute("position", new THREE.BufferAttribute(L.target.map((v, i) => v + L.sculpt[i]), 3));
      g.computeVertexNormals();
      const pos = g.attributes.position, col = new Float32Array(pos.count * 3), cs = [P.teal, P.sky, P.mustard, P.magenta];
      g.computeBoundingBox();
      const { min, max } = g.boundingBox, c = new THREE.Color();
      for (let i = 0; i < pos.count; i++) { const u = clamp((pos.getY(i) - min.y) / (max.y - min.y || 1)) * 3, a = Math.min(2, Math.floor(u)); c.copy(cs[a]).lerp(cs[a + 1], u - a); col.set([c.r, c.g, c.b], i * 3); }
      g.setAttribute("color", new THREE.BufferAttribute(col, 3));
      group = new THREE.Group(); group.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85 })));
    }
    const box = new THREE.Box3().setFromObject(group), size = box.getSize(new THREE.Vector3()), ctr = box.getCenter(new THREE.Vector3());
    const holder = new THREE.Group(); holder.add(group);
    group.position.sub(ctr);
    holder.scale.setScalar(2.4 / Math.max(size.x, size.y, size.z, 1e-6));
    // Collect first. Adding a child while traversing makes traverse visit the new child and recurse forever.
    const meshes = [];
    group.traverse((n) => { if (n.isMesh) meshes.push(n); });
    for (const n of meshes) { const o = new THREE.Mesh(n.geometry, outlineMaterial(P.ink, 0.012)); o.userData.isOutline = true; o.visible = false; n.add(o); n.userData.outline = o; }
    return holder;
  }

  async function showResult(res, tear) {
    let holder;
    try { holder = await loadResult(res); } catch (e) { console.error("viewer load failed", e); throw new Error(`The mesh file would not load in the 3D viewer (${e.message}).`); }
    renderer.render(scene, camera);
    const snapshot = canvas.toDataURL("image/png"); // frame to tear away
    experience = "result"; clearStars();
    clearRoot();
    root.rotation.set(0, 0, 0); root.scale.setScalar(1); root.add(holder);
    result = { group: holder };
    viewMode = "color"; applyViewMode();
    controls.enabled = true; controls.autoRotate = !reducedMotion; controls.autoRotateSpeed = 1.4;
    controls.addEventListener("start", () => { controls.autoRotate = false; }, { once: true });
    camera.position.set(2.6, 1.8, 4.4); controls.target.set(0, 0, 0); controls.update();
    await tear(snapshot);
    burst(new THREE.Vector3(0, 0.6, 1), 80); chime();
  }

  function reset() {
    controls.enabled = false;
    clearRoot();
    experience = "objects"; clearStars(); starCount = 0; cb.onStars(0);
    camera.position.set(0, 0, camDist()); camera.lookAt(0, 0, 0);
    cycleAt = 0; lodAuto = true;
  }

  // ---- sizing, loop ----
  const camDist = () => { const a = canvas.clientWidth / Math.max(1, canvas.clientHeight); return a >= 1 ? 5 : 5 / Math.max(a, 0.45) * 0.85; };
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    DPR.value = pr; CELL.value = 6 * pr;
    renderer.setPixelRatio(pr); renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
    if (experience !== "result") camera.position.set(0, 0, camDist());
  }
  new ResizeObserver(resize).observe(canvas);
  resize();
  camera.position.set(0, 0, camDist());

  let last = performance.now(), fpsAcc = 0, fpsN = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    if (paused || document.hidden) { last = now; return; }
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    TIME.value += dt; const t = TIME.value;
    // Drop the pixel ratio if the GPU cannot keep up, but never below 1.
    fpsAcc += dt; fpsN++;
    if (fpsAcc > 2) { if (fpsN / fpsAcc < 38 && pr > 1) { pr = Math.max(1, pr - 0.25); resize(); } fpsAcc = fpsN = 0; }

    if (experience === "result") { controls.update(); }
    else {
      const idle = now - lastInteract > 2500;
      if (experience === "objects") cycle(now);
      else if (!content || content.kind === "object") {
        // Back from a toy interlude into the stage experience.
        if (now > interludeUntil) enter(experience);
        else cycle(now);
      } else if (idle && now > experienceHoldUntil && !reducedMotion) {
        // Every ~7 s of the dots/blob experience, show two toys so the middle never goes stale.
        interludeUntil = now + 3600; experienceHoldUntil = now + 11000; cycleAt = now + nextDelay(); place(objectContent(nextName()));
      }
      // transition: scale pop with overshoot
      if (trans && content) {
        trans.t += dt / (reducedMotion ? 0.5 : 0.28);
        const k = clamp(trans.t), s = reducedMotion ? k : 1 + 2.7 * Math.pow(k - 1, 3) + 1.7 * Math.pow(k - 1, 2);
        content.group.scale.setScalar(Math.max(0.001, s));
        if (k >= 1) trans = null;
      }
      // pointer hover and spin inertia
      updatePointer();
      if (content?.kind === "object" && !ptr.down) {
        ray.setFromCamera(ptr.ndc, camera);
        content.obj.hover(!!ray.intersectObject(content.group, true)[0]);
      }
      root.rotation.y += spin.x * 0.5 * (experience === "blob" ? 0 : 1); root.rotation.x += spin.y * 0.5 * (experience === "blob" ? 0 : 1);
      spin.multiplyScalar(0.94);
      if (!ptr.down) { root.rotation.x *= 0.985; }
      content?.obj?.tick(t, dt, { p: ptr.p });
      content?.update?.(t, dt);
      if (experience === "blob" || experience === "refine") updateStars(t, dt);
    }
    updateConfetti(dt);
    renderer.render(scene, camera);
  }
  let interludeUntil = 0, experienceHoldUntil = 0;

  function enter(kind) {
    experience = kind;
    interludeUntil = 0; experienceHoldUntil = performance.now() + 7000;
    if (kind === "objects") { cycleAt = 0; clearStars(); return; }
    if (kind === "dots") { clearStars(); place(dotsContent()); }
    else { place(blobContent("stage")); if (kind === "blob") starTimer = 0.5; }
  }
  requestAnimationFrame(frame);

  return {
    // Which experience the pipeline stage index asks for.
    setStage(i) {
      if (experience === "result") return;
      const want = i === 1 ? "dots" : i === 2 ? "blob" : i === 3 ? "refine" : "objects";
      if (want !== experience) { if (want === "refine") lodAuto = true; enter(want); }
    },
    setMorph(v) { morph = clamp(v); },
    setLod(v, fromUser = true) { lod = clamp(v); if (fromUser) lodAuto = false; },
    get lodAuto() { return lodAuto; },
    get lod() { return lod; },
    setViewMode(m) { viewMode = m; applyViewMode(); },
    showResult, reset,
    rethemed() { P = palette(); if (experience === "result") applyViewMode(); else if (content?.kind === "object") place(objectContent(content.name)); },
    burst: (x = 0, y = 0.5) => burst(new THREE.Vector3(x, y, 1)),
    resetView() { camera.position.set(2.6, 1.8, 4.4); controls.target.set(0, 0, 0); controls.update(); },
    get hasResult() { return !!result; },
    // For the browser console while debugging.
    debug: () => ({ experience, kind: content?.kind, mode: content?.mode, name: content?.name, interlude: interludeUntil > performance.now(), root: root.children.map((c) => `${c.type}/${c.children.length}/${c === result?.group ? "result" : c === content?.group ? "content" : "orphan"}`) }),
    pause(v) { paused = v; },
    // PNG of the stage as it looks now, with a transparent background. `maxSide` shrinks it for thumbnails.
    // Confetti and stars sit in `extras`, so they are hidden for the frame.
    async snapshot(maxSide = 0) {
      if (!result) throw new Error("There is no mesh to capture yet.");
      extras.visible = false;
      renderer.render(scene, camera);
      const url = canvas.toDataURL("image/png"); // must be read in the same task as the render
      extras.visible = true;
      if (!maxSide || Math.max(canvas.width, canvas.height) <= maxSide) return (await fetch(url)).blob();
      const k = maxSide / Math.max(canvas.width, canvas.height);
      const small = document.createElement("canvas");
      small.width = Math.round(canvas.width * k); small.height = Math.round(canvas.height * k);
      const img = new Image(); img.src = url; await img.decode();
      small.getContext("2d").drawImage(img, 0, 0, small.width, small.height);
      return new Promise((res) => small.toBlob(res, "image/png"));
    },
    async exportAs(fmt) {
      if (!result) throw new Error("There is no mesh to export yet.");
      const g = result.group; g.updateMatrixWorld(true);
      // Export the clean meshes, not the hidden outline hulls.
      const clone = g.clone(true);
      const kill = []; clone.traverse((n) => { if (n.userData?.isOutline) kill.push(n); }); kill.forEach((n) => n.parent.remove(n));
      if (fmt === "obj") return new Blob([new OBJExporter().parse(clone)], { type: "text/plain" });
      const buf = await new GLTFExporter().parseAsync(clone, { binary: true });
      return new Blob([buf], { type: "model/gltf-binary" });
    },
  };
}
