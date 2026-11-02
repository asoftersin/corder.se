# Statistik för corder.se

Egen besöksstatistik utan cookies. Två Cloudflare Workers delar en D1-databas:

- `corder-statistik` (publik) tar emot händelser på `POST /e` och städar en gång per dygn.
- `corder-admin` (skyddad med lösenord) visar portalen och CSV-exporten.

Portalen nekar allt utan rätt lösenord. Den kan också skyddas med Cloudflare Access: ta då bort `PORTAL_LOSENORD` och fyll i `ACCESS_TEAM` och `ACCESS_AUD`.

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

4. Skapa ett långt slumpat lösenord till portalen, spara det i en lösenordshanterare och klistra in det när kommandot frågar. Det måste ha minst 20 tecken, annars släpps ingen in:

   ```bash
   npx wrangler secret put PORTAL_LOSENORD -c wrangler.admin.toml
   ```

5. Portalen svarar nu med en inloggningsruta. Användarnamnet kan vara vad som helst.

6. Slå på mätningen på sajten. Bygg med adressen till insamlingen och publicera:

   ```bash
   STATISTIK_URL=https://corder-statistik.<konto>.workers.dev python3 ../build/bygg_guider.py
   ```

   Adressen ligger som standardvärde för `STATISTIK_URL` i `build/bygg_guider.py`. Driftsatt adress är `https://corder-statistik.corder-statistik.workers.dev`, och portalen finns på `https://corder-admin.corder-statistik.workers.dev`.

7. Öppna `https://corder-admin.<konto>.workers.dev`, logga in med lösenordet och kontrollera att besöket syns.

## Ansökningar och beställningar

Formulären på `/aterforsaljare/` och `/aterforsaljare/bestall/` skickas till `POST /f` och syns överst i portalen, där de kan markeras som hanterade, raderas och exporteras. De raderas automatiskt efter 24 månader. Så länge `STATISTIK_URL` saknas i bygget, eller om tjänsten inte svarar, öppnas besökarens e-postprogram i stället.

Har databasen redan driftsatts körs `npm run db:skapa` igen för att skapa de nya tabellerna. Det påverkar inte befintliga data.

Skydd mot skräp: ursprungskontroll, dold fälla, tidskontroll och högst 10 formulär per besökare och 300 totalt per dygn. Vill ni ha ett hårdare skydd kan Cloudflare Turnstile läggas till.

**Mejl om nya ärenden är valfritt.** Utan det syns ärendena bara i portalen, så kontrollera den regelbundet. För att slå på det: skapa ett konto hos [Resend](https://resend.com), verifiera avsändardomänen och kör:

```bash
npx wrangler secret put RESEND_API_KEY -c wrangler.insamling.toml
```

Lägg sedan till `AVISERA_FRAN` och `AVISERA_TILL` under `[vars]` i `wrangler.insamling.toml` och driftsätt. Nämn Resend på integritetssidan när det är på.

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
| `modell-saknas` | Någon öppnar en modell vi saknar skal till |
| `kit`, `passar-modell` | Klick i Allt till din iPhone, val i Vad passar min iPhone? |
| `ansokan-skickad`, `bestallning-skickad`, `ansokan-mejl`, `bestallning-mejl` | Ett formulär skickas (bara händelsen, inga uppgifter) |
| `bestall`, `material`, `material-utskrift` | Klick till beställning och säljmaterial, utskrift av skylt |

Lägg till fler med `data-h="namn" data-v="värde"` på en länk eller knapp.

## Begränsningar

- Besökare räknas per dygn. Samma person räknas igen nästa dag, med flit.
- Annonsblockerare kan stoppa anrop till `workers.dev`, så siffrorna blir något för låga.
- `Origin` kan förfalskas utanför en webbläsare, så vem som helst kan skicka påhittade händelser. De kan ge skräp i rapporten men inte läsa något eller köra kod i portalen.
