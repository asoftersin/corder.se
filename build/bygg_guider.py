"""Bygger Corders guidesidor från innehall/<slug>.html.

Guiderna har samma URL som på Shopify (/blogs/nyheter/<slug>/). Originalen från Shopify
ligger orörda i kalla/ som arkiv. Skriptet bygger också skalsidor, kablar, laddare,
vanliga frågor, integritet och sitemap till ../docs/ (GitHub Pages). Kör från repots rot:

    python3 build/bygg_guider.py
"""
import html
import json
import math
import os
import re
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import Image

BYGG = Path(__file__).resolve().parent
ROT = BYGG.parent / "docs"
INNEHALL = BYGG / "innehall"
SITE = "https://corder.se"
# Adressen till den publika insamlingen (utan /e). Tom = inget spårskript läggs in på sidorna.
STATISTIK_URL = os.environ.get("STATISTIK_URL", "")

# Rekommenderade butikspriser i kronor. Enda stället där priserna anges.
PRIS = {"skal": 60, "kabel": 60, "laddare": 99}
PRISNOTIS = "Rekommenderat pris. Butiken sätter sitt eget pris."

# Fyll i adress, öppettider och telefon när de är bekräftade. Tomma fält visas inte.
BUTIKER = [
    {"namn": "Go Banana", "ort": "Jönköping", "karta": "Go+Banana+J%C3%B6nk%C3%B6ping",
     "adress": "", "postnummer": "", "oppettider": "", "telefon": ""},
    {"namn": "VIP Mullsjö", "ort": "Mullsjö", "karta": "VIP+Mullsj%C3%B6",
     "adress": "", "postnummer": "", "oppettider": "", "telefon": ""},
]

KABLAR = [
    {"id": "usb-c-till-usb-c", "namn": "USB-C till USB-C", "artikel": "Laddkabel USB-C till USB-C, 2 m, flätad", "typ": "USB-C / USB-C",
     "ean": "7350140690283", "bild": "kabel-usb-c-usb-c-2m", "farg": "Svart", "alt": "Corder laddkabel USB-C till USB-C, 2 meter, svart flätad",
     "passar": "iPhone 15 och senare, med en USB-C-laddare.", "text": "Kabeln till nyare iPhones. Tillsammans med en USB-C-laddare ger den snabbladdning."},
    {"id": "usb-a-till-usb-c", "namn": "USB-A till USB-C", "artikel": "Laddkabel USB-A till USB-C, 2 m, flätad", "typ": "USB-A / USB-C",
     "ean": "7350140690047", "bild": "kabel-usb-a-usb-c-2m", "farg": "Svart", "alt": "Corder laddkabel USB-A till USB-C, 2 meter, svart flätad",
     "passar": "iPhone 15 och senare, med en äldre laddare eller USB-port.", "text": "För dig med USB-C i telefonen men en laddare, bil eller dator med den större USB-A-porten."},
    {"id": "usb-c-till-lightning", "namn": "USB-C till Lightning", "artikel": "Laddkabel USB-C till Lightning, 2 m, flätad, svart", "typ": "USB-C / Lightning",
     "ean": "7350140690467", "bild": "kabel-usb-c-lightning-svart", "farg": "Svart", "alt": "Corder laddkabel USB-C till Lightning, 2 meter, svart flätad",
     "passar": "iPhone 14 och äldre, med en USB-C-laddare.", "text": "För iPhone med Lightning och en modern USB-C-laddare."},
    {"id": "usb-a-till-lightning", "namn": "USB-A till Lightning", "artikel": "Laddkabel USB-A till Lightning, 2 m, flätad", "typ": "USB-A / Lightning",
     "ean": "7350140690030", "bild": "kabel-usb-a-lightning-2m", "farg": "Vit", "alt": "Corder laddkabel USB-A till Lightning, 2 meter, vit",
     "passar": "iPhone 14 och äldre, med en äldre laddare eller USB-port.", "text": "Den klassiska kabeln till iPhone med Lightning och en laddare med USB-A-port."},
]
LADDARE = [
    {"id": "20w-usb-c", "namn": "Snabbladdare 20W", "artikel": "Snabbladdare 20W USB-C", "typ": "USB-C, 20 W",
     "ean": "7350140690504", "bild": "laddare-20w-usb-c", "alt": "Corder snabbladdare 20W med USB-C",
     "passar": "iPhone 15 och senare med USB-C-kabel, och iPhone 14 och äldre med USB-C till Lightning-kabel.", "text": "Snabbladdar din iPhone och räcker för de flesta i vardagen."},
    {"id": "20w-dual-port", "namn": "Snabbladdare 20W Dual Port", "artikel": "Snabbladdare 20W Dual Port", "typ": "USB-C + USB-A, 20 W",
     "ean": "7350140690771", "bild": "laddare-20w-dual-port", "alt": "Corder snabbladdare 20W med två portar",
     "passar": "Både USB-C-kablar och kablar med USB-A.", "text": "Två portar, så att både nya och gamla kablar passar i samma laddare."},
    {"id": "18w-usb-a", "namn": "Snabbladdare 18W", "artikel": "Snabbladdare 18W USB-A", "typ": "USB-A, 18 W, QC 3.0",
     "ean": "7350140690078", "bild": "laddare-18w-usb-a", "alt": "Corder snabbladdare 18W med USB-A",
     "passar": "Kablar med USB-A. iPhone snabbladdas däremot bäst via USB-C.", "text": "För dig som redan har kablar med USB-A."},
]

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
      <li><a href="/kablar/">Kablar</a></li>
      <li><a href="/laddare/">Laddare</a></li>
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
      <div><p class="foot-h">Sortiment</p><ul><li><a href="/skal/">TPU-skal</a></li><li><a href="/laddare/">Laddare</a></li><li><a href="/kablar/">Kablar</a></li></ul></div>
      <div><p class="foot-h">Företag</p><ul><li><a href="/#butiker">Hitta butik</a></li><li><a href="/aterforsaljare/">Bli återförsäljare</a></li><li><a href="/pages/vanliga-fragor-faq/#kontakt">Kontakt</a></li><li><a href="mailto:sales@corder.se">sales@corder.se</a></li></ul></div>
      <div><p class="foot-h">Resurser</p><ul><li><a href="/blogs/nyheter/">Apple-guider</a></li><li><a href="/pages/vanliga-fragor-faq/">Vanliga frågor</a></li><li><a href="/pages/integritet/">Integritet</a></li><li><a href="https://www.instagram.com/corderofficial">Instagram</a></li><li><a href="https://www.tiktok.com/@corderofficial">TikTok</a></li><li><a href="https://www.facebook.com/cordergroup">Facebook</a></li></ul></div>
    </div>
    <div class="foot-base">© 2026 Corder Group AB · Org.nr 559227-0226 · Kungsbacka · Designed and developed in Sweden</div>
  </div>
</footer>"""

CTA = """<div class="cta">
        <div>
          <h2>Corders TPU-skal</h2>
          <p>Till iPhone 14 hela vägen till iPhone 18 Pro. Säljs i fysiska butiker. Fråga butiken om din modell och färg finns inne.</p>
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


def statistik_tagg():
    if not STATISTIK_URL:
        return ""
    return f'<script src="/assets/s.js" data-e="{STATISTIK_URL.rstrip("/")}/e" defer></script>'


def sida(titel, beskr, kanonisk, innehall, schema=None, progress=False, skript="", og_typ="article"):
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
<meta property="og:type" content="{og_typ}">
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
<link rel="stylesheet" href="/assets/sida.css?v=14">
{statistik_tagg()}
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


def samling(namn, url, poster):
    """Schema för en översiktssida: samlingen och dess brödsmulor."""
    return [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": namn, "url": url, "inLanguage": "sv",
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": i, "name": n, "url": u} for i, (n, u) in enumerate(poster, 1)]}},
        brodsmulor((namn, url)),
    ]


def brodsmulor(*led):
    alla = [("Corder", SITE + "/"), *led]
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(alla, 1)]}


def erbjudande(pris, url):
    """Corder säljer bara via fysiska butiker, så priset anges som tillgängligt i butik."""
    return {"@type": "Offer", "price": str(pris), "priceCurrency": "SEK",
            "availability": "https://schema.org/InStoreOnly", "url": url}


def butik_rad(b):
    adress = ", ".join(x for x in (b["adress"], " ".join(y for y in (b["postnummer"], b["ort"]) if y) if b["adress"] else "") if x)
    delar = [f'<b>{html.escape(b["namn"])}</b><span>{html.escape(adress or b["ort"])}</span>']
    if b["oppettider"]:
        delar.append(f'<span>{html.escape(b["oppettider"])}</span>')
    lankar = [f'<a href="https://www.google.com/maps/search/?api=1&amp;query={b["karta"]}" rel="noopener" target="_blank" data-h="karta" data-v="{html.escape(b["namn"])}">Visa på karta</a>']
    if b["telefon"]:
        lankar.append(f'<a href="tel:{b["telefon"].replace(" ", "").replace("-", "")}" data-h="telefon" data-v="{html.escape(b["namn"])}">{html.escape(b["telefon"])}</a>')
    return f'<li>{"".join(delar)}<span class="kop-lankar">{"".join(lankar)}</span></li>'


def kop_block(pris, vad):
    """Pris och butiker, direkt under produkten."""
    butiker = "".join(butik_rad(b) for b in BUTIKER)
    return f"""<section class="kop" id="kop" aria-label="Pris och butiker">
      <div class="kop-pris"><span class="caps">Rek. pris</span><b>{pris} kr</b><small>{PRISNOTIS}</small></div>
      <div class="kop-butiker"><span class="caps">Finns i butik</span><ul>{butiker}</ul><small>Sortimentet varierar. Fråga butiken om {vad} finns inne.</small></div>
    </section>"""


def kop_fast(pris):
    """Fast rad längst ner på mobil."""
    return f'<div class="kop-fast"><span>Rek. pris <b>{pris} kr</b></span><a class="btn" href="#kop">Hitta butik</a></div>'


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
                       f"{SITE}/blogs/nyheter/", index, samling("Apple-guider", f"{SITE}/blogs/nyheter/",
                                                                  [(g["kort"], f'{SITE}/blogs/nyheter/{g["slug"]}/') for g in GUIDER])))
    print("skrev", ut.relative_to(ROT))



# --- Modellsidor: ett TPU-skal per iPhone-modell -------------------------------------

FARG = {"Svart": ("#1c1c1c", "black"), "Blå": ("#4a6684", "blue"), "Lila": ("#b9bdf0", "purple"),
        "Persika": ("#f5a493", "pink"), "Skogsgrön": ("#3d5143", None)}
# Modellbild per färg. Visas när man håller över skalet eller trycker på knappen.
# Bilderna visar färgen, inte alltid samma iPhone-modell som sidan gäller.
LIVSSTIL = {
    "Skogsgrön": ("/img/lifestyle/s/corder-natt-skogsgron-v3.webp", "50% 40%", "Kvinna på en nattmarknad håller upp en iPhone i skogsgrönt Corder-skal"),
    "Lila": ("/img/lifestyle/s/corder-portratt-lila.webp", "35% 40%", "Kvinna håller upp en iPhone i lila Corder-skal"),
    "Persika": ("/img/lifestyle/s/corder-uteservering-persika.webp", "30% 40%", "Kvinna på en uteservering håller upp en iPhone i persikofärgat Corder-skal"),
}
LIVSSTIL_SKRIPT = """<script>
document.querySelectorAll('.life-btn').forEach(k => k.addEventListener('click', () => {
  const pa = k.getAttribute('aria-pressed') !== 'true';
  k.setAttribute('aria-pressed', pa);
  k.closest('.model-shot').classList.toggle('visa', pa);
  k.textContent = pa ? 'Visa skalet' : 'I verkligheten';
}));
</script>"""
GAMLA_FARGER = ["Svart", "Blå", "Lila", "Persika"]
NYA_FARGER = ["Svart", "Skogsgrön"]

MODELLER = [
    {"slug": "iphone-18-pro", "namn": "iPhone 18 Pro", "bild": None, "gron": True, "extra": {"Svart": "/img/cut/17p-black.webp"}, "farger": NYA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar iPhone 17 Pro-skal till iPhone 18 Pro?", "Corders skal till iPhone 17 Pro och 18 Pro tillverkas i samma form och passar båda modellerna."),
                ("Passar skalet till iPhone 18 Pro Max?", "Nej. Pro Max har större skärm och större mått och behöver ett eget skal."),
                ("Passar skalet till iPhone Duo?", "Nej. iPhone Duo är vikbar och behöver ett helt annat skal. Corder har inte skal till Duo.")],
     "guider": ["passar-iphone-17-pro-skal-till-iphone-18-pro", "iphone-18-pro-vs-iphone-17-pro", "vilken-laddare-till-iphone-18-pro"]},
    {"slug": "iphone-17-pro", "namn": "iPhone 17 Pro", "bild": None, "gron": True, "extra": {"Svart": "/img/cut/17p-black.webp"}, "farger": NYA_FARGER, "kontakt": "USB-C",
     "kompat": [("Passar skalet till iPhone 18 Pro?", "Corders skal till iPhone 17 Pro och 18 Pro tillverkas i samma form och passar båda modellerna."),
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
                liv = ""
                if f in LIVSSTIL:
                    src, pos, livalt = LIVSSTIL[f]
                    w, h = matt(src)
                    liv = (f'<img class="life" src="{src}" alt="{html.escape(livalt)}" width="{w}" height="{h}" loading="lazy" style="object-position:{pos}">'
                           f'<button class="life-btn" type="button" aria-pressed="false">I verkligheten</button>')
                shots.append(f'<figure class="model-shot{" has-life" if liv else ""}"><div class="tile">{bild(b, alt)}{liv}</div>'
                             f'<figcaption><i style="background:{FARG[f][0]}"></i>{f}</figcaption></figure>')
            else:
                shots.append(f'<figure class="model-shot"><div class="tile empty"><div><b style="background:{FARG[f][0]}"></b>{f}</div></div>'
                             f'<figcaption><i style="background:{FARG[f][0]}"></i>{f}</figcaption></figure>')
        kabel = ("USB-C till Lightning eller USB-A till Lightning" if m["kontakt"] == "Lightning" else "USB-C till USB-C")
        ankar = "usb-c-till-lightning" if m["kontakt"] == "Lightning" else "usb-c-till-usb-c"
        specs = [("Material", "TPU (termoplastisk polyuretan)"), ("Passar", f'{m["namn"]}'), ("Färger", ", ".join(m["farger"])),
                 ("Egenskaper", "Stötdämpande, formstabilt, upphöjd kant runt kameran"), ("Laddning", f'Telefonen har {m["kontakt"]}. Rätt kabel: {kabel}, 2 m.'),
                 ("Finns hos", "Go Banana i Jönköping och VIP Mullsjö. Fråga butiken om modell och färg finns inne.")]
        specs_html = "".join(f"<div><dt>{a}</dt><dd>{html.escape(b)}</dd></div>" for a, b in specs)
        specs_html = specs_html.replace(f"Rätt kabel: {kabel}, 2 m.", f'Rätt kabel: <a href="/kablar/#{ankar}">{kabel}, 2 m</a>.')
        faq = [("Vilka färger finns skalet till " + m["namn"] + " i?", f"Skalet finns i {farger.lower()}."),
               ("Vilket material är skalet gjort av?", "TPU, termoplastisk polyuretan. Det dämpar stötar och behåller formen utan att töja sig.")] + m["kompat"] + \
              [("Vad kostar skalet?", f'Rekommenderat pris är {PRIS["skal"]} kr. Butiken sätter sitt eget pris.'),
               ("Var kan jag köpa skalet?", "Corder säljs hos Go Banana i Jönköping och VIP Mullsjö. Sortimentet kan variera, så fråga butiken om din modell och färg finns inne.")]
        faq_html = "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in faq)
        andra = "\n        ".join(modell_lank(o) for o in MODELLER if o is not m)
        guidekort = "\n      ".join(kort(guide_per_slug[s]) for s in m["guider"] if s in guide_per_slug)
        bilder = [SITE + modellbild(m, f) for f in m["farger"] if modellbild(m, f)] + \
                 [SITE + LIVSSTIL[f][0] for f in m["farger"] if f in LIVSSTIL and modellbild(m, f)]
        schema = [
            {"@context": "https://schema.org", "@type": "Product", "name": f'Corder TPU-skal till {m["namn"]}',
             "brand": {"@type": "Brand", "name": "Corder"}, "material": "TPU", "color": ", ".join(m["farger"]),
             "description": beskr, "url": url, **({"image": bilder} if bilder else {}),
             "manufacturer": {"@type": "Organization", "name": "Corder Group AB"}, "offers": erbjudande(PRIS["skal"], url)},
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
            brodsmulor(("Skal", SITE + "/skal/"), (m["namn"], url)),
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
    {kop_block(PRIS["skal"], "din modell och färg")}
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
</main>
{kop_fast(PRIS["skal"])}"""
        ut = ROT / "skal" / m["slug"] / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(sida(titel, beskr, url, innehall, schema, skript=LIVSSTIL_SKRIPT, og_typ="product"))
        print("skrev", ut.relative_to(ROT))

    lankar = "\n      ".join(modell_lank(m) for m in MODELLER)
    index = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <h1>Skal till iPhone.</h1>
      <p>TPU-skal från iPhone 14 hela vägen till iPhone 18 Pro, rek. pris {PRIS["skal"]} kr. Välj din modell för att se färger och vad som passar.</p>
    </div>
    <div class="model-grid" style="padding-bottom:clamp(48px,6vw,80px)">
      {lankar}
    </div>
    <div style="padding-bottom:clamp(72px,9vw,128px)">{CTA}</div>
  </div>
</main>"""
    ut = ROT / "skal" / "index.html"
    ut.write_text(sida("Skal till iPhone 14–18 Pro | Corder", "Corders TPU-skal till iPhone 14, 15, 16, 17 och 18 Pro. Välj din modell och se färger, kompatibilitet och var du hittar skalen i butik.",
                       f"{SITE}/skal/", index, samling("Skal", f"{SITE}/skal/",
                                                       [(m["namn"], f'{SITE}/skal/{m["slug"]}/') for m in MODELLER])))
    print("skrev skal/index.html")



def bygg_valjare():
    """Skriver modelldata till startsidans verktyg 'Vilket skal passar din iPhone?'."""
    data = []
    for m in MODELLER:
        data.append({
            "slug": m["slug"], "namn": m["namn"], "kontakt": m["kontakt"],
            "kabel": "USB-C till Lightning eller USB-A till Lightning" if m["kontakt"] == "Lightning" else "USB-C till USB-C",
            "pris": PRIS["skal"],
            "farger": [{"namn": f, "hex": FARG[f][0], "bild": liten(modellbild(m, f)) if modellbild(m, f) else None} for f in m["farger"]],
            "tips": {"q": m["kompat"][0][0], "a": m["kompat"][0][1]},
        })
    sida_ = ROT / "index.html"
    t = sida_.read_text()
    start = t.index('<script id="modeller" type="application/json">') + len('<script id="modeller" type="application/json">')
    slut = t.index("</script>", start)
    sida_.write_text(t[:start] + json.dumps(data, ensure_ascii=False) + t[slut:])
    print("skrev modelldata till index.html")

def byt_mellan(t, start, slut, ny):
    a = t.index(start) + len(start)
    return t[:a] + ny + t[t.index(slut, a):]


def bygg_startsidans_data():
    """Butikskort, butiksdata och spårskript på den handredigerade startsidan."""
    sida_ = ROT / "index.html"
    t = sida_.read_text()
    kort_ = "".join(
        f'<div class="store"><span class="caps">{html.escape(b["ort"])}</span><h3>{html.escape(b["namn"])}</h3>'
        + (f'<p>{html.escape(b["adress"])}, {html.escape(" ".join(x for x in (b["postnummer"], b["ort"]) if x))}</p>' if b["adress"] else "")
        + (f'<p>{html.escape(b["oppettider"])}</p>' if b["oppettider"] else "")
        + '<p>Fråga butiken om din modell finns inne.</p>'
        + f'<a href="https://www.google.com/maps/search/?api=1&amp;query={b["karta"]}" rel="noopener" target="_blank" data-h="karta" data-v="{html.escape(b["namn"])}">Visa på karta</a>'
        + (f'<a href="tel:{b["telefon"].replace(" ", "").replace("-", "")}" data-h="telefon" data-v="{html.escape(b["namn"])}">{html.escape(b["telefon"])}</a>' if b["telefon"] else "")
        + "</div>" for b in BUTIKER)
    t = byt_mellan(t, "<!-- butiker -->", "<!-- /butiker -->", kort_)
    # Butiksdata kräver adress, så butiker utan bekräftad adress tas inte med.
    lokala = [{"@context": "https://schema.org", "@type": "Store", "name": b["namn"],
               "address": {"@type": "PostalAddress", "streetAddress": b["adress"], "postalCode": b["postnummer"], "addressLocality": b["ort"], "addressCountry": "SE"},
               **({"telephone": b["telefon"]} if b["telefon"] else {}), **({"openingHours": b["oppettider"]} if b["oppettider"] else {})}
              for b in BUTIKER if b["adress"]]
    ld = f'<script type="application/ld+json">{json.dumps(lokala, ensure_ascii=False)}</script>' if lokala else ""
    t = byt_mellan(t, "<!-- butiksdata -->", "<!-- /butiksdata -->", ld)
    t = byt_mellan(t, "<!-- statistik -->", "<!-- /statistik -->", statistik_tagg())
    sida_.write_text(t)
    print("skrev butiker och statistik till index.html")


def fragor_html(faq):
    return "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in faq)


def faq_schema(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def bygg_tillbehor():
    guide_per_slug = {g["slug"]: g for g in GUIDER}
    sidor = [
        {"slug": "kablar", "namn": "Laddkablar", "kort": "Kablar", "rubrik": "Laddkablar.", "pris": PRIS["kabel"], "produkter": KABLAR, "kategori": "Laddkabel",
         "titel": f'Laddkablar till iPhone, flätade och 2 meter – rek. pris {PRIS["kabel"]} kr | Corder',
         "beskr": f'Flätade laddkablar på 2 meter med USB-C och Lightning till iPhone. Rek. pris {PRIS["kabel"]} kr. Se vilken kabel som passar din iPhone och var den finns i butik.',
         "ingress": f'Flätade och 2 meter långa, så att du når från väggen till sängen. Rek. pris {PRIS["kabel"]} kr.',
         "guide": ("Vilken kabel passar?", [("iPhone 15 och senare", "USB-C i telefonen. Välj USB-C till USB-C, eller USB-A till USB-C om laddaren har en USB-A-port."),
                                            ("iPhone 14 och äldre", "Lightning i telefonen. Välj USB-C till Lightning, eller USB-A till Lightning om laddaren har en USB-A-port.")]),
         "faq": [("Vilken kabel behöver jag till iPhone 15 eller senare?", "iPhone 15 och senare har USB-C. Använd USB-C till USB-C med en USB-C-laddare, eller USB-A till USB-C med en äldre laddare."),
                 ("Vilken kabel behöver jag till iPhone 14?", "iPhone 14 och äldre har Lightning. Använd USB-C till Lightning eller USB-A till Lightning."),
                 ("Hur långa är kablarna?", "Alla Corders kablar är 2 meter."),
                 ("Vad kostar kablarna?", f'Rekommenderat pris är {PRIS["kabel"]} kr. Butiken sätter sitt eget pris.'),
                 ("Går det att köpa kablarna på nätet?", "Nej. Corder säljs i fysiska butiker, till exempel hos Go Banana i Jönköping och VIP Mullsjö.")],
         "guider": ["vilken-usb-c-kabel-till-iphone", "vilken-laddare-till-iphone-18-pro"]},
        {"slug": "laddare", "namn": "Snabbladdare", "kort": "Laddare", "rubrik": "Snabbladdare.", "pris": PRIS["laddare"], "produkter": LADDARE, "kategori": "Snabbladdare",
         "titel": f'Snabbladdare till iPhone, 20W och 18W – rek. pris {PRIS["laddare"]} kr | Corder',
         "beskr": f'Snabbladdare till iPhone: 20W USB-C, 20W Dual Port och 18W USB-A. Rek. pris {PRIS["laddare"]} kr. Se vilken laddare som passar och var den finns i butik.',
         "ingress": f'Tre laddare för nya och gamla kablar. Rek. pris {PRIS["laddare"]} kr.',
         "guide": ("Vilken laddare passar?", [("Du har en USB-C-kabel", "Välj 20W USB-C. Det ger snabbladdning för iPhone."),
                                              ("Du har båda sorternas kablar", "Välj 20W Dual Port med både USB-C och USB-A."),
                                              ("Du har bara USB-A-kablar", "Välj 18W USB-A, eller byt till USB-C för snabbast laddning av iPhone.")]),
         "faq": [("Räcker 20W till min iPhone?", "Ja, för de flesta. 20W snabbladdar telefonen, men når inte Apples allra snabbaste siffror på de nyaste modellerna."),
                 ("Kan en laddare skada batteriet?", "Nej. Telefonen tar bara emot så mycket ström som den klarar."),
                 ("Vad kostar laddarna?", f'Rekommenderat pris är {PRIS["laddare"]} kr. Butiken sätter sitt eget pris.'),
                 ("Är laddarna CE-märkta?", "Ja, Corders laddare och kablar är CE-märkta.")],
         "guider": ["vilken-laddare-till-iphone-18-pro", "vilken-usb-c-kabel-till-iphone"]},
    ]
    for s in sidor:
        url = f'{SITE}/{s["slug"]}/'
        kort_ = []
        produkter = []
        for p in s["produkter"]:
            src = f'/img/produkter/{p["bild"]}.webp'
            rader = [("Typ", p["typ"]), ("Passar", p["passar"]), ("EAN", p["ean"])]
            if p.get("farg"):
                rader.insert(1, ("Färg", p["farg"]))
            dl = "".join(f"<div><dt>{a}</dt><dd>{html.escape(b)}</dd></div>" for a, b in rader)
            kort_.append(f"""<article class="produkt" id="{p["id"]}">
        <div class="produkt-bild">{bild(src, p["alt"])}</div>
        <div class="produkt-text">
          <span class="caps">{s["kategori"]}</span>
          <h2>{html.escape(p["namn"])}</h2>
          <p>{html.escape(p["text"])}</p>
          <dl class="specs-list">{dl}</dl>
          <p class="produkt-pris"><b>{s["pris"]} kr</b> <span>Rek. pris</span></p>
        </div>
      </article>""")
            produkter.append({"@context": "https://schema.org", "@type": "Product", "name": f'Corder {p["artikel"]}', "brand": {"@type": "Brand", "name": "Corder"},
                              "gtin13": p["ean"], "description": p["text"], "url": f'{url}#{p["id"]}', "image": [SITE + src],
                              "manufacturer": {"@type": "Organization", "name": "Corder Group AB"}, "offers": erbjudande(s["pris"], url)})
        rubrik, rad = s["guide"]
        val = "".join(f"<div><dt>{html.escape(a)}</dt><dd>{html.escape(b)}</dd></div>" for a, b in rad)
        guidekort = "\n      ".join(kort(guide_per_slug[x]) for x in s["guider"])
        innehall = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="model-head">
      <div>
        <nav class="crumbs" aria-label="Brödsmulor"><a href="/">Corder</a><span>/</span><span>{s["kort"]}</span></nav>
        <h1>{s["rubrik"]}</h1>
      </div>
      <p>{html.escape(s["ingress"])}</p>
    </div>
    {kop_block(s["pris"], "artikeln")}
    <div class="produkt-lista">
      {"".join(kort_)}
    </div>
    <div class="post" style="grid-template-columns:minmax(0, 760px)">
      <article class="prose">
        <h2 style="margin-top:0">{html.escape(rubrik)}</h2>
        <dl class="specs-list">{val}</dl>
        <h2 id="vanliga-fragor">Vanliga frågor</h2>
        <div class="faq">
{fragor_html(s["faq"])}
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
</main>
{kop_fast(s["pris"])}"""
        schema = [*produkter, faq_schema(s["faq"]), brodsmulor((s["kort"], url))]
        ut = ROT / s["slug"] / "index.html"
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_text(sida(s["titel"], s["beskr"], url, innehall, schema, og_typ="product"))
        print("skrev", ut.relative_to(ROT))


FRAGOR = [
    ("Köpa", [
        ("Var kan jag köpa Corder?", "I fysiska butiker, till exempel hos Go Banana i Jönköping och VIP Mullsjö. Corder säljs inte på nätet. Sortimentet varierar, så fråga butiken om din modell och färg finns inne."),
        ("Vad kostar produkterna?", f'Rekommenderat pris är {PRIS["skal"]} kr för skal och kablar och {PRIS["laddare"]} kr för snabbladdare. Butiken sätter sitt eget pris.'),
        ("Min butik har inte Corder. Kan ni fixa det?", "Tipsa oss gärna på sales@corder.se."),
    ]),
    ("Skal och passform", [
        ("Vilka iPhone-modeller finns det skal till?", "iPhone 14, 14 Pro, 15, 15 Pro, 16e, 16, 16 Pro, 17, 17 Pro och 18 Pro."),
        ("Hur vet jag vilken iPhone jag har?", "Öppna Inställningar, Allmänt och Om. Där står modellnamnet."),
        ("Finns det skal till Plus, Pro Max eller iPhone Duo?", "Nej. Våra skal är gjorda för de vanliga storlekarna, och iPhone Duo är vikbar och behöver ett helt annat skal."),
        ("Vad är skalen gjorda av?", "TPU, termoplastisk polyuretan. Det dämpar stötar och behåller formen."),
    ]),
    ("Kablar och laddare", [
        ("Vilken kabel behöver jag?", "iPhone 15 och senare har USB-C. iPhone 14 och äldre har Lightning. På sidan om kablar ser du vilken som passar din laddare."),
        ("Hur långa är kablarna?", "Alla Corders kablar är 2 meter."),
    ]),
    ("Fel och reklamation", [
        ("Min produkt är trasig. Vad gör jag?", "Vänd dig till butiken där du köpte produkten och ta med kvittot. Det är butiken som hanterar reklamationer."),
        ("Hur länge kan jag reklamera?", "Enligt konsumentköplagen kan du reklamera ett ursprungligt fel i upp till tre år från köpet. Fel som visar sig inom två år räknas som regel som ursprungliga."),
        ("Kan jag lämna tillbaka en produkt som jag ångrat?", "Det beror på butiken, eftersom ångerrätt inte gäller vid köp i fysisk butik. Fråga vad som gäller när du handlar."),
    ]),
]


def bygg_info():
    alla = [f for _, grupp in FRAGOR for f in grupp]
    url = f"{SITE}/pages/vanliga-fragor-faq/"
    grupper = "\n".join(f'<h2>{html.escape(rubrik)}</h2>\n<div class="faq">\n{fragor_html(grupp)}\n</div>' for rubrik, grupp in FRAGOR)
    innehall = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <h1>Vanliga frågor.</h1>
      <p>Om köp, pris, passform och reklamation. Hittar du inte svaret, hör av dig.</p>
    </div>
    <div class="post" style="grid-template-columns:minmax(0, 760px)">
      <article class="prose">
{grupper}
        <h2 id="kontakt">Kontakt</h2>
        <p>Frågor om produkter, eller om du vill sälja Corder: <a href="mailto:sales@corder.se">sales@corder.se</a>. Butiker och grossister hittar mer på <a href="/aterforsaljare/">sidan för återförsäljare</a>.</p>
        <p>Corder Group AB, org.nr 559227-0226, Kungsbacka.</p>
      </article>
    </div>
  </div>
</main>"""
    ut = ROT / "pages" / "vanliga-fragor-faq" / "index.html"
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(sida("Vanliga frågor om köp, pris och reklamation | Corder",
                       "Svar om var du köper Corder, rekommenderade priser, vilka skal och kablar som passar och hur en reklamation går till.",
                       url, innehall, [faq_schema(alla), brodsmulor(("Vanliga frågor", url))]))

    url = f"{SITE}/pages/integritet/"
    innehall = f"""<main id="innehall" tabindex="-1">
  <div class="wrap">
    <div class="index-head">
      <h1>Integritet.</h1>
      <p>Så hanterar corder.se uppgifter om besök.</p>
    </div>
    <div class="post" style="grid-template-columns:minmax(0, 760px)">
      <article class="prose">
        <p class="ingress">Vi använder inga cookies och sparar ingenting i din webbläsare. Vi har ingen inloggning, nätbutik eller nyhetsbrev och säljer inga uppgifter.</p>
        <h2>Besöksstatistik</h2>
        <p>Vi mäter besök med ett eget statistikverktyg för att se vilka sidor som är användbara och om besökare hittar till butikerna.</p>
        <h3>Det här sparas</h3>
        <ul>
          <li>Vilken sida som besöktes och från vilken webbplats besökaren kom.</li>
          <li>Enhetstyp (mobil, surfplatta eller dator) och land.</li>
          <li>Klick på till exempel kartlänkar, e-postlänkar och nedladdningar.</li>
        </ul>
        <h3>Det här sparas inte</h3>
        <ul>
          <li>IP-adresser och uppgifter om din webbläsare sparas inte.</li>
          <li>Vi kan inte följa dig mellan dagar eller mellan webbplatser. För att räkna besökare per dag beräknas ett engångsvärde med hjälp av IP-adress, webbläsare och en slumpnyckel som raderas efter dygnet.</li>
        </ul>
        <p>Enskilda händelser raderas efter 90 dagar. Därefter finns bara summerade siffror per dag kvar. Om din webbläsare skickar Do Not Track eller Global Privacy Control mäter vi inte alls.</p>
        <p>Statistiken behandlas hos Cloudflare, och själva webbplatsen drivs på GitHub Pages. Båda hanterar tekniska uppgifter, som IP-adresser, för att kunna leverera tjänsten.</p>
        <h2>E-post</h2>
        <p>Om du mejlar oss använder vi dina uppgifter för att svara dig.</p>
        <h2>Kontakt</h2>
        <p>Personuppgiftsansvarig är Corder Group AB, org.nr 559227-0226. Frågor, eller begäran om att få se eller radera uppgifter, skickas till <a href="mailto:sales@corder.se">sales@corder.se</a>. Du kan klaga hos Integritetsskyddsmyndigheten (IMY).</p>
      </article>
    </div>
  </div>
</main>"""
    ut = ROT / "pages" / "integritet" / "index.html"
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(sida("Integritet | Corder", "Så hanterar corder.se uppgifter om besök: inga cookies, inga sparade IP-adresser och enbart summerad statistik över tid.",
                       url, innehall, [brodsmulor(("Integritet", url))]))
    print("skrev pages/vanliga-fragor-faq och pages/integritet")


def senast_andrad(fil):
    """Datum för filens senaste commit, eller i dag om filen har ändringar som inte är committade."""
    rel = str(fil.relative_to(ROT.parent))
    andrad = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=ROT.parent, capture_output=True, text=True).stdout.strip()
    datum = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROT.parent, capture_output=True, text=True).stdout.strip()
    return date.today().isoformat() if andrad or not datum else datum


def bygg_sitemap():
    """Alla riktiga sidor. Omdirigeringar och 404 tas inte med."""
    sidor = []
    for fil in sorted(ROT.rglob("index.html"), key=lambda f: (len(f.parts), str(f))):
        if 'http-equiv="refresh"' not in fil.read_text():
            vag = fil.parent.relative_to(ROT).as_posix()
            sidor.append((SITE + "/" if vag == "." else f"{SITE}/{vag}/", senast_andrad(fil)))
    rader = "\n".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in sidor)
    (ROT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rader}\n</urlset>\n')
    print(f"skrev sitemap.xml med {len(sidor)} sidor")


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
GAMLA_SIDOR = {"pages/om-oss": "/#om-oss", "pages/contact": "/pages/vanliga-fragor-faq/#kontakt",
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
        if handle.startswith(("laddkabel", "laddningskabel")):
            return "/kablar/"
        if handle.startswith("stromadapter"):
            return "/laddare/"
        return "/#sortiment"
    mal.update({f"products/{p}": produktmal(p) for p in GAMLA_PRODUKTER})
    mal.update({f"collections/{k}": "/#sortiment" for k in GAMLA_KOLLEKTIONER})
    mal.update({"collections/mobilskal": "/skal/", "collections/kablar": "/kablar/", "collections/laddare": "/laddare/",
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
    bygg_tillbehor()
    bygg_info()
    bygg_valjare()
    bygg_startsidans_data()
    bygg_404()
    bygg_omdirigeringar()
    bygg_aterforsaljare()
    bygg_sitemap()
