// POST /api/remove — ask for anything to be removed. Body: {"id":"m00123","why":"i am in it"}
// The thing is hidden from the site at the next sweep and stays hidden until a steward has looked. No reason has to be argued.
import { cors, send, body, visitor, tooFast, clean, exists, shelve, stuck, newId, storageReady, WHY, SITE } from './_lib.js';

export async function remove(raw, v) {
  if (!storageReady()) return [503, { ok: false, problems: ['The door has no storage connected yet. Open an issue titled "remove <id>" on GitHub instead.'] }];
  const id = clean(raw && raw.id, 20).toLowerCase();
  const why = clean(raw && raw.why, 30).toLowerCase() || 'other';
  if (!WHY.includes(why)) return [422, { ok: false, problems: ['"why" must be one of: ' + WHY.join(', ') + '.'] }];
  if ((await exists(id)) === false) return [422, { ok: false, problems: [`Nothing in the work has the id "${id}".`] }];
  const slow = tooFast('x' + v, 6, 3000);
  if (slow) return [429, { ok: false, problems: [slow] }];
  const item = { kind: 'remove', door: newId(), t: new Date().toISOString(), v, id, why };
  const full = await shelve(item);
  if (full) return full;
  return [202, { ok: true, door: item.door, message: 'Asked. It will be hidden at the next sweep (meant to be hourly, sometimes a few hours) and stays hidden until a steward has looked at it. You do not have to explain.' }];
}
export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return send(res, 405, { ok: false, problems: ['POST {"id":"...","why":"..."}. See ' + SITE + 'llms.txt'] });
  try { const [code, out] = await remove(await body(req), visitor(req)); send(res, code, out); }
  catch (e) { send(res, 500, { ok: false, problems: [stuck(e)] }); }
}
