// POST /api/claim — someone who was in the 2021 calls claims their own presence with the private link the author sent them.
// Body: {"person":"p-name","token":"...","display":"the name I want shown"}  (display is optional)
//   or: {"person":"p-name","lock":"<sha-256 hex of a key the browser keeps>","display":"..."}  (no link needed; a steward confirms)
import { cors, send, body, visitor, tooFast, clean, claimed, textProblems, putItem, DoorFull, FULL, stuck, newId, storageReady, site, SITE } from './_lib.js';

export default async function handler(req, res) {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return send(res, 405, { ok: false, problems: ['POST {"person":"...","token":"..."}'] });
  try {
    const raw = await body(req), v = visitor(req);
    const slow = raw.check ? tooFast('k' + v, 300, 0) : tooFast('c' + v, 10, 2000);
    if (slow) return send(res, 429, { ok: false, problems: [slow] });
    // "This is me", pressed on the site with no private link: the browser keeps a random key and sends only its SHA-256.
    // Nothing changes until a steward confirms; after that the key works like a private link's token.
    if (raw.lock && !raw.token) {
      const person = clean(raw.person, 44), lock = clean(raw.lock, 64).toLowerCase();
      if (!/^p-[a-z0-9-]{1,40}$/.test(person) || !/^[0-9a-f]{64}$/.test(lock)) return send(res, 422, { ok: false, problems: ['Send {"person":"p-name","lock":"<sha-256 of a key you keep>"}.'] });
      const ppl = await site('data/people.json', 30000);
      const who = ppl && ppl.people.find((x) => x.id === person);
      if (!who) return send(res, 404, { ok: false, problems: ['Nobody of that name is listed.'] });
      if (who.claimed) return send(res, 409, { ok: false, problems: [who.name + ' has already claimed this place. If that was not you, use "Ask for removal" or write to the stewards.'] });
      if (who.pending && who.pending !== lock.slice(0, 12)) return send(res, 409, { ok: false, problems: ['Someone has already asked for this name and a steward has not settled it yet.'] });
      const display = clean(raw.display, 40), badName = textProblems('display', display);
      if (badName.length) return send(res, 422, { ok: false, problems: badName });
      if (!storageReady()) return send(res, 503, { ok: false, problems: ['The door has no storage connected yet.'] });
      const ask = { kind: 'ask', door: newId(), t: new Date().toISOString(), v, person, display, lock };
      await putItem(ask);
      return send(res, 202, { ok: true, person, pending: true, message: 'Asked. A steward of the work will confirm that it is you, usually within a day. Come back on this same device: your key is kept here.' });
    }
    if (!(await claimed(raw.person, raw.token))) return send(res, 403, { ok: false, problems: ['That claim link is not valid (or has not been published yet). Ask the author for a fresh one.'] });
    const display = clean(raw.display, 40);
    const bad = textProblems('display', display);
    if (bad.length) return send(res, 422, { ok: false, problems: bad });
    if (raw.check) return send(res, 200, { ok: true, person: clean(raw.person, 44), valid: true });
    if (!storageReady()) return send(res, 503, { ok: false, problems: ['The door has no storage connected yet.'] });
    const item = { kind: 'claim', door: newId(), t: new Date().toISOString(), v, person: clean(raw.person, 44), display, verified: true };
    await putItem(item);
    send(res, 202, { ok: true, person: item.person, message: 'This place in the work is yours now. Within the hour the site will show it as claimed, under the name you chose. Keep your link; it is your key.' });
  } catch (e) { if (e instanceof DoorFull) return send(res, 503, { ok: false, problems: [FULL] }); send(res, 500, { ok: false, problems: [stuck(e)] }); }
}
