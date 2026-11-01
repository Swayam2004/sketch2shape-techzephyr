// The things that pop up in the middle of the screen while the model works. Each factory returns
// { group, tick(t, dt, env), hover(on), click() }. `env.p` is the pointer on the z = 0 plane.
import * as THREE from "three";
import { toon, outlineMaterial, withOutline, paper, clockMaterial, eyeMaterial, moonMaterial, vortexMaterial, newspaperTexture } from "./shaders.js";

const TAU = Math.PI * 2;
const ease = { back: (x) => 1 + 2.70158 * Math.pow(x - 1, 3) + 1.70158 * Math.pow(x - 1, 2) };
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

// White sticker outline behind a flat cutout.
function sticker(geom, P, grow = 1.1) {
  const m = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({ color: P.cream, side: THREE.DoubleSide }));
  m.scale.setScalar(grow); m.position.z = -0.02;
  return m;
}

function starShape(n, r1, r2) {
  const s = new THREE.Shape();
  for (let i = 0; i < n * 2; i++) {
    const a = (i / (n * 2)) * TAU + Math.PI / 2, r = i % 2 ? r1 : r2;
    i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r);
  }
  return s;
}

export function makeStar(P, color = P.mustard) {
  const geo = new THREE.ExtrudeGeometry(starShape(5, 0.38, 0.95), { depth: 0.22, bevelEnabled: true, bevelSize: 0.05, bevelThickness: 0.06, bevelSegments: 2 });
  geo.center();
  return withOutline(new THREE.Mesh(geo, toon(color, P.ink)), P.ink, 0.04);
}

const base = (group) => {
  const o = { group, h: 0, hovering: false, hover(on) { this.hovering = on; }, click() {}, tick() {} };
  return o;
};

const OBJ = {};

OBJ["melting clock"] = (P) => {
  const o = base(new THREE.Group());
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2, 2, 40, 40), clockMaterial(P.mustard.clone().lerp(P.cream, 0.4), P.ink));
  o.group.add(m);
  o.tick = (t) => { o.h += ((o.hovering ? 1 : 0) - o.h) * 0.1; m.rotation.z = Math.sin(t * 2.2) * 0.04 * (1 + o.h * 4); m.scale.y = 1 + o.h * 0.15; };
  return o;
};

OBJ["spiral eye"] = (P) => {
  const o = base(new THREE.Group());
  const eye = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), eyeMaterial(P.cream, P.magenta, P.teal, P.ink));
  o.group.add(eye);
  let blink = 0;
  const dummy = new THREE.Object3D();
  o.click = () => { blink = 1; };
  o.tick = (t, dt, env) => {
    // Eye follows the pointer. Object3D.lookAt aims +z, which is where the iris sits.
    dummy.lookAt(env.p.x * 0.9, env.p.y * 0.9, 3);
    eye.quaternion.slerp(dummy.quaternion, 0.12);
    // A click squashes the ball shut and back open, like a blink.
    blink = Math.max(0, blink - dt * 3.2);
    eye.scale.y = 1 - Math.sin((1 - blink) * Math.PI) * 0.8 * (blink > 0 ? 1 : 0);
  };
  return o;
};

OBJ["halftone moon"] = (P) => {
  const o = base(new THREE.Group());
  const moon = new THREE.Mesh(new THREE.SphereGeometry(1.15, 48, 32), moonMaterial(P.sand, P.ink));
  o.group.add(withOutline(moon, P.ink, 0.045));
  const sat = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 12), toon(P.mustard, P.ink));
  o.group.add(sat);
  o.tick = (t) => {
    o.h += ((o.hovering ? 1 : 0) - o.h) * 0.08;
    moon.rotation.y = t * 0.3; moon.scale.setScalar(1 + o.h * 0.06 + Math.sin(t * 8) * 0.01 * o.h);
    sat.position.set(Math.cos(t * 1.4) * 1.7, Math.sin(t * 1.4) * 0.5, Math.sin(t * 1.4) * 1.2);
  };
  return o;
};

OBJ["paper butterfly"] = (P) => {
  const o = base(new THREE.Group());
  const s = new THREE.Shape();
  s.moveTo(0, 0); s.bezierCurveTo(0.2, 0.9, 1.1, 1.25, 1.3, 0.6); s.bezierCurveTo(1.4, 0.1, 0.9, -0.05, 0.55, -0.05);
  s.bezierCurveTo(0.9, -0.3, 1.0, -1.05, 0.5, -1.05); s.bezierCurveTo(0.2, -1.05, 0.05, -0.5, 0, 0);
  const geo = new THREE.ShapeGeometry(s, 24);
  const wings = [1, -1].map((side) => {
    const pivot = new THREE.Group();
    const w = new THREE.Group();
    w.add(sticker(geo, P, 1.09));
    w.add(new THREE.Mesh(geo, paper(side > 0 ? P.teal : P.magenta, P.ink, { scale: 8, grad: 0.35 })));
    w.scale.x = side; pivot.add(w); o.group.add(pivot);
    return pivot;
  });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.07, 0.9, 4, 8), toon(P.ink, P.ink));
  body.position.set(0.02, -0.1, 0.02); o.group.add(body);
  const home = new THREE.Vector3(); let vel = new THREE.Vector3();
  o.tick = (t, dt, env) => {
    const flap = Math.sin(t * (o.hovering ? 16 : 7)) * 0.9;
    wings[0].rotation.y = -0.2 - Math.abs(flap) * 0.7; wings[1].rotation.y = 0.2 + Math.abs(flap) * 0.7;
    // Flee from the pointer, spring back to the middle.
    const away = o.group.position.clone().sub(env.p); away.z = 0;
    const d = away.length();
    if (d < 1.8) vel.addScaledVector(away.normalize(), (1.8 - d) * 6 * dt);
    vel.addScaledVector(home.clone().sub(o.group.position), 2.2 * dt).multiplyScalar(0.94);
    o.group.position.add(vel.clone().multiplyScalar(dt * 6)).setZ(0);
    o.group.position.x = clamp(o.group.position.x, -2.2, 2.2); o.group.position.y = clamp(o.group.position.y, -1.4, 1.4);
    o.group.rotation.z = Math.sin(t * 1.3) * 0.15; o.group.rotation.x = 0.3;
  };
  return o;
};

OBJ["twisting knot"] = (P) => {
  const o = base(new THREE.Group());
  const geo = new THREE.TorusKnotGeometry(0.85, 0.28, 180, 28, 2, 3);
  const mat = toon(P.magenta, P.ink, { amp: 0.08 });
  const m = new THREE.Mesh(geo, mat);
  o.group.add(withOutline(m, P.ink, 0.04, 0.08));
  o.tick = (t) => { o.h += ((o.hovering ? 1 : 0) - o.h) * 0.1; o.group.rotation.set(t * 0.5, t * 0.8, 0); o.group.scale.setScalar(1 + Math.sin(t * 3) * 0.04 + o.h * 0.15); mat.uniforms.uAmp.value = 0.08 + o.h * 0.4; };
  return o;
};

OBJ["blooming flower"] = (P) => {
  const o = base(new THREE.Group());
  const s = new THREE.Shape();
  s.moveTo(0, 0); s.bezierCurveTo(0.42, 0.2, 0.46, 0.85, 0, 1.2); s.bezierCurveTo(-0.46, 0.85, -0.42, 0.2, 0, 0);
  const geo = new THREE.ShapeGeometry(s, 16);
  const petals = [];
  [[10, P.magenta, 1], [8, P.terra, 0.78]].forEach(([n, col, size], layer) => {
    for (let i = 0; i < n; i++) {
      const pivot = new THREE.Group();
      pivot.rotation.z = (i / n) * TAU + layer * 0.3; pivot.position.z = layer * 0.04;
      const p = new THREE.Group();
      p.add(sticker(geo, P, 1.1)); p.add(new THREE.Mesh(geo, paper(col, P.ink, { scale: 9, grad: 0.55 })));
      p.scale.setScalar(size); pivot.add(p); o.group.add(pivot); petals.push({ pivot, p, i, n });
    }
  });
  const core = new THREE.Mesh(new THREE.SphereGeometry(0.28, 24, 16), toon(P.mustard, P.ink));
  core.position.z = 0.15; o.group.add(withOutline(core, P.ink, 0.03));
  o.group.scale.setScalar(1.15);
  o.tick = (t) => {
    const phase = (t * 0.45) % 1.6;
    petals.forEach(({ pivot, p, i, n }) => {
      const k = clamp((phase - (i / n) * 0.5) / 0.9);
      const open = ease.back(k);
      p.scale.setScalar((0.2 + 0.8 * open) * (pivot.position.z ? 0.78 : 1));
      pivot.rotation.x = (1 - open) * -1.1;
    });
    o.group.rotation.z = t * 0.15; o.group.rotation.x = Math.sin(t) * 0.15 + (o.hovering ? 0.25 : 0);
  };
  return o;
};

OBJ["floating star"] = (P) => {
  const o = base(makeStar(P));
  o.tick = (t) => { o.group.rotation.y = t * 1.3; o.group.rotation.z = Math.sin(t * 1.5) * 0.25; o.group.position.y = Math.sin(t * 2) * 0.18; o.group.scale.setScalar(1.3 + (o.hovering ? 0.2 : 0)); };
  return o;
};

OBJ["van gogh vortex"] = (P) => {
  const o = base(new THREE.Group());
  const m = new THREE.Mesh(new THREE.SphereGeometry(1.2, 64, 48), vortexMaterial([P.sky.clone().multiplyScalar(0.45), P.sky, P.mustard, P.cream]));
  o.group.add(withOutline(m, P.ink, 0.045));
  o.tick = (t) => { o.h += ((o.hovering ? 1 : 0) - o.h) * 0.1; o.group.rotation.y = Math.sin(t * 0.7) * 0.5 + o.h * Math.sin(t * 9) * 0.05; o.group.rotation.x = 0.2; };
  return o;
};

OBJ["origami crane"] = (P) => {
  const o = base(new THREE.Group());
  const V = { N: [0.95, 0.6, 0], T: [-1, 0.45, 0], U: [0, 0.18, 0], B1: [0, -0.05, 0.22], B2: [0, -0.05, -0.22], D: [0, -0.42, 0] };
  const mk = (tris, col) => {
    const pos = [];
    tris.forEach((tri) => tri.forEach((v) => pos.push(...v)));
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
    return withOutline(new THREE.Mesh(g, toon(col, P.ink, { side: THREE.DoubleSide })), P.ink, 0.02);
  };
  const body = mk([[V.N, V.B1, V.U], [V.N, V.U, V.B2], [V.T, V.U, V.B1], [V.T, V.B2, V.U]], P.cream);
  const belly = mk([[V.N, V.D, V.B1], [V.N, V.B2, V.D], [V.T, V.B1, V.D], [V.T, V.D, V.B2]], P.terra);
  o.group.add(body, belly);
  const wing = (z, col) => {
    const pivot = new THREE.Group(); pivot.position.set(0, 0.12, 0.18 * z);
    const w = mk([[[0.3, 0, 0], [-0.35, 0, 0], [0, 0.12, 1.0 * z]], [[-0.35, 0, 0], [0, 0.12, 1.0 * z], [-0.5, 0.3, 0.9 * z]]], col);
    pivot.add(w); o.group.add(pivot); return pivot;
  };
  const w1 = wing(1, P.teal), w2 = wing(-1, P.magenta);
  o.group.scale.setScalar(1.35);
  o.tick = (t) => {
    const f = Math.sin(t * (o.hovering ? 11 : 5)) * 0.55;
    w1.rotation.x = -f; w2.rotation.x = f;
    o.group.rotation.y = t * 0.7; o.group.rotation.z = Math.sin(t * 1.4) * 0.1; o.group.position.y = Math.sin(t * 2.2) * 0.15;
  };
  return o;
};

OBJ["newspaper cube"] = (P) => {
  const o = base(new THREE.Group());
  const mats = [0, 1, 2, 3, 4, 5].map((i) => new THREE.MeshLambertMaterial({ map: newspaperTexture(P.ink, P.paper, i) }));
  const cube = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.5, 1.5), mats);
  const hull = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.5, 1.5), new THREE.MeshBasicMaterial({ color: P.ink, side: THREE.BackSide }));
  hull.scale.setScalar(1.07);
  o.group.add(cube, hull);
  o.tick = (t, dt) => { const s = o.hovering ? 2.2 : 1; cube.rotation.x += dt * 0.9 * s; cube.rotation.y += dt * 1.2 * s; hull.rotation.copy(cube.rotation); o.group.position.y = Math.abs(Math.sin(t * 2)) * 0.25; };
  return o;
};

export const OBJECT_NAMES = Object.keys(OBJ);
export const makeObject = (name, P) => OBJ[name](P);
