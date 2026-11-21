// POST /api/remove — ask for anything to be removed. Body: {"id":"m00123","why":"i am in it"}
// For one minute of a recording the body may also carry "seen": the other minutes of the same recording that the visitor
// had in front of them and asks for with it, e.g. {"id":"r026.0431","why":"i am in it","seen":[429,430,432]}.
// What happens next is decided by the sweep in the repository (tools/wingbeat.py has the last word; charter, section 6 and
// Amendment 13): the thing is hidden at the next sweep and stays hidden until a steward has looked, except that
//   - a whole recording (r026) is never hidden by a request: it is recorded and a steward decides;
//   - a thing a steward has restored before is not hidden again without a steward;
//   - one request hides at most MINUTES minutes of one recording, the one asked for among them.
// No reason has to be argued.
import { cors, send, body, visitor, tooFast, clean, exists, shelve, stuck, newId, storageReady, site, WHY, SITE } from './_lib.js';

export const MINUTES = 30; // MINUTES_PER_FLAG in tools/wingbeat.py: change them together
const pad4 = (n) => String(n).padStart(4, '0');

// The other minutes asked for with one minute: whole numbers inside the recording, each once, the nearest first, MINUTES - 1 at most.
export function seenMinutes(id, seen, length) {
  const m = /^(r\d{3})\.(\d{4})$/.exec(id);
  if (!m || !Array.isArray(seen)) return [];
  const here = Number(m[2]), out = new Set();
  for (const v of seen.slice(0, 2000)) {
    const n = typeof v === 'number' ? v : typeof v === 'string' && /^\d{1,4}$/.test(v) ? Number(v) : NaN;
    if (Number.isInteger(n) && n >= 0 && n < length && n !== here) out.add(n);
  }
  return [...out].sort((a, b) => Math.abs(a - here) - Math.abs(b - here) || a - b).slice(0, MINUTES - 1).sort((a, b) => a - b);
}

export async function remove(raw, v) {
  if (!storageReady()) return [503, { ok: false, problems: ['The door has no storage connected yet. Open an issue titled "remove <id>" on GitHub instead.'] }];
  const id = clean(raw && raw.id, 20).toLowerCase();
  const why = clean(raw && raw.why, 30).toLowerCase() || 'other';
  if (!WHY.includes(why)) return [422, { ok: false, problems: ['"why" must be one of: ' + WHY.join(', ') + '.'] }];
  if ((await exists(id)) === false) return [422, { ok: false, problems: [`Nothing in the work has the id "${id}".`] }];
  if (raw && raw.seen != null && !Array.isArray(raw.seen)) return [422, { ok: false, problems: ['"seen" is a list of minutes of the same recording, as numbers: [429, 430, 432].'] }];
  const slow = tooFast('x' + v, 6, 3000);
  if (slow) return [429, { ok: false, problems: [slow] }];
  const [arch, veiled] = await Promise.all([site('data/archive.json'), site('data/veiled.json')]);
  const rid = id.slice(0, 4), length = (arch && arch.recordings && Number(arch.recordings[rid])) || 0;
  const gone = (veiled && veiled.ids) || {}, kept = new Set((veiled && veiled.kept) || []);
  const isKept = (i) => kept.has(i) || (/^r\d{3}\./.test(i) && kept.has(i.slice(0, 4)));
  const seen = seenMinutes(id, raw && raw.seen, length).filter((n) => !gone[rid + '.' + pad4(n)]);
  const item = { kind: 'remove', door: newId(), t: new Date().toISOString(), v, id, why };
  if (seen.length) item.seen = seen;
  const full = await shelve(item);
  if (full) return full;
  const base = { ok: true, door: item.door };
  if (/^r\d{3}$/.test(id)) return [202, { ...base, hidden: false, message: 'Asked. A whole recording is not hidden by one request: a steward will look at it, and it stays visible until then. To have minutes of it hidden at the next sweep, ask for a minute (' + id + '.0012) and name the others you had in front of you in "seen". You do not have to explain.' }];
  if (isKept(id)) return [202, { ...base, hidden: false, message: 'Asked. A steward has looked at this before and kept it, so it stays visible until a steward has looked again. You do not have to explain.' }];
  const stay = seen.filter((n) => isKept(rid + '.' + pad4(n))).length, n = seen.length - stay;
  return [202, { ...base, hidden: true, minutes: /^r\d{3}\./.test(id) ? n + 1 : undefined, message: 'Asked. It will be hidden at the next sweep (meant to be hourly, sometimes a few hours)' + (n ? ', with ' + n + ' more minute' + (n == 1 ? '' : 's') + ' of the same recording,' : '') + ' and stays hidden until a steward has looked at it.' + (stay ? ' ' + stay + ' of the minutes you named ' + (stay == 1 ? 'was' : 'were') + ' kept by a steward before and stay' + (stay == 1 ? 's' : '') + ' visible until a steward has looked again.' : '') + ' You do not have to explain.' }];
}
export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return send(res, 405, { ok: false, problems: ['POST {"id":"...","why":"..."}. See ' + SITE + 'llms.txt'] });
  try { const [code, out] = await remove(await body(req), visitor(req)); send(res, code, out); }
  catch (e) { send(res, 500, { ok: false, problems: [stuck(e)] }); }
}
