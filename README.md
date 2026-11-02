# corder.se

Varumärkessidan för Corder (Corder Group AB). Statisk sajt som publiceras med GitHub Pages från mappen `docs/`.

## Struktur

- `docs/` – det som publiceras: startsida, guider, ikoner, typsnitt och bilder.
- `build/bygg_guider.py` – bygger guider, skalsidor, kablar, laddare, inköpslappen, vanliga frågor, integritet, 404-sidan, sitemap och omdirigeringar från gamla Shopify-adresser. Priser och butiker anges här (`PRIS`, `BUTIKER`).
- `build/innehall/` – guidernas brödtext. Titlar, beskrivningar och vanliga frågor ligger i skriptet.
- `build/kalla/` – exporten av de gamla Shopify-artiklarna (arkiv).
- `build/bildkallor/` – originalbilder och renderingar i full upplösning.
- `statistik/` – egen besöksstatistik med adminportal, se `statistik/README.md`.

## Bygga

```bash
python3 build/bygg_guider.py
```

Startsidan (`docs/index.html`) redigeras direkt, utom modelldata, butikskort och spårskript som fylls i av bygget.

Provrummet (`docs/assets/provrum.js`) öppnas från heron och färgkorten och läser samma modelldata. Skärmmåtten som ringar in modellen ligger i `SKARMAR` i skriptet: lägg till nya iPhone-modeller där.

Excel-filen med produktdata uppdateras bara om `openpyxl` finns installerat.

Kontrollera resultatet med `python3 build/kontrollera.py`. Samma kontroll, och statistikmotorns tester, körs på GitHub vid varje push.

## Förhandsgranska lokalt

```bash
python3 -m http.server 5151 --directory docs
```

## Efter publicering

Meddela Bing och andra sökmotorer via IndexNow (nyckelfilen ligger i `docs/`):

```bash
python3 build/indexnow.py
```

`docs/llms.txt` sammanfattar Corder för AI-tjänster. Uppdatera den när sortiment, butiker eller guider ändras.
