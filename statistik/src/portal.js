// Portalens enda sida. Inga externa skript eller typsnitt. Allt som ritas ut går genom esc().
export const PORTAL = `<!DOCTYPE html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corder statistik</title>
<style>
:root { --ink:#111; --muted:#6e6e6e; --line:#e7e7e7; --soft:#f4f4f2; --paper:#fff; --green:#3d5143; color-scheme:light; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:400 15px/1.5 "Inter Tight",system-ui,sans-serif; -webkit-font-smoothing:antialiased; }
.wrap { max-width:1240px; margin:0 auto; padding:0 clamp(16px,4vw,48px) 72px; }
header { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:16px; padding:24px 0; border-bottom:1px solid var(--line); margin-bottom:32px; }
.logo { font-size:1.5rem; letter-spacing:.03em; }
.logo small { font-size:.85rem; color:var(--muted); margin-left:10px; letter-spacing:0; }
.val { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
button, .exp { font:500 .85rem inherit; font-family:inherit; min-height:40px; padding:0 16px; border:1px solid var(--line); border-radius:999px; background:none; color:inherit; cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; }
button[aria-pressed=true] { background:var(--ink); border-color:var(--ink); color:#fff; }
.tal { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:32px; }
.tal div { background:var(--soft); border-radius:14px; padding:18px 20px; }
.tal b { display:block; font-size:2.2rem; font-weight:300; letter-spacing:-.03em; line-height:1.15; font-variant-numeric:tabular-nums; }
.tal span { color:var(--muted); font-size:.85rem; }
h2 { font-size:1rem; font-weight:500; margin:0 0 12px; }
.trend { margin-bottom:36px; }
svg { display:block; width:100%; height:180px; }
.rutnat { display:grid; grid-template-columns:repeat(auto-fill,minmax(min(100%,360px),1fr)); gap:32px; }
table { width:100%; border-collapse:collapse; font-size:.9rem; font-variant-numeric:tabular-nums; }
th, td { padding:8px 0; border-bottom:1px solid var(--line); text-align:right; }
th { color:var(--muted); font-weight:500; font-size:.78rem; }
th:first-child, td:first-child { text-align:left; word-break:break-word; padding-right:16px; }
td.tom { color:var(--muted); text-align:left; }
.arenden { margin-bottom:36px; }
.ar-huvud { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }
.ar-huvud h2 { margin:0; }
.ar-rad { border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-bottom:8px; }
.ar-rad.ny { border-color:var(--green); box-shadow:inset 3px 0 0 var(--green); }
.ar-topp { display:flex; flex-wrap:wrap; gap:6px 14px; align-items:center; }
.ar-topp b { font-weight:500; }
.ar-topp span, .ar-rad p { color:var(--muted); font-size:.88rem; }
.ar-rad p { margin:6px 0 0; white-space:pre-wrap; word-break:break-word; }
.ar-rad ul { margin:6px 0 0; padding-left:18px; font-size:.88rem; }
.ar-knappar { display:flex; gap:6px; margin-top:10px; }
.ar-tom { color:var(--muted); font-size:.9rem; }
.not { color:var(--muted); font-size:.82rem; margin-top:40px; max-width:680px; }
.fel { background:#fbeaea; color:#7a1f1f; padding:14px 18px; border-radius:10px; margin-bottom:24px; }
</style></head>
<body><div class="wrap">
<header><div class="logo">corder<small>statistik</small></div>
<div class="val" role="group" aria-label="Period">
<button data-d="7" aria-pressed="false">7 dagar</button><button data-d="30" aria-pressed="true">30 dagar</button><button data-d="90" aria-pressed="false">90 dagar</button>
<a class="exp" id="exp" href="/export.csv?dagar=30">Exportera CSV</a></div></header>
<div id="fel"></div>
<section class="arenden" aria-labelledby="ar-rubrik"><div class="ar-huvud"><h2 id="ar-rubrik">Ansökningar och beställningar</h2><a class="exp" href="/arenden.csv">Exportera ärenden</a></div><div id="arenden"></div></section>
<section class="tal" id="tal" aria-live="polite"></section>
<section class="trend"><h2>Sidvisningar per dag</h2><div id="graf"></div></section>
<div class="rutnat" id="tabeller"></div>
<p class="not">Besökare räknas per dygn utan cookies, så samma person räknas igen nästa dag. Summan över en period är därför dagliga besökare, inte unika personer. Annonsblockerare kan stoppa en del av mätningen, så siffrorna är något för låga.</p>
</div>
<script>
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tal = n => Number(n).toLocaleString('sv-SE');
const NAMN = { sidor:'Toppsidor', kallor:'Källor', kampanjer:'Kampanjer (UTM)', enheter:'Enheter', lander:'Länder' };
const del = (lista, test) => (lista || []).filter(p => test(p.nyckel));
const summa = (lista, test) => del(lista, test).reduce((a, p) => a + p.antal, 0);
const tabell = (rubrik, rader, kol = 'Visningar') => '<section><h2>' + esc(rubrik) + '</h2><table><thead><tr><th>Namn</th><th>' + esc(kol) + '</th><th>Besökare</th></tr></thead><tbody>'
  + (rader.length ? rader.slice(0, 15).map(p => '<tr><td>' + esc(p.nyckel) + '</td><td>' + tal(p.antal) + '</td><td>' + tal(p.unika) + '</td></tr>').join('') : '<tr><td class="tom" colspan="3">Inga data än</td></tr>')
  + '</tbody></table></section>';
function graf(trend) {
  const max = Math.max(1, ...trend.map(d => d.sidvisningar)), b = 1000 / trend.length;
  const staplar = trend.map((d, i) => { const h = Math.round(d.sidvisningar / max * 150);
    return '<rect x="' + (i * b + b * .12) + '" y="' + (160 - h) + '" width="' + (b * .76) + '" height="' + Math.max(h, 1) + '" rx="2" fill="#3d5143"><title>' + esc(d.dag) + ': ' + tal(d.sidvisningar) + ' visningar, ' + tal(d.besokare) + ' besökare</title></rect>'; }).join('');
  return '<svg viewBox="0 0 1000 180" preserveAspectRatio="none" role="img" aria-label="Sidvisningar per dag, högst ' + tal(max) + '"><line x1="0" y1="160.5" x2="1000" y2="160.5" stroke="#e7e7e7"/>' + staplar + '</svg>';
}
async function ladda(dagar) {
  document.querySelectorAll('[data-d]').forEach(k => k.setAttribute('aria-pressed', k.dataset.d == dagar));
  document.getElementById('exp').href = '/export.csv?dagar=' + dagar;
  const fel = document.getElementById('fel'); fel.innerHTML = '';
  try {
    const svar = await fetch('/api/rapport?dagar=' + dagar);
    if (!svar.ok) throw new Error(svar.status);
    const r = await svar.json(), d = r.dimensioner, h = d.handelser || [];
    const visn = r.trend.reduce((a, x) => a + x.sidvisningar, 0), bes = r.trend.reduce((a, x) => a + x.besokare, 0);
    const butik = summa(h, n => /^(karta|telefon|hitta-butik)/.test(n));
    const handlare = del(h, n => /^(nedladdning|epost · Prislista|ansokan|bestallning)/.test(n)).reduce((a, p) => a + p.antal, 0);
    document.getElementById('tal').innerHTML = [[visn,'Sidvisningar'],[bes,'Dagliga besökare, summerat'],[butik,'Klick mot butik'],[handlare,'Prislista och nedladdningar']]
      .map(([v, t]) => '<div><b>' + tal(v) + '</b><span>' + esc(t) + '</span></div>').join('');
    document.getElementById('graf').innerHTML = graf(r.trend);
    document.getElementById('tabeller').innerHTML = [
      tabell(NAMN.sidor, d.sidor || []), tabell(NAMN.kallor, d.kallor || []),
      tabell('Vald skalmodell', del(h, n => /^skalmodell( |$)/.test(n)), 'Val'),
      tabell('Butiksklick', del(h, n => /^(karta|telefon|hitta-butik)/.test(n)), 'Klick'),
      tabell('Saknade modeller', del(h, n => /^(skalmodell-saknas|modell-saknas)/.test(n)), 'Klick'),
      tabell('Återförsäljare', del(h, n => /^(nedladdning|epost|ansokan|bestallning|material)/.test(n)), 'Klick'),
      tabell('Övriga händelser', del(h, n => !/^(skalmodell|modell-saknas|karta|telefon|hitta-butik|nedladdning|epost|ansokan|bestallning|material)/.test(n)), 'Antal'),
      tabell(NAMN.kampanjer, d.kampanjer || []), tabell(NAMN.enheter, d.enheter || []), tabell(NAMN.lander, d.lander || []),
    ].join('');
  } catch (e) { fel.innerHTML = '<div class="fel" role="alert">Kunde inte hämta statistiken. Ladda om sidan, eller logga in igen.</div>'; }
}
const TYP = { ansokan:'Ansökan', bestallning:'Beställning' };
function arendeRad(a) {
  let rader = [];
  try { rader = JSON.parse(a.rader || '[]'); } catch {}
  const info = [a.ort, a.butikstyp, a.butiker && a.butiker + ' butiker', a.telefon].filter(Boolean).map(esc).join(' · ');
  return '<article class="ar-rad ' + (a.status === 'ny' ? 'ny' : '') + '"><div class="ar-topp"><b>' + esc(a.foretag) + '</b><span>' + esc(TYP[a.typ] || a.typ) + ' · ' + esc(a.skapad) + ' · ' + esc(a.status) + '</span></div>'
    + '<p>' + esc(a.kontakt) + ' · <a href="mailto:' + esc(a.epost) + '">' + esc(a.epost) + '</a>' + (info ? ' · ' + info : '') + '</p>'
    + (a.meddelande ? '<p>' + esc(a.meddelande) + '</p>' : '')
    + (rader.length ? '<ul>' + rader.map(r => '<li>' + esc(r.antal) + ' st ' + esc(r.artikel || '') + ' (' + esc(r.ean) + ')</li>').join('') + '</ul>' : '')
    + '<div class="ar-knappar"><button data-id="' + Number(a.id) + '" data-status="' + (a.status === 'ny' ? 'hanterad' : 'ny') + '">' + (a.status === 'ny' ? 'Markera hanterad' : 'Markera som ny') + '</button>'
    + '<button data-id="' + Number(a.id) + '" data-radera="1" aria-label="Radera ärende från ' + esc(a.foretag) + '">Radera</button></div></article>';
}
async function laddaArenden() {
  const yta = document.getElementById('arenden');
  try {
    const r = await fetch('/api/arenden');
    if (!r.ok) throw new Error(r.status);
    const lista = await r.json();
    yta.innerHTML = lista.length ? lista.map(arendeRad).join('') : '<p class="ar-tom">Inga ärenden än.</p>';
  } catch { yta.innerHTML = '<div class="fel" role="alert">Kunde inte hämta ärendena.</div>'; }
}
document.getElementById('arenden').addEventListener('click', async e => {
  const k = e.target.closest('button[data-id]');
  if (!k) return;
  if (k.dataset.radera && !confirm('Radera ärendet? Det går inte att ångra.')) return;
  const r = await fetch('/api/arenden/' + k.dataset.id, { method: k.dataset.radera ? 'DELETE' : 'POST', headers: { 'Content-Type': 'application/json' }, body: k.dataset.radera ? undefined : JSON.stringify({ status: k.dataset.status }) });
  if (!r.ok) alert('Det gick inte att ändra ärendet.');
  laddaArenden();
});
document.querySelectorAll('[data-d]').forEach(k => k.addEventListener('click', () => ladda(+k.dataset.d)));
ladda(30);
laddaArenden();
</script></body></html>`;
