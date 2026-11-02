// Besöksstatistik utan cookies: se /pages/integritet/. Får aldrig störa sidan.
(() => {
  const e = document.currentScript?.dataset.e;
  if (!e || navigator.doNotTrack === '1' || navigator.globalPrivacyControl) return;
  const q = new URLSearchParams(location.search);
  const send = (t, n, v) => { try {
    navigator.sendBeacon(e, new Blob([JSON.stringify({ t, n, v, p: location.pathname, r: document.referrer,
      us: q.get('utm_source'), um: q.get('utm_medium'), uc: q.get('utm_campaign') })], { type: 'text/plain' }));
  } catch {} };
  window.corderH = (n, v) => send('e', n, v);
  send('s');
  addEventListener('click', ev => {
    const a = ev.target.closest?.('a,[data-h]');
    if (!a) return;
    const h = a.getAttribute('href') || '';
    if (a.dataset.h) send('e', a.dataset.h, a.dataset.v);
    else if (h.startsWith('mailto:')) send('e', 'epost', decodeURIComponent((h.match(/subject=([^&]*)/) || [, ''])[1]) || undefined);
    else if (a.hasAttribute('download')) send('e', 'nedladdning', h.split('/').pop());
    else if (h.startsWith('/#butiker') || h === '#butiker' || h === '#kop') send('e', 'hitta-butik', location.pathname);
  }, { capture: true, passive: true });
})();
