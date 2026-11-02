// Färgvärldarna i heron: varje färg har en egen bild och rubrik, och knappen öppnar provrummet med just den färgen.
(() => {
  const hero = document.getElementById('hero');
  const val = hero?.querySelector('.hero-farger');
  if (!val) return;

  const L = '/img/lifestyle/';
  const VARLDAR = [
    { farg: 'Skogsgrön', hex: '#3d5143', bg: '#0b0b0b', rubrik: ['Skogsgrön', 'efter mörker.'], finns: 'iPhone 17–18', bild: 'corder-natt-skogsgron-v3', pos: '50% 38%', mob: '92% 38%', alt: 'Kvinna i grön bomberjacka på en nattmarknad håller upp en iPhone i Corders skogsgröna TPU-skal' },
    { farg: 'Persika', hex: '#f5a493', bg: '#2a120c', rubrik: ['Persika till', 'sista solen.'], finns: 'iPhone 14–16', bild: 'corder-uteservering-persika', pos: '30% 35%', alt: 'Kvinna på en uteservering i kvällsljus håller upp en iPhone i Corders persikofärgade skal' },
    { farg: 'Blå', hex: '#4a6684', bg: '#0e1a27', rubrik: ['Blå till', 'långa fikor.'], finns: 'iPhone 14–16', bild: 'corder-hemma-bla-svart', pos: '50% 50%', alt: 'Kvinna vid ett kaffebord håller en iPhone i Corders blå skal, med en telefon i svart skal på bordet' },
    { farg: 'Lila', hex: '#b9bdf0', bg: '#17173d', rubrik: ['Lila rakt', 'i kameran.'], finns: 'iPhone 14–16', bild: 'corder-portratt-lila', pos: '45% 40%', mob: '88% 40%', alt: 'Kvinna håller upp en iPhone i Corders lila skal' },
    { farg: 'Svart', hex: '#1c1c1c', bg: '#141210', rubrik: ['Svart går', 'till allt.'], finns: 'alla modeller', bild: 'corder-goteborg-man-svart', pos: '50% 35%', alt: 'Man i skinnjacka på en kullerstensgata håller en iPhone i Corders svarta skal' },
  ];

  const lager = hero.querySelector('.hero-lager');
  const rubrik = hero.querySelector('h1');
  const finns = hero.querySelector('.hero-finns');
  const cta = hero.querySelector('.hero-cta');
  const paus = hero.querySelector('.hero-paus');
  const lugn = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let nu = 0;
  let autospel = !lugn;
  let byter = false;

  val.insertAdjacentHTML('afterbegin', VARLDAR.map((v, i) => `<button type="button" class="hero-farg" style="--c:${v.hex}" aria-pressed="${!i}" aria-label="${v.farg}"><i aria-hidden="true"></i><span aria-hidden="true">${v.farg}</span></button>`).join(''));
  const knappar = [...val.querySelectorAll('.hero-farg')];

  const skapaBild = v => {
    const img = new Image();
    img.srcset = `${L}s/${v.bild}.webp 640w, ${L}m/${v.bild}.webp 828w, ${L}${v.bild}.webp 1122w`;
    img.sizes = hero.querySelector('.hero-lager img').sizes;
    img.src = `${L}${v.bild}.webp`;
    img.alt = v.alt;
    img.width = 1122;
    img.height = 1402;
    img.style.objectPosition = (matchMedia('(max-width: 900px)').matches && v.mob) || v.pos;
    return img;
  };
  const forladda = i => { skapaBild(VARLDAR[i % VARLDAR.length]); };

  const visaText = (v, riktning) => {
    rubrik.innerHTML = v.rubrik.map(r => `<span class="line"><span>${r}</span></span>`).join('');
    rubrik.dataset.splitDone = '1';
    finns.textContent = v.finns;
    cta.textContent = `Prova ${v.farg.toLowerCase()} på din iPhone`;
    cta.dataset.farg = v.farg;
    hero.querySelectorAll('.hero-din-val a').forEach(a => { a.dataset.farg = v.farg; });
    if (lugn) return;
    rubrik.querySelectorAll('.line > span').forEach((s, i) => s.animate(
      [{ transform: `translateY(${105 * riktning}%)` }, { transform: 'none' }],
      { duration: 760, delay: i * 70, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' }
    ));
  };

  const visa = async (i, x, y) => {
    if (i === nu || byter) return;
    byter = true;
    const v = VARLDAR[i];
    const riktning = i > nu || (nu === VARLDAR.length - 1 && i === 0) ? 1 : -1;
    const gammal = lager.querySelector('img:last-child');
    const ny = skapaBild(v);
    await ny.decode().catch(() => {});
    nu = i;
    knappar.forEach((k, n) => k.setAttribute('aria-pressed', n === i));
    hero.style.setProperty('--hero-bg', v.bg);
    visaText(v, riktning);
    lager.append(ny);
    const klar = () => { gammal.remove(); byter = false; forladda(i + 1); };
    if (lugn) return klar();
    const r = lager.getBoundingClientRect();
    const px = x === undefined ? r.width * .6 : x - r.left;
    const py = y === undefined ? r.height * .5 : y - r.top;
    const radie = Math.hypot(Math.max(px, r.width - px), Math.max(py, r.height - py));
    ny.animate({ clipPath: [`circle(0px at ${px}px ${py}px)`, `circle(${radie}px at ${px}px ${py}px)`] }, { duration: 820, easing: 'cubic-bezier(.65,0,.15,1)' }).onfinish = klar;
  };

  // Väljer man själv stannar bildspelet, så att ingenting byts under fingret.
  const stoppa = () => {
    autospel = false;
    hero.classList.add('hero-stopp');
    paus.hidden = true;
  };

  val.addEventListener('click', e => {
    const k = e.target.closest('.hero-farg');
    if (!k) return;
    stoppa();
    const i = knappar.indexOf(k);
    const r = k.getBoundingClientRect();
    visa(i, e.detail ? e.clientX : r.left + r.width / 2, e.detail ? e.clientY : r.top + r.height / 2);
    window.corderH?.('hero-farg', VARLDAR[i].farg);
  });
  hero.querySelector('.hero-copy').addEventListener('click', e => { if (e.target.closest('a')) stoppa(); });

  // Förloppet i den valda färgen är klockan: stannar animationen, stannar bytet.
  val.addEventListener('animationend', e => {
    if (e.animationName === 'hero-forlopp' && autospel) visa((nu + 1) % VARLDAR.length);
  });
  const pausa = () => hero.classList.toggle('hero-pausad', paus.getAttribute('aria-pressed') === 'true' || utanfor || hero.matches(':hover') || val.contains(document.activeElement));
  let utanfor = false;
  paus.addEventListener('click', () => {
    const pa = paus.getAttribute('aria-pressed') !== 'true';
    paus.setAttribute('aria-pressed', pa);
    paus.setAttribute('aria-label', pa ? 'Starta bildväxlingen' : 'Pausa bildväxlingen');
    pausa();
  });
  ['pointerenter', 'pointerleave', 'focusin', 'focusout'].forEach(h => hero.addEventListener(h, () => setTimeout(pausa)));
  new IntersectionObserver(([p]) => { utanfor = p.intersectionRatio < .5; pausa(); }, { threshold: .5 }).observe(hero.querySelector('.hero-stage'));

  // Svep åt sidan byter färg, lodrätt rör sig sidan som vanligt.
  let start = null;
  hero.addEventListener('touchstart', e => { const t = e.touches[0]; start = { x: t.clientX, y: t.clientY }; }, { passive: true });
  hero.addEventListener('touchend', e => {
    if (!start) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - start.x;
    const dy = t.clientY - start.y;
    start = null;
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
    stoppa();
    const i = (nu + (dx < 0 ? 1 : -1) + VARLDAR.length) % VARLDAR.length;
    visa(i, t.clientX, t.clientY);
    window.corderH?.('hero-farg', VARLDAR[i].farg);
  }, { passive: true });

  if (lugn) stoppa();
  else hero.classList.add('hero-spelar');
  hero.querySelectorAll('.hero-din-val a').forEach(a => { a.dataset.farg = VARLDAR[0].farg; });
  addEventListener('load', () => setTimeout(() => forladda(1), 1200), { once: true });
})();
