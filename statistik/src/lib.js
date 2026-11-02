// Gemensam logik för insamling och portal. Rena funktioner där det går, så att de kan testas utan Cloudflare.

const BOTAR = /bot|crawl|spider|slurp|preview|headless|lighthouse|pingdom|monitor|facebookexternalhit|curl|wget|python|axios/i;
export const GALLRA_DAGAR = 90;

export const arBot = ua => !ua || BOTAR.test(ua);

export function enhet(ua) {
  if (/ipad|tablet|(android(?!.*mobile))/i.test(ua)) return 'surfplatta';
  if (/mobi|iphone|ipod|android/i.test(ua)) return 'mobil';
  return 'dator';
}

// Dagen enligt svensk tid, så att dygnet byts vid svensk midnatt.
export const svenskDag = (nu = new Date()) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Stockholm' }).format(nu);

export function dagarSedan(dag, antal) {
  const d = new Date(`${dag}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() - antal);
  return d.toISOString().slice(0, 10);
}

const kort = (v, max) => {
  if (typeof v !== 'string') return null;
  const t = v.replace(/[\u0000-\u001f]/g, '').trim().slice(0, max);
  return t || null;
};

export function kallaFran(referens, egenVard) {
  try {
    const u = new URL(referens);
    if (!/^https?:$/.test(u.protocol)) return null;
    const vard = u.hostname.replace(/^www\./, '');
    return vard === egenVard ? null : vard;
  } catch { return null; }
}

// Ogiltiga anrop ger null. Bara sökvägen sparas, aldrig frågesträngen.
export function tolkaHandelse(data, egenVard = 'corder.se') {
  if (!data || typeof data !== 'object' || !['s', 'e'].includes(data.t)) return null;
  const sida = kort(data.p, 200);
  if (!sida || !sida.startsWith('/')) return null;
  const namn = data.t === 'e' ? kort(data.n, 40) : null;
  if (data.t === 'e' && !namn) return null;
  return {
    typ: data.t, namn, varde: data.t === 'e' ? kort(data.v, 80) : null,
    sida: sida.split(/[?#]/)[0],
    kalla: kallaFran(data.r, egenVard),
    utm_kalla: kort(data.us, 60), utm_medium: kort(data.um, 60), utm_kampanj: kort(data.uc, 60),
  };
}

const EPOST = /^[^\s@"'<>]{1,64}@[^\s@"'<>]{1,190}\.[^\s@"'<>.]{2,}$/;
export const MAX_ARENDEN_PER_BESOKARE = 10;
export const MAX_ARENDEN_PER_DAG = 300;
export const SPARA_ARENDEN_DAGAR = 730;

// Fällan är ett dolt fält som bara robotar fyller i. Ett formulär som skickas på under två sekunder är också en robot.
export const arRobotformular = data => !data || !!data.webbplats || (typeof data.tid === 'number' && data.tid < 2000);

// Ogiltiga formulär ger null.
export function tolkaArende(data) {
  if (!data || typeof data !== 'object' || !['ansokan', 'bestallning'].includes(data.typ)) return null;
  const foretag = kort(data.foretag, 120), kontakt = kort(data.kontakt, 120), epost = kort(data.epost, 254);
  if (!foretag || !kontakt || !epost || !EPOST.test(epost)) return null;
  const leverans = kort(data.leverans, 200);
  let rader = null;
  if (data.typ === 'bestallning') {
    if (!Array.isArray(data.rader) || !data.rader.length || data.rader.length > 150) return null;
    rader = [];
    for (const r of data.rader) {
      const antal = Number(r?.antal);
      if (!/^\d{13}$/.test(r?.ean) || !Number.isInteger(antal) || antal < 1 || antal > 100000) return null;
      rader.push({ ean: r.ean, artikel: kort(r.artikel, 120), antal });
    }
  }
  return {
    typ: data.typ, foretag, kontakt, epost, telefon: kort(data.telefon, 40), ort: kort(data.ort, 80), butikstyp: kort(data.butikstyp, 60),
    butiker: kort(String(data.butiker ?? ''), 10), meddelande: [leverans && `Leverans: ${leverans}`, kort(data.meddelande, 2000)].filter(Boolean).join('\n') || null, rader: rader && JSON.stringify(rader),
  };
}

export async function besokshash(nyckel, ip, ua) {
  const d = new TextEncoder().encode(`${nyckel}|${ip}|${ua}`);
  const h = new Uint8Array(await crypto.subtle.digest('SHA-256', d));
  return [...h.slice(0, 8)].map(b => b.toString(16).padStart(2, '0')).join('');
}

const DIMENSIONER = {
  sidor: ["sida", "typ = 's'"],
  kallor: ["COALESCE(kalla, 'Direkt')", "typ = 's'"],
  kampanjer: ["utm_kalla || COALESCE(' / ' || utm_medium, '') || COALESCE(' / ' || utm_kampanj, '')", "typ = 's' AND utm_kalla IS NOT NULL"],
  enheter: ['enhet', "typ = 's'"],
  lander: ["COALESCE(land, 'Okänt')", "typ = 's'"],
  handelser: ["namn || COALESCE(' · ' || varde, '')", "typ = 'e'"],
};

// Skriver om dagens rader i dagsumma, så att samma dag kan summeras flera gånger.
export function summeraSatser(db, dag) {
  const satser = [db.prepare('DELETE FROM dagsumma WHERE dag = ?').bind(dag)];
  satser.push(db.prepare(`INSERT INTO dagsumma (dag, dimension, nyckel, antal, unika)
    SELECT dag, 'total', 'sidvisningar', COUNT(*), COUNT(DISTINCT besokare) FROM handelser WHERE dag = ? AND typ = 's' GROUP BY dag`).bind(dag));
  for (const [dim, [uttryck, villkor]] of Object.entries(DIMENSIONER)) {
    satser.push(db.prepare(`INSERT INTO dagsumma (dag, dimension, nyckel, antal, unika)
      SELECT dag, ?, ${uttryck} AS n, COUNT(*), COUNT(DISTINCT besokare) FROM handelser
      WHERE dag = ? AND ${villkor} AND n IS NOT NULL GROUP BY n`).bind(dim, dag));
  }
  return satser;
}

// --- Inloggning: kontrollerar Cloudflare Access-token (RS256) ---

const b64url = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(s.length / 4) * 4, '=')), c => c.charCodeAt(0));
const json = s => JSON.parse(new TextDecoder().decode(b64url(s)));

export async function verifieraToken(token, { nycklar, aud, utfardare, nu = Date.now() / 1000 }) {
  try {
    const [h, p, s] = token.split('.');
    const huvud = json(h), last = json(p);
    if (huvud.alg !== 'RS256') return null;
    const jwk = nycklar.find(k => k.kid === huvud.kid);
    if (!jwk) return null;
    const nyckel = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', nyckel, b64url(s), new TextEncoder().encode(`${h}.${p}`));
    if (!ok || last.iss !== utfardare || !(last.exp > nu)) return null;
    if (!(Array.isArray(last.aud) ? last.aud : [last.aud]).includes(aud)) return null;
    return last;
  } catch { return null; }
}
