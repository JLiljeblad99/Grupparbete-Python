# 📊 Gemensam dashboard: E-handel – hela bilden

Den här mappen är **gruppens gemensamma dashboard**. Här har vi slagit ihop våra tre separata dashboards till en enda webbsida, så att man får en komplett bild av datan på ett ställe.

Allt bygger på samma dataset: [`archive/global_ecommerce_sales.csv`](../archive/global_ecommerce_sales.csv).

## 🚀 Så kör du dashboarden

1. Gå till projektmappen (mappen ovanför den här):
   ```bash
   git clone https://github.com/JLiljeblad99/Grupparbete-Python.git
   cd Grupparbete-Python
   ```
   Har du redan projektet räcker det att skriva `git pull` i projektmappen.
2. Installera paketen (behövs bara första gången):
   ```bash
   pip install -r requirements.txt
   ```
3. Starta dashboarden:
   ```bash
   streamlit run gemensam_dashboard/dashboard_app.py
   ```
4. Sidan öppnas i webbläsaren på http://localhost:8501. Stäng av den med `Ctrl + C` i terminalen.

**På Mac:** skriv `pip3` i stället för `pip`, och `python3 -m streamlit run …` om kommandot `streamlit` inte hittas.<br>
**På Windows:** skriv `py -m pip install -r requirements.txt` och `py -m streamlit run …`.

---

## Om datan

| | |
|---|---|
| **Fil** | `archive/global_ecommerce_sales.csv` |
| **Antal ordrar** | 2 000 (en rad = en order) |
| **Period** | 2 januari 2023 – 31 december 2025 |
| **Geografi** | 20 länder i 5 regioner |
| **Kunder** | 1 534 kundnamn i tre kundgrupper: Consumer, Corporate och Home Office |
| **Produkter** | Fyra kategorier: Furniture, Technology, Clothing & Accessories och Office Supplies |
| **Kolumner** | Order-id, datum, kund, kundgrupp, land, region, kategori, produkt, antal, pris, rabatt, försäljning, frakt, vinst och betalsätt |

Datan anger ingen valuta. Eftersom det är en global webbutik visar vi beloppen i **amerikanska dollar (USD)**. Datan verkar vara framtagen för övning, så vissa skillnader är små.

## Filerna i den här mappen

| Fil | Vad den är till för |
|---|---|
| [`dashboard_app.py`](dashboard_app.py) | **Dashboarden.** Hela appen ligger i den här filen. Den läser in CSV-filen och använder inte koden i de andra mapparna, så ingen annans del påverkas om den ändras. |
| [`README.md`](README.md) | Den här filen. Förklarar projektet och dashboarden. |
| [`.streamlit/config.toml`](.streamlit/config.toml) | **Färgtemat**: mörk bakgrund med blå detaljer. Det används automatiskt när appen startas. |

## Vad kommer från vem?

Vi gick igenom alla tre dashboards och tog med de diagram som är tydligast och de funktioner som är mest användbara.

| Del i projektet | Ansvarig | Det här finns med i den gemensamma dashboarden |
|---|---|---|
| [`wissam_kpi_dashboard/`](../wissam_kpi_dashboard/) | Wissam | De **tio KPI-korten**, en **förklaring under varje diagram**, diagrammet **Vinstmarginal per rabattnivå** och **tabellen med nedladdning** av urvalet |
| [`alya_forsaljning_produkter/`](../alya_forsaljning_produkter/) | Alyosh | **Snabböversikten** "Det viktigaste i urvalet", **försäljning och vinst per år**, **kategorier**, den **klickbara produkttabellen** med produktdetaljer, fliken om **förlustordrar** och **Tänk om: fraktavgift för små ordrar** |
| [`johan_geografi_kunder_betalning/`](../johan_geografi_kunder_betalning/) | Johan | **Datumväljaren med jämförelse** (som i Google Ads), **världskartan**, **utveckling över tid**, **kundgrupper**, **frakt, produktmix och betalsätt per region**, **klickbara diagram** som ändrar filtren och **Tänk om: tak för rabatten** |

Det mörka färgtemat och utseendet (rubrikrutan, korten och rutorna) kommer från Johans och Alyoshs delar, som redan använde samma stil.

---

## Så fungerar dashboarden

### 📅 Datum och 🎛️ filter (panelen till vänster)

- **Datum:** välj period med snabbval (t.ex. *Senaste 90 dagarna* eller *Förra året*) eller i en kalender. Från början visas **hela perioden**.
- **Jämförelse:** slå på *⚖️ Jämför med en annan period* och välj *föregående period* eller *samma period förra året*. Då visar KPI-korten en pil med förändringen, och diagrammen visar jämförelseperioden i grått.
- **Filter:** region, land, kundgrupp och kategori. Allt på sidan räknas om direkt.
- **Filtren och diagrammen hänger ihop:** klickar man på ett land på kartan, en kundgrupp eller en kategori i ett diagram ändras filtret i panelen. Klickar man igen visas alla.
- **↺ Återställ allt** tar bort alla val.

### Överst på sidan

- **Tio KPI-kort** med ett litet trenddiagram i varje kort. Håll musen över ⓘ för att se vad nyckeltalet betyder.
- **🔎 Det viktigaste i urvalet:** tre kort med toppar och dalar, t.ex. bästa månaden, största marknaden och produkten som drar in minst vinst.

| KPI | Så räknas den |
|---|---|
| 💰 Försäljning | Summan av `Total_Sales` |
| 📈 Vinst | Summan av `Profit` |
| 🎯 Vinstmarginal | Vinst ÷ försäljning |
| 🧾 Ordrar | Antal unika `Order_ID` |
| 📦 Sålda produkter | Summan av `Quantity` |
| 🛍️ Snittordervärde | Försäljning ÷ antal ordrar |
| 💵 Vinst per order | Vinst ÷ antal ordrar |
| 🏷️ Snittrabatt | Medelvärdet av `Discount_Percent` |
| 🚚 Frakt per order | Medelvärdet av `Shipping_Cost` |
| ⚠️ Förlustordrar | Ordrar med negativ vinst ÷ antal ordrar |

För rabatt, frakt och förlustordrar är det bra när siffran sjunker. Därför visas en minskning i grönt för de korten.

### Flikarna

| Flik | Diagram |
|---|---|
| 📈 **Försäljning & trender** | Utveckling över tid (försäljning, vinst, marginal eller ordrar) · Försäljning och vinst per år |
| 🛋️ **Produkter & kategorier** | Kategorier (klickbara) · Topp 10 produkter · Tabell med alla produkter · Utvecklingen för vald produkt |
| 🌍 **Geografi & kunder** | Världskarta (klickbar) · Länder med mest försäljning (klickbar) · Kundgrupper (klickbara) · Fraktkostnad per region · Vad köps i olika delar av världen? |
| 💳 **Betalning** | Hur betalar kunderna? · Betalsätt i olika delar av världen |
| 🏷️ **Rabatter & förlust** | Vinstmarginal per rabattnivå · Vem får rabatterna? · Förlustordrar per ordervärde · Förlustordrar per kategori · De produkter som har flest förlustordrar |
| 🧪 **Tänk om …** | Tak för rabatten · Små ordrar betalar sin egen frakt |

Längst ner på sidan finns **📋 Visa urvalet som tabell**, där man också kan ladda ner urvalet som en CSV-fil.

### ℹ️ En förklaring under varje diagram

Under varje diagram finns en ruta med tre delar:

- **ℹ️ Vad visar diagrammet?** Vad diagrammet handlar om.
- **👉 Så läser du det:** hur man tolkar diagrammet.
- **💡 Slutsats:** vad vi ser i urvalet just nu. Den texten räknas om när man ändrar filtren.

### 🎨 Färgschema

Samma sak har alltid samma färg, i alla flikar och diagram:

| Färg | Betyder |
|---|---|
| 🔵 Blå `#3987e5` | Försäljning och vald period. Även första värdet i varje grupp: Europa, Privatpersoner, Möbler och Kreditkort. |
| 🟢 Turkos `#199e70` | Vinst |
| 🟣 Lila `#9085e9` | Vinstmarginal |
| ⚪ Grå `#898781` | Jämförelseperioden |
| 🔴 Röd `#d03b3b` | Förlust och minskning. Rött betyder alltid något dåligt. |

| Grupp | Blå | Orange `#d95926` | Turkos | Gul `#c98500` | Lila |
|---|---|---|---|---|---|
| **Region** | Europa | Nordamerika | Asien & Stillahavet | Sydamerika | Mellanöstern & Afrika |
| **Kundgrupp** | Privatpersoner | Företag | Småföretag | | |
| **Kategori** | Möbler | Teknik | Kläder | Kontorsmaterial | |
| **Betalsätt** | Kreditkort | PayPal | Betala vid leverans | Banköverföring | |

På kartan går färgen från mörkblått (lite) till ljusblått (mycket). Färgerna syns bra på mörk bakgrund och går att skilja åt även för den som är färgblind.

---

## Sammanfattning: det här visar datan

Siffrorna gäller hela perioden 2023–2025 med alla filter påslagna.

### 📈 Försäljning & trender
- Total försäljning **$484 559** och vinst **$158 872**, en vinstmarginal på **32,8 %**.
- Försäljningen är **stabil över åren**: 164 443 (2023), 155 151 (2024) och 164 965 (2025). 2024 var ett svagare år, men 2025 blev det bästa hittills.
- Marginalen ligger stadigt runt **32–33 %** varje år.

### 🛋️ Produkter & kategorier
- **Möbler** står för över hälften av försäljningen (52,9 %).
- **Kläder** har högst marginal (37,6 %) och **kontorsmaterial** lägst (17,1 %).
- Störst försäljning har Standing Desk Converter, Ergonomic Office Chair och Corner L-Shaped Desk.

### 🌍 Geografi & kunder
- **Europa, Nordamerika och Asien** står för över **80 %** av försäljningen.
- **Mexiko, Kanada och USA** är de största länderna och har också högst marginal.
- **Frakten** tar nästan dubbelt så stor del av försäljningen i Mellanöstern & Afrika (7,2 %) som i Nordamerika (4,3 %).
- **Privatpersoner** är den viktigaste kundgruppen, med 53 % av försäljningen. **Företag** har lägst marginal (30,4 %) eftersom de oftast får stora rabatter.

### 💳 Betalning
- **Kreditkort** är vanligast (40 % av försäljningen). Kort och PayPal står tillsammans för nästan 70 %.
- Betalsättet påverkar nästan inte vinsten: skillnaden i marginal är bara cirka 1 procentenhet.

### 🏷️ Rabatter & förlustordrar
- Marginalen sjunker från **38,7 % utan rabatt** till **13,4 % vid 30 % rabatt**.
- **272 ordrar (13,6 %) gick med förlust**, de flesta små ordrar inom kontorsmaterial där frakten äter upp vinsten.

### Rekommendationer
1. **Begränsa rabatterna**, särskilt till företagskunder. Testa effekten under *🧪 Tänk om …*.
2. **Se över små ordrar inom kontorsmaterial**, t.ex. med en fraktavgift eller större förpackningar.
3. **Satsa på möbler** och på produkter med hög marginal, som kläder och teknik.
4. **Behåll fokus på Nordamerika** och räkna med högre fraktkostnader om vi vill växa i Sydamerika och Mellanöstern & Afrika.

## Förenklingar att känna till

- **Tänk om …** antar att kunderna hade köpt exakt lika mycket även med lägre rabatt eller en fraktavgift. I verkligheten kan en del kunder välja att inte köpa. Prognoserna räknar på **alla datum**, men följer filtren för region, land, kundgrupp och kategori.
- **Jämförelsen** blir missvisande om jämförelseperioden ligger före 2 januari 2023, när datan börjar. Dashboarden varnar då i panelen till vänster.
- **Kundnamnen** ser slumpmässigt ihopsatta ut, så vi analyserar inte enskilda kunder.
