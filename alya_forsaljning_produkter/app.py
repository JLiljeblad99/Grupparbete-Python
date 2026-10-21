#Lägg till försäljning & trender samt produkter & kategorier
=============================================================================
# app.py – Försäljning & Trender + Produkter & Kategorier
#
# Ett klickbart gränssnitt (en webbsida) byggt med Streamlit.
# Starta det från projektmappen med:
#     python -m streamlit run forsaljning_produkter/app.py
# Då öppnas sidan i webbläsaren. Stäng med Ctrl+C i terminalen.
# =============================================================================

# --- Importer: vi hämtar in färdiga verktyg (bibliotek) som vi vill använda ---
from pathlib import Path   # Path hjälper oss att bygga sökvägar till filer på ett säkert sätt

import pandas as pd        # pandas = verktyget för tabeller (DataFrames). "pd" är ett kortnamn
import streamlit as st     # streamlit = gör om Python-kod till en webbsida. "st" är kortnamnet


# --- Var ligger datafilen? ---
# __file__ är sökvägen till just den här filen (app.py).
# .parent betyder "mappen som filen ligger i" (forsaljning_produkter).
# .parent igen går ett steg upp (Grupparbete-Python).
# Med / bygger vi vidare på sökvägen: .../archive/global_ecommerce_sales.csv
CSV_FIL = Path(__file__).parent.parent / "archive" / "global_ecommerce_sales.csv"


# =============================================================================
# DEL 1: Läsa in och städa datan
# =============================================================================

# @st.cache_data gör att Streamlit sparar resultatet. Varje gång chefen klickar på något
# körs hela skriptet om, men tack vare cachen läses CSV-filen bara in en gång -> snabbare.
@st.cache_data
def las_data():
    # Läs CSV-filen till en tabell (DataFrame). Varje rad = en order.
    df = pd.read_csv(CSV_FIL)

    # Gör om datum-kolumnen från text ("2023-01-02") till riktiga datum.
    # errors="coerce" betyder: om något inte är ett giltigt datum, gör det till "saknas" (NaT)
    # istället för att programmet kraschar.
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")

    # Ta bort rader där datum eller försäljning saknas (t.ex. skräprader som "Hejhej").
    # dropna = "släpp rader med tomma värden", subset = kolla bara dessa kolumner.
    df = df.dropna(subset=["Order_Date", "Total_Sales", "Profit"])

    # Skapa nya kolumner för tidsperioder, så vi kan gruppera på dem senare.
    # .dt ger oss tillgång till datum-funktioner.
    # to_period("M") = månad, ("Q") = kvartal, ("Y") = år.
    # to_timestamp() gör om perioden till ett datum (första dagen i perioden),
    # vilket gör att diagrammen får en snygg tidsaxel.
    df["Månad"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    df["Kvartal"] = df["Order_Date"].dt.to_period("Q").dt.to_timestamp()
    df["År"] = df["Order_Date"].dt.year

    return df  # skicka tillbaka den städade tabellen


# =============================================================================
# DEL 2: Beräkningsfunktioner (de här kan gruppen återanvända när ni slår ihop)
# =============================================================================

def summera(df, kolumn):
    """Grupperar datan på en kolumn och räknar försäljning, vinst och marginal."""
    # groupby(kolumn) = dela upp tabellen i grupper, en per unikt värde i kolumnen
    #   (t.ex. en grupp per produktkategori).
    # .agg(...) = räkna ut något för varje grupp. Syntaxen är:
    #   NyttNamn=("KolumnAttRäknaPå", "vad vi ska räkna")
    tabell = df.groupby(kolumn).agg(
        Försäljning=("Total_Sales", "sum"),   # summan av försäljningen
        Vinst=("Profit", "sum"),              # summan av vinsten
        Ordrar=("Order_ID", "count"),         # hur många ordrar (rader) det är
        Antal_sålda=("Quantity", "sum"),      # hur många enheter som sålts
    )
    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent.
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    # round(1) = avrunda till 1 decimal så tabellen blir lättläst.
    return tabell.round(1)


# En lista med svenska månadsnamn. Plats 0 = januari, plats 11 = december.
MANADER = ["januari", "februari", "mars", "april", "maj", "juni",
           "juli", "augusti", "september", "oktober", "november", "december"]


def manadsnamn(datum):
    """Gör om ett datum till text, t.ex. 2025-06-01 -> 'juni 2025'."""
    # datum.month är 1–12, men listan börjar på 0, därför tar vi -1.
    return f"{MANADER[datum.month - 1]} {datum.year}"


# =============================================================================
# DEL 3: Själva sidan (det chefen ser)
# =============================================================================

# Inställningar för sidan: titel i webbläsarfliken och bred layout.
st.set_page_config(page_title="Försäljning & Produkter", layout="wide")

# st.title skriver en stor rubrik överst på sidan.
st.title("📊 Försäljning & Produkter")

# Läs in datan (med hjälp av funktionen vi skrev ovan).
df = las_data()

# --- Sidopanel med filter (till vänster på sidan) ---
# Allt som börjar med st.sidebar hamnar i sidopanelen.
st.sidebar.header("Filter")

# sorted(...unique()) = en sorterad lista över alla år som finns i datan, t.ex. [2023, 2024, 2025].
alla_ar = sorted(df["År"].unique())
# multiselect = en ruta där man kan välja flera alternativ. default = vad som är valt från början.
valda_ar = st.sidebar.multiselect("År", alla_ar, default=alla_ar)

# radio = knappar där man väljer exakt ett alternativ.
# index=1 betyder att alternativ nummer 2 ("Kvartal") är förvalt (Python räknar från 0).
tidsupplosning = st.sidebar.radio("Visa diagram per", ["Månad", "Kvartal", "År"], index=1)

# Filtrera tabellen: behåll bara raderna vars år finns i listan valda_ar.
# df["År"].isin(valda_ar) ger True/False för varje rad, och df[...] behåller raderna med True.
df = df[df["År"].isin(valda_ar)]

# Om användaren avmarkerat alla år finns ingen data -> visa ett meddelande och stoppa.
if df.empty:
    st.warning("Välj minst ett år i sidopanelen.")
    st.stop()  # st.stop() avslutar skriptet här, så resten av sidan inte ritas

# ---------------------------------------------------------------------------
# SNABBÖVERSIKT – det viktigaste direkt högst upp, innan man behöver klicka
# ---------------------------------------------------------------------------

# Räkna ut nyckeltal (KPI:er) för hela den filtrerade datan.
total_forsaljning = df["Total_Sales"].sum()
total_vinst = df["Profit"].sum()
marginal = total_vinst / total_forsaljning * 100
antal_ordrar = df["Order_ID"].nunique()   # nunique = antal unika värden

# Sammanställningar som vi plockar ut "bäst" och "sämst" ur.
per_manad = summera(df, "Månad")
per_ar = summera(df, "År")
per_produkt = summera(df, "Product_Name")
per_kategori = summera(df, "Product_Category")

# idxmax() = ger radens namn (index) där värdet är störst. idxmin() = där det är minst.
# Exempel: per_manad["Försäljning"].idxmax() ger datumet för månaden med mest försäljning.
topp_manad = per_manad["Försäljning"].idxmax()
dipp_manad = per_manad["Försäljning"].idxmin()
basta_ar = per_ar["Försäljning"].idxmax()
basta_produkt = per_produkt["Vinst"].idxmax()
samsta_produkt = per_produkt["Vinst"].idxmin()
basta_kategori = per_kategori["Vinst"].idxmax()
samsta_kategori = per_kategori["Vinst"].idxmin()

# st.container(border=True) = en ruta med ram runt, så översikten sticker ut.
with st.container(border=True):
    st.subheader("🔎 Snabböversikt")

    # Rad 1: de fyra viktigaste talen bredvid varandra.
    # st.columns(4) delar sidan i 4 kolumner. st.metric visar ett stort tal med etikett.
    # f"{tal:,.0f}" formaterar talet: , = tusentalsavgränsare, .0f = inga decimaler.
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total försäljning", f"{total_forsaljning:,.0f}")
    k2.metric("Total vinst", f"{total_vinst:,.0f}")
    k3.metric("Vinstmarginal", f"{marginal:.1f} %")
    k4.metric("Antal ordrar", f"{antal_ordrar:,}")

    # Rad 2: de viktigaste punkterna i tre spalter.
    # .loc[namn, "kolumn"] = hämta ett enskilt värde ur tabellen (rad, kolumn).
    # Texten är markdown: **fet stil** och "- " i början av en rad ger en punktlista.
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("**📈 Försäljning**")
        rader = [
            f"- Toppmånad: **{manadsnamn(topp_manad)}** ({per_manad.loc[topp_manad, 'Försäljning']:,.0f})",
            f"- Svagaste månad: **{manadsnamn(dipp_manad)}** ({per_manad.loc[dipp_manad, 'Försäljning']:,.0f})",
        ]
        # "Bästa år" säger bara något om man har valt mer än ett år.
        if len(valda_ar) > 1:
            rader.append(f"- Bästa år: **{basta_ar}** ({per_ar.loc[basta_ar, 'Försäljning']:,.0f})")
        # "\n".join(...) sätter ihop listan till en text med radbrytning mellan varje punkt.
        st.markdown("\n".join(rader))
    with s2:
        st.markdown("**🏆 Drar in mest vinst**")
        st.markdown(
            f"- Produkt: **{basta_produkt}** ({per_produkt.loc[basta_produkt, 'Vinst']:,.0f})\n"
            f"- Kategori: **{basta_kategori}** ({per_kategori.loc[basta_kategori, 'Vinst']:,.0f})"
        )
    with s3:
        st.markdown("**⚠️ Drar in minst vinst**")
        st.markdown(
            f"- Produkt: **{samsta_produkt}** ({per_produkt.loc[samsta_produkt, 'Vinst']:,.0f})\n"
            f"- Kategori: **{samsta_kategori}** (marginal {per_kategori.loc[samsta_kategori, 'Marginal (%)']} %)"
        )

# --- Flikar: chefen klickar mellan de två delarna för mer detaljer ---
# st.tabs skapar flikar och ger tillbaka en "behållare" per flik.
flik_trender, flik_produkter = st.tabs(["📈 Försäljning & Trender", "🛋️ Produkter & Kategorier"])


# ---------------------------------------------------------------------------
# FLIK 1: Försäljning & Trender – Hur ser försäljningen och vinsten ut?
# ---------------------------------------------------------------------------
with flik_trender:  # allt som är indraget under "with" hamnar i den här fliken
    st.header("Hur ser försäljningen och vinsten ut?")

    # Försäljning och vinst över tid, grupperat på vald tidsupplösning (Månad/Kvartal/År).
    st.subheader(f"Försäljning och vinst per {tidsupplosning.lower()}")
    over_tid = summera(df, tidsupplosning)
    # st.line_chart ritar ett linjediagram. Index (tiden) blir x-axeln,
    # och varje kolumn vi väljer blir en egen linje.
    st.line_chart(over_tid[["Försäljning", "Vinst"]])

    # Tabell per år, så chefen kan se exakta siffror.
    # st.expander = en hopfälld ruta. Innehållet syns först när man klickar på den,
    # så sidan blir inte full av tabeller som alla kanske inte behöver.
    with st.expander("Visa tabell per år"):
        st.dataframe(per_ar)   # per_ar räknade vi redan ut i snabböversikten

    # Förlustordrar – ordrar där vinsten är mindre än 0.
    forlust = df[df["Profit"] < 0]
    st.subheader("Ordrar med förlust")
    st.write(
        f"{len(forlust)} av {len(df)} ordrar ({len(forlust) / len(df) * 100:.1f} %) gick med förlust, "
        f"totalt {forlust['Profit'].sum():,.0f}."
    )


# ---------------------------------------------------------------------------
# FLIK 2: Produkter & Kategorier – Vad drar in mest vinst och försäljning?
# ---------------------------------------------------------------------------
with flik_produkter:
    st.header("Vilka kategorier och produkter drar in mest?")

    # --- Kategorier ---
    st.subheader("Per produktkategori")
    # sort_values(..., ascending=False) = sortera från störst till minst.
    kategorier = per_kategori.sort_values("Försäljning", ascending=False)

    # st.bar_chart ritar ett stapeldiagram. Med två kolumner blir det två staplar per kategori.
    # stack=False = staplarna står bredvid varandra istället för ovanpå varandra.
    st.bar_chart(kategorier[["Försäljning", "Vinst"]], stack=False)
    with st.expander("Visa tabell per kategori"):
        st.dataframe(kategorier)

    # --- Topplistor för produkter ---
    st.subheader("Topp 10 produkter")
    with st.expander("Visa topplistor"):
        # Två kolumner bredvid varandra: försäljning till vänster, vinst till höger.
        vanster, hoger = st.columns(2)
        vanster.markdown("**Mest försäljning**")
        # head(10) = de 10 första raderna efter sorteringen.
        vanster.dataframe(per_produkt.sort_values("Försäljning", ascending=False).head(10))
        hoger.markdown("**Mest vinst**")
        hoger.dataframe(per_produkt.sort_values("Vinst", ascending=False).head(10))

    # --- Klicka dig fram: kategori -> produkt -> diagram över tid ---
    st.subheader("Utforska en produkt")

    # Steg 1: välj kategori. selectbox = en rullgardinsmeny där man väljer ett alternativ.
    vald_kategori = st.selectbox("Välj kategori", sorted(df["Product_Category"].unique()))

    # Behåll bara rader i den valda kategorin.
    df_kategori = df[df["Product_Category"] == vald_kategori]

    # Steg 2: välj produkt – listan visar bara produkter i den valda kategorin.
    vald_produkt = st.selectbox("Välj produkt", sorted(df_kategori["Product_Name"].unique()))

    # Behåll bara rader för den valda produkten.
    df_produkt = df_kategori[df_kategori["Product_Name"] == vald_produkt]

    # Nyckeltal för produkten.
    p1, p2, p3 = st.columns(3)
    p1.metric("Försäljning", f"{df_produkt['Total_Sales'].sum():,.0f}")
    p2.metric("Vinst", f"{df_produkt['Profit'].sum():,.0f}")
    p3.metric("Sålda enheter", f"{df_produkt['Quantity'].sum():,.0f}")

    # Steg 3: diagram över produktens försäljning och vinst över tid.
    st.markdown(f"**{vald_produkt} – försäljning och vinst per {tidsupplosning.lower()}**")
    st.line_chart(summera(df_produkt, tidsupplosning)[["Försäljning", "Vinst"]])
