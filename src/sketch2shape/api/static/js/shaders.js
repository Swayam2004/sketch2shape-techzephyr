// Procedural materials. Every look is a shader (halftone dots, noise displacement, paper grain,
// inverted-hull outline), so the project ships no textures or artwork.
import * as THREE from "three";

export const TIME = { value: 0 };
export const DPR = { value: 1 };
// Halftone cell size in device pixels. The stage updates it when the pixel ratio changes.
export const CELL = { value: 6 };

export function palette() {
  const cs = getComputedStyle(document.documentElement);
  const c = (n) => new THREE.Color(cs.getPropertyValue(n).trim() || "#888");
  return {
    magenta: c("--magenta"), teal: c("--teal"), sky: c("--sky"), mustard: c("--mustard"),
    terra: c("--terra"), sage: c("--sage"), cream: c("--cream"), sand: c("--sand"), ink: c("--ink"), paper: c("--paper"),
  };
}

const NOISE = /* glsl */ `
float hash(vec3 p){ p = fract(p*0.3183099 + .1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vnoise(vec3 x){
  vec3 i = floor(x), f = fract(x); f = f*f*(3.0-2.0*f);
  return mix(mix(mix(hash(i+vec3(0,0,0)),hash(i+vec3(1,0,0)),f.x), mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x), mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y), f.z);
}
float fbm(vec3 p){ float s=0.0, a=0.5; for(int i=0;i<4;i++){ s+=a*vnoise(p); p*=2.03; a*=0.5; } return s; }
`;

// Ink coverage for a lit value v in 0..1, rotated 45 degrees like a print screen.
const HALFTONE = /* glsl */ `
uniform float uCell;
float halftone(float v, float cell){
  vec2 p = mat2(0.7071,0.7071,-0.7071,0.7071) * gl_FragCoord.xy / cell;
  float d = length(fract(p) - 0.5);
  float r = sqrt(clamp(1.0 - v, 0.0, 1.0)) * 0.72;
  return 1.0 - smoothstep(r - 0.06, r + 0.06, d);
}
float grain(){ return (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898,78.233))) * 43758.5453) - 0.5) * 0.07; }
`;

const common = (extra = {}) => ({ uTime: TIME, uCell: CELL, ...extra });

export function toon(base, ink, { amp = 0, light = [0.5, 0.7, 0.6], side = THREE.FrontSide } = {}) {
  return new THREE.ShaderMaterial({
    side,
    uniforms: common({ uBase: { value: base.clone() }, uInk: { value: ink.clone() }, uAmp: { value: amp }, uLight: { value: new THREE.Vector3(...light).normalize() } }),
    vertexShader: /* glsl */ `
      uniform float uTime, uAmp; varying vec3 vN, vObj; varying float vDisp;
      ${NOISE}
      void main(){
        vec3 p = position;
        float n = vnoise(p*2.2 + uTime*0.7) - 0.5;
        p += normal * uAmp * n; vDisp = n;
        vObj = position; vN = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uBase, uInk, uLight; varying vec3 vN, vObj; varying float vDisp;
      ${HALFTONE}
      void main(){
        vec3 n = normalize(vN); if(!gl_FrontFacing) n = -n;
        float v = clamp(dot(n, uLight)*0.5 + 0.55, 0.0, 1.0);
        float rim = pow(1.0 - abs(n.z), 3.0);
        float cover = halftone(v - rim*0.25, uCell);
        vec3 col = mix(uBase, uInk, cover) + grain();
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
}

// Inverted hull: the same mesh, back faces only, pushed out along the normal. Gives the cutout outline.
export function outlineMaterial(ink, thick = 0.035, amp = 0) {
  return new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: { uTime: TIME, uInk: { value: ink.clone() }, uThick: { value: thick }, uAmp: { value: amp } },
    vertexShader: /* glsl */ `
      uniform float uTime, uThick, uAmp; ${NOISE}
      void main(){
        vec3 p = position + normal * uAmp * (vnoise(position*2.2 + uTime*0.7) - 0.5);
        p += normalize(normal) * uThick;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: `uniform vec3 uInk; void main(){ gl_FragColor = vec4(uInk, 1.0); }`,
  });
}

export function withOutline(mesh, ink, thick = 0.035, amp = 0) {
  const g = new THREE.Group();
  g.add(mesh);
  g.add(new THREE.Mesh(mesh.geometry, outlineMaterial(ink, thick, amp)));
  return g;
}

// Flat cutout shapes: halftone dots in object space, gradient along y.
export function paper(base, ink, { scale = 7, grad = 0.5 } = {}) {
  return new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    uniforms: { uBase: { value: base.clone() }, uInk: { value: ink.clone() }, uScale: { value: scale }, uGrad: { value: grad } },
    vertexShader: `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uBase, uInk; uniform float uScale, uGrad; varying vec2 vP;
      void main(){
        vec2 g = mat2(0.7071,0.7071,-0.7071,0.7071) * vP * uScale;
        float d = length(fract(g) - 0.5);
        float size = clamp(0.5 - vP.y*uGrad, 0.0, 1.0) * 0.5;
        float dots = 1.0 - smoothstep(size - 0.05, size + 0.05, d);
        float n = (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898,78.233))) * 43758.5453) - 0.5) * 0.06;
        gl_FragColor = vec4(mix(uBase, uInk, dots*0.85) + n, 1.0);
      }`,
  });
}

export function clockMaterial(face, ink) {
  return new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    uniforms: { uTime: TIME, uFace: { value: face.clone() }, uInk: { value: ink.clone() } },
    vertexShader: /* glsl */ `
      uniform float uTime; varying vec2 vUv;
      void main(){
        vec3 p = position;
        // Everything below the middle sags. The face texture rides along, so the numbers and hands melt too.
        float melt = smoothstep(0.0, -1.0, p.y);
        p.y -= melt * (0.55 + 0.25*sin(p.x*3.0 + uTime*1.2));
        p.x += sin(p.y*4.0 + uTime) * 0.04 * melt;
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: /* glsl */ `
      uniform float uTime; uniform vec3 uFace, uInk; varying vec2 vUv;
      float seg(vec2 q, vec2 dir, float len){ return length(q - dir*clamp(dot(q,dir),0.0,len)); }
      void main(){
        vec2 q = vUv - 0.5; float r = length(q);
        if(r > 0.5) discard;
        float a = atan(q.x, q.y);
        float k = abs(fract(a/(6.2831853/12.0) + 0.5) - 0.5);
        float tick = step(0.37, r) * step(r, 0.45) * step(k, 0.035);
        float h = uTime*0.2, m = uTime*1.6;
        float hands = max(step(seg(q, vec2(sin(h),cos(h)), 0.22), 0.016), step(seg(q, vec2(sin(m),cos(m)), 0.34), 0.010));
        float rim = step(0.465, r);
        float ink = max(max(tick, hands), rim);
        vec2 g = mat2(0.7071,0.7071,-0.7071,0.7071) * gl_FragCoord.xy / 7.0;
        float dots = 1.0 - smoothstep(0.1, 0.18 + (1.0 - vUv.y)*0.28, length(fract(g)-0.5));
        vec3 col = mix(uFace, uInk, dots*0.35*(1.0 - vUv.y + 0.2));
        gl_FragColor = vec4(mix(col, uInk, ink), 1.0);
      }`,
  });
}

export function eyeMaterial(sclera, irisA, irisB, ink) {
  return new THREE.ShaderMaterial({
    uniforms: common({ uSclera: { value: sclera.clone() }, uA: { value: irisA.clone() }, uB: { value: irisB.clone() }, uInk: { value: ink.clone() } }),
    vertexShader: `varying vec3 vN, vObj; void main(){ vObj = position; vN = normalize(normalMatrix*normal); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: /* glsl */ `
      uniform float uTime; uniform vec3 uSclera, uA, uB, uInk; varying vec3 vN, vObj;
      ${HALFTONE}
      void main(){
        vec3 o = normalize(vObj);
        float th = acos(clamp(o.z, -1.0, 1.0));
        float v = clamp(dot(normalize(vN), normalize(vec3(0.4,0.6,0.7)))*0.5+0.6, 0.0, 1.0);
        vec3 col = mix(uSclera, uInk, halftone(v, uCell)*0.9);
        if(th < 0.95){
          float ang = atan(o.y, o.x);
          float s = fract(ang/6.2831853 + th*2.8 - uTime*0.3);
          col = mix(uA, uB, step(0.5, s));
          if(th < 0.16) col = uInk;
          if(abs(th - 0.95) < 0.04) col = uInk;
        }
        gl_FragColor = vec4(col + grain(), 1.0);
      }`,
  });
}

export function moonMaterial(base, ink) {
  return new THREE.ShaderMaterial({
    uniforms: common({ uBase: { value: base.clone() }, uInk: { value: ink.clone() } }),
    vertexShader: `varying vec3 vN, vObj; void main(){ vObj = position; vN = normalize(normalMatrix*normal); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uBase, uInk; varying vec3 vN, vObj;
      ${NOISE} ${HALFTONE}
      void main(){
        float c = fbm(normalize(vObj)*3.2);
        float crater = smoothstep(0.52, 0.62, c);
        float v = clamp(dot(normalize(vN), normalize(vec3(-0.6,0.4,0.7)))*0.6+0.45, 0.0, 1.0) - crater*0.3;
        vec3 col = mix(uBase, uInk, halftone(v, uCell));
        gl_FragColor = vec4(col + grain(), 1.0);
      }`,
  });
}

export function vortexMaterial(cols) {
  return new THREE.ShaderMaterial({
    uniforms: common({ uC0: { value: cols[0] }, uC1: { value: cols[1] }, uC2: { value: cols[2] }, uC3: { value: cols[3] } }),
    vertexShader: `varying vec3 vObj, vN; void main(){ vObj = position; vN = normalize(normalMatrix*normal); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: /* glsl */ `
      uniform float uTime; uniform vec3 uC0, uC1, uC2, uC3; varying vec3 vObj, vN;
      ${NOISE}
      void main(){
        vec2 p = vObj.xy; float r = length(p);
        float a = atan(p.y, p.x) + 2.6*exp(-r*1.6) - uTime*0.25;
        vec2 q = vec2(cos(a), sin(a)) * r;
        // Stretch the noise along the swirl so it reads as brush strokes.
        float stroke = fbm(vec3(q*vec2(9.0,2.0) + 3.0, uTime*0.15));
        float s = sin(r*11.0 - a*2.0 + stroke*5.0 + uTime*1.4);
        vec3 col = mix(uC0, uC1, smoothstep(-0.6, 0.0, s));
        col = mix(col, uC2, smoothstep(0.2, 0.8, s));
        col = mix(col, uC3, smoothstep(0.75, 1.0, s) * (0.5 + stroke));
        float limb = pow(clamp(normalize(vN).z, 0.0, 1.0), 0.45);
        gl_FragColor = vec4(col * (0.55 + 0.45*limb), 1.0);
      }`,
  });
}

// Round dots for the preprocess stage. Size scales with the pixel ratio so phones keep the look.
export function dotMaterial(ink) {
  return new THREE.ShaderMaterial({
    transparent: true,
    uniforms: { uInk: { value: ink.clone() }, uSize: { value: 7 }, uDpr: DPR },
    vertexShader: `uniform float uSize, uDpr; attribute float aSize; void main(){ gl_PointSize = uSize*aSize*uDpr; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 uInk; void main(){ float d = length(gl_PointCoord-0.5); if(d>0.5) discard; gl_FragColor = vec4(uInk, 1.0); }`,
  });
}

// Newspaper texture drawn on a canvas. The headlines are made up.
export function newspaperTexture(ink, paperCol, seed = 1) {
  const c = document.createElement("canvas");
  c.width = c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#" + paperCol.getHexString(); g.fillRect(0, 0, 512, 512);
  const inkCss = "#" + ink.getHexString();
  let s = seed * 9301;
  const r = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  g.fillStyle = inkCss;
  g.font = "bold 44px Georgia, serif";
  g.fillText(["THE DAILY WOBBLE", "MOON TIMES", "CLOCK GAZETTE", "THE PAPER EYE", "SWIRL NEWS", "STAIR HERALD"][seed % 6], 18, 56);
  g.fillRect(18, 66, 476, 4);
  for (let col = 0; col < 3; col++) {
    let y = 92;
    while (y < 490) {
      if (r() < 0.18) { // a halftone picture block
        const h = 70 + r() * 60;
        for (let yy = 0; yy < h; yy += 7) for (let xx = 0; xx < 140; xx += 7) { g.beginPath(); g.arc(18 + col * 162 + xx, y + yy, 1 + 2.6 * Math.abs(Math.sin((xx + yy + seed * 20) / 30)), 0, 7); g.fill(); }
        y += h + 10;
      } else {
        g.globalAlpha = 0.55;
        for (let l = 0; l < 4 + r() * 4; l++) { g.fillRect(18 + col * 162, y, 130 - r() * 30, 3); y += 9; }
        g.globalAlpha = 1; y += 10;
      }
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

