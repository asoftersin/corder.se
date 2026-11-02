// Publik insamling: POST /e från corder.se. Svarar alltid 204 på giltiga ursprung, så att sidan aldrig påverkas.
import { GALLRA_DAGAR, arBot, besokshash, dagarSedan, enhet, summeraSatser, svenskDag, tolkaHandelse } from './lib.js';

const MAX_STORLEK = 2048;

async function dagensNyckel(db, dag) {
  const slump = [...crypto.getRandomValues(new Uint8Array(32))].map(b => b.toString(16).padStart(2, '0')).join('');
  await db.prepare('INSERT OR IGNORE INTO dagsnyckel (dag, nyckel) VALUES (?, ?)').bind(dag, slump).run();
  return (await db.prepare('SELECT nyckel FROM dagsnyckel WHERE dag = ?').bind(dag).first()).nyckel;
}

async function taEmot(request, text, env) {
  const ua = request.headers.get('User-Agent') || '';
  if (arBot(ua) || request.headers.get('DNT') === '1' || request.headers.get('Sec-GPC') === '1') return;
  if (text.length > MAX_STORLEK) return;
  const h = tolkaHandelse(JSON.parse(text), env.EGEN_VARD || 'corder.se');
  if (!h) return;
  const dag = svenskDag();
  const nyckel = await dagensNyckel(env.DB, dag);
  const besokare = await besokshash(nyckel, request.headers.get('CF-Connecting-IP') || '', ua);
  await env.DB.prepare(`INSERT INTO handelser (dag, typ, namn, varde, sida, kalla, utm_kalla, utm_medium, utm_kampanj, enhet, land, besokare)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .bind(dag, h.typ, h.namn, h.varde, h.sida, h.kalla, h.utm_kalla, h.utm_medium, h.utm_kampanj, enhet(ua), request.cf?.country || null, besokare).run();
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== '/e') return new Response('Inte här', { status: 404 });
    const ursprung = request.headers.get('Origin');
    if (!(env.TILLATNA_URSPRUNG || '').split(',').includes(ursprung)) return new Response(null, { status: 403 });
    const cors = { 'Access-Control-Allow-Origin': ursprung, 'Access-Control-Allow-Methods': 'POST', Vary: 'Origin' };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'POST') return new Response(null, { status: 405, headers: cors });
    // Innehållet måste läsas innan svaret skickas. Fel loggas men når aldrig besökaren.
    const text = await request.text();
    ctx.waitUntil(taEmot(request, text, env).catch(e => console.error('insamling', e.message)));
    return new Response(null, { status: 204, headers: cors });
  },

  // En gång per dygn: summera gårdagen, radera gamla nycklar och gallra gamla händelser.
  async scheduled(_, env) {
    const idag = svenskDag(), igar = dagarSedan(idag, 1);
    await env.DB.batch([
      ...summeraSatser(env.DB, igar),
      env.DB.prepare('DELETE FROM dagsnyckel WHERE dag < ?').bind(idag),
      env.DB.prepare('DELETE FROM handelser WHERE dag < ?').bind(dagarSedan(idag, GALLRA_DAGAR)),
    ]);
  },
};
