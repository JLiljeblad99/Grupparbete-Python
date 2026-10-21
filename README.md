# 📊 Projektrapport & Sammanfattning: E-handelsanalys

Grupparbete i Python: analys av `archive/global_ecommerce_sales.csv`.

## Så kör du analysen

```bash
pip install -r requirements.txt
python analys.py
```

Skriptet [`analys.py`](analys.py) läser in datan med pandas, räknar ut alla nyckeltal och skriver ut sammanställningarna nedan.

### Interaktiv KPI-dashboard

```bash
streamlit run app.py
```

[`app.py`](app.py) öppnar en dashboard i webbläsaren (http://localhost:8501) med filter för datum, region, land, kategori, produkt och kundsegment. Tio KPI-kort och diagram räknas om direkt när filtren ändras.

### Geografi, kunder & betalning (Johan)

👉 **Öppna prototypen direkt i webbläsaren: [prototypjohan.streamlit.app](https://prototypjohan.streamlit.app)**

Eller kör den på din egen dator:

```bash
streamlit run johan_geografi_kunder_betalning/geografi_kunder_betalning_prototyp_app.py
```

Mappen [`johan_geografi_kunder_betalning/`](johan_geografi_kunder_betalning/) innehåller analysen, en prototyp-dashboard med världskarta och periodjämförelse, och en [README](johan_geografi_kunder_betalning/README.md) som förklarar resultaten.

---

## 1. Översikt av projektet

Projektet analyserar en global e-handelsdatamängd med **2 000 ordrar** från **2023-01-02 till 2025-12-31**. Ordrarna är lagda av **1 534 unika kunder** i **20 länder** och **5 regioner**. Varje rad är en order med kund, land, produkt, antal, pris, rabatt, frakt, vinst och betalningssätt. Valuta anges inte i datan.

**Verktyg och bibliotek:**
- **Python 3**
- **pandas**: inläsning, gruppering och beräkning av nyckeltal
- **Git och GitHub**: samarbete i teamet

## 2. Viktiga nyckeltal (KPI:er)

| KPI | Värde |
|---|---|
| **Total omsättning** | **484 559** |
| **Total vinst** | **158 872** (vinstmarginal **32,8 %**) |
| **Totalt antal sålda produkter** | **7 115 st** |
| **Totalt antal ordrar** | **2 000** |
| **Genomsnittlig rabatt** | **8,57 %** |
| Genomsnittligt ordervärde | 242 |
| Total fraktkostnad | 25 804 |

## 3. Analys & Insikter per område

### 📈 Försäljning & Trender
- Försäljningen är **stabil över åren**: 164 443 (2023), 155 151 (2024) och 164 965 (2025). Vinstmarginalen ligger konstant runt **32–33 %**.
- **2024 var ett svagare år** (−5,7 %), men 2025 återhämtade sig till den högsta nivån hittills.
- Månaderna varierar mycket, från cirka 7 300 (feb 2025) till cirka 18 000 (jun 2025), men något tydligt säsongsmönster syns inte.
- **272 ordrar (13,6 %) gick med förlust**, men tillsammans förlorade de bara cirka 950.

### 🛋️ Produkter & Kategorier

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

### 🌍 Geografi & Kunder
- **Regioner:** Europa (28,3 %), Nordamerika (27,6 %) och Asien-Stillahavsområdet (25,1 %) står för över **80 %** av försäljningen.
- **Topp-länder:** **Mexiko** (47 217), **Kanada** (45 327) och **USA** (41 333). Alla tre har den högsta marginalen, **33,8 %**.
- **Minst:** UAE, Colombia och Nigeria, med cirka 2 % var.
- **Kundsegment:** **Consumer** står för 52,9 % av försäljningen och 55 % av vinsten och har högst marginal (34,1 %). **Corporate** har lägst marginal (30,4 %).

### 💳 Betalningsmetoder

| Metod | Ordrar | Andel av försäljningen | Marginal |
|---|---|---|---|
| **Credit Card** | 797 | **39,8 %** | 32,3 % |
| PayPal | 609 | 29,5 % | 33,0 % |
| Cash on Delivery | 301 | 15,9 % | **33,3 %** |
| Bank Transfer | 293 | 14,8 % | 32,9 % |

- **Kreditkort är populärast**, och kortbetalningar (kort och PayPal) står för nästan 70 %.
- Skillnaden i lönsamhet mellan betalningssätten är **liten**, bara cirka 1 procentenhet.

## 4. Slutsatser & Rekommendationer

1. **💸 Rabatter sänker lönsamheten kraftigt.** Marginalen sjunker steg för steg från **38,7 % utan rabatt** till **13,4 % vid 30 % rabatt**. → *Begränsa rabatterna till max 10–15 %. Högre rabatter ger mycket lite vinst.*
2. **📎 Se över Office Supplies.** Kategorin har lägst marginal (17 %) och står för 224 av 272 förlustordrar. → *Inför ett minsta ordervärde eller fraktavgift för små ordrar, eller sälj produkterna i större paket.*
3. **🪑 Satsa på möbler och lönsamma nischer.** Furniture driver hälften av omsättningen. Clothing och Technology har högst marginal. → *Prioritera marknadsföring av kontorsmöbler och tillbehör med hög marginal, som headset och kavajer.*
4. **🌎 Bygg vidare i Nordamerika och väx i underrepresenterade regioner.** Mexiko, Kanada och USA är både störst och mest lönsamma. Sydamerika och Mellanöstern/Afrika står bara för cirka 9,5 % var. → *Behåll fokus på Nordamerika och testa riktade kampanjer i till exempel Brasilien och Saudiarabien.*
