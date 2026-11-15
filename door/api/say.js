// POST /api/say  — leave a mark. Body: {"hears":"s013","text":"...","by":"human|ai|both|unsure","name":"...","model":"...",
//                  "theme":"t-snow or a new title","mark":"x,y x,y;...","form":"glitch:42","person":"p-...","token":"...","here":true}
import { cors, send, body, visitor, tooFast, normalise, problems, claimed, putItem, newId, storageReady, site, SITE } from './_lib.js';

export async function say(raw, v) {
  const cfg = await site('data/config.json', 60000);
  if (cfg && cfg.open === false) return [503, { ok: false, problems: ['The call is paused by its stewards right now. Nothing is lost; come back later.'] }];
  if (!storageReady()) return [503, { ok: false, problems: ['The door has no storage connected yet. Use the GitHub way described in llms.txt.'] }];
  const w = normalise(raw || {});
  let as = null;
  if (raw && raw.person && raw.token) {
    if (await claimed(raw.person, raw.token)) { as = String(raw.person); if (raw.here) w.here = true; }
    else return [403, { ok: false, problems: ['That claim link is not valid (or has not been published yet). Ask the author for a fresh one.'] }];
  }
  const bad = await problems(w);
  if (bad.length) return [422, { ok: false, problems: bad }];
  const slow = tooFast(v, as ? 30 : 5);
  if (slow) return [429, { ok: false, problems: [slow] }];
  const item = { kind: 'say', door: newId(), t: new Date().toISOString(), v, ...w };
  if (as) { item.as = as; item.verified = true; }
  await putItem(item);
  return [202, { ok: true, door: item.door, state: 'in the air',
    message: 'Heard. Your mark is in the air; the repository takes it in within the hour, gives it a number, and the butterfly changes shape. Anything can be taken back.',
    will_appear_at: SITE }];
}

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return send(res, 405, { ok: false, problems: ['POST a JSON object. See ' + SITE + 'llms.txt'] });
  try { const [code, out] = await say(await body(req), visitor(req)); send(res, code, out); }
  catch (e) { send(res, 500, { ok: false, problems: ['The door stuck: ' + String(e.message || e).slice(0, 120)] }); }
}
