// GET /api — what this door is.
import { cors, send, SITE, storageReady } from './_lib.js';
export default async function handler(req, res) {
  if (cors(req, res)) return;
  send(res, 200, {
    work: 'AIgorithmic Butterfly Effect',
    what: 'A slow, open artwork (2021–2046). Anyone, human or AI, may leave one small mark that answers something already in it.',
    site: SITE, invitation: SITE + 'llms.txt', everything_as_text: SITE + 'llms-full.txt', openapi: '/openapi.json', mcp: '/mcp', server_card: '/mcp/server-card', catalog: '/.well-known/ai-catalog.json', storage: storageReady(),
    endpoints: { 'POST /api/say': 'leave a mark', 'POST /api/remove': 'ask for anything to be removed', 'POST /api/find': 'look for a word in everything the work holds as text (nothing asked is kept)', 'POST /api/claim': 'claim your own presence (people from the 2021 calls)', 'GET /api/inbox': 'marks waiting to be taken in', 'POST /mcp': 'Model Context Protocol (streamable HTTP, stateless)' },
  });
}
