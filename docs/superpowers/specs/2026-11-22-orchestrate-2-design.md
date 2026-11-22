# Orchestrate 2.0: design

Datum: 2026-11-22. Status: godkänd 2026-11-22, ändrad efter skarpa prov samma dag (avsnitt 13).

Märkning: **[Beslutat]** har användaren valt. **[Förslag]** har visats i dialogen utan invändning. **[Nytt]** tillkom när designen skrevs och bör läsas extra noga.

## 1. Syfte

Version 1 byggdes för de minsta planerna och sparade tokens genom en svag huvudsession. Version 2 utgår från Claude Max: en stark orkestrerare som skriver skarpa uppdrag, rätt modell för varje uppdrag och den starkaste modellen där ett felbeslut är dyrt.

**Mål**

- Bästa resultat per slutfört jobb, inte lägsta kostnad per anrop.
- Ingen högriskändring committas utan oberoende granskning och slutdom.
- Varje modellbyte och varje hoppat steg syns i slutrapporten.

**Inte mål**

- Agenter på småjobb.
- Högsta effort överallt.
- Tvingande hooks, agent teams eller ett eget workflow-skript.
- En starkare Codex-profil.

**Misslyckat även om det fungerar tekniskt:** vanliga jobb blir klart långsammare, Fable-kvoten tar slut på rutinarbete eller användaren måste godkänna sådant som förut gick automatiskt.

## 2. Valda vägar

| Fråga | Val | Bortvalt |
|---|---|---|
| Fables roll | **[Beslutat]** Orakel vid grindarna | Fable som orkestrerare: starkare i varje beslut, men tömmer kvoten och saknar färska ögon i slutdomen |
| Styrning | **[Beslutat]** Skill och agenter | Tvingande commit-hook: säkrare, men mer kod och falska stopp. Dynamic workflow: repeterbart, men går inte att styra mitt i en körning |

Spärren omprövas om en riktig körning hoppar över en grind.

## 3. Roller [Förslag]

| Roll | Agentfil | `model` | `effort` | `maxTurns` | `tools` |
|---|---|---|---|---|---|
| Orkestrerare | ingen, huvudsessionen | Opus eller bättre | minst high | – | alla |
| Orakel | `fable-oracle` | `fable` | high | 40 | Read, Grep, Glob |
| Specialist | `opus-specialist` | `opus` | high | 120 | Read, Grep, Glob, Edit, Write, Bash, PowerShell |
| Granskare | `opus-reviewer` | `opus` | high | 80 | Read, Grep, Glob, Bash, PowerShell |
| Djupgranskare | `opus-reviewer-deep` | `opus` | xhigh | 100 | som granskaren |
| Worker | `sonnet-worker` | `sonnet` | medium | 80 | som specialisten |
| UI-testare | `sonnet-ui-tester` | `sonnet` | medium | 120 | Read, Grep, Glob, Bash, ToolSearch, `mcp__obscura__*`, `mcp__plugin_playwright_playwright__*` |
| Scout | `haiku-scout` | `haiku` | medium | 40 | Read, Grep, Glob |

- Djupgranskaren är en egen fil så att xhigh är låst och inte beror på en parameter i anropet. Den granskar vid hög risk och är reserv för oraklet.
- Ingen agent har `Agent`. Bara orkestreraren delegerar.
- **[Nytt]** Ingen agent har `Skill`. Orkestreraren läser relevanta skills och skriver in det som gäller i briefen. Det håller nere startkontexten.
- UI-testaren använder det webbläsarverktyg som användarens regler anger. Den lämnar en delrapport efter varje flöde, i stället för en enda rapport på slutet.
- Granskare och UI-testare är read-only enligt instruktion, eftersom de har skal. Oraklet är read-only genom sin verktygslista.

- **[Nytt]** Oraklet har `omitClaudeMd: true`, så att stilregler och gamla försiktighetsregler inte styr domen. Grindpaketet citerar de projektregler som gäller. Övriga agenter behåller projektets regler.

**Promptstil:** Opus och Fable får utfall, gränser och skäl, utan steglistor. Sonnet och Haiku får korta steg, kravet att köra en riktig kontroll och kravet att fortsätta tills uppdraget är klart. Varje förbud anger sitt skäl och sitt undantag.

## 4. Flöde

### Steg 0: Kontroll

- Läs den egna modellen ur systemprompten och effort ur `${CLAUDE_EFFORT}`.
- Under Opus high: varna med en rad, ange hur man byter, fortsätt och ta med det i slutrapporten. **[Beslutat]** Ett stopp här vore ett extra godkännande i varje sådan körning.
- Skillen sätter inte `model` eller `effort` i sin frontmatter. De gäller bara en tur, och orkestrering spänner över många.
- Saknas agenterna: ange installationskommandot. Låtsas aldrig att en generell agent är en av rollerna.

### Steg 1: Rekognosera

Scouts svarar på avgränsade frågor, parallellt vid behov. Orkestreraren läser själv filerna som avgör planen. Klart när varje fil som ska ändras och dess anropare är kända.

### Steg 2: Planera och riskklassa

Varje del får ägare, filer, bevis och risk.

**Hög risk** är pengar eller beräkning av pengar, sparad data eller schema, migrering, auth, säkerhet, hemligheter, eller publicering av något av detta. Allt annat är låg risk. Risken får höjas under arbetet men aldrig sänkas. Klassningen görs om mot den faktiska diffen i steg 5. Blir risken hög först då körs inte grind 1 i efterhand, men djupgranskning och grind 2 krävs.

Första raden som passar gäller. En liten högriskändring går alltså till specialisten.

| Uppgift | Vem |
|---|---|
| Hög risk, svår bugg, oklar design i koden | Specialist |
| Liten, låg risk, känd plats | Orkestreraren |
| Hitta eller kartlägga | Scout |
| Avgränsat bygge, låg risk | Worker |
| Prova som användare | UI-testare |
| Fler än fem oberoende delar | Föreslå dynamic workflow |

### Steg 3: Grind 1, plan

Körs vid hög risk, oklar arkitektur eller ett beslut som är svårt att backa. Klart när domen är `Kör` eller användaren har avgjort.

### Steg 4: Bygg

- Högst fem skrivare samtidigt, aldrig två i samma fil. Delade filer tas i följd.
- Skrivare kör riktade tester. Orkestreraren kör hela kontrollen när alla är klara.
- **[Nytt]** Worktree är inte standard. Det används bara när repot har commits, `worktree.baseRef` är `"head"` och uppgiften inte beror på ocommittade ändringar.
- En agent som stannat vid turgränsen återupptas med SendMessage. En ny startas inte.
- En rapport är ett påstående. Orkestreraren läser diffen innan den bygger vidare.

### Steg 5: Granska

- Låg risk som en agent byggt: granskare när ändringen rör beteende i flera filer, annars räcker orkestrerarens egen kontroll.
- Hög risk: alltid djupgranskare, oavsett vem som byggde.
- A- och B-fynd rättas av rätt roll och går tillbaka till samma granskare. Efter två underkända varv körs grind 3.
- Klart när en granskning av den slutliga diffen har 0 A/B. En rättning efter sista granskningen betyder att steget inte är klart.

### Steg 6: Grind 2, slutdom

Körs vid hög risk, efter godkänd granskning.

### Steg 7: Avsluta

- Kör hela kontrollen. Kontrollera ögonblicksbilden (avsnitt 6). Committa och publicera enligt projektets regler.
- Rapportera ändringar, agenter med en rad var, grindar med dom och faktisk modell, samt det som inte är verifierat.

## 5. Grindarna [Beslutat: Fable. Förslag: utformning]

| | 1. Plan | 2. Slutdom | 3. Dödläge |
|---|---|---|---|
| Utlösare | Se steg 3 | Se steg 6 | Två misslyckade försök på samma fel, eller två underkända granskningar |
| Får | Begäran ordagrant, plan, valda och förkastade vägar, filvägar | Begäran ordagrant, sökväg till fryst diff, testbevis | Symptom, försök, råa fel, filvägar |
| Får inte | Orkestrerarens förhoppning om utfall | Granskarens fynd och dom | Påstådd rotorsak som om den vore fakta |
| Svarar | `Kör`, `Ändra` eller `Fråga användaren`, plus farligaste antagandet | `Släpp` eller `Stoppa`, med fil och rad per fynd | Rotorsak, säkerhet i bedömningen, nästa experiment |
| Omtag | Ett, samma agent | Ett, efter rättning och omgranskning | Inget. Ett nytt byggförsök, sedan användaren |

- Normalt högst två grindar per jobb.
- Hemligheter tas bort ur paketet innan det skickas.
- Orkestreraren får avvisa ett råd bara med bevis: fil och rad eller kommandoutdata. Annars avgör användaren. `Stoppa` efter omtaget avgörs alltid av användaren.
- Projektregler om automatisk publicering gäller först när grindarna har passerats.
- Advisorn anropas inte vid samma beslut som en grind.

### Faktisk modell och reserv

En agents uppgift om sin egen modell räcker inte. Efter varje grind läser orkestreraren modellfälten i `~/.claude/projects/*/*/subagents/agent-<id>.jsonl`.

- Alla svar från Fable: `Grind: Fable`.
- Något svar från en annan modell, till exempel efter säkerhetsfiltret: `Grind: <modell>, inte Fable`, och djupgranskaren kör grinden som ny instans.
- Fable startar inte, saknar kvot eller kräver krediter: djupgranskaren kör grinden som ny instans och rapporten säger `Grind: Opus, inte Fable`. Slå aldrig på eller godkänn krediter.
- Reserven går inte heller att köra: stanna före commit och fråga användaren.
- Loggen går inte att läsa: `Grind: modell ej verifierad`.

## 6. Fryst underlag [Nytt]

En dom gäller exakt den kod som dömdes. Utan detta kan en sen rättning smita förbi, och en granskare med skal kan ändra filer obemärkt.

`${CLAUDE_SKILL_DIR}/scripts/snapshot.sh <sökvägar>` skriver de angivna sökvägarna till ett tillfälligt git-index och returnerar ett tree-id. Det rör inte det riktiga indexet.

- Kräver minst en sökväg, så att orelaterade ospårade filer och hemligheter inte följer med.
- Klarar nya, borttagna och ospårade filer samt ett repo utan commits.
- Diffen till granskare och orakel skapas med `git diff <jobbets bas> <tree-id>` och sparas i `.orchestrate-review/` i repot, som ignorerar sig själv. Utan commits är basen det tomma trädet.
- Committen tar bara de granskade sökvägarna (`git commit --only`). Dess tree-id ska vara det godkända.
- Utan git: skicka filerna och rapportera `Underlag: inte fryst`.
- Id:t tas före granskning, efter granskning och före commit. Avvikelse betyder att domen är ogiltig.

Detta är ett hjälpskript som orkestreraren kör, ingen spärr.

## 7. Briefen [Förslag]

```
Goal:     vad som är sant när det är klart
Why:      vad användaren vill uppnå
Decided:  val som inte ska omprövas
Freedom:  vad agenten avgör själv, och när den ska stanna
Files:    får ändras / får bara läsas
Traps:    det som kan gå fel, och projektregler eller skills som gäller
Proof:    kommando, och vid beteendeändring fallet som faller före och passerar efter
Risk:     low | high
```

- Fältnamnen är engelska. Innehåll och rapport följer användarens språk. Domorden översätts.
- Scout behöver bara Goal, Why, Files och Proof.
- En bra brief går att utföra utan konversationen. Referensfilen visar ett bra och ett dåligt exempel för worker respektive specialist.

Rapport från byggare: `Status`, `Changed`, `Proof` med utdata, `Decisions` som agenten tog själv, `Open`. Granskare behåller skalan A–D och avslutar med dom samt vad som inte granskades.

## 8. Filer

```
plugins/orchestrate-claude/
  .claude-plugin/plugin.json      2.0.0
  agents/                         sju filer
  skills/orchestrate/
    SKILL.md                      flöde, riskregel, routing. Högst 120 rader
    references/briefs.md          läses före första delegeringen
    references/gates.md           läses när en grind utlöses
    scripts/snapshot.sh
plugins/orchestrate-codex/        1.1.0
README.md                         skrivs om
```

- `description` utlöses av "orchestrate", "orkestrera", "use subagents", "använd subagenter" och "kör med agenter". Inte av att en uppgift bara är stor.
- Alla `description` citeras så att strikt YAML godtar dem.
- **[Beslutat, brytande]** `skills/orchestrate/` i roten tas bort. Den är en tredje kopia som redan skiljer sig. `npx skills` hittar Claude-utgåvan via `marketplace.json`, men installerar inte agenterna och ger inte Codex-utgåvan. README anger pluginen som installationsväg för båda.
- **[Nytt]** README säger att UI-testarens MCP-namn (Obscura, Playwright) byts av den som använder andra webbläsarverktyg.

## 9. Codex [Förslag]

Samma tre agenter, modeller och effort. Ändras: briefen, omgranskning tills 0 A/B med högst två varv, worktree-rådet och rollnamnens texter. Inga grindar och inga nya roller.

## 10. Godkänt när

**Utan modellanrop**

1. All frontmatter klarar en strikt YAML-parser och `claude plugin validate` passerar.
2. En offline-start listar sju agenter med prefixet `orchestrate:`.
3. Testet av `snapshot.sh` täcker ny, ändrad, borttagen och ospårad fil, repo utan commits, tomt argument (fel) och orört riktigt index.

**Med modellanrop, i ett engångsrepo, efter användarens ja**

| Prov | Godkänt |
|---|---|
| Varje agent svarar en gång | Rätt modell och effort i loggen, och rapporten når orkestreraren |
| UI-testaren läser en lokal sida | Webbläsarverktyget laddas via ToolSearch trots verktygslistan |
| Oraklet läser en fryst diff | Ingen behörighetsfråga |
| Workerns första anrop | Under hälften av startkontexten mot samma agent med ärvda verktyg |
| Textändring | Ingen agent, ingen grind |
| Vanlig funktion i tre filer | Worker och granskare, inget Fable |
| Beloppsfunktion med inlagt avrundningsfel | Grind 1, specialist, djupgranskare, grind 2. Felet hittas. |
| Ändring efter slutdom | Domen ogiltigförklaras före commit |
| Fable otillgänglig | Reserven kör och slutrapporten säger det |

Fable-proven kräver att kontot visar Max.

**Efter första riktiga jobbet:** jämför startkontext, A/B-fynd, omtag och andel av Fable-kvoten. Effort justeras efter det, inte före.

## 11. Utrullning

Varje punkt kräver användarens ja.

1. Commit och push. Repot är publikt.
2. Installera pluginen i Claude Code och uppdatera Codex.
3. Ta bort gamla lokala kopior av skillen och dess agenter, efter att listan har visats.

## 12. Lämnat till byggaren

Exakta formuleringar i prompterna, referensfilernas disposition och testets form. Roller, modeller, effort, utlösare och stoppregler ändras inte utan nytt godkännande.

## 13. Ändrat efter skarpa prov

Avsnittet gäller där det skiljer sig från 3–10. Användaren överlät bedömning, rättning och release.

| Vad provet visade | Ändring |
|---|---|
| Oraklet fick inte läsa en diff utanför repot | Diffen ligger i repot och ignorerar sig själv |
| En funktion i tre filer byggdes utan worker och granskare | "Liten" är definierad. Beteende i flera filer går till worker |
| En avgränsad beloppsrättning tog 43 minuter, mot 15 för 1.x | Orkestreraren bygger avgränsad högrisk själv. Djupgranskning och båda grindarna är kvar |
| Specialist och granskare provade miljontals fall och kantfall utanför kontraktet | Bevis i proportion. A och B kräver ett fel som tillåten indata når. Vid en förtroendegräns räknas allt en utomstående kan skicka |
| Granskarna anropade advisorn upp till fem gånger | Granskare, orakel och scout avstår. Byggare frågar bara när de kört fast |
| Små fixar ska gå direkt, och orkestreraren är ingången | Steget Förstå och tre spår: Quick, Standard, High. Spåret väljs per begäran |
| Slutgranskningen: snabbspåret kunde committa användarens oklara ändringar | Statuskontroll före ändring, fråga före commit |
| Avrundningsprovet i avsnitt 10 | Byggaren är orkestreraren, inte specialisten |
| En falsk varning om effort | Värdet som Claude Code fyller i gäller |

## Källor, lästa 2026-11-22

- Claude Code: [subagents](https://code.claude.com/docs/en/sub-agents), [model config](https://code.claude.com/docs/en/model-config), [advisor](https://code.claude.com/docs/en/advisor), [workflows](https://code.claude.com/docs/en/workflows), [worktrees](https://code.claude.com/docs/en/worktrees), [skills](https://code.claude.com/docs/en/skills).
- [Max-planen](https://support.claude.com/en/articles/11049741-what-is-the-max-plan) och [Fable på planen](https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan).
- Anthropics effort- och promptvägledning för Fable 5.2, Opus 5.5, Sonnet 5.5 och Haiku 5.5.
