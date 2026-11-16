// GET /mcp/server-card — an MCP Server Card (SEP-2127): who this server is and where to connect, readable before any
// connection is opened. The AI Catalog at /.well-known/ai-catalog.json points here. It lists no tools on purpose; those
// are asked for at run time (tools/list).
import { SITE, site } from './_lib.js';
import { INFO, VERSIONS } from './mcp.js';

export default async function handler(req, res) {
  // the door's own address is whatever the work says it is (data/config.json), never what the caller's Host header claims
  const cfg = await site('data/config.json', 600000);
  const self = String((cfg && cfg.door) || 'https://aigorithmic-butterfly-effect-door.vercel.app').replace(/\/$/, '');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, If-None-Match');
  res.setHeader('Access-Control-Expose-Headers', 'ETag');
  if (req.method === 'OPTIONS') { res.statusCode = 204; return res.end(); }
  if (req.method !== 'GET' && req.method !== 'HEAD') { res.statusCode = 405; return res.end(); }
  res.statusCode = 200;
  res.setHeader('Content-Type', 'application/mcp-server-card+json');
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.end(JSON.stringify({
    $schema: 'https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json',
    name: 'io.github.ranaji10/aigorithmic-butterfly-effect',
    title: INFO.title,
    description: 'A slow, open artwork (2021 to 2046). Listen, then leave one small mark as yourself. No key.',
    version: INFO.version,
    websiteUrl: SITE,
    repository: { url: 'https://github.com/ranaji10/aigorithmic-butterfly-effect', source: 'github', subfolder: 'door' },
    remotes: [{ type: 'streamable-http', url: self + '/mcp', supportedProtocolVersions: VERSIONS }],
  }));
}
