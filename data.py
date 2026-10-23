"""DATA: läser in CSV-filen och gör den redo att använda.

Allt som har med själva datafilen att göra finns här: var filen ligger, hur den läses in
och hur kolumnerna översätts till svenska. Resten av dashboarden använder bara hamta_data()
och behöver inte veta något om filen.
"""
from pathlib import Path   # hjälper till att hitta filer på datorn

import pandas as pd        # läser och räknar på datan
import streamlit as st     # behövs här bara för @st.cache_data

from installningar import BETALSATT, KATEGORIER, KUNDGRUPPER, LANDER, REGIONER

# Datafilen ligger i projektmappen, bredvid den här filen. Path(__file__).parent är projektmappen.
CSV_FIL = Path(__file__).parent / "global_ecommerce_sales.csv"
NUMERISKA_KOLUMNER = ["Quantity", "Unit_Price", "Discount_Percent", "Total_Sales", "Shipping_Cost", "Profit"]


@st.cache_data   # sparar datan i minnet, så att sidan inte läser filen på nytt vid varje klick
def hamta_data():
    # Läser in alla ordrar och lägger till svenska kolumner (Region, Kundgrupp, Land osv.)
    df = pd.read_csv(CSV_FIL)
    # Gör om text till datum och tal. errors="coerce" = ogiltiga värden blir "saknas" i stället för en krasch.
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    for kolumn in NUMERISKA_KOLUMNER:
        df[kolumn] = pd.to_numeric(df[kolumn], errors="coerce")
    # Rader utan datum, försäljning eller vinst går inte att räkna på
    df = df.dropna(subset=["Order_Date", "Total_Sales", "Profit"]).copy()
    # Byt ut de engelska namnen mot svenska
    df["Region"] = df["Region"].map(REGIONER)
    df["Kundgrupp"] = df["Customer_Segment"].map(KUNDGRUPPER)
    df["Betalsätt"] = df["Payment_Method"].map(BETALSATT)
    df["Kategori"] = df["Product_Category"].map(KATEGORIER)
    df["Land"] = df["Country"].map(lambda land: LANDER[land][0])
    df["Landskod"] = df["Country"].map(lambda land: LANDER[land][1])
    df["Datum"] = df["Order_Date"].dt.date   # bara datumet, utan klockslag
    df["Förlust"] = df["Profit"] < 0         # True om ordern gick med förlust
    return df


@st.cache_data
def datumgranser():
    # Första och sista dagen i datan, t.ex. (2 jan 2023, 31 dec 2025)
    alla = hamta_data()
    return alla["Datum"].min(), alla["Datum"].max()


@st.cache_data
def land_till_region():
    # Vilken region varje land ligger i, t.ex. "USA" -> "Nordamerika"
    alla = hamta_data()
    return dict(zip(alla["Land"], alla["Region"]))
