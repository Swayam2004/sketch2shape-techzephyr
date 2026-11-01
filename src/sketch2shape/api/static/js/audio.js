// Tiny synthesized sound effects. No audio files, so nothing to license. Muted until the user opts in.
import { store } from "./store.js";

let ctx = null;
const on = () => store.get().sound;
const ac = () => (ctx ||= new (window.AudioContext || window.webkitAudioContext)());

export function pop(pitch = 1) {
  if (!on()) return;
  const a = ac(), t = a.currentTime;
  const o = a.createOscillator(), g = a.createGain();
  o.type = "triangle";
  o.frequency.setValueAtTime(520 * pitch, t);
  o.frequency.exponentialRampToValueAtTime(160 * pitch, t + 0.12);
  g.gain.setValueAtTime(0.25, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.14);
  o.connect(g).connect(a.destination);
  o.start(t); o.stop(t + 0.15);
}

// Filtered noise burst, close enough to paper.
export function rustle(len = 0.25) {
  if (!on()) return;
  const a = ac(), t = a.currentTime;
  const buf = a.createBuffer(1, Math.floor(a.sampleRate * len), a.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
  const src = a.createBufferSource(), f = a.createBiquadFilter(), g = a.createGain();
  src.buffer = buf; f.type = "highpass"; f.frequency.value = 2200; g.gain.value = 0.18;
  src.connect(f).connect(g).connect(a.destination);
  src.start(t);
}

export function chime() {
  if (!on()) return;
  [0, 4, 7, 12].forEach((n, i) => setTimeout(() => pop(1.2 * 2 ** (n / 12)), i * 90));
}
