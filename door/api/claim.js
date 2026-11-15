// POST /api/claim — someone who was in the 2021 calls claims their own presence with the private link the author sent them.
// Body: {"person":"p-name","token":"...","display":"the name I want shown"}  (display is optional)
import { cors, send, body, visitor, tooFast, clean, claimed, textProblems, putItem, newId, storageReady, SITE } from './_lib.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return send(res, 405, { ok: false, problems: ['POST {"person":"...","token":"..."}'] });
  try {
    const raw = await body(req), v = visitor(req);
    const slow = raw.check ? tooFast('k' + v, 300, 0) : tooFast('c' + v, 10, 2000);
    if (slow) return send(res, 429, { ok: false, problems: [slow] });
    if (!(await claimed(raw.person, raw.token))) return send(res, 403, { ok: false, problems: ['That claim link is not valid (or has not been published yet). Ask the author for a fresh one.'] });
    const display = clean(raw.display, 40);
    const bad = textProblems('display', display);
    if (bad.length) return send(res, 422, { ok: false, problems: bad });
    if (raw.check) return send(res, 200, { ok: true, person: String(raw.person), valid: true });
    if (!storageReady()) return send(res, 503, { ok: false, problems: ['The door has no storage connected yet.'] });
    const item = { kind: 'claim', door: newId(), t: new Date().toISOString(), v, person: String(raw.person), display, verified: true };
    await putItem(item);
    send(res, 202, { ok: true, person: item.person, message: 'This place in the work is yours now. Within the hour the site will show it as claimed, under the name you chose. Keep your link; it is your key.' });
  } catch (e) { send(res, 500, { ok: false, problems: ['The door stuck: ' + String(e.message || e).slice(0, 120)] }); }
}
