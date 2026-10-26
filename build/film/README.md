# corder: varumärkesfilm (15 s)

Filmen är skriven i kod. Varje bildruta ritas på canvas i `reel.js`, och ljudspåret syntetiseras i `music.py`.
Både bild och ljud följer samma taktrutnät: 128 BPM, 8 takter = 15,0 s.

| Takt | Tid | Scen |
|---|---|---|
| 1 | 0,00 | Fallprov: Skogsgrön 18 Pro landar, "Stötdämpande och formstabilt." |
| 2 | 1,88 | Kinetisk typografi: "Bra mobiltillbehör. Ännu bättre priser." |
| 3 | 3,75 | "Ett skal. Fem färger." Skalet byter färg på varje slag |
| 4 | 5,63 | Hero-fotot, "Skogsgrön." |
| 5 | 7,50 | Karusell iPhone 18 Pro till 14 |
| 6 | 9,38 | "Laddat och kopplat." Kabel och laddare |
| 7 | 11,25 | Produktmontage, åtta klipp på åttondelar |
| 8 | 13,13 | Slutbild med ordmärke, färger och butiker |

## Rendera

Kräver Node 22+, Google Chrome, ffmpeg och Python 3 med numpy.

```bash
python3 -I music.py music.wav
node render.mjs --video=corder-film.mp4 --audio=music.wav            # 1080p60, rörelseoskärpa, ca 3 min
node render.mjs --scale=0.5 --sub=1 --stills=2.0,8.5 --out=stills     # snabba kontrollbilder
```

`reel.html#play` spelar filmen i realtid i en webbläsare med ljud (klicka för att starta). Sidan måste serveras över http, till exempel med `python3 -m http.server`.

Bilderna i `img/` är kopior från `docs/img/`. Byts produktbilder eller butiker ut, renderar du om filmen med kommandona ovan.
