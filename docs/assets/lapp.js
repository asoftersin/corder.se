// Inköpslappen. Allt val ligger i adressen, inget sparas i webbläsaren: se /pages/integritet/.
(() => {
  const data = JSON.parse(document.getElementById('lapp-data').textContent);
  const sida = document.getElementById('innehall');
  const kvitto = document.getElementById('kvitto');
  const valModell = document.getElementById('lapp-modell');
  const valFarg = document.getElementById('lapp-farger');
  const status = document.getElementById('lapp-status');
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nyckel = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  const kanDela = navigator.share && matchMedia('(pointer: coarse)').matches;

  const q = new URLSearchParams(location.search);
  const startModell = data.modeller.find(m => m.slug === q.get('m')) || data.modeller[0];
  const lage = { modell: startModell, farg: null, kabel: q.get('k') === '1', laddare: q.get('l') === '1' };
  const hittaFarg = (m, namn) => m.farger.find(f => nyckel(f.namn) === nyckel(namn || '')) || m.farger.find(f => f.namn === lage.farg?.namn) || m.farger.find(f => f.namn === 'Skogsgrön') || m.farger[0];
  lage.farg = hittaFarg(startModell, q.get('f'));

  const rader = () => [
    { id: 'skal', typ: 'Skal', namn: `Skal till ${lage.modell.namn}`, under: lage.farg.namn, ean: lage.farg.ean, bild: lage.farg.bild },
    { id: 'kabel', typ: 'Kabel', namn: `Laddkabel ${lage.modell.kabel.namn}`, under: '2 meter', ean: lage.modell.kabel.ean, bild: lage.modell.kabel.bild },
    { id: 'laddare', typ: 'Laddare', namn: lage.modell.laddare.namn, under: 'Passar kabeln ovan', ean: lage.modell.laddare.ean, bild: lage.modell.laddare.bild },
  ];
  const valda = () => rader().filter(r => r.id === 'skal' || lage[r.id]);

  // EAN-13: 95 moduler. Returnerar svarta streck som [start, bredd, lång].
  const streck = ean => {
    const L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011'];
    const inv = s => [...s].map(b => (b === '1' ? '0' : '1')).join('');
    const G = L.map(s => [...inv(s)].reverse().join(''));
    const R = L.map(inv);
    const paritet = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL'][+ean[0]];
    const vanster = [...ean.slice(1, 7)].map((d, i) => (paritet[i] === 'L' ? L : G)[+d]).join('');
    const hoger = [...ean.slice(7)].map(d => R[+d]).join('');
    const bitar = `101${vanster}01010${hoger}101`;
    const lang = i => i < 3 || i >= 92 || (i >= 45 && i < 50);
    const ut = [];
    for (let i = 0; i < 95; i++) {
      if (bitar[i] !== '1') continue;
      let n = 1;
      while (bitar[i + n] === '1' && lang(i + n) === lang(i)) n++;
      ut.push([i, n, lang(i)]);
      i += n - 1;
    }
    return ut;
  };
  // Hela pixlar per modul, annars blir strecken ojämna och svåra att skanna.
  const modul = () => Math.max(2, Math.min(4, Math.floor((kvitto.clientWidth - 48) / 95)));
  const kod = ean => {
    const s = modul(), h = 62;
    const r = streck(ean).map(([x, n, l]) => `<rect x="${x * s}" width="${n * s}" height="${l ? h + 6 : h}"/>`).join('');
    return `<svg class="k-kod" width="${95 * s}" height="${h + 6}" viewBox="0 0 ${95 * s} ${h + 6}" shape-rendering="crispEdges" role="img" aria-label="Streckkod, EAN ${ean}">${r}</svg><span class="k-ean">${ean}</span>`;
  };

  let nyttId = null;
  const rita = () => {
    const delar = rader().map(r => {
      if (r.id !== 'skal' && !lage[r.id]) {
        return `<button class="k-lagg" type="button" data-lagg="${r.id}"><span aria-hidden="true">+</span><b>Lägg till ${r.typ.toLowerCase()}</b><small>${esc(r.namn)}</small></button>`;
      }
      const ta = r.id === 'skal' ? '' : `<button class="k-ta" type="button" data-ta="${r.id}" aria-label="Ta bort ${esc(r.typ.toLowerCase())}">Ta bort</button>`;
      return `<div class="k-rad${nyttId === r.id ? ' ny' : ''}">
        <div class="k-rubrik">${r.bild ? `<img src="${r.bild}" alt="" width="48" height="64" decoding="async">` : ''}<div><b>${esc(r.namn)}</b><span>${esc(r.under)}</span>${ta}</div></div>
        ${kod(r.ean)}
      </div>`;
    });
    kvitto.innerHTML = `<header><span class="logo">corder</span><span class="caps">Inköpslapp</span></header>
      ${delar.join('')}
      <p class="k-not">Visa lappen i butiken. Sortimentet varierar, så fråga om det finns inne. Butiken sätter sitt eget pris.</p>
      <p class="k-not k-personal"><b>Till personalen:</b> Saknar ni Corder? Beställ på <a href="/aterforsaljare/" data-h="inkopslapp-butik">corder.se/aterforsaljare</a></p>`;
    nyttId = null;
    sida.style.setProperty('--tint', lage.farg.hex);
    const [r, g, b] = lage.farg.hex.match(/\w\w/g).map(x => parseInt(x, 16));
    sida.dataset.ton = .299 * r + .587 * g + .114 * b > 140 ? 'ljus' : 'mork';
    valModell.value = lage.modell.slug;
    valFarg.innerHTML = lage.modell.farger.map(f => `<button class="sw" type="button" style="--c:${f.hex}" aria-label="${esc(f.namn)}" aria-pressed="${f === lage.farg}" data-farg="${esc(f.namn)}"></button>`).join('') + `<span>${esc(lage.farg.namn)}</span>`;
    const p = new URLSearchParams({ m: lage.modell.slug, f: nyckel(lage.farg.namn) });
    if (lage.kabel) p.set('k', '1');
    if (lage.laddare) p.set('l', '1');
    history.replaceState(null, '', `?${p}`);
  };
  const meddela = t => { status.textContent = t; };

  kvitto.addEventListener('click', e => {
    const lagg = e.target.closest('[data-lagg]');
    const ta = e.target.closest('[data-ta]');
    if (lagg) {
      lage[lagg.dataset.lagg] = true;
      nyttId = lagg.dataset.lagg;
      window.corderH?.('inkopslapp-tillagg', lagg.dataset.lagg);
      rita();
      kvitto.querySelector(`[data-ta="${lagg.dataset.lagg}"]`).focus({ preventScroll: true });
    } else if (ta) {
      lage[ta.dataset.ta] = false;
      rita();
      kvitto.querySelector(`[data-lagg="${ta.dataset.ta}"]`).focus({ preventScroll: true });
    }
  });
  valModell.addEventListener('change', () => {
    lage.modell = data.modeller.find(m => m.slug === valModell.value);
    lage.farg = hittaFarg(lage.modell);
    rita();
  });
  valFarg.addEventListener('click', e => {
    const b = e.target.closest('[data-farg]');
    if (!b) return;
    lage.farg = lage.modell.farger.find(f => f.namn === b.dataset.farg);
    rita();
    valFarg.querySelector('[aria-pressed="true"]').focus();
  });
  let senast = modul();
  addEventListener('resize', () => { if (modul() !== senast) { senast = modul(); rita(); } }, { passive: true });

  // Lappen som bild, så att den går att visa utan täckning inne i butiken.
  const ladda = src => new Promise(ok => {
    if (!src) return ok(null);
    const i = new Image();
    i.onload = () => ok(i);
    i.onerror = () => ok(null);
    i.src = src;
  });
  const radbryt = (c, text, bredd) => text.split(' ').reduce((ut, ord) => {
    const prov = ut.length ? `${ut[ut.length - 1]} ${ord}` : ord;
    if (ut.length && c.measureText(prov).width <= bredd) ut[ut.length - 1] = prov;
    else ut.push(ord);
    return ut;
  }, []);
  const somBild = async () => {
    await Promise.all(['500 34px "Inter Tight"', '400 64px Jost'].map(f => document.fonts.load(f).catch(() => {})));
    const lista = valda();
    const bilder = await Promise.all(lista.map(r => ladda(r.bild)));
    const B = 1080, M = 72, P = 64, S = 8, H_KOD = 170;
    const inre = B - 2 * M - 2 * P;
    const rad = 200 + H_KOD + 74;
    const H = M + 150 + lista.length * rad + 120 + 300 + 40 + M;
    const c = document.createElement('canvas');
    c.width = B; c.height = H;
    const x = c.getContext('2d');
    const typsnitt = (vikt, px) => `${vikt} ${px}px "Inter Tight", system-ui, sans-serif`;
    x.fillStyle = lage.farg.hex;
    x.fillRect(0, 0, B, H);
    // Papper med sågtandad nederkant.
    const botten = H - M, t = 22;
    x.fillStyle = '#fff';
    x.beginPath();
    x.moveTo(M, M);
    x.lineTo(B - M, M);
    x.lineTo(B - M, botten);
    for (let px = B - M; px > M; px -= 2 * t) { x.lineTo(px - t, botten - t); x.lineTo(px - 2 * t, botten); }
    x.lineTo(M, M);
    x.fill();
    const V = M + P, HG = B - M - P;
    let y = M + 96;
    x.fillStyle = '#111';
    x.font = '400 64px Jost, sans-serif';
    x.fillText('corder', V, y);
    x.font = typsnitt(500, 24);
    x.textAlign = 'right';
    x.fillText('INKÖPSLAPP', HG, y - 8);
    x.textAlign = 'left';
    y += 54;
    const streckad = yy => { x.save(); x.setLineDash([10, 10]); x.strokeStyle = '#bbb'; x.lineWidth = 2; x.beginPath(); x.moveTo(V, yy); x.lineTo(HG, yy); x.stroke(); x.restore(); };
    lista.forEach((r, i) => {
      streckad(y);
      const bild = bilder[i], topp = y + 28, hB = 144;
      let tx = V;
      if (bild) {
        const k = Math.min(110 / bild.naturalWidth, hB / bild.naturalHeight);
        const w = bild.naturalWidth * k, h = bild.naturalHeight * k;
        x.drawImage(bild, V + (110 - w) / 2, topp + (hB - h) / 2, w, h);
        tx = V + 134;
      }
      x.fillStyle = '#111';
      let px = 40;
      do { x.font = typsnitt(500, px); px -= 2; } while (x.measureText(r.namn).width > HG - tx - 130 && px > 22);
      x.fillText(r.namn, tx, topp + 62);
      x.fillStyle = '#6e6e6e';
      x.font = typsnitt(400, 32);
      x.fillText(r.under, tx, topp + 110);
      const kx = V + Math.floor((inre - 95 * S) / 2), ky = y + 200;
      streck(r.ean).forEach(([s, n, l]) => x.fillRect(kx + s * S, ky, n * S, l ? H_KOD : H_KOD - 14));
      x.font = typsnitt(400, 34);
      x.textAlign = 'center';
      x.fillText([...r.ean].join(' '), B / 2, ky + H_KOD + 46);
      x.textAlign = 'left';
      y += rad;
    });
    streckad(y);
    y += 56;
    x.fillStyle = '#555';
    x.font = typsnitt(400, 30);
    radbryt(x, 'Visa lappen i butiken. Sortimentet varierar, så fråga om det finns inne. Butiken sätter sitt eget pris.', inre).forEach(l => { x.fillText(l, V, y); y += 42; });
    y += 18;
    x.fillStyle = '#111';
    radbryt(x, 'Till personalen: Saknar ni Corder? Beställ på corder.se/aterforsaljare', inre).forEach(l => { x.fillText(l, V, y); y += 42; });
    return new Promise(ok => c.toBlob(ok, 'image/png'));
  };

  document.getElementById('lapp-spara').addEventListener('click', async () => {
    window.corderH?.('inkopslapp-spara', lage.modell.slug);
    const blob = await somBild();
    const namn = `corder-inkopslapp-${lage.modell.slug}.png`;
    const fil = new File([blob], namn, { type: 'image/png' });
    if (kanDela && navigator.canShare?.({ files: [fil] })) {
      try { await navigator.share({ files: [fil] }); meddela('Klart. Visa bilden i butiken.'); } catch { /* Avbrutet av besökaren. */ }
      return;
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = namn;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    meddela('Lappen är sparad som bild. Visa den i butiken.');
  });
  document.getElementById('lapp-dela').addEventListener('click', async () => {
    window.corderH?.('inkopslapp-dela', lage.modell.slug);
    if (kanDela) {
      try { await navigator.share({ title: 'Inköpslapp från Corder', url: location.href }); } catch { /* Avbrutet av besökaren. */ }
      return;
    }
    try { await navigator.clipboard.writeText(location.href); meddela('Länken till lappen är kopierad.'); } catch { meddela(location.href); }
  });

  rita();
  // Lappen matas ut bara när någon ser på, så att den aldrig blir kvar utanför bild.
  if (!document.hidden) sida.classList.add('skriv');
  requestAnimationFrame(() => requestAnimationFrame(() => sida.classList.add('levande')));
})();
