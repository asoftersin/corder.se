# Statistik för corder.se

Egen besöksstatistik utan cookies. Två Cloudflare Workers delar en D1-databas:

- `corder-statistik` (publik) tar emot händelser på `POST /e` och städar en gång per dygn.
- `corder-admin` (bakom Cloudflare Access) visar portalen och CSV-exporten.

De är separata eftersom Access skyddar en hel `workers.dev`-adress. Insamlingen måste vara öppen och portalen stängd.
Portalen kontrollerar dessutom själv Access-token och nekar allt utan giltig token.

Vad som sparas beskrivs på https://corder.se/pages/integritet/. Ändra den sidan om mätningen ändras.

## Driftsätta första gången

Allt körs från den här mappen. Gratisnivån räcker.

1. Skapa ett konto på cloudflare.com och installera beroenden:

   ```bash
   npm install
   ```

   ```bash
   npx wrangler login
   ```

2. Skapa databasen. Klistra in `database_id` från svaret i både `wrangler.insamling.toml` och `wrangler.admin.toml`:

   ```bash
   npx wrangler d1 create corder-statistik
   ```

3. Skapa tabellerna och driftsätt båda tjänsterna:

   ```bash
   npm run db:skapa
   ```

   ```bash
   npm run driftsatt
   ```

4. Skydda portalen i Cloudflare-panelen under Workers & Pages → `corder-admin` → Settings → Domains & Routes → `workers.dev`: slå på Cloudflare Access och tillåt bara din e-postadress. Lämna `corder-statistik` utan Access.

5. Kopiera team-namnet (`<team>.cloudflareaccess.com`) och programmets AUD-värde från Zero Trust → Access → Applications. Fyll i `ACCESS_TEAM` och `ACCESS_AUD` i `wrangler.admin.toml` och driftsätt igen. Portalen svarar 403 tills det är gjort.

6. Slå på mätningen på sajten. Bygg med adressen till insamlingen och publicera:

   ```bash
   STATISTIK_URL=https://corder-statistik.<konto>.workers.dev python3 ../build/bygg_guider.py
   ```

   Lägg in adressen permanent som standardvärde för `STATISTIK_URL` i `build/bygg_guider.py`, annars försvinner spårskriptet vid nästa bygge.

7. Öppna `https://corder-admin.<konto>.workers.dev`, logga in med engångskoden och kontrollera att besöket syns.

## Köra lokalt

Skapa `statistik/.dev.vars`:

```
TILLATNA_URSPRUNG="http://localhost:5151"
EGEN_VARD="localhost"
LOKAL_UTAN_INLOGGNING="ja"
```

```bash
npm run db:lokal
```

```bash
npm test
```

Starta sedan `statistik-insamling` och `statistik-admin` från `.claude/launch.json`, eller `npm run dev:insamling` och `npm run dev:admin`. Portalen finns på http://localhost:8788.

## Mätta händelser

| Namn | När |
| --- | --- |
| `karta`, `telefon` | Klick på en butiks karta eller telefonnummer |
| `hitta-butik` | Klick på en länk till butikslistan |
| `skalmodell`, `skalmodell-saknas` | Val i skalväljaren |
| `epost`, `nedladdning` | Klick på e-postlänk eller produktdata och bildpaket |
| `film-spelad`, `film-ljud` | Filmen startar eller ljudet slås på |

Lägg till fler med `data-h="namn" data-v="värde"` på en länk eller knapp.

## Begränsningar

- Besökare räknas per dygn. Samma person räknas igen nästa dag, med flit.
- Annonsblockerare kan stoppa anrop till `workers.dev`, så siffrorna blir något för låga.
- `Origin` kan förfalskas utanför en webbläsare, så vem som helst kan skicka påhittade händelser. De kan ge skräp i rapporten men inte läsa något eller köra kod i portalen.
