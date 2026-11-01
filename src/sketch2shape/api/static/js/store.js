// Small observable store. Same idea as Zustand, without a build step.
export function createStore(initial) {
  let state = initial;
  const subs = new Set();
  return {
    get: () => state,
    set(patch) {
      state = { ...state, ...(typeof patch === "function" ? patch(state) : patch) };
      subs.forEach((fn) => fn(state));
    },
    subscribe(fn) {
      subs.add(fn);
      return () => subs.delete(fn);
    },
  };
}

// The five things the user sees. `api` lists the server stages from docs/api.md that map onto each one.
export const STAGES = [
  { id: "read", label: "sketch read", short: "read", api: ["queued"] },
  { id: "prep", label: "edges and dots", short: "prep", api: ["preprocess"] },
  { id: "shape", label: "shape forming", short: "shape", api: ["generate"] },
  { id: "refine", label: "detail", short: "detail", api: ["cutout", "reconstruct"] },
  { id: "texture", label: "final render", short: "render", api: ["export"] },
];

export const stageIndexFor = (apiStage, status) => {
  if (status === "done") return STAGES.length;
  const i = STAGES.findIndex((s) => s.api.includes(apiStage || "queued"));
  return i < 0 ? 0 : i;
};

export const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
export const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 760;

export const store = createStore({
  phase: "idle", // idle | running | done | error
  stage: -1, // index into STAGES, STAGES.length once done
  progress: 0, // 0 to 1
  queuePosition: 0,
  elapsed: 0,
  device: null,
  error: null,
  result: null,
  warnings: [],
  mock: false,
  sound: false,
  theme: "cream",
  stars: 0,
});
