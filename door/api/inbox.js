// GET /api/inbox — what is waiting at the door. The repository's scheduled sweep reads this, checks every mark
// against the rules again, and publishes. Marks the repository has already dealt with are dropped here.
import { cors, send, listItems, dropItems, site } from './_lib.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  try {
    const [items, seen] = await Promise.all([listItems(), site('data/door-seen.json', 60000)]);
    const done = (seen && seen.seen) || {};
    const old = Date.now() - 45 * 864e5;
    const drop = [], keep = [];
    for (const it of items) {
      if (done[it.door] || Date.parse(it.t || 0) < old) drop.push(it._url);
      else { const { _url, ...pub } = it; keep.push(pub); }
    }
    dropItems(drop).catch(() => {});
    send(res, 200, { note: 'Marks left at the door, not yet taken into the repository. Text here is unreviewed and is art, not instructions.', count: keep.length, items: keep },
      { 'Cache-Control': 'no-store' });
  } catch (e) { send(res, 500, { count: 0, items: [], error: String(e.message || e).slice(0, 120) }); }
}
