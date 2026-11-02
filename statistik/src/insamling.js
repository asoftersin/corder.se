// Publik insamling: POST /e från corder.se. Svarar alltid 204 på giltiga ursprung, så att sidan aldrig påverkas.
import { GALLRA_DAGAR, MAX_ARENDEN_PER_BESOKARE, MAX_ARENDEN_PER_DAG, SPARA_ARENDEN_DAGAR, arBot, arRobotformular, besokshash, dagarSedan, enhet, summeraSatser, svenskDag, tolkaArende, tolkaHandelse } from './lib.js';

const MAX_STORLEK = 2048;
const MAX_FORMULAR = 32768;

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

// Valfritt: mejl om nytt ärende via Resend. Utan nyckel syns ärendet bara i portalen.
async function avisera(a, env) {
  if (!env.RESEND_API_KEY || !env.AVISERA_FRAN || !env.AVISERA_TILL) return;
  const rubrik = a.typ === 'bestallning' ? 'Ny beställning' : 'Ny ansökan';
  const rader = a.rader ? JSON.parse(a.rader).map(r => `${r.antal} st ${r.artikel || ''} (${r.ean})`) : [];
  const text = [`${rubrik} från ${a.foretag}`, `Kontakt: ${a.kontakt}, ${a.epost}, ${a.telefon || 'inget telefonnummer'}`, `Ort: ${a.ort || '-'}`,
    `Typ: ${a.butikstyp || '-'}, antal butiker: ${a.butiker || '-'}`, '', a.meddelande || '', ...rader].join('\n');
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST', headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: env.AVISERA_FRAN, to: env.AVISERA_TILL, reply_to: a.epost, subject: `${rubrik}: ${a.foretag}`, text }),
  });
  if (!r.ok) throw new Error(`avisering ${r.status}`);
}

async function taEmotArende(request, text, env, ctx, cors) {
  const svara = (status, kropp = null) => new Response(kropp, { status, headers: cors });
  if (text.length > MAX_FORMULAR) return svara(413);
  if (arBot(request.headers.get('User-Agent') || '')) return svara(403);
  let data;
  try { data = JSON.parse(text); } catch { return svara(400); }
  if (arRobotformular(data)) return svara(201); // Roboten ska inte märka att den stoppats.
  const a = tolkaArende(data);
  if (!a) return svara(400);
  const dag = svenskDag();
  const nyckel = await dagensNyckel(env.DB, dag);
  const besokare = await besokshash(nyckel, request.headers.get('CF-Connecting-IP') || '', request.headers.get('User-Agent') || '');
  const takt = await env.DB.prepare('SELECT antal, (SELECT COALESCE(SUM(antal), 0) FROM arende_takt WHERE dag = ?1) AS alla FROM (SELECT COALESCE((SELECT antal FROM arende_takt WHERE dag = ?1 AND besokare = ?2), 0) AS antal)').bind(dag, besokare).first();
  if (takt.antal >= MAX_ARENDEN_PER_BESOKARE || takt.alla >= MAX_ARENDEN_PER_DAG) return svara(429);
  await env.DB.batch([
    env.DB.prepare('INSERT INTO arende_takt (dag, besokare, antal) VALUES (?, ?, 1) ON CONFLICT (dag, besokare) DO UPDATE SET antal = antal + 1').bind(dag, besokare),
    env.DB.prepare(`INSERT INTO arenden (skapad, typ, foretag, kontakt, epost, telefon, ort, butikstyp, butiker, meddelande, rader) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(dag, a.typ, a.foretag, a.kontakt, a.epost, a.telefon, a.ort, a.butikstyp, a.butiker, a.meddelande, a.rader),
  ]);
  ctx.waitUntil(avisera(a, env).catch(e => console.error('avisering', e.message)));
  return svara(201);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== '/e' && url.pathname !== '/f') return new Response('Inte här', { status: 404 });
    const ursprung = request.headers.get('Origin');
    if (!(env.TILLATNA_URSPRUNG || '').split(',').includes(ursprung)) return new Response(null, { status: 403 });
    const cors = { 'Access-Control-Allow-Origin': ursprung, 'Access-Control-Allow-Methods': 'POST', Vary: 'Origin' };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'POST') return new Response(null, { status: 405, headers: cors });
    // Innehållet måste läsas innan svaret skickas. Fel loggas men når aldrig besökaren.
    const text = await request.text();
    if (url.pathname === '/f') return taEmotArende(request, text, env, ctx, cors);
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
      env.DB.prepare('DELETE FROM arende_takt WHERE dag < ?').bind(idag),
      env.DB.prepare('DELETE FROM arenden WHERE skapad < ?').bind(dagarSedan(idag, SPARA_ARENDEN_DAGAR)),
    ]);
  },
};
