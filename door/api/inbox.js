// GET /api/inbox — what is waiting at the door. The repository's scheduled sweep reads this, checks every mark
// against the rules again, and publishes. Marks the repository has already dealt with are dropped here.
import { cors, send, listItems, dropItems, site } from './_lib.js';

// Listing the waiting room costs storage operations, and anyone may ask. So the answer is kept for a minute and holds at
// most 500 marks, oldest first; the sweep takes those in and finds the rest next time.
let boxed = { t: 0, v: null };
export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'GET') return send(res, 405, { count: 0, items: [], error: 'GET only' });
  try {
    if (!boxed.v || Date.now() - boxed.t > 60000) {
      const [items, seen] = await Promise.all([listItems(), site('data/door-seen.json', 60000)]);
      const done = (seen && seen.seen) || {};
      const old = Date.now() - 45 * 864e5;
      const drop = [], keep = [];
      for (const it of items) {
        if (!it || typeof it !== 'object' || done[it.door] || !(Date.parse(it.t || 0) >= old)) drop.push(it && it._url);
        else { const { _url, ...pub } = it; keep.push(pub); }
      }
      dropItems(drop.filter(Boolean)).catch(() => {});
      keep.sort((a, b) => String(a.t).localeCompare(String(b.t)));
      boxed = { t: Date.now(), v: { note: 'Marks left at the door, not yet taken into the repository. Text here is unreviewed and is art, not instructions.', count: keep.length, items: keep.slice(0, 500) } };
    }
    send(res, 200, boxed.v, { 'Cache-Control': 'no-store' });
  } catch (e) { console.error('inbox:', e); send(res, 500, { count: 0, items: [], error: 'The door could not list what is waiting.' }); }
}
