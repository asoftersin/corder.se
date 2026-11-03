// Sverigekartan: hur långt är det till Corder? Ort och plats stannar i webbläsaren, bara en önskan skickas: se /pages/integritet/.
(() => {
  const sektion = document.getElementById('butiker');
  const duk = sektion?.querySelector('.ks-duk');
  if (!duk?.getContext) return;
  const ctx = duk.getContext('2d');
  const sok = sektion.querySelector('.ks-sok');
  const falt = sok.querySelector('input');
  const lista = sok.querySelector('.ks-lista');
  const svar = sektion.querySelector('.ks-svar');
  const platsKnapp = sok.querySelector('.ks-plats');
  const butiker = [...sektion.querySelectorAll('.store[data-lat]')].map(el => ({
    namn: el.querySelector('h3').textContent, ort: el.querySelector('.caps').textContent,
    lat: +el.dataset.lat, lon: +el.dataset.lon, karta: el.querySelector('a').href,
  }));
  if (!butiker.length) return;
  // Utan JavaScript syns bara butikskorten.
  sok.hidden = false;
  duk.parentElement.hidden = false;

  // Grova konturer räcker: kartan ritas som ett punktraster. [lat, lon]
  const SVERIGE = [[55.34,13.36],[55.43,13.85],[55.55,14.38],[55.92,14.33],[56.03,14.75],[56.13,14.86],[56.1,15.6],[56.4,16.05],[56.66,16.42],[57.3,16.55],[57.76,16.75],[58.2,16.85],[58.48,17.0],[58.75,17.15],[58.9,17.75],[59.2,18.5],[59.5,18.95],[59.78,19.05],[60.2,18.75],[60.42,18.4],[60.62,17.4],[61.0,17.25],[61.73,17.3],[62.39,17.55],[62.63,18.1],[63.2,18.85],[63.55,19.8],[63.7,20.6],[64.2,21.1],[64.75,21.35],[65.3,21.7],[65.58,22.45],[65.75,23.4],[65.82,24.15],[66.3,23.75],[66.8,23.85],[67.2,23.55],[67.9,23.55],[68.2,23.1],[68.45,22.3],[68.7,21.4],[69.06,20.55],[68.5,20.0],[68.42,18.95],[68.45,18.1],[68.1,18.05],[67.5,16.6],[67.0,15.95],[66.5,15.4],[66.1,14.55],[65.6,14.5],[65.1,14.25],[64.5,13.75],[64.05,12.7],[63.6,12.2],[63.0,12.1],[62.3,12.15],[61.6,12.75],[61.05,12.5],[60.5,12.55],[60.0,12.35],[59.5,11.8],[59.05,11.4],[58.9,11.15],[58.35,11.25],[57.7,11.75],[57.1,12.15],[56.67,12.72],[56.45,12.75],[56.27,12.45],[56.05,12.6],[55.65,12.88],[55.38,12.95]];
  const OAR = [
    [[57.0,18.1],[57.45,18.1],[57.95,18.75],[57.95,19.3],[57.5,18.95],[57.0,18.45]],
    [[56.2,16.35],[56.75,16.55],[57.38,17.0],[57.38,17.25],[56.75,16.95],[56.2,16.6]],
  ];
  const SJOAR = [
    [[58.4,12.45],[58.75,12.45],[59.35,12.75],[59.4,13.5],[58.95,13.95],[58.6,13.5]],
    [[57.8,14.08],[58.5,14.45],[58.92,14.65],[58.8,14.98],[58.2,14.68]],
  ];
  const ORTER = 'Stockholm,59.33,18.07;Göteborg,57.71,11.97;Malmö,55.6,13;Uppsala,59.86,17.64;Linköping,58.41,15.62;Örebro,59.27,15.21;Västerås,59.61,16.55;Helsingborg,56.05,12.69;Norrköping,58.59,16.19;Jönköping,57.78,14.16;Umeå,63.83,20.26;Lund,55.7,13.19;Borås,57.72,12.94;Huddinge,59.24,17.98;Eskilstuna,59.37,16.51;Gävle,60.67,17.14;Södertälje,59.2,17.63;Karlstad,59.38,13.5;Täby,59.44,18.07;Växjö,56.88,14.81;Halmstad,56.67,12.86;Sundsvall,62.39,17.31;Luleå,65.58,22.15;Trollhättan,58.28,12.29;Östersund,63.18,14.64;Borlänge,60.49,15.44;Falun,60.61,15.63;Kalmar,56.66,16.36;Skövde,58.39,13.85;Kristianstad,56.03,14.16;Karlskrona,56.16,15.59;Skellefteå,64.75,20.95;Uddevalla,58.35,11.94;Lidköping,58.5,13.16;Varberg,57.11,12.25;Landskrona,55.87,12.83;Nyköping,58.75,17.01;Örnsköldsvik,63.29,18.72;Trelleborg,55.38,13.16;Karlskoga,59.33,14.52;Visby,57.64,18.3;Piteå,65.32,21.48;Enköping,59.64,17.08;Kungsbacka,57.49,12.08;Ängelholm,56.24,12.86;Västervik,57.76,16.64;Motala,58.54,15.04;Alingsås,57.93,12.53;Sandviken,60.62,16.77;Hudiksvall,61.73,17.1;Katrineholm,58.99,16.21;Kiruna,67.86,20.23;Gällivare,67.13,20.66;Kalix,65.85,23.14;Haparanda,65.83,24.14;Boden,65.83,21.69;Lycksele,64.6,18.67;Vilhelmina,64.62,16.65;Storuman,65.1,17.11;Sollefteå,63.17,17.27;Härnösand,62.63,17.94;Timrå,62.49,17.33;Bollnäs,61.35,16.39;Söderhamn,61.3,17.06;Ljusdal,61.83,16.09;Mora,61,14.54;Ludvika,60.15,15.19;Avesta,60.14,16.17;Hedemora,60.28,15.99;Sälen,61.16,13.27;Arvika,59.65,12.59;Kristinehamn,59.31,14.11;Filipstad,59.71,14.17;Säffle,59.13,12.93;Åmål,59.05,12.7;Lindesberg,59.59,15.22;Köping,59.51,15.99;Arboga,59.39,15.84;Sala,59.92,16.6;Norrtälje,59.76,18.7;Nacka,59.31,18.16;Solna,59.36,18;Sollentuna,59.43,17.95;Järfälla,59.41,17.83;Tumba,59.2,17.83;Märsta,59.62,17.85;Strängnäs,59.38,17.03;Flen,59.06,16.59;Oxelösund,58.67,17.1;Finspång,58.71,15.77;Mjölby,58.33,15.13;Vadstena,58.45,14.89;Tranås,58.04,14.98;Eksjö,57.67,14.97;Nässjö,57.65,14.7;Vetlanda,57.43,15.08;Vimmerby,57.67,15.86;Värnamo,57.19,14.04;Gislaved,57.3,13.54;Gnosjö,57.36,13.74;Vaggeryd,57.5,14.15;Habo,57.91,14.07;Huskvarna,57.79,14.3;Mullsjö,57.92,13.88;Bankeryd,57.86,14.13;Tidaholm,58.18,13.96;Falköping,58.17,13.55;Hjo,58.3,14.29;Skara,58.39,13.44;Mariestad,58.71,13.82;Vara,58.26,12.96;Ulricehamn,57.79,13.41;Tranemo,57.48,13.35;Svenljunga,57.5,13.11;Kungälv,57.87,11.98;Mölndal,57.66,12.01;Partille,57.74,12.11;Stenungsund,58.07,11.82;Lysekil,58.27,11.44;Strömstad,58.94,11.17;Vänersborg,58.38,12.32;Falkenberg,56.9,12.49;Laholm,56.51,13.04;Ljungby,56.83,13.94;Alvesta,56.9,14.55;Älmhult,56.55,14.14;Oskarshamn,57.26,16.45;Nybro,56.74,15.91;Ronneby,56.21,15.28;Karlshamn,56.17,14.86;Sölvesborg,56.05,14.58;Hässleholm,56.16,13.77;Höganäs,56.2,12.55;Eslöv,55.84,13.3;Ystad,55.43,13.82;Simrishamn,55.56,14.36;Vellinge,55.47,13.02;Kävlinge,55.79,13.11;Höör,55.94,13.54;Åre,63.4,13.08;Sveg,62.03,14.36;Kramfors,62.93,17.78;Vännäs,63.91,19.75;Arvidsjaur,65.59,19.18;Arjeplog,66.05,17.89;Jokkmokk,66.61,19.82;Pajala,67.21,23.37;Älvsbyn,65.68,21;Tierp,60.35,17.51;Östhammar,60.26,18.37;Nora,59.52,15.04;Kumla,59.13,15.14;Askersund,58.88,14.9;Hallsberg,59.07,15.11;Olofström,56.28,14.53'
    .split(';').map(s => { const [namn, lat, lon] = s.split(','); return { namn, lat: +lat, lon: +lon }; });

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nyckel = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim();
  const lugn = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const RAD = Math.PI / 180;
  const avstand = (a, b) => {
    const h = Math.sin((b.lat - a.lat) * RAD / 2) ** 2 + Math.cos(a.lat * RAD) * Math.cos(b.lat * RAD) * Math.sin((b.lon - a.lon) * RAD / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(h));
  };
  const narmast = (punkt, av) => av.map(x => ({ x, km: avstand(punkt, x) })).sort((a, b) => a.km - b.km)[0];

  // Projektion med Sverige rakt upp i mitten av kartan.
  const proj = (lat, lon) => ({ x: (lon - 15) * Math.cos(lat * RAD), y: -lat });
  const inuti = (lat, lon, poly) => {
    let in_ = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [ai, oi] = poly[i], [aj, oj] = poly[j];
      if ((ai > lat) !== (aj > lat) && lon < (oj - oi) * (lat - ai) / (aj - ai) + oi) in_ = !in_;
    }
    return in_;
  };
  const punkter = [...SVERIGE, ...OAR.flat()].map(([a, o]) => proj(a, o));
  const yta = { x0: Math.min(...punkter.map(p => p.x)), x1: Math.max(...punkter.map(p => p.x)), y0: Math.min(...punkter.map(p => p.y)), y1: Math.max(...punkter.map(p => p.y)) };
  const mitt = { x: (yta.x0 + yta.x1) / 2, y: (yta.y0 + yta.y1) / 2 };
  const butiksPunkter = butiker.map(b => ({ ...b, ...proj(b.lat, b.lon) }));
  const STEG = .145;
  const prickar = [];
  let rad = 0;
  for (let y = yta.y0; y <= yta.y1; y += STEG * .866, rad++) {
    for (let x = yta.x0 - STEG + (rad % 2) * STEG / 2; x <= yta.x1 + STEG; x += STEG) {
      const lat = -y, lon = x / Math.cos(lat * RAD) + 15;
      const pa = inuti(lat, lon, SVERIGE) && !SJOAR.some(s => inuti(lat, lon, s)) || OAR.some(o => inuti(lat, lon, o));
      if (!pa) continue;
      prickar.push({ x, y, hem: Math.min(...butiksPunkter.map(b => Math.hypot(b.x - x, b.y - y))) });
    }
  }

  // Kameran och det som rör sig på kartan.
  const FARG = { grund: 'rgba(255,255,255,.2)', nara: ['rgba(143,190,160,.5)', 'rgba(164,214,182,.75)', '#c8ecd5'], vag: ['rgba(245,164,147,.45)', 'rgba(245,164,147,.75)', '#ffc4b5'], gron: ['rgba(143,190,160,.35)', 'rgba(164,214,182,.6)', '#c8ecd5'] };
  const PERSIKA = '#f5a493';
  let W = 0, H = 0, bas = 1, dpr = 1;
  const kamera = { x: mitt.x, y: mitt.y, s: 1 };
  const mal = { x: mitt.x, y: mitt.y, s: 1 };
  const vagor = [];
  let start = null, du = null, bageStart = 0, senast = 0, senasteVag = 0, syns = false, ram = null;
  const onskade = [];

  const passa = () => {
    const r = duk.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    duk.width = Math.round(W * dpr); duk.height = Math.round(H * dpr);
    const pad = Math.min(W, H) * .05;
    bas = Math.min((W - pad * 2) / (yta.x1 - yta.x0), (H - pad * 2) / (yta.y1 - yta.y0));
    if (du) sikta();
  };
  const sikta = () => {
    const b = du.butik, u = du;
    const bredd = Math.abs(b.x - u.x), hojd = Math.abs(b.y - u.y);
    const zoom = Math.min((W * .62) / Math.max(bredd * bas, 1), (H * .62) / Math.max(hojd * bas, 1));
    mal.s = Math.max(1, Math.min(2.6, zoom));
    mal.x = (b.x + u.x) / 2;
    mal.y = (b.y + u.y) / 2;
    if (mal.s === 1) { mal.x = mitt.x; mal.y = mitt.y; }
  };
  const skarm = p => ({ x: W / 2 + (p.x - kamera.x) * kamera.s * bas, y: H / 2 + (p.y - kamera.y) * kamera.s * bas });
  const kurva = (a, b) => {
    const dx = b.x - a.x, dy = b.y - a.y;
    return { x: (a.x + b.x) / 2 - dy * .22, y: (a.y + b.y) / 2 + dx * .22 };
  };
  const etikett = (text, x, y, sida, farg = '#fff') => {
    ctx.font = '500 13px "Inter Tight", system-ui, sans-serif';
    // Får texten inte plats på sin sida byter den sida.
    const bredd = ctx.measureText(text).width + 12;
    if (sida < 0 && x - bredd < W * .08) sida = 1;
    else if (sida > 0 && x + bredd > W * .92) sida = -1;
    ctx.textAlign = sida < 0 ? 'right' : 'left';
    ctx.textBaseline = 'middle';
    ctx.lineWidth = 4;
    ctx.strokeStyle = 'rgba(16,24,20,.9)';
    ctx.strokeText(text, x + sida * 12, y);
    ctx.fillStyle = farg;
    ctx.fillText(text, x + sida * 12, y);
  };

  const rita = nu => {
    const dt = Math.min(64, nu - senast);
    senast = nu;
    const stilla = lugn();
    const k = stilla ? 1 : 1 - Math.exp(-dt / 240);
    kamera.x += (mal.x - kamera.x) * k; kamera.y += (mal.y - kamera.y) * k; kamera.s += (mal.s - kamera.s) * k;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    // Prickarna tänds utifrån butikerna första gången kartan syns.
    const spridd = stilla || start === null ? (stilla ? Infinity : -1) : (nu - start) / 1000 * 8;
    if (!stilla && nu - senasteVag > 5600 && spridd > 16 && !du) { vagor.push({ x: butiksPunkter[0].x, y: butiksPunkter[0].y, t: nu, slag: 'gron', fart: 5, kraft: .7 }); senasteVag = nu; }
    for (let i = vagor.length - 1; i >= 0; i--) if ((nu - vagor[i].t) / 1000 * vagor[i].fart > 18) vagor.splice(i, 1);

    const skala = kamera.s * bas;
    const hinkar = { grund: [], nara0: [], nara1: [], nara2: [], vag0: [], vag1: [], vag2: [], gron0: [], gron1: [], gron2: [] };
    for (const p of prickar) {
      const sx = W / 2 + (p.x - kamera.x) * skala, sy = H / 2 + (p.y - kamera.y) * skala;
      if (sx < -4 || sy < -4 || sx > W + 4 || sy > H + 4 || p.hem > spridd) continue;
      let hink = 'grund';
      if (p.hem < 1.05) hink = `nara${p.hem < .3 ? 2 : p.hem < .65 ? 1 : 0}`;
      for (const v of vagor) {
        const r = (nu - v.t) / 1000 * v.fart;
        const d = Math.abs(Math.hypot(p.x - v.x, p.y - v.y) - r);
        const styrka = Math.max(0, 1 - d / 1.1) * Math.max(0, 1 - r / 18) * v.kraft;
        if (styrka > .12) hink = `${v.slag}${styrka > .6 ? 2 : styrka > .32 ? 1 : 0}`;
      }
      hinkar[hink].push(sx, sy);
    }
    const prick = Math.max(.9, Math.min(STEG * skala * .3, 3.8));
    const fyll = (lista_, farg) => {
      if (!lista_.length) return;
      ctx.fillStyle = farg;
      ctx.beginPath();
      for (let i = 0; i < lista_.length; i += 2) { ctx.moveTo(lista_[i] + prick, lista_[i + 1]); ctx.arc(lista_[i], lista_[i + 1], prick, 0, 6.2832); }
      ctx.fill();
    };
    fyll(hinkar.grund, FARG.grund);
    for (const slag of ['nara', 'gron', 'vag']) FARG[slag].forEach((f, i) => fyll(hinkar[`${slag}${i}`], f));

    // Linjen från din ort till närmaste butik.
    if (du && du.km >= 8) {
      const a = skarm(du), b = skarm(du.butik), c = skarm(kurva(du, du.butik));
      const q = stilla ? 1 : Math.min(1, (nu - bageStart) / 1100);
      const e = 1 - (1 - q) ** 3;
      const ute = t => ({ x: (1 - t) ** 2 * a.x + 2 * (1 - t) * t * c.x + t * t * b.x, y: (1 - t) ** 2 * a.y + 2 * (1 - t) * t * c.y + t * t * b.y });
      ctx.strokeStyle = PERSIKA;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      for (let t = .04; t <= e + .001; t += .04) { const p = ute(Math.min(t, e)); ctx.lineTo(p.x, p.y); }
      ctx.stroke();
      // Korta sträckor får ingen bricka: den skulle täcka hela linjen.
      if (q >= 1 && Math.hypot(a.x - b.x, a.y - b.y) > 120) {
        const m = ute(.5);
        ctx.font = '600 12px "Inter Tight", system-ui, sans-serif';
        const text = du.kmText;
        const b_ = ctx.measureText(text).width + 18;
        ctx.fillStyle = PERSIKA;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(m.x - b_ / 2, m.y - 12, b_, 24, 12); else ctx.rect(m.x - b_ / 2, m.y - 12, b_, 24);
        ctx.fill();
        ctx.fillStyle = '#2a120c'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(text, m.x, m.y + .5);
      }
    }

    // Butikerna pulserar. Ligger de tätt delar de etikett.
    const fas = stilla ? .5 : (nu % 2400) / 2400;
    const skarmar = butiksPunkter.map(skarm);
    const sida = du && du.km >= 8 && skarm(du).x > skarm(du.butik).x ? -1 : 1;
    const klar = new Set();
    skarmar.forEach((s, i) => {
      ctx.strokeStyle = `rgba(255,255,255,${.7 * (1 - fas)})`;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(s.x, s.y, 5 + fas * 17, 0, 6.2832); ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(s.x, s.y, 4.2, 0, 6.2832); ctx.fill();
      if (klar.has(i)) return;
      const grupp = skarmar.map((o, j) => j).filter(j => !klar.has(j) && Math.hypot(skarmar[j].x - s.x, skarmar[j].y - s.y) < 74);
      grupp.forEach(j => klar.add(j));
      etikett(grupp.map(j => butiksPunkter[j].ort).join(', '), s.x, s.y, sida);
    });

    for (const o of onskade) {
      if (o === du) continue;
      const s = skarm(o);
      ctx.fillStyle = PERSIKA;
      ctx.beginPath(); ctx.arc(s.x, s.y, 3, 0, 6.2832); ctx.fill();
    }
    if (du && du.km >= 8) {
      const s = skarm(du);
      ctx.fillStyle = PERSIKA;
      ctx.beginPath(); ctx.arc(s.x, s.y, 5, 0, 6.2832); ctx.fill();
      ctx.strokeStyle = PERSIKA; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(s.x, s.y, 9, 0, 6.2832); ctx.stroke();
      etikett(du.namn, s.x, s.y, -sida, '#ffd9cf');
    }
  };

  const loop = nu => {
    ram = null;
    if (!syns) return;
    rita(nu);
    if (!lugn()) ram = requestAnimationFrame(loop);
  };
  const vack = () => {
    if (lugn()) rita(performance.now());
    else if (syns && ram === null) { senast = performance.now(); ram = requestAnimationFrame(loop); }
  };
  new ResizeObserver(() => { passa(); vack(); }).observe(duk);
  new IntersectionObserver(([e]) => {
    syns = e.isIntersecting;
    if (syns && start === null) { start = performance.now(); senasteVag = start; }
    vack();
  }, { threshold: .08 }).observe(duk);
  document.fonts?.ready.then(vack);

  // Svaret: det som är nära blir en lapp, det som är långt bort blir en önskan.
  const kmText = km => `${km < 100 ? Math.max(1, Math.round(km)) : Math.round(km / 10) * 10} km`;
  const tipsText = ort => `Hej! Har ni tänkt på att ta in Corder? Svenska skal, kablar och laddare till iPhone. Jag letar efter dem i ${ort}. Allt för butiker finns på https://corder.se/aterforsaljare/`;
  const tipsLank = ort => `mailto:?subject=${encodeURIComponent('Har ni tänkt på att ta in Corder?')}&body=${encodeURIComponent(tipsText(ort))}`;
  const onskaKnapp = (ort, kort) => (window.corderH
    ? `<button class="${kort ? 'ks-lank' : 'ks-cta'}" type="button" data-onska>Önska Corder i ${esc(ort)}</button>`
    : `<a class="${kort ? 'ks-lank' : 'ks-cta'}" href="mailto:sales@corder.se?subject=${encodeURIComponent(`Önskar Corder i ${ort}`)}">Önska Corder i ${esc(ort)}</a>`);
  const tipsaKnapp = ort => `<a class="ks-cta ghost" href="${esc(tipsLank(ort))}" data-tipsa data-h="tipsa-butik">Tipsa din mobilbutik</a>`;
  const lappLank = 'href="/inkopslapp/" data-h="inkopslapp" data-v="karta"';

  const visaSvar = (ort, km, b) => {
    const karta = `<a href="${esc(b.karta)}" rel="noopener" target="_blank" data-h="karta" data-v="${esc(b.namn)}"`;
    let html_;
    if (km < 8) {
      html_ = `<b class="ks-km">Här finns vi.</b>
        <p>${esc(b.namn)} säljer Corder i ${esc(b.ort)}. Gör en lapp med streckkoder, så ser personalen direkt vad du menar.</p>
        <div class="ks-val"><a class="ks-cta" ${lappLank}>Skapa inköpslapp</a>${karta} class="ks-cta ghost">Visa på karta</a></div>`;
    } else if (km <= 130) {
      html_ = `<b class="ks-km">${kmText(km)}</b>
        <p>${km <= 40 ? 'Du har nära.' : 'En bit, men det går.'} Närmast från ${esc(ort)} är ${esc(b.namn)} i ${esc(b.ort)}, räknat fågelvägen. Gör en lapp med streckkoder att visa i butiken.</p>
        <div class="ks-val"><a class="ks-cta" ${lappLank}>Skapa inköpslapp</a>${karta} class="ks-cta ghost">Visa på karta</a></div>
        ${km > 40 ? `<p class="ks-mer">Hellre närmare? ${onskaKnapp(ort, true)}</p>` : ''}`;
    } else {
      html_ = `<b class="ks-km">${kmText(km)}</b>
        <p>Långt att åka för ett skal. Vi har inte kommit till ${esc(ort)} än, så säg till oss, eller till butiken där du brukar handla.</p>
        <div class="ks-val">${onskaKnapp(ort)}${tipsaKnapp(ort)}</div>
        <p class="ks-mer">Eller <a ${lappLank}>visa en inköpslapp i din mobilbutik</a>, där står hur de beställer. Närmast i dag: ${karta}>${esc(b.namn)} i ${esc(b.ort)}</a>.</p>`;
    }
    svar.innerHTML = html_;
    if (!lugn()) svar.animate([{ opacity: 0, transform: 'translateY(16px)' }, { opacity: 1, transform: 'none' }], { duration: 560, easing: 'cubic-bezier(.16,1,.3,1)' });
    window.ScrollTrigger?.refresh();
  };

  const valjOrt = (ort, kalla) => {
    const { x: butik, km } = narmast(ort, butiker);
    const b = butiksPunkter[butiker.indexOf(butik)];
    du = { ...ort, ...proj(ort.lat, ort.lon), butik: b, km, kmText: kmText(km) };
    falt.value = ort.namn;
    start ??= performance.now() - 4000;
    sikta();
    bageStart = performance.now();
    if (km >= 8) vagor.push({ x: du.x, y: du.y, t: bageStart, slag: 'vag', fart: 7, kraft: 1 });
    visaSvar(ort.namn, km, b);
    vack();
    window.corderH?.('ort-sok', km <= 130 ? 'nära' : 'långt');
    stangLista();
    if (kalla !== 'tangent' && innerWidth <= 900) falt.blur();
    if (innerWidth <= 900) {
      const r = svar.getBoundingClientRect();
      if (r.top < 60 || r.top > innerHeight * .4) scrollTo({ top: r.top + scrollY - 76, behavior: lugn() ? 'auto' : 'smooth' });
    }
  };

  // Rullgardinen med orter.
  let traffar = [], aktiv = -1;
  const stangLista = () => { lista.hidden = true; aktiv = -1; falt.setAttribute('aria-expanded', 'false'); falt.removeAttribute('aria-activedescendant'); };
  const visaLista = () => {
    const s = nyckel(falt.value);
    traffar = s ? ORTER.filter(o => nyckel(o.namn).startsWith(s)).concat(ORTER.filter(o => !nyckel(o.namn).startsWith(s) && nyckel(o.namn).includes(s))).slice(0, 5) : [];
    aktiv = -1;
    falt.removeAttribute('aria-activedescendant');
    if (!traffar.length) return stangLista();
    lista.innerHTML = traffar.map((o, i) => `<li id="ks-ort-${i}" role="option" aria-selected="false" data-i="${i}">${esc(o.namn)}</li>`).join('');
    lista.hidden = false;
    falt.setAttribute('aria-expanded', 'true');
  };
  const markera = i => {
    aktiv = (i + traffar.length) % traffar.length;
    [...lista.children].forEach((li, j) => li.setAttribute('aria-selected', j === aktiv));
    falt.setAttribute('aria-activedescendant', `ks-ort-${aktiv}`);
  };
  const okand = namn => {
    du = null;
    Object.assign(mal, mitt, { s: 1 });
    vack();
    svar.innerHTML = `<p>Vi hittar inte ${esc(namn)} på kartan. Prova närmaste större ort, eller använd din plats.</p>`;
    window.ScrollTrigger?.refresh();
  };
  falt.addEventListener('input', visaLista);
  falt.addEventListener('focus', () => falt.select());
  falt.addEventListener('blur', () => setTimeout(stangLista, 120));
  falt.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' && !lista.hidden) { e.preventDefault(); markera(aktiv + 1); }
    if (e.key === 'ArrowUp' && !lista.hidden) { e.preventDefault(); markera(aktiv - 1); }
    if (e.key === 'Escape') stangLista();
  });
  lista.addEventListener('pointerdown', e => {
    const li = e.target.closest('li');
    if (!li) return;
    e.preventDefault();
    valjOrt(traffar[+li.dataset.i]);
  });
  sok.addEventListener('submit', e => {
    e.preventDefault();
    const s = nyckel(falt.value);
    if (!s) return falt.focus();
    const ort = lista.hidden || aktiv < 0 ? ORTER.find(o => nyckel(o.namn) === s) || (!lista.hidden ? traffar[0] : null) : traffar[aktiv];
    if (ort) valjOrt(ort, 'tangent'); else okand(falt.value.trim());
  });
  sok.querySelectorAll('[data-ort]').forEach(b => b.addEventListener('click', () => valjOrt(ORTER.find(o => o.namn === b.dataset.ort))));

  // Platsen läses bara här i webbläsaren och skickas aldrig.
  if (!navigator.geolocation) platsKnapp.hidden = true;
  platsKnapp.addEventListener('click', () => {
    platsKnapp.setAttribute('aria-busy', 'true');
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      platsKnapp.removeAttribute('aria-busy');
      const { x: ort, km } = narmast({ lat: coords.latitude, lon: coords.longitude }, ORTER);
      if (km > 120) { svar.innerHTML = '<p>Du verkar vara utanför Sverige. Skriv orten du vill handla i.</p>'; return; }
      valjOrt(ort);
    }, () => {
      platsKnapp.removeAttribute('aria-busy');
      svar.innerHTML = '<p>Vi fick inte tillgång till din plats. Skriv din ort i stället.</p>';
      falt.focus();
    }, { maximumAge: 600000, timeout: 8000 });
  });

  // Önskan är det enda som skickas: ortens namn, från listan ovan och aldrig fritext.
  const kanDela = navigator.share && matchMedia('(pointer: coarse)').matches;
  svar.addEventListener('click', e => {
    const onska = e.target.closest('[data-onska]');
    if (onska && du) {
      window.corderH?.('onskad-ort', du.namn);
      if (!onskade.some(o => o.namn === du.namn)) onskade.push(du);
      vagor.push({ x: du.x, y: du.y, t: performance.now(), slag: 'vag', fart: 9, kraft: 1 });
      vack();
      const tack = document.createElement('div');
      tack.className = 'ks-tack';
      tack.innerHTML = `<b>Tack. ${esc(du.namn)} är noterat.</b><span>Önskningarna visar oss var vi ska leta butiker härnäst. Snabbast går det om din mobilbutik hör av sig.</span>`;
      const val = onska.closest('.ks-val, .ks-mer');
      if (val.classList.contains('ks-mer')) { val.replaceWith(tack); tack.insertAdjacentHTML('beforeend', `<div class="ks-val">${tipsaKnapp(du.namn)}</div>`); }
      else { onska.remove(); val.before(tack); }
      window.ScrollTrigger?.refresh();
      return;
    }
    const tipsa = e.target.closest('[data-tipsa]');
    if (tipsa && kanDela && du) {
      e.preventDefault();
      navigator.share({ title: 'Corder', text: tipsText(du.namn) }).catch(() => {});
    }
  });
})();
