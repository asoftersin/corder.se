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

function csv(r) {
  const rader = [['Dimension', 'Nyckel', 'Antal', 'Dagliga besökare summerat']];
  for (const d of r.trend) rader.push(['dag', d.dag, d.sidvisningar, d.besokare]);
  for (const [dim, poster] of Object.entries(r.dimensioner)) for (const p of poster) rader.push([dim, p.nyckel, p.antal, p.unika]);
  return '﻿' + rader.map(x => x.map(csvCell).join(';')).join('\r\n') + '\r\n';
}

export default {
  async fetch(request, env) {
    if (request.method !== 'GET') return svar('Metoden stöds inte', 'text/plain; charset=utf-8', 405);
    let ok = false;
    try { ok = await inloggad(request, env); } catch (e) { console.error('inloggning', e.message); }
    if (!ok) return svar('Du behöver logga in.', 'text/plain; charset=utf-8', 403);
    const url = new URL(request.url);
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
