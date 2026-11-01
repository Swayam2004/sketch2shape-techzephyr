// Local history of generated designs. IndexedDB holds the blobs (sketch, mesh files, thumbnail), because
// localStorage is too small for a .glb. Nothing leaves the browser, and clearing site data removes it.
const DB = "sketch2shape-history";
const STORE = "designs";
const KEEP = 24; // oldest designs go first, so the cache stays around 100 MB at most

function open() {
  return new Promise((res, rej) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "id" });
    req.onsuccess = () => res(req.result);
    req.onerror = () => rej(req.error);
  });
}

async function run(mode, fn) {
  const db = await open();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, mode);
    const out = fn(tx.objectStore(STORE));
    tx.oncomplete = () => { db.close(); res(out?.result); };
    tx.onerror = tx.onabort = () => { db.close(); rej(tx.error); };
  });
}

const blobOf = async (url) => (url ? (await fetch(url)).blob() : null);

export const history = {
  // Private browsing and some embedded browsers block IndexedDB, so callers treat a failure as "no history".
  async list() {
    const all = (await run("readonly", (s) => s.getAll())) || [];
    return all.sort((a, b) => b.createdAt - a.createdAt);
  },
  async add({ result, sketch, thumb, prompt, seed }) {
    const entry = {
      id: crypto.randomUUID(), createdAt: Date.now(), prompt, seed,
      sketch, thumb, glb: await blobOf(result.glb), obj: await blobOf(result.obj), image: await blobOf(result.image),
      meta: { iou: result.iou, device: result.device, timings: result.timings, warnings: result.warnings },
    };
    await run("readwrite", (s) => s.put(entry));
    const all = await this.list();
    for (const old of all.slice(KEEP)) await this.remove(old.id);
    return entry;
  },
  remove: (id) => run("readwrite", (s) => s.delete(id)),
  clear: () => run("readwrite", (s) => s.clear()),
};

// Turn a stored design back into the object the viewer and download buttons expect.
export function toResult(entry) {
  const url = (b) => (b ? URL.createObjectURL(b) : null);
  return { kind: "files", glb: url(entry.glb), obj: url(entry.obj), image: url(entry.image), ...entry.meta };
}
