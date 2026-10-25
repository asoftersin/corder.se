"""Meddelar Bing (och därmed ChatGPT:s sök) och andra IndexNow-motorer om corder.se:s sidor.

Kör efter att en ändring har publicerats på GitHub Pages:

    python3 build/indexnow.py            # alla sidor i sitemap.xml
    python3 build/indexnow.py /blogs/nyheter/ny-guide/   # bara vissa sidor
"""
import json
import re
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://corder.se"


def nyckel():
    filer = [f for f in DOCS.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", f.name)]
    assert len(filer) == 1, "Hittade inte exakt en IndexNow-nyckelfil i docs/"
    return filer[0].stem


def adresser(args):
    if args:
        return [SITE + a if a.startswith("/") else a for a in args]
    return re.findall(r"<loc>([^<]+)</loc>", (DOCS / "sitemap.xml").read_text())


def skicka(urls):
    key = nyckel()
    data = json.dumps({"host": "corder.se", "key": key, "keyLocation": f"{SITE}/{key}.txt", "urlList": urls}).encode()
    # curl i stället för urllib: python.org-Python på macOS saknar ofta rotcertifikat
    svar = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                           "-H", "Content-Type: application/json; charset=utf-8", "--data-binary", "@-",
                           "https://api.indexnow.org/indexnow"], input=data, capture_output=True, check=True)
    print(f"IndexNow svarade {svar.stdout.decode()} för {len(urls)} adresser")


if __name__ == "__main__":
    skicka(adresser(sys.argv[1:]))
