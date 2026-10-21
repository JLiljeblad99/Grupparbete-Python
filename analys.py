"""E-handelsanalys av global_ecommerce_sales.csv.

Kör från projektmappen:  python analys.py
"""
from pathlib import Path

import pandas as pd

CSV_FIL = Path(__file__).parent / "archive" / "global_ecommerce_sales.csv"


def las_data(fil=CSV_FIL):
    df = pd.read_csv(fil, parse_dates=["Order_Date"])
    df["Year"] = df["Order_Date"].dt.year
    return df


def nyckeltal(df):
    """Beräknar projektets KPI:er."""
    total_sales = df["Total_Sales"].sum()
    total_profit = df["Profit"].sum()
    return {
        "Total omsättning": round(total_sales, 2),
        "Total vinst": round(total_profit, 2),
        "Vinstmarginal (%)": round(total_profit / total_sales * 100, 1),
        "Totalt antal sålda produkter": int(df["Quantity"].sum()),
        "Totalt antal ordrar": df["Order_ID"].nunique(),
        "Genomsnittlig rabatt (%)": round(df["Discount_Percent"].mean(), 2),
        "Genomsnittligt ordervärde": round(df["Total_Sales"].mean(), 2),
        "Total fraktkostnad": round(df["Shipping_Cost"].sum(), 2),
        "Unika kunder": df["Customer_Name"].nunique(),
        "Ordrar med förlust": int((df["Profit"] < 0).sum()),
    }


def sammanstall(df, kolumn):
    """Grupperar på en kolumn och visar ordrar, försäljning, vinst och marginal."""
    tabell = df.groupby(kolumn).agg(
        Ordrar=("Order_ID", "count"),
        Försäljning=("Total_Sales", "sum"),
        Vinst=("Profit", "sum"),
        Antal=("Quantity", "sum"),
    )
    tabell["Andel försäljning (%)"] = tabell["Försäljning"] / tabell["Försäljning"].sum() * 100
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    return tabell.sort_values("Försäljning", ascending=False).round(1)


def rubrik(text):
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


def main():
    df = las_data()
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", None)

    rubrik("Nyckeltal (KPI:er)")
    for namn, varde in nyckeltal(df).items():
        print(f"{namn:32} {varde:>12,}")

    rubrik("Försäljning per år")
    print(sammanstall(df, "Year"))

    rubrik("Försäljning per produktkategori")
    print(sammanstall(df, "Product_Category"))

    produkter = sammanstall(df, "Product_Name")
    rubrik("Topp 5 produkter efter försäljning")
    print(produkter.head(5))
    rubrik("Topp 5 produkter efter vinst")
    print(produkter.sort_values("Vinst", ascending=False).head(5))
    rubrik("Produkter med lägst marginal")
    print(produkter.sort_values("Marginal (%)").head(5))

    rubrik("Försäljning per region")
    print(sammanstall(df, "Region"))
    rubrik("Topp 10 länder")
    print(sammanstall(df, "Country").head(10))
    rubrik("Försäljning per kundsegment")
    print(sammanstall(df, "Customer_Segment"))
    rubrik("Betalningsmetoder")
    print(sammanstall(df, "Payment_Method"))

    rubrik("Rabattens påverkan på marginalen")
    print(sammanstall(df, "Discount_Percent").sort_index())

    rubrik("Förlustordrar per kategori")
    print(df[df["Profit"] < 0]["Product_Category"].value_counts())


if __name__ == "__main__":
    main()
