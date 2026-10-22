# 📊 KPI-dashboard för ledningsgruppen (Wissam)

En interaktiv dashboard i Streamlit som visar företagets viktigaste nyckeltal (KPI:er) från `archive/global_ecommerce_sales.csv`. Alla siffror räknas om direkt när man ändrar filtren.

## Starta

Kör från projektmappen (`Grupparbete-Python`):

```bash
pip install -r requirements.txt
streamlit run wissam_kpi_dashboard/kpi_dashboard_app.py
```

**På Windows:** skriv `py -m pip install -r requirements.txt` och `py -m streamlit run wissam_kpi_dashboard/kpi_dashboard_app.py`.

Appen öppnas i webbläsaren på http://localhost:8501.

## Filerna i mappen

| Fil | Vad den gör |
|---|---|
| [`kpi_dashboard_app.py`](kpi_dashboard_app.py) | **Dashboarden.** Filter i sidopanelen, tio KPI-kort, fyra diagram med förklaringar och nedladdning av den filtrerade datan. |
| [`kpi_analys.py`](kpi_analys.py) | **Analysen.** Räknar fram alla nyckeltal och skriver ut dem som tabeller i terminalen: `python wissam_kpi_dashboard/kpi_analys.py` |
| [`.streamlit/config.toml`](.streamlit/config.toml) | Gruppens gemensamma mörka färgtema. |

## Filter

- 📅 **Datumintervall**
- 🌍 **Region och land.** Länderna begränsas till de valda regionerna.
- 🛒 **Produktkategori och produkt.** Produkterna begränsas till de valda kategorierna.
- 👥 **Kundsegment**
- ↺ **Återställ alla filter**

Ett tomt filter betyder att alla värden ingår.

## KPI-korten

| KPI | Så räknas den |
|---|---|
| 💰 Total omsättning | Summan av `Total_Sales` |
| 📈 Total vinst | Summan av `Profit` |
| 🎯 Vinstmarginal | Vinst ÷ omsättning |
| 🧾 Antal ordrar | Antal unika `Order_ID` |
| 📦 Sålda produkter | Summan av `Quantity` |
| 🛍️ Snittordervärde (AOV) | Omsättning ÷ antal ordrar |
| 💵 Snittvinst per order | Vinst ÷ antal ordrar |
| 🏷️ Snittrabatt | Medelvärdet av `Discount_Percent` |
| 🧺 Snitt produkter per order | Sålda produkter ÷ antal ordrar |
| ⚠️ Andel förlustordrar | Ordrar med negativ vinst ÷ antal ordrar |

## Diagrammen

| Diagram | Vad det visar |
|---|---|
| Omsättning och vinst per månad | Hur försäljningen och vinsten har utvecklats över tid. |
| Omsättning och vinst per kategori | Vilka produktgrupper som säljer mest och vilka som är mest lönsamma. |
| Topp 10 länder efter omsättning | Var våra viktigaste marknader finns. |
| Vinstmarginal per rabattnivå | Hur mycket rabatterna minskar vinsten. Utan rabatt är marginalen 38,7 %, med 30 % rabatt bara 13,4 %. |
