// Adminportalen. Nekar allt utan giltig Cloudflare Access-token, även om Access skulle vara avstängt.
import { dagarSedan, summeraSatser, svenskDag, verifieraToken } from './lib.js';
import { PORTAL } from './portal.js';

const SAKERHET = {
  'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store',
};
const svar = (kropp, typ, status = 200, extra = {}) => new Response(kropp, { status, headers: { 'Content-Type': typ, ...SAKERHET, ...extra } });

let cache = { team: null, nycklar: null, tid: 0 };

async function hamtaNycklar(team) {
  if (cache.team === team && Date.now() - cache.tid < 3600e3) return cache.nycklar;
  const r = await fetch(`https://${team}.cloudflareaccess.com/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error('kunde inte hämta nycklar');
  cache = { team, nycklar: (await r.json()).keys, tid: Date.now() };
  return cache.nycklar;
}

async function inloggad(request, env) {
  if (env.LOKAL_UTAN_INLOGGNING === 'ja') {
    // Bara för wrangler dev. Gäller aldrig på en publik adress.
    return ['localhost', '127.0.0.1'].includes(new URL(request.url).hostname);
  }
  const token = request.headers.get('Cf-Access-Jwt-Assertion');
  if (!token || !env.ACCESS_TEAM || !env.ACCESS_AUD) return false;
  const nycklar = await hamtaNycklar(env.ACCESS_TEAM);
  return !!await verifieraToken(token, { nycklar, aud: env.ACCESS_AUD, utfardare: `https://${env.ACCESS_TEAM}.cloudflareaccess.com` });
}

async function rapport(env, dagar) {
  const idag = svenskDag(), fran = dagarSedan(idag, dagar - 1);
  // Dagens och gårdagens siffror räknas om vid varje visning, så att de är färska även om dygnsjobbet missats.
  await env.DB.batch([...summeraSatser(env.DB, dagarSedan(idag, 1)), ...summeraSatser(env.DB, idag)]);
  const { results: rader } = await env.DB.prepare('SELECT dag, dimension, nyckel, antal, unika FROM dagsumma WHERE dag >= ? ORDER BY dag').bind(fran).all();
  const ut = { idag, fran, trend: [], dimensioner: {} };
  const perDag = new Map();
  for (let i = dagar - 1; i >= 0; i--) perDag.set(dagarSedan(idag, i), { dag: dagarSedan(idag, i), sidvisningar: 0, besokare: 0 });
  for (const r of rader) {
    if (r.dimension === 'total') {
      const d = perDag.get(r.dag);
      if (d) { d.sidvisningar = r.antal; d.besokare = r.unika; }
      continue;
    }
    const dim = ut.dimensioner[r.dimension] ??= new Map();
    const post = dim.get(r.nyckel) ?? { nyckel: r.nyckel, antal: 0, unika: 0 };
    post.antal += r.antal; post.unika += r.unika;
    dim.set(r.nyckel, post);
  }
  ut.trend = [...perDag.values()];
  for (const k of Object.keys(ut.dimensioner)) ut.dimensioner[k] = [...ut.dimensioner[k].values()].sort((a, b) => b.antal - a.antal);
  return ut;
}

const csvCell = v => {
  const s = String(v ?? '');
  // Inleds cellen med ett formeltecken, gör den till text så att Excel inte kör den.
  const saker = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s;
  return /[;"\n]/.test(saker) ? `"${saker.replace(/"/g, '""')}"` : saker;
};

function arendenCsv(rader) {
  const kol = ['skapad', 'typ', 'status', 'foretag', 'kontakt', 'epost', 'telefon', 'ort', 'butikstyp', 'butiker', 'meddelande', 'rader'];
  return '\ufeff' + [kol, ...rader.map(r => kol.map(k => r[k]))].map(x => x.map(csvCell).join(';')).join('\r\n') + '\r\n';
}

// Ändringar kräver JSON från portalen själv, så att en annan webbplats inte kan skicka dem med din inloggning.
const egenBegaran = (request, url) => request.headers.get('Origin') === url.origin && request.headers.get('Content-Type') === 'application/json';

async function andraArende(request, env, id) {
  if (request.method === 'DELETE') {
    await env.DB.prepare('DELETE FROM arenden WHERE id = ?').bind(id).run();
    return svar('{}', 'application/json; charset=utf-8');
  }
  const { status } = await request.json().catch(() => ({}));
  if (!['ny', 'hanterad'].includes(status)) return svar('Ogiltig status', 'text/plain; charset=utf-8', 400);
  await env.DB.prepare('UPDATE arenden SET status = ? WHERE id = ?').bind(status, id).run();
  return svar('{}', 'application/json; charset=utf-8');
}

function csv(r) {
  const rader = [['Dimension', 'Nyckel', 'Antal', 'Dagliga besökare summerat']];
  for (const d of r.trend) rader.push(['dag', d.dag, d.sidvisningar, d.besokare]);
  for (const [dim, poster] of Object.entries(r.dimensioner)) for (const p of poster) rader.push([dim, p.nyckel, p.antal, p.unika]);
  return '﻿' + rader.map(x => x.map(csvCell).join(';')).join('\r\n') + '\r\n';
}

export default {
  async fetch(request, env) {
    let ok = false;
    try { ok = await inloggad(request, env); } catch (e) { console.error('inloggning', e.message); }
    if (!ok) return svar('Du behöver logga in.', 'text/plain; charset=utf-8', 403);
    const url = new URL(request.url);
    const arende = url.pathname.match(/^\/api\/arenden\/(\d+)$/);
    if (arende && ['POST', 'DELETE'].includes(request.method)) {
      if (!egenBegaran(request, url)) return svar('Nekad', 'text/plain; charset=utf-8', 403);
      return andraArende(request, env, +arende[1]);
    }
    if (request.method !== 'GET') return svar('Metoden stöds inte', 'text/plain; charset=utf-8', 405);
    if (url.pathname === '/api/arenden' || url.pathname === '/arenden.csv') {
      const { results } = await env.DB.prepare('SELECT * FROM arenden ORDER BY id DESC LIMIT 500').all();
      return url.pathname === '/arenden.csv'
        ? svar(arendenCsv(results), 'text/csv; charset=utf-8', 200, { 'Content-Disposition': 'attachment; filename="corder-arenden.csv"' })
        : svar(JSON.stringify(results), 'application/json; charset=utf-8');
    }
    if (url.pathname === '/') return svar(PORTAL, 'text/html; charset=utf-8');
    if (url.pathname === '/api/rapport' || url.pathname === '/export.csv') {
      const dagar = [7, 30, 90].includes(+url.searchParams.get('dagar')) ? +url.searchParams.get('dagar') : 30;
      const r = await rapport(env, dagar);
      return url.pathname === '/export.csv'
        ? svar(csv(r), 'text/csv; charset=utf-8', 200, { 'Content-Disposition': `attachment; filename="corder-statistik-${r.fran}-${r.idag}.csv"` })
        : svar(JSON.stringify(r), 'application/json; charset=utf-8');
    }
    return svar('Inte här', 'text/plain; charset=utf-8', 404);
  },
};
