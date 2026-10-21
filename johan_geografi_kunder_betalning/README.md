# 🌍 Geografi, kunder och betalning

**Ansvarig:** Johan (JLiljeblad99)

Den här delen av projektet tittar på **var** vi säljer, **vem** som köper och **hur** kunderna betalar.

## Filerna i den här mappen

| Fil | Vad den är till för |
|---|---|
| [`README.md`](README.md) | Den här filen. Förklarar resultaten med enkla ord. |
| [`geografi_kunder_betalning_analys.py`](geografi_kunder_betalning_analys.py) | **Analysen.** Räknar fram alla siffror och skriver ut dem som tabeller i terminalen. |
| [`geografi_kunder_betalning_prototyp_app.py`](geografi_kunder_betalning_prototyp_app.py) | **Prototypen (dashboarden).** En interaktiv webbsida där man själv kan välja period, jämföra perioder, filtrera och utforska en världskarta. |
| [`.streamlit/config.toml`](.streamlit/config.toml) | **Färgtemat** (mörkt med blå detaljer) för prototypen. Gäller bara den här appen. |

## Så kör du filerna

Kör kommandona från projektmappen (mappen ovanför den här):

```bash
# Installera paketen (behövs bara en gång)
pip install -r requirements.txt

# Analysen: skriver ut tabellerna i terminalen
python johan_geografi_kunder_betalning/geografi_kunder_betalning_analys.py

# Prototypen: öppnar dashboarden i webbläsaren
streamlit run johan_geografi_kunder_betalning/geografi_kunder_betalning_prototyp_app.py
```

På Windows skriver man `py` i stället för `python` och `py -m streamlit run` i stället för `streamlit run`.

Analysen skriver först ut en översikt (två tabeller) och sedan en tabell för varje fråga nedan.

## Vad kan man göra i prototypen?

- **📅 Datum:** välj period med snabbval (t.ex. *Senaste 90 dagarna*) eller i en kalender, och jämför med *föregående period* eller *samma period förra året*, som i Google Ads.
- **🎛️ Filter:** välj region och kundgrupp. Allt på sidan räknas om direkt.
- **📈 Utveckling över tid:** försäljning, vinst eller ordrar i perioden, med jämförelseperioden som en streckad linje.
- **🗺️ Världskarta:** se försäljning, vinst, marginal eller förändring per land. Klicka på ett land för att se dess profil.
- **🔍 Sök land:** allt om ett land, jämfört med snittet.
- **🧪 Tänk om …:** en prognos som visar hur mycket mer vi hade tjänat med ett tak för rabatterna.
- **Våra fyra frågor:** svaren nedan, som interaktiva diagram.

I prototypen visas beloppen i **amerikanska dollar (USD)**. Datan anger ingen valuta, och dollar är det mest rimliga för en global webbutik.

## Ord som är bra att känna till

| Ord | Betyder |
|---|---|
| **Försäljning** | Hur mycket kunderna har betalat för det de köpt. |
| **Vinst** | Det som blir kvar till företaget när kostnaderna är betalda. |
| **Vinstmarginal** | Hur stor del av försäljningen som blir vinst. 30 % betyder att vi tjänar 30 av varje 100 vi säljer för. |
| **Kundgrupp** | Vilken sorts kund det är: **Consumer** (privatperson), **Corporate** (företag) eller **Home Office** (småföretag och folk som driver firma hemifrån – kallas **Småföretag** i prototypen). |
| **Region** | En del av världen, till exempel Europa eller Nordamerika. |

Datan säger inte vilken valuta det är, så i analysen står beloppen utan valuta (i prototypen antar vi USD).

---

## Översikt: Var och till vem säljer vi mest?

Innan vi går in på frågorna tittar vi på helheten: vilka delar av världen och vilka kundgrupper står för mest försäljning och vinst?

### Regioner

| Region | Ordrar | Försäljning | Vinst | Andel av all försäljning | Andel av all vinst | Vinstmarginal |
|---|---|---|---|---|---|---|
| **Europa** | 503 | **137 006** | **45 672** | **28 %** | **29 %** | 33,3 % |
| Nordamerika | 578 | 133 876 | 45 250 | 28 % | 28 % | **33,8 %** |
| Asien och Stillahavsområdet | 520 | 121 708 | 39 117 | 25 % | 25 % | 32,1 % |
| Sydamerika | 191 | 46 051 | 14 681 | 9 % | 9 % | 31,9 % |
| Mellanöstern och Afrika | 208 | 45 918 | 14 153 | 9 % | 9 % | 30,8 % |

**Svar:** **Europa** säljer mest och ger mest vinst, men **Nordamerika** ligger nästan lika högt och har flest ordrar och bäst vinstmarginal. Tillsammans med Asien står de tre regionerna för **över 80 %** av både försäljningen och vinsten. Sydamerika och Mellanöstern/Afrika är mycket mindre, och där tjänar vi också lite mindre på varje försäljning.

### Kundgrupper

| Kundgrupp | Ordrar | Försäljning | Vinst | Andel av all försäljning | Andel av all vinst | Vinstmarginal |
|---|---|---|---|---|---|---|
| **Privatpersoner (Consumer)** | 1 006 | **256 288** | **87 300** | **53 %** | **55 %** | **34,1 %** |
| Företag (Corporate) | 623 | 146 050 | 44 463 | 30 % | 28 % | 30,4 % |
| Småföretag (Home Office) | 371 | 82 221 | 27 109 | 17 % | 17 % | 33,0 % |

**Svar:** **Privatpersoner** är klart viktigast. De står för över hälften av både försäljningen och vinsten och har bäst vinstmarginal. Företagen står för 30 % av försäljningen men bara 28 % av vinsten. Varför det är så tar vi reda på i fråga 1.

---

## Fråga 1: Varför tjänar vi minst på företagskunder?

Företagskunderna (**Corporate**) ger oss lägst vinstmarginal. Vi ville veta varför.

| Kundgrupp | Ordrar | Rabatt i snitt | Ordrar med mer än 10 % rabatt | Vinstmarginal |
|---|---|---|---|---|
| Privatpersoner (Consumer) | 1 006 | 7,2 % | 22 % | **34,1 %** |
| Småföretag (Home Office) | 371 | 7,8 % | 25 % | 33,0 % |
| **Företag (Corporate)** | 623 | **11,3 %** | **41 %** | **30,4 %** |

**Svar:** Företagen får **större rabatter**. Ungefär 4 av 10 företagsordrar har mer än 10 % rabatt. För privatpersoner är det bara 2 av 10. När vi ger mer rabatt blir det mindre kvar i vinst.

👉 **Vad kan vi göra?** Var mer försiktiga med stora rabatter till företag. Det stämmer med gruppens huvudslutsats om att höga rabatter sänker vinsten.

---

## Fråga 2: Kostar frakten mer i vissa delar av världen?

Vi jämförde hur mycket frakten kostar i förhållande till hur mycket vi säljer.

| Region | Frakt per order i snitt | Andel av försäljningen som går till frakt |
|---|---|---|
| Nordamerika | 10,0 | **4,3 %** |
| Europa | 12,3 | 4,5 % |
| Asien och Stillahavsområdet | 14,5 | 6,2 % |
| Sydamerika | 15,4 | 6,4 % |
| Mellanöstern och Afrika | 16,0 | **7,2 %** |

**Svar:** Ja. I Mellanöstern och Afrika går **nästan dubbelt så stor del** av pengarna till frakt som i Nordamerika. Ju längre bort från de stora marknaderna, desto dyrare blir frakten.

👉 **Vad kan vi göra?** Om vi vill växa i de mindre regionerna måste vi räkna med högre fraktkostnader, till exempel genom att samla fler varor i varje leverans.

---

## Fråga 3: Köper man olika saker i olika delar av världen?

Tabellen visar hur stor del av försäljningen i varje region som kommer från varje produktkategori. Varje rad blir tillsammans 100 %.

| Region | Möbler | Teknik | Kläder | Kontorsmaterial |
|---|---|---|---|---|
| Europa | **56 %** | 27 % | 14 % | 3 % |
| Nordamerika | **55 %** | 27 % | 14 % | 4 % |
| Asien och Stillahavsområdet | 52 % | 29 % | 14 % | 5 % |
| Mellanöstern och Afrika | 47 % | **34 %** | 16 % | 4 % |
| Sydamerika | 45 % | **34 %** | 17 % | 4 % |

**Svar:** Ja, lite. Europa och Nordamerika köper mest **möbler**. Sydamerika och Mellanöstern/Afrika köper mer **teknik** än de andra.

👉 **Vad kan vi göra?** Lyft fram tekniska produkter när vi marknadsför oss i Sydamerika och Mellanöstern/Afrika.

---

## Fråga 4: Betalar man på olika sätt i olika delar av världen?

Tabellen visar hur stor del av ordrarna i varje region som betalades med varje metod. Varje rad blir tillsammans 100 %.

| Region | Kreditkort | PayPal | Betalning vid leverans | Banköverföring |
|---|---|---|---|---|
| Nordamerika | **45 %** | 29 % | 12 % | 14 % |
| Sydamerika | 42 % | 29 % | 15 % | 13 % |
| Asien och Stillahavsområdet | 41 % | 31 % | 15 % | 14 % |
| Europa | 35 % | 31 % | **18 %** | 16 % |
| Mellanöstern och Afrika | 33 % | 33 % | 16 % | **18 %** |

**Svar:** Kreditkort är vanligast överallt, men mest i **Nordamerika**. I **Europa** betalar fler vid leverans, och i **Mellanöstern/Afrika** är PayPal lika vanligt som kort.

👉 **Vad kan vi göra?** Erbjud alla betalsätt i alla regioner, särskilt betalning vid leverans i Europa. Gruppens analys visar att betalsättet nästan inte påverkar vinsten, så det handlar om att göra det lätt för kunden att köpa.

---

## Sammanfattning

- **Europa och Nordamerika** är våra största regioner. Tillsammans med Asien står de för över 80 % av försäljningen och vinsten.
- **Privatpersoner** är den viktigaste kundgruppen, med över hälften av försäljningen och vinsten.

1. **Företagskunder** ger minst vinst eftersom de får störst rabatter.
2. **Frakten** är nästan dubbelt så dyr i Mellanöstern/Afrika som i Nordamerika.
3. **Europa och Nordamerika** köper mest möbler. **Sydamerika och Mellanöstern/Afrika** köper mer teknik.
4. **Kreditkort** är vanligast överallt, men i Europa är betalning vid leverans populärare än på andra håll.

> **Bra att veta:** Datan verkar vara framtagen för övning och inte hämtad från ett riktigt företag. Vissa skillnader är därför små. Kundnamnen ser slumpmässigt ihopsatta ut, så vi har inte analyserat enskilda kunder.
