"""Bygger /aterforsaljare/: sidan för butiker och grossister, produktdata (CSV och Excel) och bildpaket.

Inga priser publiceras här. Prislistan skickas på begäran från sales@corder.se.
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
from bygg_guider import ROT, SITE, liten, matt, sida  # noqa: E402

UT = ROT / "aterforsaljare"
URL = f"{SITE}/aterforsaljare/"
MAIL = "sales@corder.se"
AMNE = "Prislista och startsortiment"
TEXT = ("Hej!\n\nVi är intresserade av att sälja Corder.\n\nFöretag:\nAntal butiker:\nTyp av butik (kiosk, servicehandel, grossist ...):\n"
        "Kontaktperson och telefon:\n\nSkicka gärna prislista och förslag på startsortiment.\n")
MAILTO = f"mailto:{MAIL}?subject={quote(AMNE)}&body={quote(TEXT)}"

SKAL_EAN = {
    ("iPhone 14", "Svart"): "7350140690405", ("iPhone 14", "Blå"): "7350140690719", ("iPhone 14", "Lila"): "7350140690726", ("iPhone 14", "Persika"): "7350140690733",
    ("iPhone 14 Pro", "Svart"): "7350140690412", ("iPhone 14 Pro", "Blå"): "7350140690740", ("iPhone 14 Pro", "Lila"): "7350140690757", ("iPhone 14 Pro", "Persika"): "7350140690764",
    ("iPhone 15", "Svart"): "7350140690511", ("iPhone 15", "Blå"): "7350140690528", ("iPhone 15", "Lila"): "7350140690535", ("iPhone 15", "Persika"): "7350140690542",
    ("iPhone 15 Pro", "Svart"): "7350140690559", ("iPhone 15 Pro", "Blå"): "7350140690566", ("iPhone 15 Pro", "Lila"): "7350140690573", ("iPhone 15 Pro", "Persika"): "7350140690580",
    ("iPhone 16e", "Svart"): "7350140690672", ("iPhone 16e", "Blå"): "7350140690689", ("iPhone 16e", "Lila"): "7350140690696", ("iPhone 16e", "Persika"): "7350140690702",
    ("iPhone 16", "Svart"): "7350140690597", ("iPhone 16", "Blå"): "7350140690603", ("iPhone 16", "Lila"): "7350140690610", ("iPhone 16", "Persika"): "7350140690627",
    ("iPhone 16 Pro", "Svart"): "7350140690634", ("iPhone 16 Pro", "Blå"): "7350140690641", ("iPhone 16 Pro", "Lila"): "7350140690658", ("iPhone 16 Pro", "Persika"): "7350140690665",
    ("iPhone 17", "Svart"): "7350140690788", ("iPhone 17", "Skogsgrön"): "7350140690795",
    ("iPhone 17 Pro", "Svart"): "7350140690801", ("iPhone 17 Pro", "Skogsgrön"): "7350140690818",
    ("iPhone 18 Pro", "Svart"): "7350140690825", ("iPhone 18 Pro", "Skogsgrön"): "7350140690832",
}
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
LADDNING = [  # artikel, kategori, kontakt, EAN, bild
    ("Laddkabel USB-C till USB-C, 2 m, flätad", "Laddkabel", "USB-C / USB-C", "7350140690283", "kabel-usb-c-usb-c-2m"),
    ("Laddkabel USB-A till USB-C, 2 m, flätad", "Laddkabel", "USB-A / USB-C", "7350140690047", "kabel-usb-a-usb-c-2m"),
    ("Laddkabel USB-C till Lightning, 2 m, flätad, svart", "Laddkabel", "USB-C / Lightning", "7350140690467", "kabel-usb-c-lightning-svart"),
    ("Laddkabel USB-A till Lightning, 2 m, flätad", "Laddkabel", "USB-A / Lightning", "7350140690030", "kabel-usb-a-lightning-2m"),
    ("Snabbladdare 20W USB-C", "Snabbladdare", "USB-C, 20 W", "7350140690504", "laddare-20w-usb-c"),
    ("Snabbladdare 20W Dual Port", "Snabbladdare", "USB-C + USB-A, 20 W", "7350140690771", "laddare-20w-dual-port"),
    ("Snabbladdare 18W USB-A", "Snabbladdare", "USB-A, 18 W, QC 3.0", "7350140690078", "laddare-18w-usb-a"),
]
KOLUMNER = ["Artikel", "Kategori", "Modell", "Färg", "Material/typ", "EAN/GTIN-13", "Bild", "Produktsida"]


def produktrader():
    rader = []
    for modell, slug, pre, farger in SKAL_MODELLER:
        for f in farger:
            rader.append([f"TPU-skal {modell}, {f.lower()}", "Mobilskal", modell, f, "TPU, matt",
                          SKAL_EAN.get((modell, f), ""), f"{SITE}/img/cut/{pre}-{BILDFARG[f]}.webp", f"{SITE}/skal/{slug}/"])
    for namn, kat, typ, ean, b in LADDNING:
        rader.append([namn, kat, "", "", typ, ean, f"{SITE}/img/produkter/{b}.webp", f"{SITE}/#laddning"])
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
            z.write(f, f"corder-bildpaket/{f.parent.name}/{f.name}")
        z.writestr("corder-bildpaket/LASMIG.txt",
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
        <a class="btn" href="{MAILTO}">Få prislista och startsortiment</a>
        <a class="btn ghost" href="#resurser">Produktdata och bilder</a>
      </div>
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
      <a class="rv dark" href="{MAILTO}"><span class="caps">Mejl</span><b>Prislista</b><small>Inköpspriser för butik och grossist, på begäran</small></a>
    </div>
  </div>
</section>

<section class="b2b-faq">
  <div class="wrap b2b-faq-grid">
    <h2 class="rv">Vanliga frågor.</h2>
    <div class="faq rv">{faq}</div>
  </div>
</section>

<section class="b2b-end">
  <div class="wrap rv">
    <h2>Vill ni sälja Corder?</h2>
    <p>Berätta lite om er butik eller kedja, så skickar vi prislista och ett förslag på startsortiment.</p>
    <a class="btn" href="{MAILTO}">{MAIL}</a>
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
    html_ = sida(titel, beskr, URL, innehall(rader, bilder), schema=schema, skript=SKRIPT)
    (UT / "index.html").write_text(html_, encoding="utf-8")
    print(f"skrev aterforsaljare/ med {rader} artiklar och {bilder} bilder")


if __name__ == "__main__":
    bygg_aterforsaljare()
