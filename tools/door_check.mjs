// Does the door still work with the storage library that is installed in door/node_modules?
//   cd door && npm ci --ignore-scripts && cd .. && node tools/door_check.mjs
// Used by .github/workflows/dependencies.yml before a dependency update is merged, and by hand before any change to door/.
// It never touches the real store and nothing leaves the machine:
//   1. the door's own storage functions (door/api/_lib.js) run against a stand-in for the blob service on this machine, and
//      every request they make is compared with what the service is known to accept;
//   2. the whole door is started as in a rehearsal (door/dev.mjs) and a mark is left and found again.
// Prints one line per check; exits 1 if anything is off.
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = process.env.ABE_CHECK_ROOT || path.dirname(path.dirname(fileURLToPath(import.meta.url)));   // ABE_CHECK_ROOT: check another checkout with this script
let bad = 0;
const ok = (name, cond, detail) => { console.log((cond ? 'ok   ' : 'FAIL ') + name + (cond || !detail ? '' : '  -> ' + detail)); if (!cond) bad++; };

// ---- 1. the storage functions against a stand-in ----
const seen = [], kept = {};
const srv = http.createServer((q, s) => { let b = ''; q.on('data', (c) => b += c); q.on('end', () => {
  const u = new URL(q.url, 'http://x'); seen.push({ m: q.method, p: u.pathname, q: Object.fromEntries(u.searchParams), h: q.headers, b });
  const self = 'http://127.0.0.1:' + srv.address().port;
  s.setHeader('content-type', 'application/json');
  if (q.method === 'PUT') { const pn = u.searchParams.get('pathname'); kept[pn] = b; return s.end(JSON.stringify({ url: self + '/file/' + pn, downloadUrl: self + '/file/' + pn, pathname: pn, contentType: 'application/json', contentDisposition: 'inline', etag: '"e"' })); }
  if (q.method === 'GET' && u.pathname.startsWith('/file/')) return s.end(kept[u.pathname.slice(6)] || 'null');
  if (q.method === 'GET') return s.end(JSON.stringify({ blobs: Object.keys(kept).map((pn) => ({ url: self + '/file/' + pn, downloadUrl: self + '/file/' + pn, pathname: pn, size: kept[pn].length, uploadedAt: new Date().toISOString(), etag: '"e"' })), hasMore: false, folders: [] }));
  if (q.method === 'POST' && u.pathname === '/delete') { try { for (const x of JSON.parse(b).urls) delete kept[new URL(x).pathname.slice(6)]; } catch {} return s.end('null'); }
  s.statusCode = 404; s.end('{}'); }); });
await new Promise((r) => srv.listen(0, '127.0.0.1', r));
process.env.VERCEL_BLOB_API_URL = 'http://127.0.0.1:' + srv.address().port;
process.env.BLOB_READ_WRITE_TOKEN = 'vercel_blob_rw_rehearsal_notarealsecret';
delete process.env.ABE_LOCAL_STORE;
process.env.ABE_SITE_DIR = root;
try {
  const lib = await import(pathToFileURL(path.join(root, 'door/api/_lib.js')).href);
  ok('the door sees a blob store', lib.storageReady());
  await lib.putItem({ kind: 'say', door: 'check-1', t: new Date().toISOString(), hears: 's001', text: 'rehearsal', by: 'ai' });
  const put = seen.find((x) => x.m === 'PUT');
  ok('put: one PUT to /?pathname=inbox/<id>.json', !!put && put.p === '/' && put.q.pathname === 'inbox/check-1.json', JSON.stringify(put && [put.p, put.q]));
  ok('put: no random suffix, JSON, one minute of cache', !!put && put.h['x-add-random-suffix'] === '0' && put.h['x-content-type'] === 'application/json' && put.h['x-cache-control-max-age'] === '60', JSON.stringify(put && Object.fromEntries(Object.entries(put.h).filter(([k]) => k.startsWith('x-')))));
  ok('put: the mark arrives whole', !!put && JSON.parse(put.b).door === 'check-1');
  const items = await lib.listItems();
  const ls = seen.filter((x) => x.m === 'GET' && x.p === '/');
  ok('list: GET /?prefix=inbox/ with a limit', ls.length > 0 && ls.every((x) => x.q.prefix === 'inbox/' && +x.q.limit > 0), JSON.stringify(ls.map((x) => x.q)));
  ok('list: the mark is read back with its address', items.length === 1 && items[0].door === 'check-1' && /inbox\/check-1\.json$/.test(items[0]._url || ''), JSON.stringify(items).slice(0, 200));
  await lib.dropItems(items.map((x) => x._url));
  const del = seen.find((x) => x.m === 'POST' && x.p === '/delete');
  ok('delete: POST /delete with the addresses', !!del && JSON.parse(del.b).urls.length === 1 && Object.keys(kept).length === 0, del && del.b);
  ok('every request carries the store token', seen.filter((x) => !x.p.startsWith('/file/')).every((x) => x.h.authorization === 'Bearer ' + process.env.BLOB_READ_WRITE_TOKEN));
} catch (e) { ok('the storage functions run', false, String(e && e.stack || e).slice(0, 400)); }
srv.close();

// ---- 2. the whole door, as in a rehearsal ----
const store = fs.mkdtempSync(path.join(os.tmpdir(), 'abe-door-')), port = 18000 + Math.floor(Math.random() * 2000), base = 'http://localhost:' + port;
const env = { ...process.env, ABE_LOCAL_STORE: store }; delete env.BLOB_READ_WRITE_TOKEN; delete env.VERCEL_BLOB_API_URL;
const child = spawn(process.execPath, [path.join(root, 'door/dev.mjs'), String(port)], { env, stdio: ['ignore', 'pipe', 'pipe'] });
let out = ''; child.stdout.on('data', (d) => out += d); child.stderr.on('data', (d) => out += d);
try {
  for (let i = 0; i < 50 && !/rehearsal at/.test(out); i++) await new Promise((r) => setTimeout(r, 200));
  ok('the door starts', /rehearsal at/.test(out), out.slice(-300));
  const j = async (p, o) => { const r = await fetch(base + p, o); let body = null; try { body = await r.json(); } catch {} return [r.status, body]; };
  const [s0, b0] = await j('/api');
  ok('GET /api describes the door', s0 === 200 && !!b0, String(s0));
  const [s1, b1] = await j('/api/say', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ hears: 's001', text: 'A rehearsal mark; it never leaves this machine.', by: 'ai', name: 'door check' }) });
  ok('POST /api/say takes a mark', s1 === 202 && b1 && b1.ok === true, s1 + ' ' + JSON.stringify(b1).slice(0, 200));
  const [s2, b2] = await j('/api/inbox');
  ok('GET /api/inbox shows it waiting', s2 === 200 && JSON.stringify(b2).includes('A rehearsal mark'), s2 + ' ' + JSON.stringify(b2).slice(0, 200));
  const [s3, b3] = await j('/api/say', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ hears: 's001', text: 'see https://example.com', by: 'ai' }) });
  ok('POST /api/say still refuses a link', s3 === 422 && b3 && b3.ok === false, s3 + ' ' + JSON.stringify(b3).slice(0, 200));
  const [s4] = await j('/mcp/server-card');
  ok('GET /mcp/server-card answers', s4 === 200, String(s4));
} catch (e) { ok('the rehearsal runs', false, String(e).slice(0, 300)); }
child.kill(); fs.rmSync(store, { recursive: true, force: true });
console.log(bad ? bad + ' check(s) failed.' : 'The door works with the installed storage library.');
process.exit(bad ? 1 : 0);
