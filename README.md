# corder.se

Varumärkessidan för Corder (Corder Group AB). Statisk sajt som publiceras med GitHub Pages från mappen `docs/`.

## Struktur

- `docs/` – det som publiceras: startsida, guider, ikoner, typsnitt och bilder.
- `build/bygg_guider.py` – bygger guidesidorna, 404-sidan och omdirigeringar från gamla Shopify-adresser.
- `build/innehall/` – guidernas brödtext. Titlar, beskrivningar och vanliga frågor ligger i skriptet.
- `build/kalla/` – exporten av de gamla Shopify-artiklarna (arkiv).
- `build/bildkallor/` – originalbilder och renderingar i full upplösning.

## Bygga

```bash
python3 build/bygg_guider.py
```

Startsidan (`docs/index.html`) redigeras direkt.

## Förhandsgranska lokalt

```bash
python3 -m http.server 5151 --directory docs
```
