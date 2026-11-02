"""Kontrollerar den färdiga sajten i docs/. Körs på GitHub vid varje push och går att köra lokalt:

    python3 build/kontrollera.py
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://corder.se"
fel = []


class Sida(HTMLParser):
    def __init__(self):
        super().__init__()
        self.id = set()
        self.lankar = []
        self.ld = []
        self._ld = False
        self.bilder_utan_matt = 0
        self.h1 = 0

    def handle_starttag(self, tagg, attr):
        a = dict(attr)
        if a.get("id"):
            self.id.add(a["id"])
        if tagg == "h1":
            self.h1 += 1
        if tagg == "a" and a.get("href"):
            self.lankar.append(a["href"])
        if tagg in ("img", "script", "source", "video", "link"):
            for k in ("src", "poster"):
                if a.get(k):
                    self.lankar.append(a[k])
            if tagg == "link" and a.get("rel") in ("stylesheet", "icon", "manifest", "apple-touch-icon"):
                self.lankar.append(a["href"])
            for k in ("srcset", "imagesrcset"):
                if a.get(k):
                    self.lankar += [d.strip().split(" ")[0] for d in a[k].split(",")]
        if tagg == "img" and not ("width" in a and "height" in a):
            self.bilder_utan_matt += 1
        self._ld = tagg == "script" and a.get("type") == "application/ld+json"

    def handle_endtag(self, tagg):
        if tagg == "script":
            self._ld = False

    def handle_data(self, data):
        if self._ld and data.strip():
            self.ld.append(data)


def fil_for(sokvag):
    """Filen som GitHub Pages skulle servera för en sökväg."""
    p = ROT / sokvag.lstrip("/")
    return p / "index.html" if sokvag.endswith("/") or p.is_dir() else p


sidor = {}
for fil in ROT.rglob("*.html"):
    s = Sida()
    text = fil.read_text()
    s.feed(text)
    sidor[fil] = (s, text)


def kolla_schema(fil, poster):
    for o in poster if isinstance(poster, list) else poster.get("@graph", [poster]):
        typ = o.get("@type")
        if typ == "ProductGroup":
            if not o.get("hasVariant"):
                fel.append(f"{fil}: ProductGroup saknar varianter")
            for v in o.get("hasVariant", []):
                if not re.fullmatch(r"\d{13}", v.get("gtin13", "")):
                    fel.append(f"{fil}: variant utan EAN: {v.get('name')}")
                if v.get("offers", {}).get("priceCurrency") != "SEK" or not v.get("offers", {}).get("price"):
                    fel.append(f"{fil}: variant utan pris: {v.get('name')}")
        if typ == "Product" and not o.get("offers"):
            fel.append(f"{fil}: Product utan offers: {o.get('name')}")


for fil, (s, text) in sidor.items():
    rel = fil.relative_to(ROT)
    omdirigering = 'http-equiv="refresh"' in text
    for block in s.ld:
        try:
            kolla_schema(rel, json.loads(block))
        except json.JSONDecodeError as e:
            fel.append(f"{rel}: trasig JSON-LD: {e}")
    if omdirigering:
        continue
    if s.h1 != 1 and fil.name == "index.html":
        fel.append(f"{rel}: {s.h1} H1-rubriker")
    if s.bilder_utan_matt:
        fel.append(f"{rel}: {s.bilder_utan_matt} bilder utan mått")
    if re.search(r"localhost:\d|ERSATT-MED", text):
        fel.append(f"{rel}: innehåller lokal adress eller platshållare")
    for lank in s.lankar:
        if "${" in lank:
            continue
        lank = lank.replace(SITE, "") if lank.startswith(SITE) else lank
        if re.match(r"[a-z]+:|//", lank):
            continue
        adress, _, ankare_ = lank.partition("#")
        adress = adress.split("?")[0]
        mal = fil if not adress else fil_for(adress) if adress.startswith("/") else fil_for(str((fil.parent / adress).relative_to(ROT)) + ("/" if adress.endswith("/") else ""))
        if not mal.exists():
            fel.append(f"{rel}: trasig länk {lank}")
        elif ankare_ and mal.suffix == ".html" and mal in sidor and ankare_ not in sidor[mal][0].id and 'http-equiv="refresh"' not in sidor[mal][1]:
            fel.append(f"{rel}: ankaret saknas {lank}")

karta = set(re.findall(r"<loc>([^<]+)</loc>", (ROT / "sitemap.xml").read_text()))
for fil, (s, text) in sidor.items():
    if fil.name != "index.html" or 'http-equiv="refresh"' in text:
        continue
    vag = fil.parent.relative_to(ROT).as_posix()
    adress = f"{SITE}/" if vag == "." else f"{SITE}/{vag}/"
    gomd = 'name="robots" content="noindex"' in text
    if gomd == (adress in karta):
        fel.append(f"sitemap.xml: {adress} {'ska inte vara med' if gomd else 'saknas'}")

# Streckkoderna på inköpslappen ska gå att skanna i kassan.
lapp = re.search(r'id="lapp-data"[^>]*>(.*?)</script>', (ROT / "inkopslapp" / "index.html").read_text(), re.S)
for m in json.loads(lapp[1])["modeller"]:
    for artikel in [*m["farger"], m["kabel"], m["laddare"]]:
        e = artikel["ean"]
        if not re.fullmatch(r"\d{13}", e) or sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(e)) % 10:
            fel.append(f"inkopslapp: ogiltig EAN {e} ({m['namn']}, {artikel['namn']})")

print(f"Kontrollerade {len(sidor)} sidor.")
if fel:
    print(f"{len(fel)} fel:")
    print("\n".join(f"  {f}" for f in sorted(set(fel))))
    sys.exit(1)
print("Inga fel.")
