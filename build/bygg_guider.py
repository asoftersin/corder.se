"""Bygger Corders guidesidor från innehall/<slug>.html.

Bara de tre guider som drar trafik enligt Search Console finns kvar, med samma URL
som på Shopify (/blogs/nyheter/<slug>/). Originalen från Shopify ligger orörda i
kalla/ som arkiv. Sajten byggs till ../docs/ (GitHub Pages). Kör från repots rot:

    python3 build/bygg_guider.py
"""
import html
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image

BYGG = Path(__file__).resolve().parent
ROT = BYGG.parent / "docs"
INNEHALL = BYGG / "innehall"
SITE = "https://corder.se"

GUIDER = [
    {
        "slug": "passar-iphone-17-pro-skal-till-iphone-18-pro",
        "omslag": {"bg": "#e9ece4", "bilder": ["/img/cut/17p-skogsgron.webp"]},
        "nyckel": [
            "iPhone 18 Pro har samma yttermått som 17 Pro.",
            "Kameraplatån är ungefär 0,1 mm tjockare.",
            "Skal med öppet kamerahål brukar passa.",
            "Tighta skal kan vara för trånga runt kameran.",
        ],
        "titel": "Passar iPhone 17 Pro-skal till iPhone 18 Pro? Så vet du",
        "kort": "Passar iPhone 17 Pro-skal till iPhone 18 Pro?",
        "kategori": "Mobilskal",
        "beskrivning": "Ofta, men inte alltid. iPhone 18 Pro har samma mått som 17 Pro men en lite tjockare kameraplatå. Här är vilka skal som passar och hur du testar.",
        "publicerad": "2026-10-25",
        "uppdaterad": "2026-10-25",
        "faq": [
            ("Passar iPhone 17 Pro-skal till iPhone 18 Pro?", "Ofta. Måtten är desamma, men kameraplatån på 18 Pro är ungefär en tiondels millimeter tjockare, så skal med tight passform runt kameran kan vara för trånga."),
            ("Säger Apple att skalen passar?", "Nej. Apple anger att iPhone 17 Pro och 18 Pro officiellt inte delar skal på grund av den tjockare kameraplatån."),
            ("Passar iPhone 18 Pro-skal på iPhone 17 Pro?", "Oftast ja. Skalet har lite mer utrymme runt kameran och sitter därför bra på 17 Pro."),
            ("Gäller samma sak för Pro Max?", "Ja. iPhone 18 Pro Max har samma mått som 17 Pro Max och samma lilla skillnad i kameraplatån."),
        ],
    },
    {
        "slug": "iphone-18-pro-vs-iphone-17-pro",
        "omslag": {"bg": "#2f3b33", "text": "18 Pro", "undertext": "vs 17 Pro"},
        "nyckel": [
            "Samma mått och skärmstorlek som 17 Pro.",
            "Ny huvudkamera med variabel bländare.",
            "A20 Pro-chip och snabbare laddning.",
            "Störst uppgradering för dig med 15 Pro eller äldre.",
        ],
        "titel": "iPhone 18 Pro vs iPhone 17 Pro: alla skillnader och ska du uppgradera?",
        "kort": "iPhone 18 Pro vs iPhone 17 Pro",
        "kategori": "iPhone",
        "beskrivning": "Kameran, chippet och laddningen är nya, utsidan är densamma. Här är skillnaderna mellan iPhone 18 Pro och 17 Pro och vem som har nytta av att uppgradera.",
        "publicerad": "2026-10-25",
        "uppdaterad": "2026-10-25",
        "faq": [
            ("Vad är skillnaden mellan iPhone 18 Pro och 17 Pro?", "iPhone 18 Pro har en huvudkamera med variabel bländare, det nya A20 Pro-chippet och snabbare laddning. Mått och skärmstorlek är desamma."),
            ("Lönar det sig att byta från iPhone 17 Pro?", "För de flesta inte efter bara ett år, om du inte fotograferar mycket. Från 15 Pro eller äldre är skillnaden tydlig."),
            ("Hur snabbt laddar iPhone 18 Pro?", "Enligt Apple når den 50 procent på cirka 15 minuter med kabel och en kraftfull USB-C-laddare."),
            ("Passar mitt gamla skal?", "Ofta, eftersom måtten är desamma, men kameraplatån är lite tjockare så tighta skal kan vara för trånga."),
        ],
    },
    {
        "slug": "iphone-duo-allt-du-behover-veta",
        "omslag": {"bg": "#1d1d1f", "text": "Duo", "undertext": "Vikbar iPhone"},
        "nyckel": [
            "Apples första vikbara iPhone, säljs sedan 23 oktober 2026.",
            "5,4 tums yttre och 7,6 tums inre skärm.",
            "Samma A20 Pro-chip som iPhone 18 Pro.",
            "Från 1 999 dollar i USA.",
        ],
        "titel": "iPhone Duo: Apples första vikbara iPhone – allt du behöver veta",
        "kort": "iPhone Duo: allt du behöver veta",
        "kategori": "iPhone",
        "beskrivning": "iPhone Duo är Apples första vikbara iPhone. Skärmar, kamera, chip, pris, laddning och vad du ska tänka på när det gäller skal till en vikbar telefon.",
        "publicerad": "2026-10-25",
        "uppdaterad": "2026-10-25",
        "faq": [
            ("Vad är iPhone Duo?", "Apples första vikbara iPhone. Hopfälld har den en 5,4 tums skärm och utfälld en 7,6 tums skärm."),
            ("När släpptes iPhone Duo?", "Den presenterades i september 2026 och började säljas den 23 oktober 2026."),
            ("Vad kostar iPhone Duo?", "Startpriset i USA är 1 999 dollar för 256 GB."),
            ("Vilket chip har iPhone Duo?", "A20 Pro, samma chip som iPhone 18 Pro."),
        ],
    },
    {
        "slug": "vilken-laddare-till-iphone-18-pro",
        "omslag": {"bg": "#e8e8e5", "bilder": ["/img/produkter/laddare-20w-usb-c.webp"]},
        "nyckel": [
            "Snabbast med USB-C-kabel och kraftfull laddare.",
            "MagSafe ger upp till 25 W trådlöst.",
            "En 20 W-laddare räcker för de flesta i vardagen.",
            "En kraftigare laddare skadar inte batteriet.",
        ],
        "titel": "Vilken laddare till iPhone 18 Pro? Watt, kabel och MagSafe förklarat",
        "kort": "Vilken laddare till iPhone 18 Pro?",
        "kategori": "Laddning",
        "beskrivning": "Räcker en 20 W-laddare till iPhone 18 Pro? Så snabbt laddar den med kabel och MagSafe, vad watt betyder och när en kraftigare laddare lönar sig.",
        "publicerad": "2026-10-25",
        "uppdaterad": "2026-10-25",
        "faq": [
            ("Räcker en 20 W-laddare till iPhone 18 Pro?", "Ja, för de flesta. Den snabbladdar telefonen, men når inte Apples allra snabbaste siffror som kräver en kraftigare laddare."),
            ("Hur snabbt laddar iPhone 18 Pro trådlöst?", "Upp till 25 W med MagSafe eller en Qi2-laddare som stöder 25 W."),
            ("Kan en kraftigare laddare skada batteriet?", "Nej. Telefonen tar bara emot så mycket ström som den klarar."),
            ("Vilken kabel behöver jag?", "En USB-C till USB-C-kabel tillsammans med en USB-C-laddare ger snabbladdning."),
        ],
    },
    {
        "slug": "vilken-usb-c-kabel-till-iphone",
        "omslag": {"bg": "#e3e6ea", "bilder": ["/img/produkter/kabel-usb-c-usb-c-2m.webp"]},
        "nyckel": [
            "iPhone 15 och senare har USB-C.",
            "iPhone 14 och äldre har Lightning.",
            "USB-C till USB-C ger snabbladdning på nya iPhones.",
            "Flätad kabel och 2 meter är bekvämt i vardagen.",
        ],
        "titel": "Vilken USB-C-kabel till iPhone? Så väljer du rätt kabel",
        "kort": "Vilken USB-C-kabel till iPhone?",
        "kategori": "Laddning",
        "beskrivning": "Vilken kabel passar din iPhone? USB-C eller Lightning, USB-A eller USB-C, och vad som skiljer en bra kabel från en dålig. Enkel guide för alla modeller.",
        "publicerad": "2026-10-25",
        "uppdaterad": "2026-10-25",
        "faq": [
            ("Vilka iPhones har USB-C?", "iPhone 15 och alla senare modeller, inklusive iPhone 18 Pro och iPhone Duo."),
            ("Vilken kabel ska jag ha till iPhone 14?", "iPhone 14 har Lightning, så du behöver en USB-C till Lightning- eller USB-A till Lightning-kabel."),
            ("Fungerar en Android-kabel till iPhone?", "Ja, om din iPhone har USB-C. USB-C är en gemensam standard."),
            ("Hur lång kabel ska jag välja?", "1 meter räcker vid skrivbordet. 2 meter gör att du når från väggen till sängen eller soffan."),
        ],
    },
    {
        "slug": "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd",
        "omslag": {"bg": "#e5eae6", "bilder": ["/img/cut/17p-skogsgron.webp"]},
        "nyckel": [
            "TPU är termoplastisk polyuretan, mellan gummi och hård plast.",
            "TPU dämpar stötar bra och töjer sig inte med tiden.",
            "Silikon är mjukare men drar åt sig ludd och kan bli glappt.",
            "Välj färgad TPU om skalet ska se nytt ut länge.",
        ],
        "titel": "Vad är ett TPU-skal? TPU vs silikon – vilket skyddar bäst?",
        "kort": "Vad är ett TPU-skal? TPU vs silikon",
        "kategori": "Mobilskal",
        "beskrivning": "TPU är det vanligaste materialet i mobilskal. Här är skillnaden mot silikon, om TPU-skal gulnar och hur du väljer ett skal som håller.",
        "publicerad": "2023-03-15",
        "uppdaterad": "2026-10-24",
        "faq": [
            ("Vad betyder TPU?", "TPU står för termoplastisk polyuretan, ett material mellan gummi och hård plast som är flexibelt men behåller formen."),
            ("Är TPU samma sak som silikon?", "Nej. Silikon är mjukare och mer gummiaktigt. TPU är fastare, töjer sig inte och drar inte åt sig ludd på samma sätt."),
            ("Skyddar TPU bättre än silikon?", "TPU dämpar stötar mycket bra och behåller passformen över tid, så för de flesta ger ett TPU-skal ett bättre och mer hållbart skydd."),
            ("Gulnar TPU-skal?", "Genomskinliga TPU-skal kan gulna med tiden av UV-ljus och hudfett. Färgade TPU-skal påverkas betydligt mindre."),
        ],
    },
    {
        "slug": "har-iphone-13-och-14-samma-skal-en-utforlig-guide",
        "omslag": {"bg": "#e3e8ef", "bilder": ["/img/cut/16-blue.webp", "/img/cut/16p-black.webp"]},
        "nyckel": [
            "iPhone 13-skal passar inte iPhone 14.",
            "iPhone 13 Pro-skal passar inte heller iPhone 14 Pro.",
            "Nästan varje generation kräver ett nytt skal.",
            "iPhone 17 Pro-skal passar ofta 18 Pro, men inte garanterat.",
        ],
        "titel": "Har iPhone 13 och 14 samma skal? Så vet du vilka skal som passar",
        "kort": "Har iPhone 13 och 14 samma skal?",
        "kategori": "Mobilskal",
        "beskrivning": "Nej, iPhone 13-skal passar inte iPhone 14. Här är skillnaderna, vad som gäller för Pro-modellerna och vilka skal som passar ända fram till iPhone 18 Pro.",
        "publicerad": "2023-11-14",
        "uppdaterad": "2026-10-24",
        "faq": [
            ("Passar iPhone 13-skal till iPhone 14?", "Nej. Telefonerna är lika höga och breda, men iPhone 14 är lite tjockare och har ett större kameraparti, så ett iPhone 13-skal sitter inte ordentligt."),
            ("Passar iPhone 14-skal till iPhone 13?", "Det går ofta att få på, men det glappar runt kameran och knapparna hamnar inte exakt rätt, så skyddet blir sämre."),
            ("Passar iPhone 13 Pro-skal till iPhone 14 Pro?", "Nej. Kamerapartiet på iPhone 14 Pro är både bredare och högre än på 13 Pro."),
            ("Passar iPhone 17 Pro-skal till iPhone 18 Pro?", "Ofta, eftersom yttermåtten är desamma. Kameraplatån på 18 Pro är dock något tjockare och Apple säger att modellerna inte officiellt delar skal, så tighta skal kan vara för trånga."),
        ],
    },
    {
        "slug": "basta-skarmskydd-till-iphone-2026-hardat-glas-bast-i-test",
        "omslag": {"bg": "#2d2c2f", "text": "9H", "undertext": "Härdat glas"},
        "nyckel": [
            "Härdat glas är det bästa valet för de flesta.",
            "Ceramic Shield tål sprickor men kan fortfarande repas.",
            "9H anger reptålighet, inte hur stora stötar glaset klarar.",
            "Köp alltid ett skydd märkt för din exakta modell.",
        ],
        "titel": "Bästa skärmskydd till iPhone 2026 – så väljer du rätt härdat glas",
        "kort": "Bästa skärmskydd till iPhone 2026",
        "kategori": "Skärmskydd",
        "beskrivning": "Vad gör ett skärmskydd bäst i test? Typer av härdat glas, vad 9H betyder, montering utan bubblor och vilka skydd som passar iPhone 13 till 18 Pro.",
        "publicerad": "2026-03-25",
        "uppdaterad": "2026-10-24",
        "faq": [
            ("Behöver man skärmskydd med Ceramic Shield?", "För de flesta ja. Ceramic Shield tål sprickor bättre, men glaset kan fortfarande repas av sand och småsten i fickan."),
            ("Vad betyder 9H på skärmskydd?", "9H är en hårdhet på blyertsskalan som visar hur väl ytan står emot repor. Det säger inget om hur stora stötar glaset tål."),
            ("Passar iPhone 17 Pro-skärmskydd till iPhone 18 Pro?", "Flera tillverkare uppger att skärmen har samma mått, men välj helst ett skydd som är märkt för iPhone 18 Pro."),
            ("Passar iPhone 15-skärmskydd till iPhone 16?", "Nej, iPhone 16 har andra mått. Köp ett skydd gjort för din exakta modell."),
        ],
    },
]

MANADER = ["januari", "februari", "mars", "april", "maj", "juni", "juli",
           "augusti", "september", "oktober", "november", "december"]


def svenskt_datum(iso):
    ar, man, dag = iso.split("-")
    return f"{int(dag)} {MANADER[int(man) - 1]} {ar}"


def ankare(text):
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    t = t.translate(str.maketrans("åäöé", "aaoe"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def lasminuter(*delar):
    ord_ = sum(len(re.sub(r"<[^>]+>", " ", d).split()) for d in delar)
    return max(1, math.ceil(ord_ / 200))


@lru_cache(maxsize=None)
def matt(src):
    """Bredd och höjd för en bild under docs/, så att webbläsaren kan reservera plats."""
    with Image.open(ROT / src.lstrip("/")) as im:
        return im.size


def liten(src, storlek="s"):
    """Mindre version av en produktbild (img/cut/s, img/cut/xs eller img/produkter/s)."""
    for mapp in ("/img/cut/", "/img/produkter/"):
        if src.startswith(mapp):
            return src.replace(mapp, f"{mapp}{'s' if mapp == '/img/produkter/' else storlek}/")
    return src


def bild(src, alt="", storlek="s", extra='loading="lazy"'):
    s = liten(src, storlek)
    w, h = matt(s)
    return f'<img src="{s}" alt="{html.escape(alt)}" width="{w}" height="{h}" {extra}>'


def omslag(o, klass=""):
    if "text" in o:
        inne = f'<div class="cover-text">{o["text"]}<small>{o["undertext"]}</small></div>'
    elif len(o["bilder"]) > 1:
        inne = '<div class="cover-pair">' + "".join(bild(b) for b in o["bilder"]) + "</div>"
    else:
        inne = bild(o["bilder"][0])
    return f'<div class="cover {klass}" style="--cover-bg:{o["bg"]}">{inne}</div>'


def meta(g):
    return (f'<div class="post-meta"><span>{g["kategori"]}</span>'
            f'<span>{g["minuter"]} min läsning</span>'
            f'<span>Uppdaterad {svenskt_datum(g["uppdaterad"])}</span></div>')


def kort(g, featured=False):
    return (f'<a class="card{" featured" if featured else ""}" href="/blogs/nyheter/{g["slug"]}/">'
            f'{omslag(g["omslag"])}<div>{meta(g)}<h3 style="margin-top:12px">{html.escape(g["kort"])}</h3>'
            f'<p style="margin-top:10px">{html.escape(g["beskrivning"])}</p></div></a>')


HEADER = """<header class="top">
  <div class="wrap">
    <a href="/" class="logo" aria-label="Corder startsida">corder</a>
    <button class="menu-btn" aria-expanded="false" aria-controls="meny" onclick="const o=this.closest('.top').classList.toggle('open');this.setAttribute('aria-expanded',o);this.querySelector('b').textContent=o?'Stäng':'Meny';document.body.style.overflow=o?'hidden':''"><span></span><b>Meny</b></button>
    <ul id="meny">
      <li><a href="/skal/">Skal</a></li>
      <li><a href="/#laddning">Laddning</a></li>
      <li><a href="/#butiker">Butiker</a></li>
      <li><a href="/aterforsaljare/">Återförsäljare</a></li>
      <li><a href="/blogs/nyheter/">Apple-guider</a></li>
    </ul>
  </div>
  {progress}
</header>"""

FOOTER = """<footer>
  <div class="wrap">
    <div class="foot">
      <a href="/" class="logo">corder</a>
      <div><p class="foot-h">Sortiment</p><ul><li><a href="/skal/">TPU-skal</a></li><li><a href="/#laddning">Laddare</a></li><li><a href="/#laddning">Kablar</a></li></ul></div>
      <div><p class="foot-h">Företag</p><ul><li><a href="/#butiker">Hitta butik</a></li><li><a href="/aterforsaljare/">Bli återförsäljare</a></li><li><a href="mailto:sales@corder.se">sales@corder.se</a></li></ul></div>
      <div><p class="foot-h">Resurser</p><ul><li><a href="/blogs/nyheter/">Apple-guider</a></li><li><a href="https://www.instagram.com/corderofficial">Instagram</a></li><li><a href="https://www.tiktok.com/@corderofficial">TikTok</a></li><li><a href="https://www.facebook.com/cordergroup">Facebook</a></li></ul></div>
    </div>
    <div class="foot-base">© 2026 Corder Group AB · Org.nr 559227-0226 · Kungsbacka · Designed and developed in Sweden</div>
  </div>
</footer>"""

CTA = """<div class="cta">
        <div>
          <h2>Corders TPU-skal</h2>
          <p>Till iPhone 14 hela vägen till iPhone 18 Pro. Finns hos Go Banana i Jönköping och VIP Mullsjö.</p>
        </div>
        <a class="btn" href="/#butiker">Hitta butik</a>
      </div>"""

# Läsframsteg och markering av aktuellt avsnitt i innehållsförteckningen.
SKRIPT = """<script>
(() => {
  const art = document.querySelector('.prose');
  const links = [...document.querySelectorAll('.toc a')];
  const heads = links.map(a => document.getElementById(a.hash.slice(1)));
  const top = document.querySelector('.top');
  const tick = () => {
    const r = art.getBoundingClientRect();
    const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
    top.style.setProperty('--read-p', p.toFixed(3));
    let cur = 0;
    heads.forEach((h, i) => { if (h.getBoundingClientRect().top < 140) cur = i; });
    links.forEach((a, i) => a.classList.toggle('on', i === cur));
  };
  addEventListener('scroll', tick, { passive: true });
  addEventListener('resize', tick);
  tick();
})();
</script>"""


def sida(titel, beskr, kanonisk, innehall, schema=None, progress=False, skript=""):
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>\n'
                 for s in (schema or []))
    head = HEADER.replace("{progress}", '<div class="progress" aria-hidden="true"></div>' if progress else "")
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<meta name="description" content="{html.escape(beskr)}">
<link rel="canonical" href="{kanonisk}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(titel)}">
<meta property="og:description" content="{html.escape(beskr)}">
<meta property="og:url" content="{kanonisk}">
<meta property="og:site_name" content="Corder">
<meta property="og:locale" content="sv_SE">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/inter-tight-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/sida.css?v=13">
{ld}</head>
<body>
<a class="skip" href="#innehall">Hoppa till innehållet</a>

{head}

{innehall}

{FOOTER}
{skript}
</body>
</html>
"""


def bygg():
    for g in GUIDER:
        body = (INNEHALL / f'{g["slug"]}.html').read_text().strip()
        avsnitt = []

        def satt_id(m):
            rubrik = m.group(1)
            avsnitt.append((ankare(rubrik), rubrik))
            return f'<h2 id="{ankare(rubrik)}">{rubrik}</h2>'
        body = re.sub(r"<h2>(.*?)</h2>", satt_id, body)
        avsnitt.append(("vanliga-fragor", "Vanliga frågor"))
        faq = "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>"
                        for q, a in g["faq"])
        g["minuter"] = lasminuter(body, faq)
        g["_body"], g["_avsnitt"], g["_faq"] = body, avsnitt, faq

    for g in GUIDER:
        url = f'{SITE}/blogs/nyheter/{g["slug"]}/'
        schema = [
            {"@context": "https://schema.org", "@type": "Article",
             "headline": g["titel"], "description": g["beskrivning"],
             "datePublished": g["publicerad"], "dateModified": g["uppdaterad"],
             "inLanguage": "sv", "mainEntityOfPage": url,
             "author": {"@type": "Organization", "name": "Corder"},
             "publisher": {"@type": "Organization", "name": "Corder"}},
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Corder", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Apple-guider", "item": SITE + "/blogs/nyheter/"},
                {"@type": "ListItem", "position": 3, "name": g["kort"], "item": url}]},
        ]
        toc = "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in g["_avsnitt"])
        nyckel = "".join(f"<li>{html.escape(k)}</li>" for k in g["nyckel"])
        andra = sorted((o for o in GUIDER if o is not g), key=lambda o: o["kategori"] != g["kategori"])[:3]
        ovriga = "\n      ".join(kort(o) for o in andra)
        ingress, resten = g["_body"].split("</p>", 1)
        ingress += "</p>"
        innehall = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="post-head">
      <nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><a href="/blogs/nyheter/">Apple-guider</a></nav>
      <span class="tag">{g["kategori"]}</span>
      <h1>{html.escape(g["titel"])}</h1>
      <div class="post-meta"><span>Corder</span><span>{g["minuter"]} min läsning</span><span>Uppdaterad {svenskt_datum(g["uppdaterad"])}</span></div>
    </div>
    {omslag(g["omslag"], "post-cover")}
    <div class="post">
      <nav class="toc" aria-label="Innehåll"><span class="caps">Innehåll</span><ol>{toc}</ol></nav>
      <article class="prose">
        <details class="toc-mobile"><summary>Innehåll</summary><ol>{toc}</ol></details>
{ingress}
        <div class="keys"><span class="caps">I korthet</span><ul>{nyckel}</ul></div>
{resten}
        <h2 id="vanliga-fragor">Vanliga frågor</h2>
        <div class="faq">
{g["_faq"]}
        </div>
        {CTA}
      </article>
    </div>
  </div>
  <section class="related">
    <div class="wrap">
      <h2>Fler guider</h2>
      <div class="cards">
      {ovriga}
      </div>
    </div>
  </section>
</main>"""
        ut = ROT / "blogs" / "nyheter" / g["slug"] / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(sida(f'{g["titel"]} | Corder', g["beskrivning"], url, innehall, schema,
                           progress=True, skript=SKRIPT))
        print("skrev", ut.relative_to(ROT))

    forsta, *resten = GUIDER
    index = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <h1>Apple-guider.</h1>
      <p>Raka svar om skal, material och vilka tillbehör som passar vilken iPhone.</p>
    </div>
    <div class="index-body cards">
      {kort(forsta, featured=True)}
      {"".join(kort(g) for g in resten)}
    </div>
  </div>
</main>"""
    ut = ROT / "blogs" / "nyheter" / "index.html"
    ut.write_text(sida("Apple-guider | Corder", "Raka svar om TPU-skal, skärmskydd och vilka skal som passar vilken iPhone, från Corder.",
                       f"{SITE}/blogs/nyheter/", index))
    print("skrev", ut.relative_to(ROT))



# --- Modellsidor: ett TPU-skal per iPhone-modell -------------------------------------

FARG = {"Svart": ("#1c1c1c", "black"), "Blå": ("#4a6684", "blue"), "Lila": ("#b9bdf0", "purple"),
        "Persika": ("#f5a493", "pink"), "Skogsgrön": ("#3d5143", None)}
GAMLA_FARGER = ["Svart", "Blå", "Lila", "Persika"]
NYA_FARGER = ["Svart", "Skogsgrön"]

MODELLER = [
    {"slug": "iphone-18-pro", "namn": "iPhone 18 Pro", "bild": None, "gron": True, "extra": {"Svart": "/img/cut/17p-black.webp"}, "farger": NYA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 17 Pro-skal till iPhone 18 Pro?", "Ofta, eftersom måtten är desamma. Kameraplatån på 18 Pro är dock ungefär en tiondels millimeter tjockare, så tighta skal kan vara för trånga."),
                ("Passar skalet till iPhone 18 Pro Max?", "Nej. Pro Max har större skärm och större mått och behöver ett eget skal."),
                ("Passar skalet till iPhone Duo?", "Nej. iPhone Duo är vikbar och behöver ett helt annat skal. Corder har inte skal till Duo.")],
     "guider": ["passar-iphone-17-pro-skal-till-iphone-18-pro", "iphone-18-pro-vs-iphone-17-pro", "vilken-laddare-till-iphone-18-pro"]},
    {"slug": "iphone-17-pro", "namn": "iPhone 17 Pro", "bild": None, "gron": True, "extra": {"Svart": "/img/cut/17p-black.webp"}, "farger": NYA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar skalet till iPhone 18 Pro?", "Ofta, eftersom måtten är desamma, men kameraplatån på 18 Pro är något tjockare. Apple anger att modellerna officiellt inte delar skal."),
                ("Passar iPhone 16 Pro-skal till iPhone 17 Pro?", "Nej. iPhone 17 Pro har en helt ny design med en bred kameraplatå."),
                ("Passar skalet till iPhone 17?", "Nej. iPhone 17 har en annan form och ett annat kameraparti än 17 Pro.")],
     "guider": ["passar-iphone-17-pro-skal-till-iphone-18-pro", "iphone-18-pro-vs-iphone-17-pro", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-17", "namn": "iPhone 17", "bild": None, "gron": False, "extra": {"Svart": "/img/cut/17-black.webp", "Skogsgrön": "/img/cut/17-skogsgron.webp"}, "farger": NYA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 16-skal till iPhone 17?", "Nej. iPhone 17 är något större och har ett nytt kameraparti."),
                ("Passar skalet till iPhone 17 Pro?", "Nej. Pro-modellen har en annan form och en bred kameraplatå."),
                ("Finns det en vanlig iPhone 18?", "Apple väntas släppa vanliga iPhone 18 under våren 2027. Hur skalen passar vet vi först då.")],
     "guider": ["vilken-usb-c-kabel-till-iphone", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "har-iphone-13-och-14-samma-skal-en-utforlig-guide"]},
    {"slug": "iphone-16-pro", "namn": "iPhone 16 Pro", "bild": "16p", "farger": GAMLA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar skalet till iPhone 17 Pro?", "Nej. iPhone 17 Pro har en helt ny design med en bred kameraplatå."),
                ("Passar iPhone 15 Pro-skal till iPhone 16 Pro?", "Nej. iPhone 16 Pro är större och har dessutom en kameraknapp på sidan."),
                ("Passar skalet till iPhone 16?", "Nej. iPhone 16 har en annan storlek och ett annat kameraparti.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-16", "namn": "iPhone 16", "bild": "16", "farger": GAMLA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 15-skal till iPhone 16?", "Nej. iPhone 16 har en ny kameraplacering och en kameraknapp på sidan."),
                ("Passar skalet till iPhone 17?", "Nej. iPhone 17 är något större och har ett nytt kameraparti."),
                ("Passar skalet till iPhone 16e?", "Nej. iPhone 16e har en kamera och en egen form.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-16e", "namn": "iPhone 16e", "bild": "16e", "farger": GAMLA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 16-skal till iPhone 16e?", "Nej. iPhone 16e har bara en kamera och en egen form, så skalet behöver vara gjort för just 16e."),
                ("Hur ser jag att jag har en iPhone 16e?", "16e har en enda kamera på baksidan. Du kan också se modellnamnet under Inställningar, Allmänt, Om."),
                ("Vilken kabel behöver iPhone 16e?", "iPhone 16e har USB-C, så en USB-C till USB-C-kabel ger snabbladdning.")],
     "guider": ["silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone", "har-iphone-13-och-14-samma-skal-en-utforlig-guide"]},
    {"slug": "iphone-15-pro", "namn": "iPhone 15 Pro", "bild": "15p", "farger": GAMLA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar skalet till iPhone 16 Pro?", "Nej. iPhone 16 Pro är större och har en kameraknapp på sidan."),
                ("Passar iPhone 14 Pro-skal till iPhone 15 Pro?", "Nej. iPhone 15 Pro har andra mått."),
                ("Passar skalet till iPhone 15?", "Nej. iPhone 15 har ett annat kameraparti än Pro-modellen.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-15", "namn": "iPhone 15", "bild": "15", "farger": GAMLA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 14-skal till iPhone 15?", "Nej. iPhone 15 har andra mått."),
                ("Passar skalet till iPhone 16?", "Nej. iPhone 16 har en ny kameraplacering och en kameraknapp på sidan."),
                ("Passar skalet till iPhone 15 Pro?", "Nej. Pro-modellen har ett annat kameraparti.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-14-pro", "namn": "iPhone 14 Pro", "bild": "14p", "farger": GAMLA_FARGER, "kontakt": "Lightning",
     "kompat": [("Passar iPhone 13 Pro-skal till iPhone 14 Pro?", "Nej. Kamerapartiet på iPhone 14 Pro är både bredare och högre."),
                ("Passar skalet till iPhone 15 Pro?", "Nej. iPhone 15 Pro har andra mått."),
                ("Passar skalet till iPhone 14?", "Nej. iPhone 14 har ett annat kameraparti än Pro-modellen.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
    {"slug": "iphone-14", "namn": "iPhone 14", "bild": "14", "farger": GAMLA_FARGER, "kontakt": "Lightning",
     "kompat": [("Passar iPhone 13-skal till iPhone 14?", "Nej. iPhone 14 är lite tjockare och har ett större kameraparti."),
                ("Passar skalet till iPhone 15?", "Nej. iPhone 15 har andra mått."),
                ("Passar skalet till iPhone 14 Pro?", "Nej. Pro-modellen har ett annat kameraparti.")],
     "guider": ["har-iphone-13-och-14-samma-skal-en-utforlig-guide", "silikon-vs-tpu-vilket-mobilskal-ger-bast-skydd", "vilken-usb-c-kabel-till-iphone"]},
]


def modellbild(m, farg):
    if farg in m.get("extra", {}):
        return m["extra"][farg]
    if m.get("bild") and FARG[farg][1]:
        return f'/img/cut/{m["bild"]}-{FARG[farg][1]}.webp'
    if m.get("gron") and farg == "Skogsgrön":
        return "/img/cut/17p-skogsgron.webp"
    return None


def tumme(m):
    for f in m["farger"]:
        if modellbild(m, f):
            return modellbild(m, f)
    return None


def modell_lank(m):
    b = tumme(m)
    tum = bild(b, storlek="xs") if b else '<span class="nopic"></span>'
    return (f'<a class="model-link" href="/skal/{m["slug"]}/">{tum}<span><b>{m["namn"]}</b>'
            f'<small>{", ".join(m["farger"])}</small></span></a>')


def bygg_skal():
    guide_per_slug = {g["slug"]: g for g in GUIDER}
    for m in MODELLER:
        url = f'{SITE}/skal/{m["slug"]}/'
        farger = " och ".join([", ".join(m["farger"][:-1]), m["farger"][-1]]) if len(m["farger"]) > 1 else m["farger"][0]
        titel = f'Skal till {m["namn"]} – TPU-skal i {farger.lower()} | Corder'
        beskr = (f'Corders TPU-skal till {m["namn"]} finns i {farger.lower()}. Formstabilt och stötdämpande. '
                 f'Se färgerna, vilka skal som passar och var du hittar Corder i butik.')
        swatches = "".join(f'<span class="swatch"><i style="background:{FARG[f][0]}"></i>{f}</span>' for f in m["farger"])
        shots = []
        for f in m["farger"]:
            b = modellbild(m, f)
            if b:
                alt = f'Corder TPU-skal till {m["namn"]} i {f.lower()}'
                shots.append(f'<figure class="model-shot"><div class="tile">{bild(b, alt)}</div>'
                             f'<figcaption><i style="background:{FARG[f][0]}"></i>{f}</figcaption></figure>')
            else:
                shots.append(f'<figure class="model-shot"><div class="tile empty"><div><b style="background:{FARG[f][0]}"></b>{f}</div></div>'
                             f'<figcaption><i style="background:{FARG[f][0]}"></i>{f}</figcaption></figure>')
        kabel = ("USB-C till Lightning eller USB-A till Lightning" if m["kontakt"] == "Lightning" else "USB-C till USB-C")
        specs = [("Material", "TPU (termoplastisk polyuretan)"), ("Passar", f'{m["namn"]}'), ("Färger", ", ".join(m["farger"])),
                 ("Egenskaper", "Stötdämpande, formstabilt, upphöjd kant runt kameran"), ("Laddning", f'Telefonen har {m["kontakt"]}. Rätt kabel: {kabel}, 2 m.'),
                 ("Finns hos", "Go Banana i Jönköping och VIP Mullsjö")]
        specs_html = "".join(f"<div><dt>{a}</dt><dd>{html.escape(b)}</dd></div>" for a, b in specs)
        faq = [("Vilka färger finns skalet till " + m["namn"] + " i?", f"Skalet finns i {farger.lower()}."),
               ("Vilket material är skalet gjort av?", "TPU, termoplastisk polyuretan. Det dämpar stötar och behåller formen utan att töja sig.")] + m["kompat"] + \
              [("Var kan jag köpa skalet?", "Corders skal finns hos Go Banana i Jönköping och VIP Mullsjö. Butiker som vill sälja Corder kan kontakta sales@corder.se.")]
        faq_html = "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in faq)
        andra = "\n        ".join(modell_lank(o) for o in MODELLER if o is not m)
        guidekort = "\n      ".join(kort(guide_per_slug[s]) for s in m["guider"] if s in guide_per_slug)
        bilder = [SITE + modellbild(m, f) for f in m["farger"] if modellbild(m, f)]
        schema = [
            {"@context": "https://schema.org", "@type": "Product", "name": f'Corder TPU-skal till {m["namn"]}',
             "brand": {"@type": "Brand", "name": "Corder"}, "material": "TPU", "color": ", ".join(m["farger"]),
             "description": beskr, "url": url, **({"image": bilder} if bilder else {}),
             "manufacturer": {"@type": "Organization", "name": "Corder Group AB"}},
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Corder", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Skal", "item": SITE + "/skal/"},
                {"@type": "ListItem", "position": 3, "name": m["namn"], "item": url}]},
        ]
        innehall = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="model-head">
      <div>
        <nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><a href="/skal/">Skal</a></nav>
        <span class="tag">TPU-skal</span>
        <h1>Skal till {m["namn"]}</h1>
        <div class="swatches">{swatches}</div>
      </div>
      <p>Corders TPU-skal till {m["namn"]} finns i {farger.lower()}. Samma enkla form som alla våra skal: stötdämpande, formstabilt och med upphöjd kant runt kameran.</p>
    </div>
    <div class="model-gallery{" few" if len(m["farger"]) <= 2 else ""}" style="--n:{len(m["farger"])}">
      {"".join(shots)}
    </div>
    <div class="post" style="grid-template-columns:minmax(0, 760px)">
      <article class="prose">
        <h2 id="om-skalet" style="margin-top:0">Om skalet</h2>
        <dl class="specs-list">{specs_html}</dl>
        <h2 id="vanliga-fragor">Vanliga frågor om skal till {m["namn"]}</h2>
        <div class="faq">
{faq_html}
        </div>
        {CTA}
        <h2>Andra modeller</h2>
        <div class="model-grid">
        {andra}
        </div>
      </article>
    </div>
  </div>
  <section class="related">
    <div class="wrap">
      <h2>Läs mer</h2>
      <div class="cards">
      {guidekort}
      </div>
    </div>
  </section>
</main>"""
        ut = ROT / "skal" / m["slug"] / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(sida(titel, beskr, url, innehall, schema))
        print("skrev", ut.relative_to(ROT))

    lankar = "\n      ".join(modell_lank(m) for m in MODELLER)
    index = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <h1>Skal till iPhone.</h1>
      <p>TPU-skal från iPhone 14 hela vägen till iPhone 18 Pro. Välj din modell för att se färger och vad som passar.</p>
    </div>
    <div class="model-grid" style="padding-bottom:clamp(48px,6vw,80px)">
      {lankar}
    </div>
    <div style="padding-bottom:clamp(72px,9vw,128px)">{CTA}</div>
  </div>
</main>"""
    ut = ROT / "skal" / "index.html"
    ut.write_text(sida("Skal till iPhone 14–18 Pro | Corder", "Corders TPU-skal till iPhone 14, 15, 16, 17 och 18 Pro. Välj din modell och se färger, kompatibilitet och var du hittar skalen i butik.",
                       f"{SITE}/skal/", index))
    print("skrev skal/index.html")



def bygg_valjare():
    """Skriver modelldata till startsidans verktyg 'Vilket skal passar din iPhone?'."""
    data = []
    for m in MODELLER:
        data.append({
            "slug": m["slug"], "namn": m["namn"], "kontakt": m["kontakt"],
            "kabel": "USB-C till Lightning eller USB-A till Lightning" if m["kontakt"] == "Lightning" else "USB-C till USB-C",
            "farger": [{"namn": f, "hex": FARG[f][0], "bild": liten(modellbild(m, f)) if modellbild(m, f) else None} for f in m["farger"]],
            "tips": {"q": m["kompat"][0][0], "a": m["kompat"][0][1]},
        })
    sida_ = ROT / "index.html"
    t = sida_.read_text()
    start = t.index('<script id="modeller" type="application/json">') + len('<script id="modeller" type="application/json">')
    slut = t.index("</script>", start)
    sida_.write_text(t[:start] + json.dumps(data, ensure_ascii=False) + t[slut:])
    print("skrev modelldata till index.html")

def bygg_404():
    innehall = """<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head" style="padding-bottom:clamp(24px,4vw,40px)">
      <h1>Sidan finns inte.</h1>
      <p>Länken kan vara gammal. Corder har bytt webbplats och webbshoppen är stängd.</p>
    </div>
    <div class="cards" style="padding-bottom:clamp(72px,9vw,128px)">
      <a class="card" href="/"><div><span class="tag">Start</span><h3 style="margin-top:14px">Till startsidan</h3><p style="margin-top:8px">TPU-skal, laddare och kablar för iPhone.</p></div></a>
      <a class="card" href="/#butiker"><div><span class="tag">Butiker</span><h3 style="margin-top:14px">Hitta Corder i butik</h3><p style="margin-top:8px">Go Banana i Jönköping och VIP Mullsjö.</p></div></a>
      <a class="card" href="/blogs/nyheter/"><div><span class="tag">Guider</span><h3 style="margin-top:14px">Apple-guider</h3><p style="margin-top:8px">Raka svar om skal och vilka som passar vilken iPhone.</p></div></a>
    </div>
  </div>
</main>"""
    fanga = """<script>
(() => {
  const p = location.pathname;
  const mal = p.startsWith('/collections') || p.startsWith('/products') ? '/#sortiment'
    : p.startsWith('/blogs/') ? '/blogs/nyheter/' : p.startsWith('/pages/') ? '/' : null;
  if (mal) location.replace(mal);
})();
</script>"""
    html_ = sida("Sidan finns inte | Corder", "Sidan du letade efter finns inte längre.", f"{SITE}/", innehall, skript=fanga)
    (ROT / "404.html").write_text(html_.replace('<link rel="canonical" href="https://corder.se/">\n', ''))
    print("skrev 404.html")


# Gamla Shopify-adresser. GitHub Pages saknar serverredirects, så varje adress får en
# liten sida som skickar vidare direkt. 404-sidan fångar resten med samma regler.
GAMLA_PRODUKTER = ["skarmskydd-iphone-14-13-13-pro", "laddkabel-usb-c-till-lightning", "laddningskabel-iphone",
                   "laddningskabel-usb-c", "laddkabel-usb-c", "stromadapter-20w-double-port", "stromadapter-20w-usb-c",
                   "stromadapter-snabbladdning-18w", "silikonskal-iphone-14", "silikonskal-iphone-14-pro",
                   "silikonskal-iphone-15", "silikonskal-iphone-15-pro", "silikonskal-iphone-16",
                   "silikonskal-iphone-16-pro", "silikonskal-iphone-16e"]
GAMLA_KOLLEKTIONER = ["kablar", "mobilskal", "skarmskydd", "laddare", "bastsaljare", "airpods-skal",
                      "nyheter-2", "sommarkollektion-2022", "all", "frontpage"]
GAMLA_SIDOR = {"pages/om-oss": "/#om-oss", "pages/contact": "/#butiker", "pages/vanliga-fragor-faq": "/",
               "cart": "/", "account": "/", "account/login": "/", "search": "/", "collections": "/#sortiment",
               "products": "/#sortiment"}


def gamla_guider():
    behall = {g["slug"] for g in GUIDER}
    flode = (BYGG / "kalla" / "atom-1.xml").read_text()
    slugs = re.findall(r'href="https://corder\.se/blogs/nyheter/([^"]+)"', flode)
    return [s for s in dict.fromkeys(slugs) if s not in behall]


def omdirigering(mal):
    return f"""<!DOCTYPE html>
<html lang="sv"><head><meta charset="utf-8">
<title>Corder</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{SITE}{mal}">
<meta http-equiv="refresh" content="0; url={mal}">
<script>location.replace("{mal}")</script>
</head><body><p>Sidan har flyttat. <a href="{mal}">Fortsätt till Corder</a>.</p></body></html>
"""


def bygg_omdirigeringar():
    mal = dict(GAMLA_SIDOR)
    def produktmal(handle):
        if handle.startswith("silikonskal-iphone-"):
            return "/skal/iphone-" + handle.removeprefix("silikonskal-iphone-") + "/"
        if handle.startswith(("laddkabel", "laddningskabel", "stromadapter")):
            return "/#laddning"
        return "/#sortiment"
    mal.update({f"products/{p}": produktmal(p) for p in GAMLA_PRODUKTER})
    mal.update({f"collections/{k}": "/#sortiment" for k in GAMLA_KOLLEKTIONER})
    mal.update({"collections/mobilskal": "/skal/", "collections/kablar": "/#laddning", "collections/laddare": "/#laddning",
                "collections": "/skal/", "products": "/skal/"})
    mal.update({f"blogs/nyheter/{s}": "/blogs/nyheter/" for s in gamla_guider()})
    for vag, till in mal.items():
        ut = ROT / vag / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(omdirigering(till))
    print(f"skrev {len(mal)} omdirigeringar")


if __name__ == "__main__":
    from bygg_aterforsaljare import bygg_aterforsaljare
    bygg()
    bygg_skal()
    bygg_valjare()
    bygg_404()
    bygg_omdirigeringar()
    bygg_aterforsaljare()
