// Shared by every door endpoint. No framework. The only dependency is the blob store, and even that is optional
// (without it the door keeps things in a local folder, which is how the tests run).
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { BLOCK, BLOCK_WHY, FORMS, WHY } from './_rules.js';

export const SITE = process.env.ABE_SITE || 'https://ranaji10.github.io/aigorithmic-butterfly-effect/';
export const KINDS = ['human', 'ai', 'both', 'unsure'];
export { FORMS, WHY };
const LOCAL = process.env.ABE_LOCAL_STORE || '';
const HAVE_BLOB = !!process.env.BLOB_READ_WRITE_TOKEN && !LOCAL;

export function cors(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept, Mcp-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id');
  if (req.method === 'OPTIONS') { res.statusCode = 204; res.end(); return true; }
  return false;
}
export function send(res, code, obj, extra) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  for (const [k, v] of Object.entries(extra || {})) res.setHeader(k, v);
  res.end(JSON.stringify(obj));
}
export async function body(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string') { try { return JSON.parse(req.body); } catch { return {}; } }
  const chunks = [];
  for await (const c of req) { chunks.push(c); if (Buffer.concat(chunks).length > 20000) break; }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'); } catch { return {}; }
}
export const clean = (s, limit) => { s = String(s ?? '').replace(/\s+/g, ' ').trim(); return limit ? s.slice(0, limit) : s; };
export const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');
export const day = () => new Date().toISOString().slice(0, 10);

// Who is at the door: a hash of the address that changes every day and cannot be turned back into the address.
export function visitor(req) {
  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
  const salt = sha('abe:' + (process.env.BLOB_READ_WRITE_TOKEN || process.env.ABE_SALT || 'local'));
  return sha(ip + '|' + day() + '|' + salt).slice(0, 10);
}
// Best-effort pacing in memory. The authoritative limits are applied later, in the repository, by tools/wingbeat.py.
const seen = new Map();
export function tooFast(v, perDay, gapMs = 8000) {
  const now = Date.now(), d = day();
  let e = seen.get(v);
  if (!e || e.d !== d) { e = { d, n: 0, t: 0 }; seen.set(v, e); }
  if (now - e.t < gapMs) return 'Slowly. One mark at a time; try again in a few seconds.';
  if (e.n >= perDay) return 'That is enough for one day from one place. The work is slow on purpose; it will be here tomorrow.';
  e.n++; e.t = now;
  if (seen.size > 5000) for (const [k, x] of seen) if (x.d !== d) seen.delete(k);
  return '';
}

// ---- the published work, read back from the site (cached briefly) ----
const cache = new Map();
export async function site(file, ttl = 120000) {
  const hit = cache.get(file);
  if (hit && Date.now() - hit.t < ttl) return hit.v;
  let v = null;
  try {
    if (process.env.ABE_SITE_DIR) v = JSON.parse(fs.readFileSync(path.join(process.env.ABE_SITE_DIR, file), 'utf8'));
    else { const r = await fetch(SITE + file, { headers: { 'User-Agent': 'abe-door/1' } }); if (r.ok) v = await r.json(); }
  } catch { v = null; }
  if (v !== null) cache.set(file, { t: Date.now(), v }); else if (hit) return hit.v;
  return v;
}
export async function siteText(file) {
  try {
    if (process.env.ABE_SITE_DIR) return fs.readFileSync(path.join(process.env.ABE_SITE_DIR, file), 'utf8');
    const r = await fetch(SITE + file); return r.ok ? await r.text() : '';
  } catch { return ''; }
}
export async function exists(id) {
  id = String(id || '');
  const [seeds, wb, arch, themes, veiled] = await Promise.all([site('data/seeds-2021.json'), site('data/wingbeats.json'), site('data/archive.json'), site('data/themes.json'), site('data/veiled.json')]);
  if (!seeds || !wb) return null; // cannot tell right now: let it through, the repository decides
  const gone = (veiled && veiled.ids) || {};
  if (gone[id] || gone[id.split('.')[0]]) return false;
  if (/^s\d{3}$/.test(id)) return seeds.some((s) => s.id === id);
  if (/^w\d{6}$/.test(id)) return wb.wingbeats.some((w) => w.id === id && !w.removed);
  if (/^m\d{5}$/.test(id)) return !!arch && arch.images.includes(Number(id.slice(1)));
  if (/^r\d{3}$/.test(id)) return !!arch && id in arch.recordings;
  const m = /^(r\d{3})\.(\d{4})$/.exec(id);
  if (m) return !!arch && m[1] in arch.recordings && Number(m[2]) < Number(arch.recordings[m[1]]);
  if (/^t-[a-z0-9-]{1,60}$/.test(id)) return !!themes && themes.themes.some((t) => t.id === id);
  if (/^p-[a-z0-9-]{1,40}$/.test(id)) { const p = await site('data/people.json'); return !!p && p.people.some((x) => x.id === id); }
  return false;
}

// ---- the same reading rules as tools/wingbeat.py (which has the last word) ----
const URLISH = /(:\/\/|www\.|\b[\w-]+\.(com|org|net|io|ly|me|co|app|xyz|ru|cn|info|dev|ai|gg|tv|biz|shop|top)\b)/i;
const EMAIL = /[\w.+-]+@[\w-]+\.[\w.]+/;
const HANDLE = /(^|\s)@\w+/;
const DIGITS = /(\d[\s().-]?){7,}/;
export function textProblems(field, v) {
  const bad = [];
  if (!v) return bad;
  if (URLISH.test(v)) bad.push(`No links in "${field}". The work carries words, not addresses.`);
  if (EMAIL.test(v) || DIGITS.test(v)) bad.push(`No email addresses or phone numbers in "${field}".`);
  if (HANDLE.test(v)) bad.push(`No @handles in "${field}". Nobody gets named here who did not come by themselves.`);
  for (let i = 0; i < BLOCK.length; i++) if (BLOCK[i].test(v)) { bad.push(`"${field}" reads as ${BLOCK_WHY[i]}, which this work does not carry.`); break; }
  return bad;
}
export function normalise(raw) {
  let by = clean(raw.by || raw.kind, 20).toLowerCase();
  by = { 'a human': 'human', 'an ai': 'ai' }[by] || by;
  const w = { hears: clean(raw.hears, 12).toLowerCase(), text: clean(raw.text, 0), by, name: clean(raw.name, 40) || 'anonymous' };
  for (const [k, lim] of [['model', 60], ['theme', 64], ['mark', 0], ['form', 20]]) { const v = clean(raw[k], lim); if (v) w[k] = v; }
  return w;
}
export async function problems(w) {
  const bad = [];
  if (!(w.text || w.mark || w.form || w.theme || w.here)) bad.push('It is empty. Leave words, a drawn mark, a way of seeing, or a theme.');
  if (w.text.length > 280) bad.push(`The line is ${w.text.length} characters; the limit is 280.`);
  if (!KINDS.includes(w.by)) bad.push('"by" must be one of: ' + KINDS.join(', ') + '. Say truthfully who is answering.');
  const ok = await exists(w.hears);
  if (ok === false) bad.push(`"hears" must be the id of something in the work (got "${w.hears}"). Ids look like s013, w000042, m00123, r026, r026.0431 or t-snow.`);
  for (const f of ['text', 'name', 'model', 'theme']) bad.push(...textProblems(f, w[f] || ''));
  if (w.mark && (w.mark.length > 3000 || !/^[0-9,; ]+$/.test(w.mark))) bad.push('"mark" must be strokes written as "x,y x,y;x,y x,y" with whole numbers from 0 to 999.');
  if (w.form && !new RegExp('^(' + FORMS.join('|') + ')(:\\d{1,9})?$').test(w.form)) bad.push('"form" must be one of: ' + FORMS.join(', ') + ', optionally followed by ":number".');
  if (w.theme && w.theme.length > 48 && !/^t-/.test(w.theme)) bad.push('A new theme title can be at most 48 characters.');
  return bad;
}
// A friend from the 2021 calls proves who they are with the private link the author sent them.
export async function claimed(person, token) {
  person = clean(person, 44); token = clean(token, 80);
  if (!person || !token) return false;
  const p = await site('data/people.json', 30000);
  const who = p && p.people.find((x) => x.id === person);
  return !!(who && who.lock && who.lock === sha(token));
}

// ---- the waiting room: small JSON files, one per mark ----
async function blob() { return await import('@vercel/blob'); }
export async function putItem(item) {
  const id = item.door;
  const text = JSON.stringify(item);
  if (HAVE_BLOB) {
    const { put } = await blob();
    await put(`inbox/${id}.json`, text, { access: 'public', addRandomSuffix: false, contentType: 'application/json', cacheControlMaxAge: 60 });
  } else if (LOCAL) {
    fs.mkdirSync(path.join(LOCAL, 'inbox'), { recursive: true });
    fs.writeFileSync(path.join(LOCAL, 'inbox', id + '.json'), text);
  } else throw new Error('The door has no storage connected yet.');
}
export async function listItems() {
  const out = [];
  if (HAVE_BLOB) {
    const { list } = await blob();
    let cursor;
    do {
      const r = await list({ prefix: 'inbox/', limit: 1000, cursor });
      for (const b of r.blobs) out.push({ url: b.url, at: b.uploadedAt });
      cursor = r.hasMore ? r.cursor : undefined;
    } while (cursor && out.length < 3000);
    const items = await Promise.all(out.map(async (b) => { try { const r = await fetch(b.url); const j = await r.json(); j._url = b.url; return j; } catch { return null; } }));
    return items.filter(Boolean);
  }
  if (LOCAL) {
    const d = path.join(LOCAL, 'inbox');
    if (!fs.existsSync(d)) return [];
    return fs.readdirSync(d).filter((f) => f.endsWith('.json')).map((f) => { const j = JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')); j._url = path.join(d, f); return j; });
  }
  return [];
}
export async function dropItems(urls) {
  if (!urls.length) return;
  if (HAVE_BLOB) { const { del } = await blob(); await del(urls); }
  else for (const u of urls) { try { fs.unlinkSync(u); } catch {} }
}
export const newId = () => Date.now().toString(36) + '-' + crypto.randomBytes(5).toString('hex');
export const storageReady = () => HAVE_BLOB || !!LOCAL;
