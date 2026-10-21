"""KPI-dashboard för ledningsgruppen, baserat på global_ecommerce_sales.csv.

Installera paketen (en gång):
    pip install streamlit pandas plotly
    (eller: pip install -r requirements.txt)

Starta appen från projektmappen:
    streamlit run app.py

Appen öppnas i webbläsaren på http://localhost:8501
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

CSV_FIL = Path(__file__).parent / "archive" / "global_ecommerce_sales.csv"
NUMERISKA_KOLUMNER = ["Quantity", "Unit_Price", "Discount_Percent", "Total_Sales", "Shipping_Cost", "Profit"]

# Nycklar för filtren i st.session_state – används av återställningsknappen
FILTER_NYCKLAR = ["datum", "regioner", "lander", "kategorier", "produkter", "segment"]

st.set_page_config(page_title="E-handel KPI-dashboard", page_icon="📊", layout="wide")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def las_data(fil=CSV_FIL):
    """Läser in CSV-filen och säkerställer korrekta datatyper.

    Resultatet cachas så att filen bara läses en gång, inte vid varje filterändring.
    """
    df = pd.read_csv(fil)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    for kolumn in NUMERISKA_KOLUMNER:
        df[kolumn] = pd.to_numeric(df[kolumn], errors="coerce")
    # Rader med ogiltigt datum eller belopp kan inte användas i beräkningarna
    return df.dropna(subset=["Order_Date", "Total_Sales", "Profit"])


def filtrera(df, kolumn, valda):
    """Filtrerar på en kolumn. Ett tomt val betyder 'Alla'."""
    return df[df[kolumn].isin(valda)] if valda else df


# ---------------------------------------------------------------------------
# Sidopanel med filter
# ---------------------------------------------------------------------------
def aterstall_filter():
    """Tar bort filtervärdena så att alla widgets återgår till standard."""
    for nyckel in FILTER_NYCKLAR:
        st.session_state.pop(nyckel, None)


def flerval(etikett, alternativ, nyckel):
    """Flervalsmeny som rensar bort val som inte längre finns bland alternativen.

    Behövs för de beroende menyerna: väljer man bort en region ska länderna
    i den regionen också försvinna ur valet.
    """
    if nyckel in st.session_state:
        st.session_state[nyckel] = [v for v in st.session_state[nyckel] if v in alternativ]
    return st.multiselect(etikett, alternativ, key=nyckel, placeholder="Alla")


def sidopanel(df):
    """Ritar filtren i sidopanelen och returnerar den filtrerade datan."""
    with st.sidebar:
        st.header("🔎 Filter")
        st.button("↺ Återställ alla filter", on_click=aterstall_filter, width="stretch")

        # Datumintervall
        forsta, sista = df["Order_Date"].min().date(), df["Order_Date"].max().date()
        datum = st.date_input(
            "📅 Datumintervall",
            value=(forsta, sista),
            min_value=forsta,
            max_value=sista,
            format="YYYY-MM-DD",
            key="datum",
        )
        # Medan man väljer i kalendern finns bara startdatumet – använd då sista datumet som slut
        start, slut = (datum[0], datum[1]) if len(datum) == 2 else (datum[0], sista)
        df = df[df["Order_Date"].dt.date.between(start, slut)]

        # Region och land – länderna begränsas till de valda regionerna
        st.subheader("🌍 Geografi")
        regioner = flerval("Region", sorted(df["Region"].unique()), "regioner")
        df = filtrera(df, "Region", regioner)
        lander = flerval("Land", sorted(df["Country"].unique()), "lander")
        df = filtrera(df, "Country", lander)

        # Kategori och produkt – produkterna begränsas till de valda kategorierna
        st.subheader("🛒 Produkter")
        kategorier = flerval("Produktkategori", sorted(df["Product_Category"].unique()), "kategorier")
        df = filtrera(df, "Product_Category", kategorier)
        produkter = flerval("Produkt", sorted(df["Product_Name"].unique()), "produkter")
        df = filtrera(df, "Product_Name", produkter)

        st.subheader("👥 Kunder")
        segment = flerval("Kundsegment", sorted(df["Customer_Segment"].unique()), "segment")
        df = filtrera(df, "Customer_Segment", segment)

        st.caption("Tomt filter = alla värden ingår.")
    return df


# ---------------------------------------------------------------------------
# KPI:er
# ---------------------------------------------------------------------------
def berakna_kpi(df):
    """Räknar ut alla KPI:er för den (filtrerade) datan."""
    ordrar = df["Order_ID"].nunique()
    oms = df["Total_Sales"].sum()
    vinst = df["Profit"].sum()
    return {
        "oms": oms,
        "vinst": vinst,
        "marginal": vinst / oms * 100 if oms else 0,
        "ordrar": ordrar,
        "antal": df["Quantity"].sum(),
        "aov": oms / ordrar if ordrar else 0,
        "vinst_per_order": vinst / ordrar if ordrar else 0,
        "rabatt": df["Discount_Percent"].mean(),
        "frakt": df["Shipping_Cost"].sum(),
        "forlust": df.loc[df["Profit"] < 0, "Order_ID"].nunique() / ordrar * 100 if ordrar else 0,
    }


def tal(varde, decimaler=0):
    """Formaterar tal med mellanslag som tusentalsavgränsare, t.ex. 484 559."""
    return f"{varde:,.{decimaler}f}".replace(",", " ").replace(".", ",")


def visa_kpi_kort(k):
    """Visar de tio KPI-korten i två rader."""
    kort = [
        ("💰 Total omsättning", tal(k["oms"])),
        ("📈 Total vinst", tal(k["vinst"])),
        ("🎯 Vinstmarginal", f"{tal(k['marginal'], 1)} %"),
        ("🧾 Antal ordrar", tal(k["ordrar"])),
        ("📦 Sålda produkter", tal(k["antal"])),
        ("🛍️ Snittordervärde (AOV)", tal(k["aov"], 2)),
        ("💵 Snittvinst per order", tal(k["vinst_per_order"], 2)),
        ("🏷️ Snittrabatt", f"{tal(k['rabatt'], 1)} %"),
        ("🚚 Total fraktkostnad", tal(k["frakt"])),
        ("⚠️ Andel förlustordrar", f"{tal(k['forlust'], 1)} %"),
    ]
    for rad in (kort[:5], kort[5:]):
        for kolumn, (etikett, varde) in zip(st.columns(5), rad):
            kolumn.metric(etikett, varde, border=True)


# ---------------------------------------------------------------------------
# Diagram
# ---------------------------------------------------------------------------
def visa_diagram(df):
    """Visar diagram över trend, kategorier, regioner och rabatter."""
    vanster, hoger = st.columns(2)

    # Försäljning och vinst per månad
    per_manad = (
        df.groupby(df["Order_Date"].dt.to_period("M").dt.to_timestamp())[["Total_Sales", "Profit"]]
        .sum()
        .rename(columns={"Total_Sales": "Omsättning", "Profit": "Vinst"})
    )
    fig = px.line(per_manad, markers=True, title="Omsättning och vinst per månad")
    fig.update_layout(xaxis_title=None, yaxis_title=None, legend_title=None)
    vanster.plotly_chart(fig, width="stretch")

    # Omsättning och vinst per kategori
    per_kategori = (
        df.groupby("Product_Category")[["Total_Sales", "Profit"]]
        .sum()
        .sort_values("Total_Sales")
        .rename(columns={"Total_Sales": "Omsättning", "Profit": "Vinst"})
    )
    fig = px.bar(per_kategori, orientation="h", barmode="group", title="Omsättning och vinst per kategori")
    fig.update_layout(xaxis_title=None, yaxis_title=None, legend_title=None)
    hoger.plotly_chart(fig, width="stretch")

    vanster, hoger = st.columns(2)

    # Topp 10 länder
    per_land = df.groupby("Country")["Total_Sales"].sum().nlargest(10).sort_values()
    fig = px.bar(per_land, orientation="h", title="Topp 10 länder efter omsättning")
    fig.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
    vanster.plotly_chart(fig, width="stretch")

    # Rabattens påverkan på vinstmarginalen
    per_rabatt = df.groupby("Discount_Percent")[["Total_Sales", "Profit"]].sum()
    per_rabatt["Marginal (%)"] = per_rabatt["Profit"] / per_rabatt["Total_Sales"] * 100
    per_rabatt.index = per_rabatt.index.astype(int).astype(str) + " %"
    fig = px.bar(per_rabatt, y="Marginal (%)", title="Vinstmarginal per rabattnivå")
    fig.update_layout(xaxis_title="Rabatt", yaxis_title="Marginal (%)")
    hoger.plotly_chart(fig, width="stretch")


def visa_data(df):
    """Visar den filtrerade datan och en knapp för att ladda ner den."""
    with st.expander(f"📋 Visa filtrerad data ({len(df)} rader)"):
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button(
            "⬇️ Ladda ner som CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="filtrerad_data.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Huvudprogram
# ---------------------------------------------------------------------------
def main():
    st.title("📊 E-handel – KPI-dashboard")

    try:
        data = las_data()
    except FileNotFoundError:
        st.error(f"Hittar inte datafilen: {CSV_FIL}")
        st.stop()

    filtrerad = sidopanel(data)

    # Felhantering: inga ordrar matchar filtren
    if filtrerad.empty:
        st.warning("Inga ordrar matchar de valda filtren. Ändra filtren eller klicka på **Återställ alla filter**.")
        st.stop()

    forsta, sista = filtrerad["Order_Date"].min(), filtrerad["Order_Date"].max()
    st.caption(f"Visar {len(filtrerad):,} av {len(data):,} ordrar · {forsta:%Y-%m-%d} – {sista:%Y-%m-%d}".replace(",", " "))

    visa_kpi_kort(berakna_kpi(filtrerad))
    st.divider()
    visa_diagram(filtrerad)
    visa_data(filtrerad)


main()
