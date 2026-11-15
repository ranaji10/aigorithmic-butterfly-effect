// Local rehearsal: serves the site, the media folder and the door on one port, with nothing leaving the machine.
//   ABE_MEDIA_DIR=../aigorithmic-butterfly-effect-archive node door/dev.mjs [port]
// Marks are kept in a local folder (door/.local-store) instead of the blob store.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url)), root = path.dirname(here);
const port = Number(process.argv[2] || 8000), base = `http://localhost:${port}/`;
process.env.ABE_LOCAL_STORE ||= path.join(here, '.local-store');
process.env.ABE_SITE_DIR ||= root;
const media = process.env.ABE_MEDIA_DIR || '';
const routes = {};
for (const n of ['say', 'inbox', 'remove', 'claim', 'mcp', 'index']) routes[n] = (await import(`./api/${n}.js`)).default;
const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4', '.opus': 'audio/ogg', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.md': 'text/plain; charset=utf-8' };
http.createServer(async (req, res) => {
  const u = new URL(req.url, base);
  let p = decodeURIComponent(u.pathname);
  const api = p === '/mcp' ? 'mcp' : p === '/api' ? 'index' : (/^\/api\/(\w+)$/.exec(p) || [])[1];
  if (api && routes[api]) { req.query = Object.fromEntries(u.searchParams); return routes[api](req, res); }
  let file = p.startsWith('/media/') && media ? path.join(media, p.slice(7)) : path.join(root, p === '/' ? 'index.html' : p);
  if (!file.startsWith(media && p.startsWith('/media/') ? media : root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.statusCode = 404; return res.end('not found'); }
  res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (p === '/data/config.json') { const c = JSON.parse(fs.readFileSync(file, 'utf8')); c.door = base.slice(0, -1); return res.end(JSON.stringify(c)); }
  if (p === '/data/archive.json' && media) { const a = JSON.parse(fs.readFileSync(file, 'utf8')); a.media = base + 'media/'; return res.end(JSON.stringify(a)); }
  fs.createReadStream(file).pipe(res);
}).listen(port, () => console.log('rehearsal at ' + base));
