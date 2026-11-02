// Formulär för butiker. Skickas till Corders tjänst, eller som mejl om tjänsten saknas eller inte svarar.
(() => {
  const start = Date.now();
  const rubriker = { foretag: 'Företag', kontakt: 'Kontaktperson', epost: 'E-post', telefon: 'Telefon', ort: 'Ort', butikstyp: 'Typ av butik', butiker: 'Antal butiker', leverans: 'Leveransadress', meddelande: 'Meddelande' };
  const skapa = (tagg, text) => { const e = document.createElement(tagg); if (text) e.textContent = text; return e; };
  document.querySelectorAll('form[data-form]').forEach(f => {
    const svar = f.querySelector('.form-svar');
    const knapp = f.querySelector('[type=submit]');
    const visaMejl = (data, fel) => {
      const rader = (data.rader || []).map(r => `${r.antal} st ${r.artikel} (EAN ${r.ean})`);
      const text = [...Object.keys(rubriker).filter(k => data[k]).map(k => `${rubriker[k]}: ${data[k]}`), ...(rader.length ? ['', ...rader] : [])].join('\n');
      const mejl = `mailto:${f.dataset.mejl}?subject=${encodeURIComponent(`${f.dataset.amne}: ${data.foretag}`)}&body=${encodeURIComponent(text)}`;
      svar.className = 'form-svar';
      svar.replaceChildren(skapa('span', `${fel ? 'Det gick inte att skicka formuläret. ' : ''}Ditt e-postprogram öppnas med uppgifterna ifyllda. Öppnas inget? Kopiera texten och mejla den till ${f.dataset.mejl}.`));
      const ruta = skapa('textarea'); ruta.readOnly = true; ruta.value = text; ruta.setAttribute('aria-label', 'Text att kopiera'); svar.append(ruta);
      if (mejl.length < 1900) location.href = mejl;
    };
    f.addEventListener('submit', async ev => {
      ev.preventDefault();
      const data = Object.fromEntries(new FormData(f));
      data.typ = f.dataset.form;
      data.tid = Date.now() - start;
      const rader = [...document.querySelectorAll('input[data-ean]')].filter(i => +i.value > 0)
        .map(i => ({ ean: i.dataset.ean, artikel: i.dataset.artikel, antal: Math.floor(+i.value) }));
      if (f.dataset.form === 'bestallning') {
        if (!rader.length) { svar.className = 'form-svar fel'; svar.textContent = 'Fyll i antal på minst en artikel.'; return; }
        data.rader = rader;
      }
      if (!f.dataset.url) { window.corderH?.(`${data.typ}-mejl`); return visaMejl(data); }
      knapp.disabled = true;
      try {
        const r = await fetch(f.dataset.url, { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body: JSON.stringify(data) });
        if (!r.ok) throw new Error(r.status);
        window.corderH?.(`${data.typ}-skickad`);
        svar.className = 'form-svar';
        svar.textContent = f.dataset.tack;
        f.querySelectorAll('input:not([data-ean]),textarea').forEach(i => { i.value = ''; });
      } catch { visaMejl(data, true); }
      knapp.disabled = false;
    });
  });
})();
