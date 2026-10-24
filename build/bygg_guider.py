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
from pathlib import Path

BYGG = Path(__file__).resolve().parent
ROT = BYGG.parent / "docs"
INNEHALL = BYGG / "innehall"
SITE = "https://corder.se"

GUIDER = [
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


def omslag(o, klass=""):
    if "text" in o:
        inne = f'<div class="cover-text">{o["text"]}<small>{o["undertext"]}</small></div>'
    elif len(o["bilder"]) > 1:
        inne = '<div class="cover-pair">' + "".join(f'<img src="{b}" alt="" loading="lazy">' for b in o["bilder"]) + "</div>"
    else:
        inne = f'<img src="{o["bilder"][0]}" alt="" loading="lazy">'
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
    <ul>
      <li><a href="/#sortiment">Sortiment</a></li>
      <li><a href="/#butiker">Butiker</a></li>
      <li><a href="/#aterforsaljare">Företag</a></li>
      <li><a href="/blogs/nyheter/" aria-current="page">Apple-guider</a></li>
    </ul>
  </div>
  {progress}
</header>"""

FOOTER = """<footer>
  <div class="wrap">
    <div class="foot">
      <a href="/" class="logo">corder</a>
      <div><h4>Sortiment</h4><ul><li><a href="/#sortiment">TPU-skal</a></li><li><a href="/#sortiment">Laddare</a></li><li><a href="/#sortiment">Kablar</a></li></ul></div>
      <div><h4>Företag</h4><ul><li><a href="/#butiker">Hitta butik</a></li><li><a href="/#aterforsaljare">Bli återförsäljare</a></li><li><a href="mailto:sales@corder.se">sales@corder.se</a></li></ul></div>
      <div><h4>Resurser</h4><ul><li><a href="/blogs/nyheter/">Apple-guider</a></li><li><a href="https://www.instagram.com/corderofficial">Instagram</a></li><li><a href="https://www.tiktok.com/@corderofficial">TikTok</a></li><li><a href="https://www.facebook.com/cordergroup">Facebook</a></li></ul></div>
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
<link rel="stylesheet" href="/assets/sida.css?v=5">
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
        ovriga = "\n      ".join(kort(o) for o in GUIDER if o is not g)
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
    mal.update({f"products/{p}": "/#sortiment" for p in GAMLA_PRODUKTER})
    mal.update({f"collections/{k}": "/#sortiment" for k in GAMLA_KOLLEKTIONER})
    mal.update({f"blogs/nyheter/{s}": "/blogs/nyheter/" for s in gamla_guider()})
    for vag, till in mal.items():
        ut = ROT / vag / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(omdirigering(till))
    print(f"skrev {len(mal)} omdirigeringar")


if __name__ == "__main__":
    bygg()
    bygg_404()
    bygg_omdirigeringar()
