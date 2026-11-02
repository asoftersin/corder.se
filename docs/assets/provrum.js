// Provrummet: välj iPhone, prova färgerna i helskärm, gå vidare till inköpslappen.
// Skärmstorleken läses bara här i webbläsaren och skickas aldrig: se /pages/integritet/.
(() => {
  const modeller = JSON.parse(document.getElementById('modeller')?.textContent || '[]');
  if (!modeller.length || !window.HTMLDialogElement) return;

  const PRIS = { kabel: 60, laddare: 99 };
  // Mörk bakgrund som låter skalet lysa. Svart skal behöver ljus bakgrund för att synas.
  const FLOD = {
    Skogsgrön: { bg: '#141d17', fg: '#fff', namn: '#2b3a30' },
    Svart: { bg: '#e4e2dc', fg: '#111', namn: '#d3d0c8' },
    Blå: { bg: '#14263a', fg: '#fff', namn: '#26415c' },
    Lila: { bg: '#25265f', fg: '#fff', namn: '#393b86' },
    Persika: { bg: '#6b2a1c', fg: '#fff', namn: '#8a3c2a' },
  };
  // iPhone uppger inte modell, men skärmens mått i punkter ringar in den. Display Zoom kan ge fel, så vi säger aldrig säkert.
  const SKARMAR = {
    '402x874': ['iphone-18-pro', 'iphone-17-pro', 'iphone-17', 'iphone-16-pro'],
    '393x852': ['iphone-16', 'iphone-15-pro', 'iphone-15', 'iphone-14-pro'],
    '390x844': ['iphone-16e', 'iphone-14'],
  };
  const UTAN_SKAL = {
    '430x932': 'Plus och Pro Max',
    '428x926': 'Plus och Pro Max',
    '440x956': 'Pro Max',
    '420x912': 'iPhone Air',
  };
  const skarm = () => (/iPhone/.test(navigator.userAgent) ? `${Math.min(screen.width, screen.height)}x${Math.max(screen.width, screen.height)}` : '');
  const kort = namn => namn.replace('iPhone ', '');
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nyckel = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  const stor = bild => bild.replace('/cut/s/', '/cut/');
  const lugn = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  const d = document.createElement('dialog');
  d.className = 'pr';
  d.id = 'provrum';
  d.setAttribute('aria-label', 'Provrummet');
  d.innerHTML = `
    <div class="pr-flod" aria-hidden="true"></div>
    <a class="logo pr-logo" href="/" aria-label="Corder startsida">corder</a>
    <button class="pr-stang" type="button" aria-label="Stäng provrummet"><span aria-hidden="true"></span></button>
    <div class="pr-sida pr-val"></div>
    <div class="pr-sida pr-prov" hidden>
      <div class="pr-scen">
        <span class="pr-namn" aria-hidden="true"></span>
        <img class="pr-skal" alt="" width="511" height="1020" decoding="async" draggable="false">
      </div>
      <div class="pr-panel">
        <button class="pr-byt" type="button"></button>
        <h2 class="pr-rubrik" aria-live="polite"></h2>
        <div class="pr-sw" role="group" aria-label="Välj färg"></div>
        <div class="pr-till" role="group" aria-label="Lägg till på lappen">
          <button type="button" data-till="kabel" aria-pressed="false"></button>
          <button type="button" data-till="laddare" aria-pressed="false"></button>
        </div>
        <a class="pr-cta" data-h="inkopslapp" data-v="provrum"></a>
        <p class="pr-not">Rek. pris. Finns i Jönköping och Mullsjö. Bor du någon annanstans? Visa lappen i din mobilbutik, där står hur de beställer.</p>
      </div>
    </div>`;
  document.body.append(d);

  const [val, prov, scen, namn, skal, byt, rubrik, sw, cta, flod] = ['.pr-val', '.pr-prov', '.pr-scen', '.pr-namn', '.pr-skal', '.pr-byt', '.pr-rubrik', '.pr-sw', '.pr-cta', '.pr-flod'].map(q => d.querySelector(q));
  const tillagg = [...d.querySelectorAll('[data-till]')];
  const lage = { modell: null, farg: null, onskad: null, filter: null, kabel: false, laddare: false };
  let egenPost = false;

  // Färgen sveper in som en cirkel från där du tryckte.
  const svep = (farg, x = innerWidth / 2, y = innerHeight / 2) => {
    const f = FLOD[farg] || FLOD.Skogsgrön;
    // --bg styr knappar och ringar direkt, --yta byts när svepet täcker skärmen.
    d.style.setProperty('--bg', f.bg);
    d.style.setProperty('--fg', f.fg);
    d.style.setProperty('--pr-namn', f.namn);
    if (lugn()) { d.style.setProperty('--yta', f.bg); return; }
    const vag = document.createElement('div');
    vag.style.cssText = `position:absolute;inset:0;background:${f.bg}`;
    flod.append(vag);
    const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    vag.animate({ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] }, { duration: 620, easing: 'cubic-bezier(.65,0,.15,1)' }).onfinish = () => {
      d.style.setProperty('--yta', f.bg);
      vag.remove();
    };
  };

  const visaSkal = (riktning = 1) => {
    skal.src = stor(lage.farg.bild);
    skal.alt = `Corder TPU-skal till ${lage.modell.namn} i ${lage.farg.namn.toLowerCase()}`;
    if (lugn()) return;
    skal.animate([
      { opacity: 0, transform: `translate3d(${46 * riktning}px, 18px, 0) rotate(${5 * riktning}deg) scale(.94)` },
      { opacity: 1, transform: 'none' },
    ], { duration: 620, easing: 'cubic-bezier(.16,1,.3,1)' });
    namn.animate([{ opacity: 0, transform: `translateX(${-30 * riktning}px)` }, { opacity: 1, transform: 'none' }], { duration: 700, easing: 'cubic-bezier(.16,1,.3,1)' });
  };

  const uppdatera = () => {
    const summa = lage.modell.pris + (lage.kabel ? PRIS.kabel : 0) + (lage.laddare ? PRIS.laddare : 0);
    const delar = [`m=${lage.modell.slug}`, `f=${nyckel(lage.farg.namn)}`];
    if (lage.kabel) delar.push('k=1');
    if (lage.laddare) delar.push('l=1');
    cta.href = `/inkopslapp/?${delar.join('&')}`;
    cta.innerHTML = `<span>Skapa inköpslapp</span><b>${summa} kr</b>`;
    tillagg.forEach(b => b.setAttribute('aria-pressed', lage[b.dataset.till]));
    history.replaceState({ ...history.state, pr: { m: lage.modell.slug, f: lage.farg.namn, k: lage.kabel, l: lage.laddare } }, '');
  };

  const valjFarg = (f, x, y, riktning) => {
    if (f === lage.farg) return;
    lage.farg = f;
    lage.onskad = f.namn;
    namn.textContent = f.namn;
    namn.style.setProperty('--n', f.namn.length);
    rubrik.textContent = `${f.namn} till ${lage.modell.namn}`;
    sw.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', b.dataset.farg === f.namn));
    svep(f.namn, x, y);
    visaSkal(riktning);
    uppdatera();
  };
  const stega = (steg, x, y) => {
    const f = lage.modell.farger;
    valjFarg(f[(f.indexOf(lage.farg) + steg + f.length) % f.length], x, y, steg);
    window.corderH?.('provrum-farg', lage.farg.namn);
  };

  const visaProv = (m, x, y) => {
    lage.modell = m;
    lage.farg = null;
    m.farger.forEach(f => { new Image().src = stor(f.bild); });
    const startfarg = m.farger.find(f => f.namn === lage.onskad) || m.farger.find(f => f.namn === 'Skogsgrön') || m.farger.find(f => f.namn === 'Lila') || m.farger[0];
    byt.innerHTML = `<span>${esc(m.namn)}</span><u>Byt modell</u>`;
    sw.innerHTML = m.farger.map(f => `<button type="button" style="--c:${f.hex}" data-farg="${esc(f.namn)}" aria-label="${esc(f.namn)}" aria-pressed="false"></button>`).join('');
    tillagg[0].innerHTML = `<i aria-hidden="true"></i><span>Kabel till ${esc(m.kontakt)}</span><em>${PRIS.kabel} kr</em>`;
    tillagg[1].innerHTML = `<i aria-hidden="true"></i><span>Laddare</span><em>${PRIS.laddare} kr</em>`;
    val.hidden = true;
    prov.hidden = false;
    valjFarg(startfarg, x, y, 1);
    cta.focus({ preventScroll: true });
  };

  const rad = m => `<button class="pr-rad" type="button" data-slug="${m.slug}"><span>${esc(kort(m.namn))}</span><span class="pr-prickar" aria-hidden="true">${m.farger.map(f => `<i style="--c:${f.hex}"></i>`).join('')}</span></button>`;
  const visaVal = () => {
    const kod = skarm();
    const passar = lage.filter ? modeller.filter(m => m.farger.some(f => f.namn === lage.filter)) : modeller;
    const troliga = passar.filter(m => SKARMAR[kod]?.includes(m.slug));
    const ovriga = passar.filter(m => !troliga.includes(m));
    const ledtrad = UTAN_SKAL[kod]
      ? `<p class="pr-ledtrad">Din skärm ser ut som en ${UTAN_SKAL[kod]}. Dit har vi tyvärr inga skal, men <a href="/kablar/">kablarna</a> och <a href="/laddare/">laddarna</a> passar.</p>`
      : '';
    val.innerHTML = `<div class="pr-val-head">
        <span class="caps">Provrummet</span>
        <h2>${lage.filter ? `${esc(lage.filter)} till<br>vilken iPhone?` : 'Vilken iPhone<br>har du?'}</h2>
        ${ledtrad}
        <p class="pr-hjalp">Har du en annan modell? Skal finns från iPhone 14, men inte till Plus, Pro Max eller Air. <a href="/blogs/nyheter/vilken-iphone-har-jag/">Så hittar du din modell</a>.</p>
      </div>
      <div class="pr-listor">
        ${troliga.length ? `<span class="caps">Stämmer med din skärm</span><div class="pr-lista trolig">${troliga.map(rad).join('')}</div><span class="caps">Övriga modeller</span>` : ''}
        <div class="pr-lista">${ovriga.map(rad).join('')}</div>
      </div>`;
    prov.hidden = true;
    val.hidden = false;
    val.scrollTop = 0;
    if (!lugn()) val.querySelectorAll('.pr-rad').forEach((b, i) => b.animate([{ opacity: 0, transform: 'translateY(18px)' }, { opacity: 1, transform: 'none' }], { duration: 560, delay: 60 + i * 28, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' }));
    val.querySelector('.pr-rad')?.focus({ preventScroll: true });
  };

  const oppna = ({ slug, farg, x, y } = {}) => {
    if (d.open) return;
    lage.onskad = lage.filter = farg || null;
    const start = FLOD[farg] || FLOD.Skogsgrön;
    d.style.setProperty('--bg', start.bg);
    d.style.setProperty('--yta', start.bg);
    d.style.setProperty('--fg', start.fg);
    d.style.setProperty('--pr-namn', start.namn);
    d.showModal();
    document.documentElement.classList.add('pr-oppen');
    if (location.hash !== '#provrum') { history.pushState(history.state, '', '#provrum'); egenPost = true; }
    const m = modeller.find(a => a.slug === slug);
    if (m) visaProv(m, x, y); else visaVal();
    if (!lugn() && x !== undefined) {
      const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
      d.animate({ clipPath: [`circle(24px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] }, { duration: 720, easing: 'cubic-bezier(.65,0,.15,1)' });
    }
  };
  const stang = () => {
    d.close();
    document.documentElement.classList.remove('pr-oppen');
  };
  const begarStang = () => {
    if (egenPost) { egenPost = false; history.back(); return; }
    // Kom man direkt till #provrum finns inget på den här sajten att backa till.
    history.replaceState(null, '', location.pathname + location.search);
    stang();
  };

  // Länkarna fungerar som vanliga ankare utan JavaScript.
  document.addEventListener('click', e => {
    const a = e.target.closest?.('[data-provrum]');
    if (!a) return;
    e.preventDefault();
    oppna({ slug: a.dataset.slug, farg: a.dataset.farg, x: e.clientX, y: e.clientY });
  });
  d.addEventListener('cancel', e => { e.preventDefault(); begarStang(); });
  d.querySelector('.pr-stang').addEventListener('click', begarStang);
  addEventListener('popstate', () => { if (d.open && location.hash !== '#provrum') { egenPost = false; stang(); } });

  val.addEventListener('click', e => {
    const b = e.target.closest('.pr-rad');
    if (!b) return;
    window.corderH?.('skalmodell', b.dataset.slug);
    visaProv(modeller.find(m => m.slug === b.dataset.slug), e.clientX, e.clientY);
  });
  byt.addEventListener('click', () => { lage.filter = null; visaVal(); });
  sw.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    const f = lage.modell.farger;
    const ny = f.find(x => x.namn === b.dataset.farg);
    if (ny === lage.farg) return;
    const r = b.getBoundingClientRect();
    valjFarg(ny, r.left + r.width / 2, r.top + r.height / 2, f.indexOf(ny) > f.indexOf(lage.farg) ? 1 : -1);
    window.corderH?.('provrum-farg', ny.namn);
  });
  tillagg.forEach(b => b.addEventListener('click', () => {
    lage[b.dataset.till] = !lage[b.dataset.till];
    uppdatera();
    window.corderH?.('provrum-tillagg', b.dataset.till);
  }));
  d.addEventListener('keydown', e => {
    if (prov.hidden || !['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
    stega(e.key === 'ArrowRight' ? 1 : -1);
  });

  // Svep på skalet byter färg. Med mus lutar skalet efter pekaren.
  let drag = null;
  scen.addEventListener('pointerdown', e => { drag = e.clientX; });
  addEventListener('pointerup', e => {
    if (drag === null || !d.open || prov.hidden) { drag = null; return; }
    const dx = e.clientX - drag;
    drag = null;
    if (Math.abs(dx) > 40) stega(dx < 0 ? 1 : -1, e.clientX, e.clientY);
  });
  if (matchMedia('(hover: hover)').matches && !lugn()) {
    scen.addEventListener('pointermove', e => {
      const r = scen.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - .5;
      const y = (e.clientY - r.top) / r.height - .5;
      skal.style.setProperty('--ry', `${x * 16}deg`);
      skal.style.setProperty('--rx', `${y * -10}deg`);
    });
    scen.addEventListener('pointerleave', () => { skal.style.setProperty('--ry', '0deg'); skal.style.setProperty('--rx', '0deg'); });
  }

  // Har telefonen en känd skärm kommer modellerna direkt i heron: ett tryck, sen är du inne.
  const din = document.querySelector('.hero-din');
  const troliga = modeller.filter(m => SKARMAR[skarm()]?.includes(m.slug));
  if (din && troliga.length) {
    din.querySelector('.hero-din-val').innerHTML = troliga.map(m => `<a href="#hitta-skal" data-provrum data-slug="${m.slug}" data-h="provrum" data-v="hero-skarm">${esc(kort(m.namn))}</a>`).join('');
    din.hidden = false;
  }

  // Tillbaka från inköpslappen, eller en delad länk.
  if (location.hash === '#provrum') {
    const s = history.state?.pr;
    Object.assign(lage, s ? { kabel: s.k, laddare: s.l } : {});
    oppna({ slug: s?.m, farg: s?.f });
    if (s) uppdatera();
  }
})();
