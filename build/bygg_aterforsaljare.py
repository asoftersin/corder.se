"""Bygger /aterforsaljare/: sidan för butiker och grossister, produktdata (CSV och Excel) och bildpaket.

Rekommenderade butikspriser visas, inköpspriserna skickas på begäran från sales@corder.se.
Kör: python3 -I build/bygg_aterforsaljare.py (Excel skapas bara om openpyxl finns).
"""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bygg_guider import KABLAR, LADDARE, MODELLER, PRIS, ROT, SITE, SKAL_EAN, STATISTIK_URL, bild, brodsmulor, liten, matt, sida  # noqa: E402

UT = ROT / "aterforsaljare"
URL = f"{SITE}/aterforsaljare/"
MAIL = "sales@corder.se"
AMNE = "Prislista och startsortiment"
TEXT = ("Hej!\n\nVi är intresserade av att sälja Corder.\n\nFöretag:\nAntal butiker:\nTyp av butik (kiosk, servicehandel, grossist ...):\n"
        "Kontaktperson och telefon:\n\nSkicka gärna prislista och förslag på startsortiment.\n")
MAILTO = f"mailto:{MAIL}?subject={quote(AMNE)}&body={quote(TEXT)}"

SKAL_MODELLER = [  # modell, slug, bildprefix, färger
    ("iPhone 14", "iphone-14", "14", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 14 Pro", "iphone-14-pro", "14p", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 15", "iphone-15", "15", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 15 Pro", "iphone-15-pro", "15p", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 16e", "iphone-16e", "16e", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 16", "iphone-16", "16", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 16 Pro", "iphone-16-pro", "16p", ["Svart", "Blå", "Lila", "Persika"]),
    ("iPhone 17", "iphone-17", "17", ["Svart", "Skogsgrön"]),
    ("iPhone 17 Pro", "iphone-17-pro", "17p", ["Svart", "Skogsgrön"]),
    ("iPhone 18 Pro", "iphone-18-pro", "17p", ["Svart", "Skogsgrön"]),
]
BILDFARG = {"Svart": "black", "Blå": "blue", "Lila": "purple", "Persika": "pink", "Skogsgrön": "skogsgron"}
KOLUMNER = ["Artikel", "Kategori", "Modell", "Färg", "Material/typ", "EAN/GTIN-13", "Bild", "Produktsida"]


def produktrader():
    rader = []
    for modell, slug, pre, farger in SKAL_MODELLER:
        for f in farger:
            rader.append([f"TPU-skal {modell}, {f.lower()}", "Mobilskal", modell, f, "TPU, matt",
                          SKAL_EAN.get((modell, f), ""), f"{SITE}/img/cut/{pre}-{BILDFARG[f]}.webp", f"{SITE}/skal/{slug}/"])
    for sida_, kat, artiklar in (("kablar", "Laddkabel", KABLAR), ("laddare", "Snabbladdare", LADDARE)):
        for a in artiklar:
            rader.append([a["artikel"], kat, "", "", a["typ"], a["ean"], f'{SITE}/img/produkter/{a["bild"]}.webp', f'{SITE}/{sida_}/#{a["id"]}'])
    return rader


def skriv_produktdata():
    rader = produktrader()
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(KOLUMNER)
    w.writerows(rader)
    (UT / "corder-produktdata.csv").write_text("﻿" + buf.getvalue(), encoding="utf-8")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print("openpyxl saknas, hoppar över Excel (befintlig fil behålls)")
        return len(rader)
    wb = Workbook()
    ws = wb.active
    ws.title = "Corder produktdata"
    ws.append(KOLUMNER)
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="111111")
    for r in rader:
        ws.append(r)
    for i, bredd in enumerate((44, 14, 16, 12, 22, 16, 48, 44), 1):
        ws.column_dimensions[chr(64 + i)].width = bredd
    for rad in ws.iter_rows(min_row=2, min_col=6, max_col=6):
        for c in rad:
            c.number_format = "@"
    ws.freeze_panes = "A2"
    wb.save(UT / "corder-produktdata.xlsx")
    return len(rader)


def skriv_bildpaket():
    filer = sorted((ROT / "img" / "cut").glob("*.webp")) + sorted((ROT / "img" / "produkter").glob("*.webp"))
    filer = [f for f in filer if f.stem != "kabel-usb-c-lightning-vit"]  # säljs inte
    with zipfile.ZipFile(UT / "corder-bildpaket.zip", "w", zipfile.ZIP_STORED) as z:
        for f in filer:
            # Fast datum, så att filen bara ändras när bilderna gör det.
            z.writestr(zipfile.ZipInfo(f"corder-bildpaket/{f.parent.name}/{f.name}", (2026, 1, 1, 0, 0, 0)), f.read_bytes())
        z.writestr(zipfile.ZipInfo("corder-bildpaket/LASMIG.txt", (2026, 1, 1, 0, 0, 0)),
                   "Frilagda produktbilder från Corder (WebP med transparent bakgrund).\n"
                   "Fritt att använda för att marknadsföra och sälja Corders produkter.\n"
                   "Frågor: sales@corder.se\n")
    return len(filer)


FAQ = [
    ("Säljer ni till grossister och kedjor?", "Ja. Vi säljer både direkt till butiker och via grossister, och tar fram ett startsortiment efter er yta och era kunder."),
    ("Har alla artiklar EAN-kod?", "Ja, alla artiklar har EAN via GS1 Sverige. Koderna finns i produktdatan (Excel och CSV) här på sidan."),
    ("Vilka iPhone-modeller finns det skal till?", "iPhone 14, 14 Pro, 15, 15 Pro, 16e, 16 och 16 Pro i svart, blå, lila och persika, samt iPhone 17, 17 Pro och 18 Pro i svart och skogsgrön."),
    ("Är produkterna CE-märkta?", "Ja, laddare och kablar är CE-märkta och alla produkter levereras i butiksfärdiga förpackningar med corder-ordmärket."),
    ("Vad kostar det?", "Skal och kablar har rekommenderat butikspris 60 kr och snabbladdare 99 kr. Inköpspriser för butik och grossist finns i prislistan, som vi skickar på begäran."),
    ("Vad händer om det inte säljer?", "Första startpaketet har 90 dagars säljgaranti. Det som inte har sålts byter vi mot andra artiklar eller tar tillbaka och krediterar, så länge förpackningen är obruten."),
    ("Säljer Corder själva på nätet?", "Nej. Corder säljs bara i fysiska butiker, så ni konkurrerar inte med vår egen webbutik."),
]


def formular(typ, amne, tack, falt, knapp):
    url = f'{STATISTIK_URL.rstrip("/")}/f' if STATISTIK_URL else ""
    notis = ("Vi använder uppgifterna för att svara er." if url else "Knappen öppnar ditt e-postprogram med uppgifterna ifyllda.")
    return f"""<form class="form" data-form="{typ}" data-url="{url}" data-mejl="{MAIL}" data-amne="{amne}" data-tack="{tack}">
      {falt}
      <label class="falla" aria-hidden="true">Lämna tomt<input name="webbplats" tabindex="-1" autocomplete="off"></label>
      <small class="bred">{notis} Läs mer under <a href="/pages/integritet/">integritet</a>.</small>
      <button class="btn" type="submit">{knapp}</button>
      <div class="form-svar" role="status" aria-live="polite"></div>
    </form>"""


GRUNDFALT = """<label>Företag<input name="foretag" required maxlength="120" autocomplete="organization"></label>
      <label>Kontaktperson<input name="kontakt" required maxlength="120" autocomplete="name"></label>
      <label>E-post<input name="epost" type="email" required maxlength="254" autocomplete="email"></label>
      <label>Telefon<input name="telefon" type="tel" maxlength="40" autocomplete="tel"></label>"""


def ansokan():
    typer = "".join(f"<option>{t}</option>" for t in ("Kiosk", "Servicehandel", "Livsmedelsbutik", "Drivmedelsstation", "Elektronikbutik", "Grossist", "Annat"))
    falt = f"""{GRUNDFALT}
      <label>Ort<input name="ort" maxlength="80" autocomplete="address-level2"></label>
      <label>Typ av butik<select name="butikstyp"><option value="">Välj</option>{typer}</select></label>
      <label>Antal butiker<input name="butiker" type="number" min="1" max="99999" inputmode="numeric"></label>
      <label class="bred">Något vi bör veta?<textarea name="meddelande" maxlength="2000"></textarea></label>"""
    return formular("ansokan", "Prislista och startsortiment", "Tack! Vi har tagit emot er ansökan och hör av oss via e-post.", falt, "Skicka ansökan")


def innehall(antal_rader, antal_bilder):
    def kbild(i, p):
        src = liten(f"/img/{p}.webp")
        w, h = matt(src)
        return f'<img src="{src}" alt="" width="{w}" height="{h}" loading="lazy" class="k{i}">'
    kollage = "".join(kbild(i, p) for i, p in enumerate(("cut/17p-skogsgron", "produkter/kabel-usb-c-usb-c-2m", "cut/16p-pink",
                                             "produkter/laddare-20w-dual-port", "cut/16-blue", "produkter/kabel-usb-c-lightning-svart")))
    faq = "".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
    return f"""<main id="innehall" class="b2b">

<section class="b2b-hero">
  <div class="wrap b2b-hero-grid">
    <div class="b2b-hero-text rv">
      <span class="caps">För butiker och grossister</span>
      <h1>Ett sortiment som säljer i volym.</h1>
      <p>Kablar, laddare och iPhone-skal för kunder som behöver något nu. Impulspris, snabb rotation och exponering i eget Corder-ställ eller i tunnor längs gångarna.</p>
      <div class="b2b-actions">
        <a class="btn" href="#ansok">Få prislista och startsortiment</a>
        <a class="btn ghost" href="#resurser">Produktdata och bilder</a>
      </div>
      <ul class="b2b-kvitto">
        <li><b>{PRIS["skal"]} kr</b> rek. pris för <a href="/skal/">skal</a> och <a href="/kablar/">kablar</a></li>
        <li><b>{PRIS["laddare"]} kr</b> rek. pris för <a href="/laddare/">snabbladdare</a></li>
        <li><b>90 dagar</b> säljgaranti på första startpaketet</li>
        <li><b>Hela Sverige</b> leverans till butik eller grossistlager</li>
      </ul>
    </div>
    <div class="b2b-stat rv">
      <span class="caps">I en enda butik, VIP Mullsjö</span>
      <b data-count="20000">20 000</b>
      <p>sålda Corder-produkter per år, ungefär</p>
      <div class="b2b-split" aria-label="Fördelning">
        <span style="--w:60%"><i></i>Kablar ca 12 000</span>
        <span style="--w:40%"><i></i>Skal och laddare ca 8 000</span>
      </div>
    </div>
  </div>
</section>

<section class="b2b-film rv">
  <div class="wrap">
    <div class="b2b-film-frame">
      <video muted loop playsinline autoplay preload="metadata" poster="/video/corder-film-poster.webp" width="1920" height="1080"
        aria-label="Kort film om Corders sortiment: TPU-skal i fem färger, kablar och laddare.">
        <source src="/video/corder-film-720.mp4" type="video/mp4" media="(max-width: 900px)">
        <source src="/video/corder-film-1080.mp4" type="video/mp4">
      </video>
    </div>
  </div>
</section>

<section class="b2b-why">
  <div class="wrap">
    <h2 class="rv">Därför säljer det.</h2>
    <div class="b2b-cards">
      <div class="b2b-card rv"><span>01</span><h3>Akut behov</h3><p>Kabeln är glömd, laddaren står kvar hemma eller skalet har spruckit. Kunden behöver lösningen nu, inte om tre dagar.</p></div>
      <div class="b2b-card rv"><span>02</span><h3>Impulspris</h3><p>60 kr för skal och kablar, 99 kr för snabbladdare. Under gränsen där kunden tänker efter, och lätt att plocka med i förbifarten.</p></div>
      <div class="b2b-card rv"><span>03</span><h3>Där kunderna går</h3><p>I tunnor längs gångarna eller i ett eget Corder-ställ. Ett kompakt sortiment som täcker de vanligaste behoven: rätt kabel, en snabbladdare och skal till de populäraste iPhone-modellerna.</p></div>
    </div>
  </div>
</section>

<section class="b2b-case">
  <div class="wrap b2b-case-grid">
    <div class="b2b-case-text rv">
      <span class="caps">Så fungerar det i praktiken</span>
      <h2>VIP Mullsjö: tunnorna som bevis.</h2>
      <p>I VIP Mullsjö säljs Corder från ett eget ställ och från tunnor längs gångarna, där kunderna redan går förbi. Tunnorna står för den stora volymen. Totalt säljer vi ungefär 20 000 produkter om året i butiken, främst laddkablar.</p>
      <p>VIP Mullsjö drivs av Corders medgrundare Anton Lindkvist. Därför vet vi exakt vad som säljer, vad som inte gör det och hur exponeringen ska se ut. Den kunskapen tar vi med till er butik.</p>
      <p><a href="vip-mullsjo/">Läs hela kundcaset</a></p>
    </div>
    <div class="b2b-kollage rv" aria-hidden="true">{kollage}</div>
  </div>
</section>

<section class="b2b-start">
  <div class="wrap">
    <div class="b2b-start-head rv">
      <h2>Kom igång med ett startpaket.</h2>
      <p>Fyllda och klara att ställa ut, med pris på skylten. Vi anpassar skalen efter era kunder.</p>
    </div>
    <div class="b2b-paket">
      <div class="rv"><span class="caps">Volym i gången</span><h3>Kabelpaket</h3><b>200 kablar</b><p>USB-C och Lightning, alla 2 meter och flätade, för tunna eller hylla längs gångarna. Det som säljer mest i VIP Mullsjö.</p><small>Rek. pris 60 kr</small></div>
      <div class="rv"><span class="caps">Tillägg</span><h3>Laddarpaket</h3><b>60 snabbladdare</b><p>20W USB-C och Dual Port för de nya iPhone-modellerna, 18W USB-A för äldre kablar. Ställs bredvid kablarna.</p><small>Rek. pris 99 kr</small></div>
      <div class="rv dark"><span class="caps">Begränsat antal</span><h3>Corder-ställ</h3><b>60 artiklar och ställ</b><p>Kablar, laddare och skal i vårt eget ställ, som ingår i första ordern. Passar kiosk, disk och mindre butiker.</p><small>Så långt lagret räcker</small></div>
    </div>
    <div class="b2b-garanti rv">
      <div><span class="caps">Säljgaranti</span><h3>Säljer det inte, tar vi tillbaka det.</h3></div>
      <p>Det som inte har sålts efter 90 dagar byter vi mot andra artiklar eller tar tillbaka och krediterar. Gäller det första startpaketet per butik, för produkter i obruten förpackning.</p>
    </div>
  </div>
</section>

<section class="b2b-facts">
  <div class="wrap">
    <h2 class="rv">Klart för butik.</h2>
    <dl class="b2b-fact-grid">
      <div class="rv"><dt>EAN</dt><dd>Streckkod per artikel via GS1 Sverige</dd></div>
      <div class="rv"><dt>CE-märkt</dt><dd>Laddare och kablar</dd></div>
      <div class="rv"><dt>Butiksfärdigt</dt><dd>Förpackat med corder-ordmärket</dd></div>
      <div class="rv"><dt>Svenskt bolag</dt><dd>Corder Group AB, org.nr 559227-0226</dd></div>
      <div class="rv"><dt>Hela Sverige</dt><dd>Leverans till butik eller grossistlager</dd></div>
      <div class="rv"><dt>Ingen nätbutik</dt><dd>Vi konkurrerar inte med er</dd></div>
    </dl>
  </div>
</section>

<section class="b2b-res" id="resurser">
  <div class="wrap">
    <div class="b2b-start-head rv">
      <h2>Allt inköparen behöver.</h2>
      <p>Ladda ner direkt, utan inloggning.</p>
    </div>
    <div class="b2b-dl">
      <a class="rv" href="corder-produktdata.xlsx" download><span class="caps">Excel</span><b>Produktdata</b><small>{antal_rader} artiklar med EAN, modell, färg och bildlänk</small></a>
      <a class="rv" href="corder-produktdata.csv" download><span class="caps">CSV</span><b>Produktdata</b><small>Samma data för affärssystem och import</small></a>
      <a class="rv" href="corder-bildpaket.zip" download><span class="caps">ZIP</span><b>Bildpaket</b><small>{antal_bilder} frilagda produktbilder med transparent bakgrund</small></a>
      <a class="rv dark" href="#ansok"><span class="caps">Formulär</span><b>Prislista</b><small>Inköpspriser för butik och grossist, på begäran</small></a>
    </div>
    <div class="b2b-dl" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr))">
      <a class="rv" href="bestall/" data-h="bestall"><span class="caps">Säljer ni redan Corder?</span><b>Beställ påfyllning</b><small>Välj artiklar och antal efter EAN</small></a>
      <a class="rv" href="material/" data-h="material"><span class="caps">Utskrift</span><b>Säljmaterial</b><small>Skyltar med ert butiksnamn och era priser</small></a>
      <a class="rv" href="vip-mullsjo/"><span class="caps">Kundcase</span><b>VIP Mullsjö</b><small>Så säljs 20 000 produkter om året i en butik</small></a>
    </div>
  </div>
</section>

<section class="b2b-faq">
  <div class="wrap b2b-faq-grid">
    <h2 class="rv">Vanliga frågor.</h2>
    <div class="faq rv">{faq}</div>
  </div>
</section>

<section class="b2b-ansok" id="ansok">
  <div class="wrap b2b-ansok-grid">
    <div class="b2b-ansok-text rv">
      <h2>Vill ni sälja Corder?</h2>
      <p>Berätta lite om er butik eller kedja, så skickar vi prislista och ett förslag på startsortiment.</p>
      <p>Hellre mejl? Skriv till <a href="{MAILTO}">{MAIL}</a>.</p>
    </div>
    {ansokan()}
  </div>
</section>

</main>"""


SKRIPT = """<script>
(() => {
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rv = [...document.querySelectorAll('.rv')];
  if (still || !('IntersectionObserver' in window)) { rv.forEach(e => e.classList.add('in')); return; }
  document.documentElement.classList.add('anim');
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
  rv.forEach(e => io.observe(e));
  const n = document.querySelector('[data-count]');
  if (n) {
    // Siffran står kvar som 20 000 tills animationen faktiskt kör (bakgrundsflikar och sökmotorer ser rätt värde)
    const mal = +n.dataset.count, fmt = v => Math.round(v).toLocaleString('sv-SE');
    let t0 = null;
    const step = t => { t0 ??= t; const p = Math.min(1, (t - t0) / 1600); n.textContent = fmt(mal * (1 - Math.pow(1 - p, 4))); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  const v = document.querySelector('.b2b-film video');
  if (v) new IntersectionObserver(([e]) => e.isIntersecting ? v.play().catch(() => {}) : v.pause(), { threshold: .25 }).observe(v);
})();
</script>"""


FORM_SKRIPT = '<script src="/assets/f.js?v=1" defer></script>'
ANTAL_PER_DAG = round(20000 / 365)


def skriv(vag, html_):
    ut = UT / vag / "index.html"
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(html_, encoding="utf-8")
    print("skrev", ut.relative_to(ROT))


def bygg_bestall():
    url = f"{URL}bestall/"
    grupper = {}
    for artikel, kat, modell, farg, _, ean, _, _ in produktrader():
        grupper.setdefault(modell or kat, []).append((artikel, farg, ean))
    rader = []
    for grupp, artiklar in grupper.items():
        rader.append(f'<tr class="grupp"><th colspan="3" scope="colgroup">{grupp}</th></tr>')
        rader += [f"""<tr data-sok="{(artikel + " " + ean).lower()}"><th scope="row"><label for="a{ean}">{artikel}</label></th><td class="ean">{ean}</td><td><input id="a{ean}" type="number" min="0" max="100000" inputmode="numeric" data-ean="{ean}" data-artikel="{artikel}"></td></tr>""" for artikel, _, ean in artiklar]
    falt = f"""{GRUNDFALT}
      <label class="bred">Leveransadress<input name="leverans" maxlength="200" autocomplete="street-address"></label>
      <label class="bred">Meddelande<textarea name="meddelande" maxlength="2000"></textarea></label>"""
    innehall_ = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <div><nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><a href="/aterforsaljare/">Återförsäljare</a></nav><h1>Beställ påfyllning.</h1></div>
      <p>För er som redan säljer Corder. Beställningen blir bindande först när vi har bekräftat pris och leverans via e-post.</p>
    </div>
    <div class="best-sok">
      <label>Sök artikel eller EAN<input type="search" id="best-sok" autocomplete="off"></label>
      <div class="best-summa" role="status"><b id="best-antal">0</b> st valda</div>
    </div>
    <div class="best-tabell">
      <table>
        <thead><tr><th scope="col">Artikel</th><th scope="col" class="ean">EAN</th><th scope="col">Antal</th></tr></thead>
        <tbody>{"".join(rader)}</tbody>
      </table>
    </div>
    <div style="max-width:760px;padding-bottom:clamp(72px,9vw,128px)">
      {formular("bestallning", "Beställning", "Tack! Vi har tagit emot beställningen och bekräftar pris och leverans via e-post.", falt, "Skicka beställning")}
    </div>
  </div>
</main>"""
    skript = """<script>
(() => {
  const falt = [...document.querySelectorAll('input[data-ean]')];
  const summa = document.getElementById('best-antal');
  const rader = [...document.querySelectorAll('tr[data-sok]')];
  const grupper = [...document.querySelectorAll('tr.grupp')];
  document.addEventListener('input', e => {
    if (e.target.matches('input[data-ean]')) summa.textContent = falt.reduce((a, i) => a + Math.max(0, Math.floor(+i.value) || 0), 0);
    if (e.target.id !== 'best-sok') return;
    const q = e.target.value.trim().toLowerCase();
    rader.forEach(r => { r.hidden = !r.dataset.sok.includes(q); });
    grupper.forEach(g => {
      let n = g.nextElementSibling, syns = false;
      while (n && !n.classList.contains('grupp')) { syns ||= !n.hidden; n = n.nextElementSibling; }
      g.hidden = !syns;
    });
  });
})();
</script>"""
    skriv("bestall", sida("Beställ påfyllning för återförsäljare | Corder", "Beställ Corders kablar, laddare och skal efter artikel och EAN.", url, innehall_,
                          [brodsmulor(("Återförsäljare", URL), ("Beställ påfyllning", url))], skript=FORM_SKRIPT + skript, noindex=True))


def skylt(id_, rubrik, beskr, inne, klass=""):
    return f"""<article class="mat-post" id="{id_}">
        <h2>{rubrik}</h2>
        <p>{beskr}</p>
        <div class="skylt {klass}"><div class="skylt-inne">
          <div class="skylt-logo">corder</div>
          {inne}
          <div class="skylt-fot"><span data-butik></span><span>Designat i Sverige</span></div>
        </div></div>
        <button class="btn" type="button" data-skriv="{id_}">Skriv ut</button>
      </article>"""


def skyltbilder(*src):
    return '<div class="skylt-bild">' + "".join(bild(s, extra='decoding="async"') for s in src) + "</div>"


def bygg_material():
    url = f"{URL}material/"
    kabeltabell = """<table>
            <thead><tr><th scope="col">Din iPhone</th><th scope="col">Laddare med USB-C</th><th scope="col">Laddare med USB-A</th></tr></thead>
            <tbody>
              <tr><th scope="row">iPhone 15 och senare</th><td>USB-C till USB-C</td><td>USB-A till USB-C</td></tr>
              <tr><th scope="row">iPhone 14 och äldre</th><td>USB-C till Lightning</td><td>USB-A till Lightning</td></tr>
            </tbody>
          </table>"""
    skyltar = [
        skylt("kablar", "Kablar", "Till tunna eller hylla längs gångarna.",
              f'<h3>Laddkablar.</h3><p>Flätade och 2 meter. USB-C och Lightning.</p>{skyltbilder("/img/produkter/kabel-usb-c-usb-c-2m.webp", "/img/produkter/kabel-usb-c-lightning-svart.webp")}<div class="skylt-pris"><span data-pris="kabel">{PRIS["kabel"]}</span><small> kr</small></div>'),
        skylt("laddare", "Laddare", "Att ställa bredvid kablarna.",
              f'<h3>Snabbladdare.</h3><p>20W USB-C, 20W Dual Port och 18W USB-A.</p>{skyltbilder("/img/produkter/laddare-20w-usb-c.webp", "/img/produkter/laddare-20w-dual-port.webp")}<div class="skylt-pris"><span data-pris="laddare">{PRIS["laddare"]}</span><small> kr</small></div>', "tonad"),
        skylt("skal", "Skal", "Till stället eller skalhyllan.",
              f'<h3>Skal till din iPhone.</h3><p>TPU-skal till iPhone 14 hela vägen till iPhone 18 Pro. Fråga personalen om din modell.</p>{skyltbilder("/img/cut/17p-skogsgron.webp", "/img/cut/16p-pink.webp")}<div class="skylt-pris"><span data-pris="skal">{PRIS["skal"]}</span><small> kr</small></div>'),
        skylt("vilken-kabel", "Vilken kabel passar?", "Sparar frågor i kassan. Sätt den vid kablarna.",
              f'<h3>Vilken kabel passar?</h3><p>Hitta din iPhone och din laddare.</p>{kabeltabell}<p style="margin-top:auto">Alla kablar är 2 meter. Modellnamnet står under Inställningar, Allmänt, Om.</p>'),
        skylt("salj-har", "Här säljs Corder", "Till dörr, fönster eller disk.",
              f'<h3 style="margin-top:auto">Här finns Corder.</h3><p>Kablar, laddare och iPhone-skal när du behöver dem nu.</p>{skyltbilder("/img/cut/17p-skogsgron.webp", "/img/produkter/kabel-usb-c-usb-c-2m.webp")}', "morkgron"),
    ]
    innehall_ = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <div><nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><a href="/aterforsaljare/">Återförsäljare</a></nav><h1>Säljmaterial.</h1></div>
      <p>Skyltar i A4 att skriva ut. Lägg till ert butiksnamn och ändra till era priser. Inget sparas eller skickas.</p>
    </div>
    <form class="mat-val" onsubmit="return false">
      <label>Butikens namn<input id="mat-butik" maxlength="40" autocomplete="off"></label>
      <label>Pris kablar, kr<input data-prisval="kabel" type="number" min="0" max="9999" value="{PRIS["kabel"]}"></label>
      <label>Pris laddare, kr<input data-prisval="laddare" type="number" min="0" max="9999" value="{PRIS["laddare"]}"></label>
      <label>Pris skal, kr<input data-prisval="skal" type="number" min="0" max="9999" value="{PRIS["skal"]}"></label>
      <button class="btn mat-knapp" type="button" data-skriv="alla">Skriv ut alla</button>
    </form>
    <div class="mat-rutnat">
      {"".join(skyltar)}
    </div>
  </div>
</main>"""
    skript = """<script>
(() => {
  document.getElementById('mat-butik').addEventListener('input', e => {
    document.querySelectorAll('[data-butik]').forEach(s => { s.textContent = e.target.value; });
  });
  document.querySelectorAll('[data-prisval]').forEach(i => i.addEventListener('input', () => {
    document.querySelectorAll(`[data-pris="${i.dataset.prisval}"]`).forEach(s => { s.textContent = i.value; });
  }));
  document.addEventListener('click', e => {
    const k = e.target.closest('[data-skriv]');
    if (!k) return;
    const id = k.dataset.skriv;
    document.body.dataset.skriv = id;
    document.querySelectorAll('.mat-post').forEach(p => p.classList.toggle('skriv', p.id === id));
    window.corderH?.('material-utskrift', id);
    window.print();
  });
  addEventListener('afterprint', () => { delete document.body.dataset.skriv; });
})();
</script>"""
    skriv("material", sida("Säljmaterial för butiker | Corder", "Skyltar i A4 till butiker som säljer Corder, med eget butiksnamn och egna priser.", url, innehall_,
                           [brodsmulor(("Återförsäljare", URL), ("Säljmaterial", url))], skript=skript, noindex=True))


def bygg_case():
    url = f"{URL}vip-mullsjo/"
    beskr = "Så säljer VIP Mullsjö ungefär 20 000 Corder-produkter om året, främst laddkablar, från tunnor längs gångarna och ett eget ställ."
    innehall_ = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <div><nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><a href="/aterforsaljare/">Återförsäljare</a></nav><h1>VIP Mullsjö.</h1></div>
      <p>Så säljs ungefär 20 000 Corder-produkter om året i en enda butik.</p>
    </div>
    <div class="case-tal">
      <div><b>20 000</b><span>sålda produkter per år, ungefär</span></div>
      <div><b>ca {ANTAL_PER_DAG}</b><span>produkter per dag i snitt</span></div>
      <div><b>60 %</b><span>av försäljningen är kablar, ca 12 000 per år</span></div>
    </div>
    <div class="post" style="grid-template-columns:minmax(0, 760px)">
      <article class="prose">
        <p class="ingress">VIP Mullsjö säljer Corder där kunderna redan går: i tunnor längs gångarna och i ett eget ställ.</p>
        <h2>Tunnorna står för volymen</h2>
        <p>Den stora volymen kommer från tunnorna. Kunden behöver inte leta upp en tillbehörshylla, utan ser kablarna i förbifarten. Priset står på skylten, och 60 kr är lätt att plocka med när kabeln är glömd eller trasig.</p>
        <h2>Kablarna drar, resten följer med</h2>
        <p>Laddkablar står för ungefär 12 000 av de 20 000 produkterna. Skal och laddare står för ungefär 8 000. Därför börjar vi gärna med kablar i en ny butik och lägger till laddare bredvid. Skalen anpassas efter butikens kunder.</p>
        <h2>Så kan ni göra samma sak</h2>
        <ul>
          <li>Börja med ett <a href="/aterforsaljare/#ansok">startpaket</a>. Första paketet per butik har 90 dagars säljgaranti.</li>
          <li>Ställ produkterna längs gångarna, inte bara vid kassan.</li>
          <li>Skriv ut <a href="/aterforsaljare/material/">skyltar</a> med era priser och butiksnamn.</li>
        </ul>
        <h2>Bra att veta</h2>
        <p>VIP Mullsjö drivs av Corders medgrundare Anton Lindkvist, och siffrorna är ungefärliga. Resultatet i en annan butik beror på läge och kundflöde, så se dem som ett exempel på vad rätt exponering kan ge, inte som ett löfte.</p>
        <div class="cta">
          <div><h2>Vill ni testa i er butik?</h2><p>Berätta om butiken, så skickar vi prislista och förslag på startsortiment.</p></div>
          <div class="cta-knappar"><a class="btn" href="/aterforsaljare/#ansok">Få prislista</a></div>
        </div>
      </article>
    </div>
  </div>
</main>"""
    schema = [{"@context": "https://schema.org", "@type": "Article", "headline": "VIP Mullsjö: 20 000 sålda Corder-produkter om året", "description": beskr, "inLanguage": "sv", "mainEntityOfPage": url,
               "author": {"@type": "Organization", "name": "Corder"}, "publisher": {"@type": "Organization", "name": "Corder"}, "datePublished": "2026-11-02", "dateModified": "2026-11-02"},
              brodsmulor(("Återförsäljare", URL), ("VIP Mullsjö", url))]
    skriv("vip-mullsjo", sida("VIP Mullsjö: 20 000 sålda produkter om året | Corder", beskr, url, innehall_, schema))


def bygg_aterforsaljare():
    UT.mkdir(parents=True, exist_ok=True)
    rader = skriv_produktdata()
    bilder = skriv_bildpaket()
    titel = "Sälj Corder i din butik – för återförsäljare och grossister | Corder"
    beskr = ("Kablar, laddare och iPhone-skal som säljer i volym: ca 20 000 sålda per år i en enda butik, från eget ställ och tunnor längs gångarna. "
             "Ladda ner produktdata och bilder eller be om prislista och startsortiment.")
    schema = [
        {"@context": "https://schema.org", "@type": "WebPage", "@id": URL, "url": URL, "name": "Sälj Corder i din butik",
         "description": beskr, "inLanguage": "sv", "publisher": {"@id": f"{SITE}/#org"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Corder", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Återförsäljare", "item": URL}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    html_ = sida(titel, beskr, URL, innehall(rader, bilder), schema=schema, skript=FORM_SKRIPT + SKRIPT)
    (UT / "index.html").write_text(html_, encoding="utf-8")
    print(f"skrev aterforsaljare/ med {rader} artiklar och {bilder} bilder")
    bygg_bestall()
    bygg_material()
    bygg_case()


if __name__ == "__main__":
    bygg_aterforsaljare()
