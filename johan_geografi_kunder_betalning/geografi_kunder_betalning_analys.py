"""Analys av geografi, kunder och betalningsmetoder.

Först visas en översikt:
  - Vilka regioner står för mest försäljning och vinst?
  - Vilka kundgrupper står för mest försäljning och vinst?

Sedan svarar programmet på fyra frågor:
  1. Varför har kundgruppen Corporate lägst vinstmarginal?
  2. Kostar frakten mer i vissa regioner?
  3. Köper man olika saker i olika delar av världen?
  4. Betalar man på olika sätt i olika delar av världen?

Förklaring av resultaten finns i README.md i samma mapp.

Kör från projektmappen:
    python johan_geografi_kunder_betalning/geografi_kunder_betalning_analys.py
"""
from pathlib import Path   # hjälper till att hitta filer på datorn

import pandas as pd        # verktyget vi använder för att läsa och räkna på datan

# Här ligger datan vi analyserar: filen global_ecommerce_sales.csv i mappen archive.
# Path(__file__).parent är mappen det här programmet ligger i (johan_geografi_kunder_betalning),
# och .parent en gång till går upp till projektmappen, där mappen archive finns.
CSV_FIL = Path(__file__).parent.parent / "archive" / "global_ecommerce_sales.csv"


def las_data():
    # Läser in CSV-filen till en tabell (kallas "df", kort för DataFrame).
    # parse_dates gör att Order_Date läses som datum i stället för vanlig text.
    return pd.read_csv(CSV_FIL, parse_dates=["Order_Date"])


def rubrik(text):
    # Skriver ut en tydlig rubrik så att det blir lätt att se var varje fråga börjar
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


# ---------------------------------------------------------------------------
# Översikt: vem står för mest försäljning och vinst?
# ---------------------------------------------------------------------------
def oversikt(df, kolumn, titel):
    # Samma uträkning fungerar för både regioner och kundgrupper,
    # så vi skickar in vilken kolumn vi vill dela upp efter (t.ex. "Region")
    rubrik(f"Översikt: {titel}")

    # Dela upp ordrarna efter kolumnen och summera försäljning och vinst för varje del
    tabell = df.groupby(kolumn).agg(
        Ordrar=("Order_ID", "count"),
        Försäljning=("Total_Sales", "sum"),
        Vinst=("Profit", "sum"),
    )

    # Hur stor del av ALL försäljning och ALL vinst som varje del står för, i procent
    tabell["Andel försäljning (%)"] = tabell["Försäljning"] / tabell["Försäljning"].sum() * 100
    tabell["Andel vinst (%)"] = tabell["Vinst"] / tabell["Vinst"].sum() * 100

    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100

    # Sortera så att den som säljer mest hamnar överst
    print(tabell.sort_values("Försäljning", ascending=False).round(1))


# ---------------------------------------------------------------------------
# Fråga 1: Varför har Corporate lägst vinstmarginal?
# ---------------------------------------------------------------------------
def fraga_1_kundgrupper(df):
    rubrik("Fråga 1: Varför har Corporate lägst vinstmarginal?")

    # Dela upp alla ordrar efter kundgrupp och räkna ut några siffror för varje grupp
    tabell = df.groupby("Customer_Segment").agg(
        Ordrar=("Order_ID", "count"),               # hur många ordrar gruppen gjort
        Försäljning=("Total_Sales", "sum"),         # hur mycket gruppen köpt för totalt
        Vinst=("Profit", "sum"),                    # hur mycket vi tjänat på gruppen
        Snittrabatt=("Discount_Percent", "mean"),   # genomsnittlig rabatt i procent
    )

    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100

    # Sortera så att gruppen med lägst rabatt hamnar först, och avrunda till en decimal
    print(tabell.sort_values("Snittrabatt").round(1))

    # Jämför hur ofta varje grupp får en stor rabatt (mer än 10 %)
    print("\nAndel ordrar med mer än 10 % rabatt:")
    stor_rabatt = df["Discount_Percent"] > 10
    andel = stor_rabatt.groupby(df["Customer_Segment"]).mean() * 100
    for grupp, procent in andel.sort_values().items():
        print(f"  {grupp:15} {procent:5.1f} %")


# ---------------------------------------------------------------------------
# Fråga 2: Kostar frakten mer i vissa regioner?
# ---------------------------------------------------------------------------
def fraga_2_frakt(df):
    rubrik("Fråga 2: Kostar frakten mer i vissa regioner?")

    # Summera försäljning och fraktkostnad för varje region
    tabell = df.groupby("Region").agg(
        Försäljning=("Total_Sales", "sum"),
        Fraktkostnad=("Shipping_Cost", "sum"),
        Snittfrakt_per_order=("Shipping_Cost", "mean"),
    )

    # Hur mycket av varje 100 i försäljning som går till frakt (valutan står inte i datan)
    tabell["Frakt av försäljning (%)"] = tabell["Fraktkostnad"] / tabell["Försäljning"] * 100

    # Sortera så att regionen med dyrast frakt (i förhållande till försäljningen) hamnar sist
    print(tabell.sort_values("Frakt av försäljning (%)").round(1))


# ---------------------------------------------------------------------------
# Fråga 3: Köper man olika saker i olika delar av världen?
# ---------------------------------------------------------------------------
def fraga_3_produktmix(df):
    rubrik("Fråga 3: Hur stor del av försäljningen är varje kategori, per region? (%)")

    # Gör en tabell med regioner som rader och produktkategorier som kolumner.
    # Varje ruta = hur mycket den regionen köpt av den kategorin.
    tabell = pd.crosstab(
        df["Region"], df["Product_Category"],
        values=df["Total_Sales"], aggfunc="sum",
        normalize="index",   # gör om till andelar, så att varje rad blir 100 %
    ) * 100

    # Sortera så att regionerna som köper mest möbler hamnar överst
    print(tabell.sort_values("Furniture", ascending=False).round(1))


# ---------------------------------------------------------------------------
# Fråga 4: Betalar man på olika sätt i olika delar av världen?
# ---------------------------------------------------------------------------
def fraga_4_betalning(df):
    rubrik("Fråga 4: Hur stor del av ordrarna betalas med varje metod, per region? (%)")

    # Samma typ av tabell som i fråga 3, men här räknar vi antal ordrar per betalmetod
    tabell = pd.crosstab(
        df["Region"], df["Payment_Method"],
        normalize="index",   # gör om till andelar, så att varje rad blir 100 %
    ) * 100

    # Sortera så att regionerna som använder kreditkort mest hamnar överst
    print(tabell.sort_values("Credit Card", ascending=False).round(1))


def main():
    # Läs in all data från CSV-filen och visa vilken fil som används
    df = las_data()
    print(f"Data hämtad från {CSV_FIL.name} ({len(df)} ordrar)")

    # Gör så att breda tabeller skrivs ut på en rad i stället för att delas upp
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", None)

    # Börja med översikten för regioner och kundgrupper
    oversikt(df, "Region", "Försäljning och vinst per region")
    oversikt(df, "Customer_Segment", "Försäljning och vinst per kundgrupp")

    # Kör sedan de fyra frågorna i tur och ordning
    fraga_1_kundgrupper(df)
    fraga_2_frakt(df)
    fraga_3_produktmix(df)
    fraga_4_betalning(df)


# Kör programmet bara när filen startas direkt (inte när någon annan fil använder den)
if __name__ == "__main__":
    main()
