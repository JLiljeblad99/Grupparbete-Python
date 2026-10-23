# 📊 E-commerce Customer Sales Dashboard

Grupparbete i Python: analys av `global_ecommerce_sales.csv` (2 000 ordrar, 2023–2025), med en interaktiv dashboard byggd i **Streamlit** och **Plotly**.

👉 **Öppna dashboarden direkt i webbläsaren: [analysprojekt.streamlit.app](https://analysprojekt.streamlit.app)**

**Innehåll**

1. [Kom igång](#-kom-igång)
2. [Projektets filer](#️-projektets-filer)
3. [Hur delarna hänger ihop](#-hur-delarna-hänger-ihop)
4. [Så gör du vanliga ändringar](#️-så-gör-du-vanliga-ändringar)
5. [Jobba tillsammans utan konflikter](#-jobba-tillsammans-utan-konflikter)
6. [Så fungerar dashboarden](#-så-fungerar-dashboarden)
7. [Om datan](#-om-datan)
8. [Projektrapport: analys och slutsatser](#-projektrapport-analys-och-slutsatser)

---

## 🚀 Kom igång

```bash
git clone https://github.com/JLiljeblad99/Grupparbete-Python.git
cd Grupparbete-Python
pip install -r requirements.txt        # behövs bara första gången
streamlit run dashboard_app.py
```

Sidan öppnas på http://localhost:8501. Stäng av den med `Ctrl + C` i terminalen. Har du redan projektet räcker det med `git pull`.

- **Mac:** skriv `pip3` i stället för `pip`, och `python3 -m streamlit run dashboard_app.py` om kommandot `streamlit` inte hittas.
- **Windows:** skriv `py -m pip install -r requirements.txt` och `py -m streamlit run dashboard_app.py`.
- **Streamlit Cloud:** appen ligger på [analysprojekt.streamlit.app](https://analysprojekt.streamlit.app) och uppdateras automatiskt varje gång någon pushar till `main`. I appens inställningar ska *Main file path* vara `dashboard_app.py`.

När du sparar en fil visar Streamlit en ruta uppe till höger. Klicka på **Rerun** för att se ändringen, eller på **Always rerun** så laddas sidan om automatiskt varje gång.

---

## 🗂️ Projektets filer

```
Grupparbete-Python/
├── dashboard_app.py        startfilen – sätter ihop sidan, innehåller nästan ingen egen kod
│
├── installningar.py        fasta värden: färger, svenska namn, standardval
├── data.py                 läser in CSV-filen och översätter kolumnerna
├── berakningar.py          alla uträkningar (summor, marginaler, perioder, prognoser)
├── formatering.py          hur tal, belopp, procent och datum skrivs ("$137 006", "33,8 %")
├── diagram.py              alla Plotly-diagram och kartan
├── stil.py                 CSS: hur korten, rubrikerna och rutorna ser ut
│
├── ui/                     allt som syns på sidan
│   ├── komponenter.py      byggstenar: kort, rubrik, förklaring, visa diagram
│   ├── filter.py           sidans minne: vad som är valt, Uppdatera, Återställ, klick i diagram
│   ├── sidopanel.py        panelen till vänster: datum, jämförelse och filter
│   ├── oversikt.py         rubriken, KPI-korten, snabböversikten och tabellen längst ner
│   ├── trender.py          flik: Försäljning & trender
│   ├── produkter.py        flik: Produkter & kategorier
│   ├── geografi.py         flik: Geografi & kunder
│   ├── betalning.py        flik: Betalning
│   ├── rabatter.py         flik: Rabatter & förlust
│   └── tank_om.py          flik: Tänk om …
│
├── global_ecommerce_sales.csv   datan (läses av data.py)
├── .streamlit/config.toml  färgtemat (mörkt), läses automatiskt av Streamlit
├── requirements.txt        paketen som behövs (pandas, streamlit, plotly) – används av Streamlit Cloud
├── .gitignore              filer som git ska strunta i (t.ex. __pycache__)
└── README.md               den här filen
```

### Vad varje fil gör

| Fil | Syfte | Innehåller | Ändra här när du vill … |
|---|---|---|---|
| [`dashboard_app.py`](dashboard_app.py) | Startfilen. Bestämmer **ordningen** på sidan. | Sidinställningar, inläsning av datan, sidopanel, KPI-kort, listan med flikar, tabellen. | … lägga till, ta bort eller byta ordning på flikar. |
| [`installningar.py`](installningar.py) | Ett ställe för **alla fasta värden**, så att samma sak ser likadan ut överallt. | Färger (`BLA`, `MATT_FARG`, `REGION_FARG` …), översättningar (`REGIONER`, `LANDER` …), snabbval för datum. | … byta en färg, ett svenskt namn eller ett standardval. |
| [`data.py`](data.py) | Det **enda** stället som läser datafilen. | `hamta_data()` (läser och städar CSV:n, lägger till svenska kolumner), `datumgranser()`, `land_till_region()`. | … lägga till en ny kolumn som flera delar behöver, eller byta datafil. |
| [`berakningar.py`](berakningar.py) | **All räkning** på datan. Ritar inget. | `summera()`, `nyckeltal()`, perioder och jämförelse, `tidsserie()`, klassen `Urval`, och en funktion per diagram (sorterade per flik). | … ändra hur en siffra räknas ut, eller lägga till en ny uträkning. |
| [`formatering.py`](formatering.py) | Gör om tal och datum till **svensk text**. | `tal()`, `pengar()`, `procent()`, `procentenheter()`, `forandring()`, `datum_text()`, `steg_text()`. | … ändra hur tal eller datum skrivs ut. |
| [`diagram.py`](diagram.py) | **Bygger alla diagram.** Tar färdiga siffror och ger tillbaka en Plotly-figur. | `snygga_till()` (gemensamt utseende), `jamforelse_staplar()`, och en funktion per diagram (sorterade per flik). | … ändra hur ett diagram ser ut: färg, höjd, text på staplarna, hover-rutor. |
| [`stil.py`](stil.py) | Sidans **CSS**. | `lagg_till_css()`. | … ändra utseendet på KPI-korten, rubrikerna eller förklaringsrutorna. |
| [`ui/komponenter.py`](ui/komponenter.py) | **Byggstenarna** som alla flikar använder. | `kort()`, `rubrik()`, `forklaring()`, `punktkort()`, `visa()`. | … ändra hur *alla* kort eller förklaringar ser ut. |
| [`ui/filter.py`](ui/filter.py) | Håller reda på **vad som är valt**. | Startvärden, Uppdatera, Återställ, klick på land/stapel i diagram, `las_urval()`. | … lägga till ett filter eller ändra vad ett klick i ett diagram gör. |
| [`ui/sidopanel.py`](ui/sidopanel.py) | **Ritar panelen** till vänster. | Datumväljaren, jämförelsen, filterlistorna, knapparna. | … ändra hur panelen ser ut. |
| [`ui/oversikt.py`](ui/oversikt.py) | Det som står **ovanför och under flikarna**. | Sidrubriken, `KPI_KORT` (de tio korten), snabböversikten, tabellen med nedladdning. | … lägga till eller ändra ett KPI-kort. |
| [`ui/trender.py`](ui/trender.py) … [`ui/tank_om.py`](ui/tank_om.py) | **En fil per flik.** | En funktion `visa_flik(urval)` som ritar fliken: kort, diagram och förklaringar. | … ändra eller lägga till något i en flik. |
| [`.streamlit/config.toml`](.streamlit/config.toml) | Streamlits **färgtema** (bakgrund, knappar). | `[theme]` med färgkoder. | … ändra bakgrunds- eller knappfärg. Ändra då samma färg i `installningar.py`. |
| [`requirements.txt`](requirements.txt) | **Paketen** som behövs för att köra appen. | `pandas`, `streamlit`, `plotly`. | … börja använda ett nytt paket. Utan det kraschar appen på Streamlit Cloud. |

---

## 🧩 Hur delarna hänger ihop

Streamlit kör om **hela** `dashboard_app.py` uppifrån och ner varje gång man klickar på något. Så här går ett varv:

```
 global_ecommerce_sales.csv
      │
      ▼
 data.hamta_data()                    läser filen en gång och sparar den i minnet (@st.cache_data)
      │  alla ordrar
      ▼
 ui/filter.las_urval()                läser vad som är valt (st.session_state)
      │  └── berakningar.skapa_urval()  filtrerar och räknar ut nyckeltal och tidsserier
      │
      ▼  urval  (ett Urval-objekt: urval.df, urval.jmf, urval.period, urval.nu …)
      │
      ├── ui/sidopanel.visa(urval)
      ├── ui/oversikt.visa_kpi_kort(urval)
      └── ui/<flik>.visa_flik(urval)    för varje flik:
                 │
                 ├── berakningar.<uträkning>(urval.df)   →  tabell med siffror
                 ├── diagram.<diagram>(tabell)           →  Plotly-figur
                 └── komponenter.kort / visa / forklaring  →  syns på sidan
```

**Lagren och reglerna mellan dem:**

| Lager | Filer | Får använda | Får **inte** |
|---|---|---|---|
| Inställningar | `installningar.py` | ingenting | importera andra projektfiler |
| Data | `data.py` | installningar | räkna nyckeltal eller rita |
| Uträkningar | `berakningar.py` | installningar | använda `st.` (Streamlit) eller Plotly |
| Text | `formatering.py` | installningar | räkna på datan |
| Diagram | `diagram.py` | installningar, formatering | använda `st.` eller räkna på hela datan |
| Sidan | `ui/`, `stil.py`, `dashboard_app.py` | allt ovan | innehålla stora uträkningar (lägg dem i `berakningar.py`) |

Med de här reglerna vet man alltid var något finns: **en siffra är fel → `berakningar.py`. Ett diagram ser fel ut → `diagram.py`. Något står på fel ställe → `ui/`.**

### `Urval`: det som filtren har valt ut

Alla flikar får samma `urval` och läser det de behöver. Fälten finns i klassen `Urval` i [`berakningar.py`](berakningar.py). De viktigaste är:

| Fält | Vad det är |
|---|---|
| `urval.df` | Ordrarna i vald period, efter alla filter. **Det här använder nästan alla diagram.** |
| `urval.jmf` | Samma sak för jämförelseperioden. `None` om man inte jämför. |
| `urval.df_alla_lander` | Vald period, men alla länder (kartan och topplistan visar alltid alla länder). |
| `urval.bas` | Alla datum, men filtrerat på region, kundgrupp och kategori (används av *Tänk om …*). |
| `urval.period`, `urval.jamfor_period` | `(första dag, sista dag)` |
| `urval.land`, `urval.regioner`, `urval.kundgrupper`, `urval.kategorier` | Det som är valt i filtren. |
| `urval.nu`, `urval.forut` | De tio nyckeltalen för vald period och jämförelseperioden (en `dict`). |
| `urval.serie_nu`, `urval.serie_jmf` | Nyckeltalen per dag, vecka eller månad. |
| `urval.frekvens`, `urval.steg` | `"D"`/`"7D"`/`"MS"` och `"dag"`/`"vecka"`/`"månad"`. Beror på periodens längd. |

---

## 🛠️ Så gör du vanliga ändringar

### Lägga till ett nytt diagram i en flik

Exempel: *Försäljning per veckodag* i fliken Försäljning & trender.

**1. Uträkningen** i [`berakningar.py`](berakningar.py), under rubriken för fliken:

```python
def per_veckodag(df):
    # Försäljning för varje veckodag (måndag = 0)
    return df.groupby(df["Order_Date"].dt.dayofweek)["Total_Sales"].sum()
```

**2. Diagrammet** i [`diagram.py`](diagram.py), under samma rubrik:

```python
def per_veckodag(serie):
    # Stående staplar med försäljningen per veckodag
    fig = go.Figure(go.Bar(x=["mån", "tis", "ons", "tor", "fre", "lör", "sön"], y=serie.values,
                           marker_color=MATT_FARG["Försäljning"], marker_cornerradius=4))
    snygga_till(fig, 320, pengar_y=True)
    return fig
```

**3. Visa det** i fliken, [`ui/trender.py`](ui/trender.py):

```python
    with kort("🗓️", "Försäljning per veckodag"):
        serie = berakningar.per_veckodag(urval.df)
        visa(diagram.per_veckodag(serie), "veckodag")      # namnet måste vara unikt på sidan
        forklaring("Hur mycket vi säljer varje veckodag.",
                   f"Bäst säljer vi på dag {serie.idxmax()}.")
```

Tänk på:
- Lägg alltid diagrammet i ett `kort(...)` och avsluta med `forklaring(...)`, så att alla kort ser likadana ut.
- Det andra argumentet till `visa()` (här `"veckodag"`) måste vara **unikt** på hela sidan.
- Använd färgerna i `installningar.py` (`MATT_FARG`, `KATEGORI_FARG` …) i stället för egna färgkoder.
- Två kort bredvid varandra: `vanster, hoger = st.columns(2)` och sedan `with vanster, kort(...):`.

### Göra ett diagram klickbart (filtrera sidan)

Skicka med en funktion från [`ui/filter.py`](ui/filter.py) till `visa()`:

```python
visa(fig, "kategorier", partial(nar_stapel_klickas, "kategori"))   # liggande staplar med kategorinamn på y-axeln
visa(fig, "karta", nar_land_klickas)                              # karta eller staplar med länder
```

### Lägga till en ny flik

1. Skapa `ui/min_flik.py` med en funktion `visa_flik(urval)` (kopiera gärna en befintlig flik som mall).
2. Lägg till fliken i `FLIKAR` i [`dashboard_app.py`](dashboard_app.py): `"🆕 Min flik": min_flik,` och importera den på raden `from ui import …`.

### Lägga till ett KPI-kort

Lägg till nyckeltalet i `nyckeltal()` i [`berakningar.py`](berakningar.py) och en rad i `KPI_KORT` i [`ui/oversikt.py`](ui/oversikt.py). Korten visas i rader om fem.

### Ändra en färg eller ett namn

Ändra bara i [`installningar.py`](installningar.py). Alla diagram och CSS:en hämtar sina värden därifrån. Bakgrunds- och knappfärger finns också i [`.streamlit/config.toml`](.streamlit/config.toml).

### Om du lägger till något som ska sparas mellan klick

Widgetar med `key="..."` sparas automatiskt i `st.session_state`. Lägg till nyckeln i `FLIKARNAS_VAL` i [`ui/filter.py`](ui/filter.py) om valet ska nollställas när man klickar på **↺ Återställ allt**.

### Testa innan du pushar

1. Kör `streamlit run dashboard_app.py` och klicka igenom **alla** flikar.
2. Testa med jämförelse påslagen (⚖️), med ett land valt och med en kort period (t.ex. *Senaste 7 dagarna*). Det är där fel brukar dyka upp, t.ex. när en tabell blir tom.
3. Kontrollera att det inte finns någon röd felruta på sidan eller fel i terminalen.

---

## 🤝 Jobba tillsammans utan konflikter

Eftersom varje flik har en egen fil kan vi jobba samtidigt utan att ändra på samma ställe. Det här är vem som är **huvudansvarig** för vilka filer, utifrån vem som gjorde den delen från början:

| Ansvarig | Filer |
|---|---|
| **Alyosh** | `ui/trender.py`, `ui/produkter.py` |
| **Johan** | `ui/geografi.py`, `ui/betalning.py`, `ui/sidopanel.py`, `ui/filter.py` |
| **Wissam** | `ui/oversikt.py` (KPI-korten), `ui/rabatter.py` |
| **Alla** | `ui/tank_om.py`, `berakningar.py`, `diagram.py`, `installningar.py`, `ui/komponenter.py`, `stil.py`, `dashboard_app.py`, `README.md` |

**Regler:**

1. **`git pull` innan du börjar**, varje gång.
2. **Gemensamma filer:** i `berakningar.py` och `diagram.py` lägger du nya funktioner **under rubriken för din flik**. Då ändrar vi på olika ställen i filen, och git kan slå ihop ändringarna själv. Ändra inte i någon annans funktioner utan att säga till.
3. **Säg till i gruppen innan du ändrar** `installningar.py`, `ui/komponenter.py`, `stil.py` eller `snygga_till()`/`jamforelse_staplar()` i `diagram.py`, eftersom de påverkar alla flikar.
4. **Små commits ofta**, med en tydlig beskrivning på svenska (t.ex. *"Geografi: lägg till diagram över frakt per land"*).
5. Gärna en **egen branch** och en pull request på GitHub för större ändringar: `git switch -c johan/frakt-per-land`.
6. Får du en konflikt ändå: öppna filen, leta upp `<<<<<<<`, behåll båda ändringarna om de inte hör ihop, och ta bort markeringarna.

**Kodstil:** kommentarer och namn på svenska utan å, ä och ö i namnen (`berakningar`, `forklaring`). Varje funktion har en kommentar som förklarar vad den gör, och varje fil börjar med en beskrivning av vad som finns i den.

---

## 🖥️ Så fungerar dashboarden

### 📅 Datum och 🎛️ filter (panelen till vänster)

- **Datum:** välj period med snabbval (t.ex. *Senaste 90 dagarna* eller *Förra året*) eller i en kalender. Från början visas **hela perioden**.
- **Jämförelse:** slå på *⚖️ Jämför med en annan period* och välj *föregående period* eller *samma period förra året*. Då visar KPI-korten en pil med förändringen, och diagrammen visar jämförelseperioden i grått.
- **Filter:** region, land, kundgrupp och kategori. En tom lista betyder att alla ingår.
- **✓ Uppdatera:** ändringarna i panelen börjar gälla först när man klickar på **Uppdatera**. Knappen lyser blått när det finns ändringar som inte gäller än.
- **Filtren och diagrammen hänger ihop:** klickar man på ett land på kartan, en kundgrupp eller en kategori filtreras sidan **direkt**, och filtret i panelen ändras. Klickar man igen visas alla.
- **↺ Återställ allt** går tillbaka till hela perioden och alla filter, direkt.
- **Flikarna:** vald flik syns i adressen (`?flik=…`), så man kan skicka en länk direkt till en viss flik.

### Överst på sidan

- **Tio KPI-kort.** När man jämför två perioder visar en pil hur mycket nyckeltalet har ändrats. Håll musen över ⓘ för att se vad nyckeltalet betyder och siffran för jämförelseperioden.
- **🔎 Det viktigaste i urvalet:** tre kort med toppar och dalar.

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

För rabatt, frakt och förlustordrar är det bra när siffran sjunker, så där visas en minskning i grönt.

### Flikarna

| Flik | Fil | Diagram |
|---|---|---|
| 📈 **Försäljning & trender** | `ui/trender.py` | Utveckling över tid · Försäljning och vinst per år |
| 🛋️ **Produkter & kategorier** | `ui/produkter.py` | Kategorier (klickbara) · Topp 10 produkter · Tabell med alla produkter · Utvecklingen för vald produkt |
| 🌍 **Geografi & kunder** | `ui/geografi.py` | Världskarta (klickbar) · Länder med mest försäljning (klickbar) · Kundgrupper (klickbara) · Fraktkostnad per region · Vad köps i olika delar av världen? |
| 💳 **Betalning** | `ui/betalning.py` | Lönsamhet per betalsätt · Betalsätt i vald region eller valt land |
| 🏷️ **Rabatter & förlust** | `ui/rabatter.py` | Vinstmarginal per rabattnivå · Vem får rabatterna? · Förlustordrar per ordervärde och per kategori · Produkterna med flest förlustordrar |
| 🧪 **Tänk om …** | `ui/tank_om.py` | Tak för rabatten · Små ordrar betalar sin egen frakt |

Under varje diagram finns en förklaring: **ℹ️ Vad visar diagrammet?** och **💡** en slutsats om urvalet just nu, som räknas om när man ändrar filtren. Längst ner finns **📋 Visa urvalet som tabell**, där man kan ladda ner urvalet som CSV.

### 🎨 Färgschema

Samma sak har alltid samma färg. Färgerna finns i [`installningar.py`](installningar.py).

| Färg | Betyder |
|---|---|
| 🔵 Blå `#3987e5` | Försäljning och vald period. Även första värdet i varje grupp. |
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

### Förenklingar att känna till

- **Tänk om …** antar att kunderna hade köpt exakt lika mycket även med lägre rabatt eller en fraktavgift. Prognoserna räknar på **alla datum**, men följer filtren för region, land, kundgrupp och kategori.
- **Jämförelsen** blir missvisande om jämförelseperioden ligger före 2 januari 2023, när datan börjar. Dashboarden varnar då i panelen.
- **Kundnamnen** ser slumpmässigt ihopsatta ut, så vi analyserar inte enskilda kunder.

---

## 📁 Om datan

| | |
|---|---|
| **Fil** | `global_ecommerce_sales.csv` |
| **Antal ordrar** | 2 000 (en rad = en order) |
| **Period** | 2 januari 2023 – 31 december 2025 |
| **Geografi** | 20 länder i 5 regioner |
| **Kunder** | 1 534 kundnamn i tre kundgrupper: Consumer, Corporate och Home Office |
| **Produkter** | Fyra kategorier: Furniture, Technology, Clothing & Accessories och Office Supplies |
| **Kolumner** | Order-id, datum, kund, kundgrupp, land, region, kategori, produkt, antal, pris, rabatt, försäljning, frakt, vinst och betalsätt |

Datan anger ingen valuta. Eftersom det är en global webbutik visar vi beloppen i **amerikanska dollar (USD)**. I dashboarden översätts namnen till svenska (se `installningar.py`).

**Verktyg och bibliotek:** Python 3 · **pandas** (inläsning och beräkningar) · **Streamlit** (webbsidan) · **Plotly** (diagram och världskarta) · **Git och GitHub** (samarbete).

---

## 📝 Projektrapport: analys och slutsatser

### Vem gjorde vad?

Från början gjorde vi var sin dashboard och slog sedan ihop dem. De separata delarna är borttagna, men finns kvar i git-historiken.

| Ursprunglig del | Ansvarig | Det här finns med i den gemensamma dashboarden |
|---|---|---|
| KPI-dashboard | Wissam | De **tio KPI-korten**, en **förklaring under varje diagram**, **Vinstmarginal per rabattnivå** och **tabellen med nedladdning** |
| Försäljning & produkter | Alyosh | **Snabböversikten**, **försäljning och vinst per år**, **kategorier**, den **klickbara produkttabellen**, **förlustordrar** och **Tänk om: fraktavgift för små ordrar** |
| Geografi, kunder & betalning | Johan | **Datumväljaren med jämförelse**, **världskartan**, **utveckling över tid**, **kundgrupper**, **frakt, produktmix och betalsätt per region**, **klickbara diagram** och **Tänk om: tak för rabatten** |

### Viktiga nyckeltal (hela perioden)

| KPI | Värde |
|---|---|
| **Total omsättning** | **484 559** |
| **Total vinst** | **158 872** (vinstmarginal **32,8 %**) |
| **Totalt antal sålda produkter** | **7 115 st** |
| **Totalt antal ordrar** | **2 000** |
| **Genomsnittlig rabatt** | **8,57 %** |
| Genomsnittligt ordervärde | 242 |
| Total fraktkostnad | 25 804 |

### 📈 Försäljning & trender
- Försäljningen är **stabil över åren**: 164 443 (2023), 155 151 (2024) och 164 965 (2025). Vinstmarginalen ligger konstant runt **32–33 %**.
- **2024 var ett svagare år** (−5,7 %), men 2025 återhämtade sig till den högsta nivån hittills.
- Månaderna varierar mycket, från cirka 7 300 (feb 2025) till cirka 18 000 (jun 2025), men något tydligt säsongsmönster syns inte.
- **272 ordrar (13,6 %) gick med förlust**, men tillsammans förlorade de bara cirka 950.

### 🛋️ Produkter & kategorier

| Kategori | Andel av försäljningen | Andel av vinsten | Marginal |
|---|---|---|---|
| **Furniture** | **52,9 %** | **51,1 %** | 31,7 % |
| Technology | 28,8 % | 30,4 % | 34,6 % |
| Clothing & Accessories | 14,3 % | 16,4 % | **37,6 %** |
| Office Supplies | 4,0 % | 2,1 % | **17,1 %** |

- **Störst försäljning:** Standing Desk Converter (46 614), Ergonomic Office Chair (45 405) och Corner L-Shaped Desk (41 070).
- **Störst vinst:** Ergonomic Office Chair (15 105), Standing Desk Converter (14 694) och Corner L-Shaped Desk (13 663).
- **Högst marginal:** Business Casual Blazer (41,9 %) och Wireless Bluetooth Headphones (37,5 %).
- **Problemprodukter:** Paper Clips Box går **med förlust** (−8,9 %), och Highlighters Neon Pack går runt utan vinst. **224 av 513 Office Supplies-ordrar (44 %) gick med förlust.** Det beror troligen på att fraktkostnaden är hög i förhållande till det låga priset.

### 🌍 Geografi & kunder
- **Regioner:** Europa (28,3 %), Nordamerika (27,6 %) och Asien-Stillahavsområdet (25,1 %) står för över **80 %** av försäljningen.
- **Topp-länder:** **Mexiko** (47 217), **Kanada** (45 327) och **USA** (41 333). Alla tre har den högsta marginalen, **33,8 %**.
- **Minst:** UAE, Colombia och Nigeria, med cirka 2 % var.
- **Frakten** tar nästan dubbelt så stor del av försäljningen i Mellanöstern & Afrika (7,2 %) som i Nordamerika (4,3 %).
- **Kundsegment:** **Consumer** står för 52,9 % av försäljningen och 55 % av vinsten och har högst marginal (34,1 %). **Corporate** har lägst marginal (30,4 %), eftersom de oftast får stora rabatter.

### 💳 Betalningsmetoder

| Metod | Ordrar | Andel av försäljningen | Marginal |
|---|---|---|---|
| **Credit Card** | 797 | **39,8 %** | 32,3 % |
| PayPal | 609 | 29,5 % | 33,0 % |
| Cash on Delivery | 301 | 15,9 % | **33,3 %** |
| Bank Transfer | 293 | 14,8 % | 32,9 % |

- **Kreditkort är populärast**, och kortbetalningar (kort och PayPal) står för nästan 70 %.
- Skillnaden i lönsamhet mellan betalningssätten är **liten**, bara cirka 1 procentenhet.

### Slutsatser & rekommendationer

1. **💸 Rabatter sänker lönsamheten kraftigt.** Marginalen sjunker steg för steg från **38,7 % utan rabatt** till **13,4 % vid 30 % rabatt**. → *Begränsa rabatterna till max 10–15 %, särskilt till företagskunder. Testa effekten under 🧪 Tänk om ….*
2. **📎 Se över Office Supplies.** Kategorin har lägst marginal (17 %) och står för 224 av 272 förlustordrar. → *Inför ett minsta ordervärde eller fraktavgift för små ordrar, eller sälj produkterna i större paket.*
3. **🪑 Satsa på möbler och lönsamma nischer.** Furniture driver hälften av omsättningen. Clothing och Technology har högst marginal. → *Prioritera marknadsföring av kontorsmöbler och tillbehör med hög marginal, som headset och kavajer.*
4. **🌎 Bygg vidare i Nordamerika och väx i underrepresenterade regioner.** Mexiko, Kanada och USA är både störst och mest lönsamma. Sydamerika och Mellanöstern/Afrika står bara för cirka 9,5 % var. → *Behåll fokus på Nordamerika, räkna med högre fraktkostnader och testa riktade kampanjer i till exempel Brasilien och Saudiarabien.*
