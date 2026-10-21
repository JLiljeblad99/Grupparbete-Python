"""PROTOTYP: interaktivt interface för delen Geografi, kunder och betalning.

Det här är en webbsida (byggd med Streamlit) där man kan utforska datan själv:
  - välja period med ett datumreglage och jämföra med en annan period
  - se försäljning och vinst över tid
  - filtrera på region och kundgrupp
  - se en interaktiv världskarta och klicka på länder
  - testa "Tänk om ..." med ett rabattreglage
  - se svaren på våra fyra frågor som diagram

Starta så här (från projektmappen):
    pip install -r requirements.txt
    streamlit run johan_geografi_kunder_betalning/geografi_kunder_betalning_prototyp_app.py

Då öppnas sidan automatiskt i webbläsaren. Det mörka färgtemat ligger i
.streamlit/config.toml i samma mapp och gäller bara den här appen.

Om valutan: datan säger inte vilken valuta det är. Eftersom det är en global
webbutik antar vi amerikanska dollar (USD), som är vanligast i internationell handel.
"""
from datetime import date, timedelta

import pandas as pd                 # läser och räknar på datan
import plotly.express as px         # gör interaktiva diagram och kartor
import plotly.graph_objects as go   # används för tidsdiagrammet
import streamlit as st              # bygger webbsidan

# Vi återanvänder inläsningen av CSV-filen från vår analysfil,
# så att appen och analysen alltid använder exakt samma data
from geografi_kunder_betalning_analys import las_data


# ===========================================================================
# 1. INSTÄLLNINGAR: färger och svenska namn
# ===========================================================================

# Fasta färger som används i hela appen. Samma sak har alltid samma färg,
# t.ex. är Europa alltid blå, oavsett vilket diagram man tittar på.
# Färgerna är anpassade för mörk bakgrund och går att skilja åt även för färgblinda.
BLA, ORANGE, TURKOS, GUL, ROSA, LILA = "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"
GRA = "#898781"

# Diagrammens "ram": textfärg, rutnät och bakgrund till hjälprutor
TEXT, TEXT_SVAG, RUTNAT, AXEL, KORT = "#e8eaf0", "#a3a8b4", "#232a36", "#2f3746", "#151a23"

# Skala från mörkblått (lite) till ljusblått (mycket). På mörk bakgrund lyser "mycket" starkast.
BLA_SKALA = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]

# Datan är på engelska. Här översätter vi till svenska så att alla förstår.
REGIONER = {
    "Europe": "Europa",
    "North America": "Nordamerika",
    "Asia Pacific": "Asien & Stillahavet",
    "South America": "Sydamerika",
    "Middle East & Africa": "Mellanöstern & Afrika",
}
KUNDGRUPPER = {
    "Consumer": "Privatpersoner",
    "Corporate": "Företag",
    "Home Office": "Småföretag",
}
BETALSATT = {
    "Credit Card": "Kreditkort",
    "PayPal": "PayPal",
    "Cash on Delivery": "Betala vid leverans",
    "Bank Transfer": "Banköverföring",
}
KATEGORIER = {
    "Furniture": "Möbler",
    "Technology": "Teknik",
    "Clothing & Accessories": "Kläder",
    "Office Supplies": "Kontorsmaterial",
}
# Svenskt namn + landskod (koden behövs för att kartan ska veta var landet ligger)
LANDER = {
    "Argentina": ("Argentina", "ARG"), "Australia": ("Australien", "AUS"),
    "Brazil": ("Brasilien", "BRA"), "Canada": ("Kanada", "CAN"),
    "China": ("Kina", "CHN"), "Colombia": ("Colombia", "COL"),
    "France": ("Frankrike", "FRA"), "Germany": ("Tyskland", "DEU"),
    "India": ("Indien", "IND"), "Italy": ("Italien", "ITA"),
    "Japan": ("Japan", "JPN"), "Mexico": ("Mexiko", "MEX"),
    "Nigeria": ("Nigeria", "NGA"), "Saudi Arabia": ("Saudiarabien", "SAU"),
    "South Africa": ("Sydafrika", "ZAF"), "South Korea": ("Sydkorea", "KOR"),
    "Spain": ("Spanien", "ESP"), "UAE": ("Förenade Arabemiraten", "ARE"),
    "United Kingdom": ("Storbritannien", "GBR"), "United States": ("USA", "USA"),
}
MANADER = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]

# Koppla varje region, kundgrupp osv. till sin fasta färg
REGION_FARG = dict(zip(REGIONER.values(), [BLA, ORANGE, TURKOS, GUL, ROSA]))
KUNDGRUPP_FARG = dict(zip(KUNDGRUPPER.values(), [BLA, ORANGE, TURKOS]))
BETALSATT_FARG = dict(zip(BETALSATT.values(), [BLA, ORANGE, TURKOS, GUL]))
KATEGORI_FARG = dict(zip(KATEGORIER.values(), [BLA, ORANGE, TURKOS, GUL]))
PERIOD_FARG = {"Vald period": BLA, "Jämförelseperiod": GRA}


# ===========================================================================
# 2. HJÄLPFUNKTIONER
# ===========================================================================

@st.cache_data   # sparar datan i minnet, så att sidan inte läser filen på nytt vid varje klick
def hamta_data():
    df = las_data()
    # Byt ut de engelska namnen mot svenska
    df["Region"] = df["Region"].map(REGIONER)
    df["Kundgrupp"] = df["Customer_Segment"].map(KUNDGRUPPER)
    df["Betalsätt"] = df["Payment_Method"].map(BETALSATT)
    df["Kategori"] = df["Product_Category"].map(KATEGORIER)
    df["Land"] = df["Country"].map(lambda land: LANDER[land][0])
    df["Landskod"] = df["Country"].map(lambda land: LANDER[land][1])
    df["Datum"] = df["Order_Date"].dt.date   # bara datumet, utan klockslag
    return df


def tal(varde):
    # Skriver stora tal på svenskt sätt: 137006.2 -> "137 006"
    return f"{varde:,.0f}".replace(",", " ")


def pengar(varde):
    # Skriver belopp i dollar: 137006.2 -> "$137 006"
    return f"${tal(varde)}"


def procent(varde):
    # Skriver procent på svenskt sätt: 33.84 -> "33,8 %"
    return f"{varde:.1f} %".replace(".", ",")


def procent_andring(varde):
    # Som procent(), men alltid med + eller − framför: 12.34 -> "+12,3 %"
    return f"{varde:+.1f} %".replace(".", ",")


def pengar_exakt(varde):
    # Belopp med ören/cent, för små belopp: 12.345 -> "$12,35"
    return f"${varde:.2f}".replace(".", ",")


def datum_text(dag):
    # Skriver ett datum på svenska: 2023-01-02 -> "2 jan 2023"
    return f"{dag.day} {MANADER[dag.month - 1]} {dag.year}"


def period_text(period):
    return f"{datum_text(period[0])} – {datum_text(period[1])}"


def forandring(nu, forut):
    # Hur mycket något har ändrats i procent, t.ex. "+12 %". Tomt om det inte går att räkna.
    if forut is None or forut == 0:
        return None
    return f"{(nu / forut - 1) * 100:+.1f} %".replace(".", ",")


def summera(df, kolumn):
    # Räknar ut försäljning, vinst, marginal m.m. för varje värde i en kolumn (t.ex. varje region)
    tabell = df.groupby(kolumn).agg(
        Ordrar=("Order_ID", "count"),
        Försäljning=("Total_Sales", "sum"),
        Vinst=("Profit", "sum"),
        Frakt=("Shipping_Cost", "sum"),
    )
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    tabell["Frakt per order"] = tabell["Frakt"] / tabell["Ordrar"]
    return tabell.reset_index()


def snygga_till(fig, hojd=380, pengar_x=False, pengar_y=False):
    # Samma proffsiga utseende på alla diagram: mörk stil, diskret rutnät, svenska tal
    fig.update_layout(
        height=hojd,
        margin=dict(l=10, r=10, t=40, b=10),
        separators=", ",                    # decimalkomma och mellanslag mellan tusental
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=TEXT_SVAG, size=13),
        title=dict(x=0, xanchor="left", font=dict(color=TEXT, size=15)),   # rubriken till vänster
        # förklaringen (vilken färg är vad) uppe till höger, så att den inte krockar med axeltexterna
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right",
                    title=None, font=dict(color=TEXT_SVAG)),
        hoverlabel=dict(bgcolor=KORT, bordercolor=AXEL, font=dict(color=TEXT, size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.35,                        # smalare staplar med luft emellan
    )
    # Diskreta rutnätslinjer och axlar, så att datan står i fokus
    # automargin gör plats för axeltexterna så att de inte klipps av
    fig.update_xaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_x else "", tickfont=dict(color=TEXT_SVAG))
    fig.update_yaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_y else "", tickfont=dict(color=TEXT_SVAG))
    return fig


def liggande_staplar(fig, tabell, kolumn):
    # För liggande stapeldiagram: gör plats till höger så att talen vid staplarna inte klipps av
    fig.update_traces(textposition="outside", cliponaxis=False, showlegend=False,
                      textfont=dict(color=TEXT, size=13), marker_cornerradius=4)
    fig.update_xaxes(range=[0, tabell[kolumn].max() * 1.22], showgrid=False, showticklabels=False, title=None)
    fig.update_yaxes(title=None, showgrid=False)
    return fig


def visa(fig):
    # Visar ett diagram på sidan, utan Plotlys verktygsrad (enklare för användaren)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def visa_tabell(tabell):
    # En hopfällbar ruta där man kan se siffrorna bakom diagrammet
    with st.expander("📋 Visa siffrorna i en tabell"):
        st.dataframe(tabell.round(1), hide_index=True, width="stretch")


def svarsruta(text):
    # En markerad ruta med svaret på en fråga, skrivet i klartext
    st.markdown(f'<div class="svar"><span class="svar-ikon">💡</span><div>{text}</div></div>',
                unsafe_allow_html=True)


def rubrik(ikon, titel, undertitel=""):
    # En snygg avsnittsrubrik med ikon och en kort förklaring under
    st.markdown(f'<div class="avsnitt"><span class="avsnitt-ikon">{ikon}</span>{titel}</div>'
                + (f'<div class="avsnitt-under">{undertitel}</div>' if undertitel else ""),
                unsafe_allow_html=True)


# ===========================================================================
# 3. SIDANS UTSEENDE (CSS = instruktioner för hur sidan ska se ut)
# ===========================================================================

st.set_page_config(page_title="Geografi, kunder & betalning", page_icon="🌍", layout="wide")

st.markdown(f"""
<style>
/* Mjukare, modernare typsnitt och lite mer luft */
html, body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
.block-container {{ padding-top: 2.2rem; max-width: 1400px; }}

/* Rubrikrutan högst upp: mörk bakgrund med färgsken som långsamt rör sig */
.hero {{
    position: relative; overflow: hidden; border-radius: 20px; padding: 34px 36px 30px 36px;
    margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.08);
    background:
        radial-gradient(circle at 15% 20%, rgba(57,135,229,0.45), transparent 45%),
        radial-gradient(circle at 85% 30%, rgba(144,133,233,0.40), transparent 45%),
        radial-gradient(circle at 60% 110%, rgba(213,81,129,0.30), transparent 50%),
        #0f1420;
    background-size: 140% 140%;
    animation: sken 14s ease-in-out infinite alternate;
}}
@keyframes sken {{ from {{ background-position: 0% 0%; }} to {{ background-position: 100% 100%; }} }}
.hero h1 {{ color: #fff; margin: 6px 0 0 0; font-size: 2.4rem; font-weight: 750; letter-spacing: -0.02em; }}
.hero p  {{ color: rgba(255,255,255,0.78); margin: 8px 0 0 0; font-size: 1.05rem; max-width: 760px; }}
.etikett {{
    display: inline-block; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18);
    padding: 3px 12px; border-radius: 999px; font-size: 0.75rem; letter-spacing: 0.12em; color: #fff;
}}
.chips {{ margin-top: 18px; display: flex; gap: 8px; flex-wrap: wrap; }}
.chip {{
    background: rgba(11,14,20,0.55); border: 1px solid rgba(255,255,255,0.12); color: #e8eaf0;
    padding: 6px 12px; border-radius: 10px; font-size: 0.88rem;
}}

/* Nyckeltalskorten: mörka kort med tunn kant som lyser upp när man håller musen över */
div[data-testid="stMetric"] {{
    background: linear-gradient(180deg, #161c27 0%, #11161f 100%);
    border: 1px solid {AXEL}; border-radius: 16px; padding: 16px 18px;
    transition: border-color .2s ease, transform .2s ease;
}}
div[data-testid="stMetric"]:hover {{ border-color: {BLA}; transform: translateY(-2px); }}
div[data-testid="stMetricValue"] {{ font-weight: 700; letter-spacing: -0.01em; }}

/* Avsnittsrubriker */
.avsnitt {{ font-size: 1.35rem; font-weight: 700; color: {TEXT}; margin: 26px 0 2px 0; }}
.avsnitt-ikon {{ margin-right: 10px; }}
.avsnitt-under {{ color: {TEXT_SVAG}; font-size: 0.95rem; margin-bottom: 8px; }}

/* Svarsrutor */
.svar {{
    display: flex; gap: 12px; align-items: flex-start; margin-top: 10px;
    background: linear-gradient(90deg, rgba(57,135,229,0.14), rgba(57,135,229,0.03));
    border: 1px solid rgba(57,135,229,0.30); border-radius: 12px; padding: 14px 16px; color: {TEXT};
}}
.svar-ikon {{ font-size: 1.2rem; }}

/* Kortet i sidopanelen som visar vilka perioder som jämförs */
.period-ruta {{
    background: linear-gradient(180deg, #161c27 0%, #11161f 100%); border: 1px solid {AXEL};
    border-radius: 14px; padding: 12px 14px; margin: 2px 0 10px 0; font-size: 0.92rem; color: {TEXT};
}}
.period-rad {{ display: flex; gap: 10px; align-items: flex-start; padding: 5px 0; }}
.period-etikett {{ color: {TEXT_SVAG}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }}
.prick {{ width: 10px; height: 10px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }}
.prick.bla {{ background: {BLA}; box-shadow: 0 0 8px {BLA}; }}
.prick.gra {{ background: {GRA}; }}

/* Flikarna lite större och tydligare */
button[role="tab"] p, div[role="tab"] p {{ font-size: 0.98rem; }}
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# 4. SIDOPANELEN: period, jämförelse och filter
# ===========================================================================

alla = hamta_data()
FORSTA_DAG, SISTA_DAG = alla["Datum"].min(), alla["Datum"].max()

def manader_bakat(dag, antal):
    # Flyttar ett datum ett antal månader bakåt, t.ex. 1 okt -> 1 jul om antal = 3
    return (pd.Timestamp(dag) - pd.DateOffset(months=antal)).date()


def snabbval_period(val):
    # Räknar ut start- och slutdatum för ett snabbval, som i Google Ads.
    # Datan slutar 31 dec 2025, så "senaste", "denna månad" osv. räknas från datans sista dag.
    dag = SISTA_DAG
    manad_start = dag.replace(day=1)
    kvartal_start = date(dag.year, 3 * ((dag.month - 1) // 3) + 1, 1)
    perioder = {
        "Senaste 7 dagarna": (dag - timedelta(days=6), dag),
        "Senaste 30 dagarna": (dag - timedelta(days=29), dag),
        "Senaste 90 dagarna": (dag - timedelta(days=89), dag),
        "Denna månad": (manad_start, dag),
        "Förra månaden": (manader_bakat(manad_start, 1), manad_start - timedelta(days=1)),
        "Detta kvartal": (kvartal_start, dag),
        "Förra kvartalet": (manader_bakat(kvartal_start, 3), kvartal_start - timedelta(days=1)),
        "I år": (date(dag.year, 1, 1), dag),
        "Förra året": (date(dag.year - 1, 1, 1), date(dag.year - 1, 12, 31)),
        "Hela perioden": (FORSTA_DAG, SISTA_DAG),
    }
    start, slut = perioder[val]
    return max(start, FORSTA_DAG), min(slut, SISTA_DAG)   # håll oss inom datans datum


def jamforelse_for(val, per):
    # Räknar ut jämförelseperioden automatiskt utifrån den valda perioden, som i Google Ads
    start, slut = per
    langd = (slut - start).days + 1
    if val == "Föregående period":
        # lika många dagar, precis före den valda perioden
        return (start - timedelta(days=langd), start - timedelta(days=1))
    # "Samma period förra året": samma datum, ett år tidigare
    return ((pd.Timestamp(start) - pd.DateOffset(years=1)).date(),
            (pd.Timestamp(slut) - pd.DateOffset(years=1)).date())


def som_period(valt):
    # Kalendern ger (första dag, sista dag). Har man bara hunnit klicka på första dagen
    # finns ingen sista dag än – då blir svaret None (ingen färdig period).
    if isinstance(valt, (tuple, list)):
        return (valt[0], valt[1]) if len(valt) == 2 else None
    return (valt, valt)


SNABBVAL = ["Senaste 7 dagarna", "Senaste 30 dagarna", "Senaste 90 dagarna", "Denna månad",
            "Förra månaden", "Detta kvartal", "Förra kvartalet", "I år", "Förra året",
            "Hela perioden", "Anpassat"]
JAMFOR_VAL = ["Föregående period", "Samma period förra året", "Anpassat"]
STANDARD_PERIOD = snabbval_period("I år")
STANDARD_JAMFOR = "Samma period förra året"

# Startvärden första gången sidan öppnas: i år, jämfört med samma period förra året
st.session_state.setdefault("snabbval", "I år")
st.session_state.setdefault("period_datum", STANDARD_PERIOD)
st.session_state.setdefault("jamfor_pa", True)
st.session_state.setdefault("jamfor_val", STANDARD_JAMFOR)
st.session_state.setdefault("jamfor_datum", jamforelse_for(STANDARD_JAMFOR, STANDARD_PERIOD))


# --- Det här körs automatiskt när man ändrar något i sidopanelen ---

def nar_snabbval_andras():
    # Man valde t.ex. "Senaste 30 dagarna": fyll i kalendern med de datumen
    if st.session_state["snabbval"] != "Anpassat":
        st.session_state["period_datum"] = snabbval_period(st.session_state["snabbval"])


def nar_kalendern_andras():
    # Man valde egna datum i kalendern: visa "Anpassat" i listan med snabbval
    st.session_state["snabbval"] = "Anpassat"


def nar_jamfor_kalendern_andras():
    # Man valde egna datum för jämförelsen: visa "Anpassat" i jämförelselistan
    st.session_state["jamfor_val"] = "Anpassat"


def aterstall():
    # Körs när man klickar på "Återställ": tar bort alla val så att allt visas som från början
    for nyckel in ["snabbval", "period_datum", "jamfor_pa", "jamfor_val", "jamfor_datum",
                   "senaste_period", "senaste_jamfor", "filter_region", "filter_kundgrupp", "valt_land"]:
        st.session_state.pop(nyckel, None)


# --- Datumväljaren: EN knapp högst upp på sidan som öppnar en ruta, som i Google Ads och GA4 ---

def aktuell_period():
    # Den valda perioden just nu (eller förra valet, om man bara hunnit klicka på första dagen)
    return som_period(st.session_state["period_datum"]) or st.session_state.get("senaste_period", STANDARD_PERIOD)


def aktuell_jamforelse(per):
    # Jämförelseperioden just nu, eller None om jämförelsen är avstängd
    if not st.session_state.get("jamfor_pa"):
        return None
    val = st.session_state.get("jamfor_val", STANDARD_JAMFOR)
    if val != "Anpassat":
        return jamforelse_for(val, per)
    return som_period(st.session_state.get("jamfor_datum")) or st.session_state.get("senaste_jamfor")


period = aktuell_period()
jamfor_period = aktuell_jamforelse(period)
st.session_state["senaste_period"], st.session_state["senaste_jamfor"] = period, jamfor_period
start, slut = period
langd = (slut - start).days + 1

# Ett kort i sidopanelen visar alltid vilka perioder som gäller. Under det finns en knapp
# som öppnar en ruta där man väljer datum och jämförelse, som i Google Ads och GA4.
rad_jamfor = (f'<div class="period-rad"><span class="prick gra"></span><div><span class="period-etikett">'
              f'Jämförs med</span><br>{period_text(jamfor_period)}</div></div>') if jamfor_period else ""
with st.sidebar:
    st.markdown("### 📅 Datum")
    st.markdown(f'<div class="period-ruta"><div class="period-rad"><span class="prick bla"></span><div>'
                f'<span class="period-etikett">Vald period · {tal(langd)} {"dag" if langd == 1 else "dagar"}</span>'
                f'<br>{period_text(period)}</div></div>{rad_jamfor}</div>', unsafe_allow_html=True)
    with st.popover("Ändra datum och jämförelse", icon="✏️", width="stretch"):
        snabb_kolumn, kalender_kolumn = st.columns([1, 1.6], gap="medium")

        # Vänster: snabbval. Ett klick fyller i kalendern till höger.
        with snabb_kolumn:
            st.markdown("**Snabbval**")
            st.radio("Snabbval", SNABBVAL, key="snabbval", on_change=nar_snabbval_andras,
                     label_visibility="collapsed")

        # Höger: kalendern för perioden, och jämförelsen under den
        with kalender_kolumn:
            st.markdown("**🔵 Period**")
            st.date_input("Period", key="period_datum", min_value=FORSTA_DAG, max_value=SISTA_DAG,
                          format="YYYY-MM-DD", on_change=nar_kalendern_andras, label_visibility="collapsed")
            if som_period(st.session_state["period_datum"]) is None:
                st.caption("👆 Klicka på sista dagen i kalendern.")

            st.toggle("⚖️ Jämför med en annan period", key="jamfor_pa")
            if st.session_state["jamfor_pa"]:
                jamfor_val = st.selectbox("Jämför med", JAMFOR_VAL, key="jamfor_val")
                # Om man inte valt egna datum räknas jämförelsens datum ut automatiskt
                if jamfor_val != "Anpassat":
                    st.session_state["jamfor_datum"] = jamforelse_for(jamfor_val, period)
                st.markdown("**⚪ Jämförelseperiod**")
                st.date_input("Jämförelseperiod", key="jamfor_datum", min_value=date(2015, 1, 1),
                              max_value=SISTA_DAG, format="YYYY-MM-DD",
                              on_change=nar_jamfor_kalendern_andras, label_visibility="collapsed")
        st.caption(f"Datan går från {datum_text(FORSTA_DAG)} till {datum_text(SISTA_DAG)}. "
                   "Allt på sidan uppdateras direkt när du ändrar något här.")

    # Varna om jämförelsen börjar innan datan gör – då blir jämförelsen inte rättvis
    if jamfor_period and jamfor_period[0] < FORSTA_DAG:
        st.warning(f"Jämförelseperioden börjar före {datum_text(FORSTA_DAG)}, när datan saknas. "
                   "Jämförelsen blir därför missvisande – välj en kortare period.")

    st.markdown("### 🎛️ Filter")
    valda_regioner = st.multiselect("🌍 Region", list(REGIONER.values()),
                                    default=list(REGIONER.values()), key="filter_region")
    valda_kundgrupper = st.multiselect(
        "👥 Kundgrupp", list(KUNDGRUPPER.values()), default=list(KUNDGRUPPER.values()), key="filter_kundgrupp",
        help="**Privatpersoner** = vanliga konsumenter. **Företag** = större företag. "
             "**Småföretag** = små företag och folk som driver firma hemifrån (heter \"Home Office\" i datan).")
    st.button("↺ Återställ allt", on_click=aterstall, width="stretch")

# Behåll bara de ordrar som matchar region och kundgrupp
bas = alla[alla["Region"].isin(valda_regioner) & alla["Kundgrupp"].isin(valda_kundgrupper)]


def i_period(data, per):
    # Plockar ut ordrarna mellan två datum (båda dagarna räknas med)
    return data[(data["Datum"] >= per[0]) & (data["Datum"] <= per[1])]


df = i_period(bas, period)                                         # vald period
jmf = i_period(bas, jamfor_period) if jamfor_period else None      # jämförelseperiod
if jmf is not None and jmf.empty:
    jmf = None   # ingen data i jämförelseperioden (t.ex. före 2023)

with st.sidebar:
    if jamfor_period and jmf is None:
        st.warning("Det finns ingen data för jämförelseperioden. Välj en annan period.")
    st.divider()
    st.download_button("⬇️ Ladda ner urvalet (CSV)",
                       df.drop(columns=["Landskod", "Datum"]).to_csv(index=False).encode("utf-8"),
                       file_name="urval_geografi_kunder_betalning.csv", width="stretch")

# Om filtren inte ger några ordrar alls: visa ett meddelande och stoppa här
if df.empty:
    st.warning("Inga ordrar matchar dina val. Välj minst en region och en kundgrupp, eller en längre period.")
    st.stop()


# ===========================================================================
# 5. RUBRIKRUTAN
# ===========================================================================

# Små "etiketter" under rubriken som visar vad man har valt just nu
chips = [f"🔵 {period_text(period)}"]
if jmf is not None:
    chips.append(f"⚪ Jämförs med {period_text(jamfor_period)}")
chips += [f"🌍 {len(valda_regioner)} av {len(REGIONER)} regioner",
          f"👥 {len(valda_kundgrupper)} av {len(KUNDGRUPPER)} kundgrupper",
          "💵 Belopp i USD"]
chips_html = "".join(f'<span class="chip">{text}</span>' for text in chips)

st.markdown(
    '<div class="hero"><span class="etikett">PROTOTYP</span>'
    '<h1>🌍 Geografi, kunder &amp; betalning</h1>'
    '<p>Utforska var vi säljer, vem som köper och hur kunderna betalar. '
    'Välj datum och filter i panelen till vänster – allt uppdateras direkt.</p>'
    f'<div class="chips">{chips_html}</div></div>',
    unsafe_allow_html=True,
)


# ===========================================================================
# 6. NYCKELTAL MED SMÅ TRENDDIAGRAM
# ===========================================================================

def nyckeltal(data):
    # De fyra viktigaste siffrorna för en period
    if data is None:
        return None
    forsaljning, vinst = data["Total_Sales"].sum(), data["Profit"].sum()
    return {"Försäljning": forsaljning, "Vinst": vinst,
            "Marginal": vinst / forsaljning * 100, "Ordrar": len(data)}


nu, forut = nyckeltal(df), nyckeltal(jmf)

# Hur detaljerade diagrammen över tid ska vara beror på hur lång period man valt:
# kort period = en punkt per dag, mellanlång = per vecka, lång = per månad
if langd <= 45:
    FREKVENS, STEG = "D", "dag"
elif langd <= 210:
    FREKVENS, STEG = "7D", "vecka"
else:
    FREKVENS, STEG = "MS", "månad"


def tidsserie(data, forskjutning=timedelta(0)):
    # Summerar försäljning, vinst och ordrar per dag/vecka/månad i den valda perioden.
    # "forskjutning" används för jämförelsen: dess datum flyttas fram så att de hamnar
    # ovanpå den valda periodens datum (dag 1 mot dag 1, dag 2 mot dag 2 osv.), som i Google Ads.
    datum = data["Order_Date"] + pd.Timedelta(forskjutning)
    if FREKVENS == "MS":
        # Varje order hamnar på första dagen i sin månad
        steg = pd.date_range(pd.Timestamp(start).replace(day=1), pd.Timestamp(slut), freq="MS")
        punkt = datum.dt.to_period("M").dt.to_timestamp()
    else:
        # Räkna dagar från periodens start. Per vecka: dag 0–6 = vecka 1, dag 7–13 = vecka 2 osv.
        langd_steg = 1 if FREKVENS == "D" else 7
        steg = pd.date_range(pd.Timestamp(start), pd.Timestamp(slut), freq=f"{langd_steg}D")
        dagar = (datum - pd.Timestamp(start)).dt.days // langd_steg * langd_steg
        punkt = pd.Timestamp(start) + pd.to_timedelta(dagar, unit="D")
    serie = data.assign(Punkt=punkt).groupby("Punkt").agg(
        Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"), Ordrar=("Order_ID", "count"))
    serie = serie.reindex(steg, fill_value=0)   # dagar/veckor utan ordrar får värdet 0
    serie["Marginal"] = serie["Vinst"] / serie["Försäljning"].where(serie["Försäljning"] > 0) * 100
    return serie


serie_nu = tidsserie(df)
FLYTT = (start - jamfor_period[0]) if jmf is not None else timedelta(0)
serie_jmf = tidsserie(jmf, FLYTT) if jmf is not None else None

# Värdena till de små trenddiagrammen i korten
trend = (lambda kol: serie_nu[kol].fillna(0).round(1).tolist()) if len(serie_nu) > 1 else (lambda kol: None)


def mot(text):
    # Texten bredvid pilen, t.ex. "mot $155 151" – siffran för jämförelseperioden
    return f"mot {text}" if forut else None


k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Försäljning", pengar(nu["Försäljning"]),
          delta=forandring(nu["Försäljning"], forut and forut["Försäljning"]),
          delta_description=mot(forut and pengar(forut["Försäljning"])),
          chart_data=trend("Försäljning"), chart_type="area")
k2.metric("📈 Vinst", pengar(nu["Vinst"]),
          delta=forandring(nu["Vinst"], forut and forut["Vinst"]),
          delta_description=mot(forut and pengar(forut["Vinst"])),
          chart_data=trend("Vinst"), chart_type="area")
k3.metric("🎯 Vinstmarginal", procent(nu["Marginal"]),
          delta=(f"{nu['Marginal'] - forut['Marginal']:+.1f} %-enh.".replace(".", ",", 1) if forut else None),
          delta_description=mot(forut and procent(forut["Marginal"])),
          chart_data=trend("Marginal"), chart_type="line",
          help="Hur stor del av försäljningen som blir vinst. Pilen visar skillnaden i procentenheter.")
k4.metric("📦 Ordrar", tal(nu["Ordrar"]),
          delta=forandring(nu["Ordrar"], forut and forut["Ordrar"]),
          delta_description=mot(forut and tal(forut["Ordrar"])),
          chart_data=trend("Ordrar"), chart_type="bar")
if forut:
    st.caption(f"🔵 {period_text(period)} jämfört med ⚪ {period_text(jamfor_period)}. "
               "Pilen visar förändringen, siffran bredvid är värdet för jämförelseperioden. "
               f"De små diagrammen visar utvecklingen per {STEG}.")
else:
    st.caption(f"De små diagrammen i korten visar utvecklingen per {STEG}. "
               "Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster för att se hur det har förändrats.")


# ===========================================================================
# 7. TIDSDIAGRAM: utvecklingen i den valda perioden, med jämförelsen ovanpå
# ===========================================================================

rubrik("📈", "Utveckling över tid",
       f"Varje punkt är en {STEG} i perioden du valt."
       + (" Den streckade grå linjen är jämförelseperioden, lagd ovanpå så att första dagen jämförs med första dagen."
          if serie_jmf is not None else " Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster för att se en jämförelse här."))

tid_matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Ordrar"], default="Försäljning",
                                key="tid_matt", label_visibility="collapsed") or "Försäljning"
prefix = "" if tid_matt == "Ordrar" else "$"   # ordrar är antal, inte pengar

MANADER_LANGA = ["januari", "februari", "mars", "april", "maj", "juni",
                 "juli", "augusti", "september", "oktober", "november", "december"]


def steg_text(dag):
    # Hur en punkt beskrivs när man håller musen över den, t.ex. "3 okt 2025" eller "oktober 2025"
    if FREKVENS == "MS":
        return f"{MANADER_LANGA[dag.month - 1]} {dag.year}"
    text = datum_text(dag.date())
    return f"veckan från {text}" if FREKVENS == "7D" else text


x = serie_nu.index
tid = go.Figure()
# Jämförelsen ritas först (streckad grå linje) så att den valda perioden hamnar ovanpå
if serie_jmf is not None:
    tid.add_trace(go.Scatter(
        x=x, y=serie_jmf[tid_matt], name=f"Jämförelse ({period_text(jamfor_period)})",
        mode="lines", line=dict(color=GRA, width=2, dash="dash"),
        customdata=[steg_text(d - pd.Timedelta(FLYTT)) for d in x],
        hovertemplate="⚪ %{customdata}: " + prefix + "%{y:,.0f}<extra></extra>"))
# Den valda perioden: blå linje med fylld yta under
tid.add_trace(go.Scatter(
    x=x, y=serie_nu[tid_matt], name=f"Vald period ({period_text(period)})",
    mode="lines+markers" if len(x) <= 60 else "lines",
    line=dict(color=BLA, width=3, shape="spline" if FREKVENS == "MS" else "linear", smoothing=0.5),
    marker=dict(size=7), fill="tozeroy", fillcolor="rgba(57,135,229,0.15)",
    customdata=[steg_text(d) for d in x],
    hovertemplate="🔵 %{customdata}: " + prefix + "%{y:,.0f}<extra></extra>"))

snygga_till(tid, hojd=380, pengar_y=prefix == "$")
tid.update_layout(hovermode="x unified", legend=dict(traceorder="reversed"))
# Svenska datum på axeln: högst cirka 8 etiketter så att de inte trängs
hopp = max(1, len(x) // 8)
etiketter = x[::hopp]
tid.update_xaxes(showgrid=False, tickvals=etiketter,
                 ticktext=[f"{MANADER[d.month - 1]} {d.year}" if FREKVENS == "MS" else f"{d.day} {MANADER[d.month - 1]}"
                           for d in etiketter],
                 hoverformat=" ")   # dölj den engelska rubriken i rutan, datumet står redan på svenska
tid.update_yaxes(rangemode="tozero")
visa(tid)

if serie_jmf is not None:
    summa_nu, summa_jmf = serie_nu[tid_matt].sum(), serie_jmf[tid_matt].sum()
    svarsruta(f"{tid_matt} i vald period: <b>{prefix}{tal(summa_nu)}</b>, mot {prefix}{tal(summa_jmf)} "
              f"i jämförelseperioden – en förändring på <b>{forandring(summa_nu, summa_jmf) or '–'}</b>.")


# ===========================================================================
# 8. VÄRLDSKARTAN
# ===========================================================================

rubrik("🗺️", "Världskarta", "Håll musen över ett land för att se siffrorna. Klicka på ett land för att öppna det i fliken 🔍 Sök land.")

alternativ = ["Försäljning", "Vinst", "Marginal (%)", "Ordrar"]
if jmf is not None:
    alternativ.append("Förändring (%)")   # bara när man jämför: hur mycket varje land ökat/minskat
matt = st.segmented_control("Vad ska kartan visa?", alternativ, default="Försäljning",
                            label_visibility="collapsed")
matt = matt if matt in alternativ else "Försäljning"   # om man klickar bort valet, visa försäljning

per_land = df.groupby(["Land", "Landskod", "Region"], as_index=False).agg(
    Ordrar=("Order_ID", "count"),
    Försäljning=("Total_Sales", "sum"),
    Vinst=("Profit", "sum"),
)
per_land["Marginal (%)"] = per_land["Vinst"] / per_land["Försäljning"] * 100

# Försäljningen i jämförelseperioden för varje land, och hur mycket den har förändrats
if jmf is not None:
    innan = jmf.groupby("Landskod")["Total_Sales"].sum()
    per_land["Jämförelse"] = per_land["Landskod"].map(innan)
    per_land["Förändring (%)"] = (per_land["Försäljning"] / per_land["Jämförelse"] - 1) * 100
else:
    per_land["Jämförelse"] = per_land["Förändring (%)"] = float("nan")

# Förändring visas med två färger: blått = ökning, rött = minskning, grått = oförändrat.
# Övriga mått visas från mörkblått (lite) till ljusblått (mycket).
if matt == "Förändring (%)":
    # Ett land som gått från nästan inget till lite kan öka med flera tusen procent och göra
    # alla andra länder grå. Därför slutar färgskalan vid ±100 % (det exakta talet syns när man
    # håller musen över landet).
    tak = min(100, max(10, per_land["Förändring (%)"].abs().quantile(0.9)))
    farger = dict(color_continuous_scale=[[0, "#e66767"], [0.5, "#383835"], [1, BLA]],
                  range_color=[-tak, tak])
else:
    farger = dict(color_continuous_scale=BLA_SKALA)

karta = px.choropleth(per_land, locations="Landskod", color=matt, projection="natural earth",
                      custom_data=["Land", "Region", "Försäljning", "Vinst", "Marginal (%)", "Ordrar",
                                   "Jämförelse", "Förändring (%)"], **farger)
hover = ("<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
         "Försäljning: $%{customdata[2]:,.0f}<br>Vinst: $%{customdata[3]:,.0f}<br>"
         "Marginal: %{customdata[4]:.1f} %<br>Ordrar: %{customdata[5]}")
if jmf is not None:
    hover += "<br>⚪ Jämförelse: $%{customdata[6]:,.0f} (%{customdata[7]:+.1f} %)"
karta.update_traces(marker_line_color="rgba(11,14,20,0.9)", marker_line_width=0.6,
                    hovertemplate=hover + "<extra></extra>")
karta.update_geos(
    showframe=False, showcoastlines=False, showcountries=True, countrycolor="rgba(255,255,255,0.08)",
    showland=True, landcolor="#1a202b", showocean=False, bgcolor="rgba(0,0,0,0)",
    lataxis_range=[-58, 85],   # klipp bort Antarktis så att kartan blir större
)
snygga_till(karta, hojd=500)
karta.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar=dict(
    title=dict(text=matt, font=dict(color=TEXT_SVAG)), thickness=10, len=0.6, outlinewidth=0,
    tickformat=",.0f", tickprefix="$" if matt in ("Försäljning", "Vinst") else "",
    ticksuffix=" %" if "%" in matt else "", tickfont=dict(color=TEXT_SVAG)))

# on_select gör att man kan klicka på ett land och direkt se landets profil längre ner
klick = st.plotly_chart(karta, width="stretch", theme=None, config={"displayModeBar": False},
                        on_select="rerun", selection_mode="points", key="karta")
if klick and klick.selection.points:
    # Kartan talar om landskoden för landet man klickade på, t.ex. "MEX". Gör om den till landets namn.
    kod = klick.selection.points[0].get("location")
    namn = per_land.loc[per_land["Landskod"] == kod, "Land"]
    if not namn.empty:
        st.session_state["valt_land"] = namn.iloc[0]


# ===========================================================================
# 9. FLIKAR
# ===========================================================================

st.write("")
flikar = st.tabs([
    "📊 Översikt",
    "⚖️ Jämför perioder",
    "🔍 Sök land",
    "🧪 Tänk om …",
    "1️⃣ Företagskunder",
    "2️⃣ Frakt",
    "3️⃣ Vad köps var?",
    "4️⃣ Betalsätt",
])

# ---------------------------------------------------------------------------
# Flik: Översikt – vilka regioner och kundgrupper står för mest?
# ---------------------------------------------------------------------------
with flikar[0]:
    rubrik("📊", "Vilka regioner och kundgrupper står för mest?")
    visa_som = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal (%)"],
                                    default="Försäljning", key="oversikt_matt") or "Försäljning"
    som_text = procent if "%" in visa_som else pengar

    vanster, hoger = st.columns(2)
    resultat = {}
    for kolumn, dimension, titel, farg_karta in [(vanster, "Region", "Per region", REGION_FARG),
                                                  (hoger, "Kundgrupp", "Per kundgrupp", KUNDGRUPP_FARG)]:
        with kolumn:
            tabell = summera(df, dimension).sort_values(visa_som)
            if jmf is None:
                # Utan jämförelse: en stapel per region/kundgrupp i sin egen färg
                fig = px.bar(tabell, x=visa_som, y=dimension, orientation="h", color=dimension,
                             color_discrete_map=farg_karta, title=titel, text=tabell[visa_som].map(som_text))
                fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>")
                visa(liggande_staplar(snygga_till(fig), tabell, visa_som))
            else:
                # Med jämförelse: blå stapel = vald period, grå stapel = jämförelseperioden
                tabell["Jämförelse"] = tabell[dimension].map(summera(jmf, dimension).set_index(dimension)[visa_som])
                if "%" in visa_som:
                    andring = (tabell[visa_som] - tabell["Jämförelse"]).map(
                        lambda v: f"{v:+.1f} %-enh.".replace(".", ",", 1))
                else:
                    andring = ((tabell[visa_som] / tabell["Jämförelse"] - 1) * 100).map(procent_andring)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=tabell[dimension], x=tabell["Jämförelse"], orientation="h",
                                     name="Jämförelse", marker_color=GRA,
                                     customdata=tabell["Jämförelse"].map(som_text),
                                     hovertemplate="%{y}<br>⚪ Jämförelse: %{customdata}<extra></extra>"))
                fig.add_trace(go.Bar(y=tabell[dimension], x=tabell[visa_som], orientation="h",
                                     name="Vald period", marker_color=BLA,
                                     text=tabell[visa_som].map(som_text) + "  (" + andring.fillna("–") + ")",
                                     textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
                                     hovertemplate="%{y}<br>🔵 Vald period: %{text}<extra></extra>"))
                snygga_till(fig)
                fig.update_traces(marker_cornerradius=4)
                fig.update_layout(barmode="group", title_text=titel, bargroupgap=0.1,
                                  legend=dict(traceorder="reversed"), margin=dict(t=70))
                storst = max(tabell[visa_som].max(), tabell["Jämförelse"].max())
                fig.update_xaxes(range=[0, storst * 1.45], showgrid=False, showticklabels=False, title=None)
                fig.update_yaxes(showgrid=False, title=None)
                visa(fig)
            visa_tabell(tabell)
            resultat[dimension] = tabell
    regioner, grupper = resultat["Region"], resultat["Kundgrupp"]

    svarsruta(f"Högst {visa_som.lower()} har <b>{regioner.iloc[-1]['Region']}</b> bland regionerna "
              f"och <b>{grupper.iloc[-1]['Kundgrupp']}</b> bland kundgrupperna.")

# ---------------------------------------------------------------------------
# Flik: Jämför perioder – vald period mot jämförelseperioden
# ---------------------------------------------------------------------------
with flikar[1]:
    rubrik("⚖️", "Jämför två perioder")
    if jmf is None:
        st.info("📅 Slå på **⚖️ Jämför** under 📅 Datum i panelen till vänster, "
                "till exempel *Samma period förra året*, så visas jämförelsen här.")
    else:
        st.markdown(f'<div class="avsnitt-under">🔵 <b>Vald period:</b> {period_text(period)} &nbsp;&nbsp; '
                    f'⚪ <b>Jämförelseperiod:</b> {period_text(jamfor_period)}</div>', unsafe_allow_html=True)
        jamfor_matt = st.segmented_control("Jämför", ["Försäljning", "Vinst", "Ordrar"],
                                           default="Försäljning", key="jamfor_matt") or "Försäljning"

        vanster, hoger = st.columns(2)
        andringar = []
        for kolumn, dimension, titel in [(vanster, "Region", "Per region"), (hoger, "Kundgrupp", "Per kundgrupp")]:
            # Räkna ut samma sak för båda perioderna och lägg dem i samma tabell
            a = summera(df, dimension)[[dimension, jamfor_matt]].assign(Period="Vald period")
            b = summera(jmf, dimension)[[dimension, jamfor_matt]].assign(Period="Jämförelseperiod")
            bada = pd.concat([b, a])
            with kolumn:
                fig = px.bar(bada, x=dimension, y=jamfor_matt, color="Period", barmode="group", title=titel,
                             color_discrete_map=PERIOD_FARG,
                             category_orders={dimension: a.sort_values(jamfor_matt, ascending=False)[dimension].tolist()})
                fig.update_traces(marker_cornerradius=4,
                                  hovertemplate="%{x}<br>%{fullData.name}: "
                                  + ("$" if jamfor_matt != "Ordrar" else "") + "%{y:,.0f}<extra></extra>")
                fig.update_layout(bargroupgap=0.08)
                visa(snygga_till(fig, 380, pengar_y=jamfor_matt != "Ordrar").update_xaxes(title=None))
            # Spara förändringen i procent för varje region/kundgrupp
            sammans = a.merge(b, on=dimension, suffixes=("", " innan"))
            sammans["Förändring (%)"] = (sammans[jamfor_matt] / sammans[f"{jamfor_matt} innan"] - 1) * 100
            andringar.append(sammans.rename(columns={dimension: "Namn"})[["Namn", "Förändring (%)"]])

        # Visa förändringen som staplar: grönt = ökning, rött = minskning
        andring = pd.concat(andringar).sort_values("Förändring (%)")
        andring["Riktning"] = andring["Förändring (%)"].map(lambda v: "Ökning" if v >= 0 else "Minskning")
        fig = px.bar(andring, x="Förändring (%)", y="Namn", orientation="h", color="Riktning",
                     color_discrete_map={"Ökning": "#0ca30c", "Minskning": "#d03b3b"},
                     title=f"Förändring i {jamfor_matt.lower()} jämfört med jämförelseperioden",
                     text=andring["Förändring (%)"].map(procent_andring))
        fig.update_traces(textposition="outside", cliponaxis=False, marker_cornerradius=4,
                          hovertemplate="%{y}: %{text}<extra></extra>")
        storst = andring["Förändring (%)"].abs().max() * 1.3 or 1
        snygga_till(fig, 420)
        fig.update_xaxes(range=[-storst, storst], ticksuffix=" %", zeroline=True, zerolinecolor=AXEL)
        fig.update_yaxes(title=None)
        visa(fig)

        bast, samst = andring.iloc[-1], andring.iloc[0]
        svarsruta(f"Störst ökning: <b>{bast['Namn']}</b> ({procent_andring(bast['Förändring (%)'])}). "
                  f"Svagast utveckling: <b>{samst['Namn']}</b> ({procent_andring(samst['Förändring (%)'])}).")

# ---------------------------------------------------------------------------
# Flik: Sök land – en profil för ett valt land
# ---------------------------------------------------------------------------
with flikar[2]:
    rubrik("🔍", "Välj ett land och se allt om det", "Du kan också klicka på ett land på kartan.")

    # Länderna sorteras så att det land som säljer mest står först i listan
    lander = per_land.sort_values("Försäljning", ascending=False)["Land"].tolist()
    forvalt = st.session_state.get("valt_land")
    land = st.selectbox("Sök eller välj land", lander, index=lander.index(forvalt) if forvalt in lander else 0)

    ett_land = df[df["Land"] == land]
    rad = per_land[per_land["Land"] == land].iloc[0]

    # Jämför landet med ett genomsnittligt land i urvalet
    snitt_forsaljning = per_land["Försäljning"].mean()
    snitt_order = nu["Försäljning"] / nu["Ordrar"]
    landets_order = rad["Försäljning"] / rad["Ordrar"]

    st.markdown(f'<div class="avsnitt-under"><b>{land}</b> ligger i regionen <b>{rad["Region"]}</b>. '
                f'Pilarna jämför med genomsnittet för alla länder i urvalet.</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("💰 Försäljning", pengar(rad["Försäljning"]),
             delta=f"{(rad['Försäljning'] / snitt_forsaljning - 1) * 100:+.0f} %", delta_description="mot snittlandet")
    b.metric("🎯 Vinstmarginal", procent(rad["Marginal (%)"]),
             delta=f"{rad['Marginal (%)'] - nu['Marginal']:+.1f} procentenheter".replace(".", ","))
    c.metric("🧾 Snittorder", pengar(landets_order),
             delta=f"{(landets_order / snitt_order - 1) * 100:+.0f} %", delta_description="mot snittet",
             help="Hur mycket en order är värd i genomsnitt")
    d.metric("📦 Ordrar", tal(rad["Ordrar"]))

    vanster, hoger = st.columns(2)
    with vanster:
        kat = ett_land.groupby("Kategori", as_index=False)["Total_Sales"].sum().sort_values("Total_Sales")
        fig = px.bar(kat, x="Total_Sales", y="Kategori", orientation="h", color="Kategori",
                     color_discrete_map=KATEGORI_FARG, title=f"Vad köper man i {land}?",
                     text=kat["Total_Sales"].map(pengar))
        fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>")
        visa(liggande_staplar(snygga_till(fig, 320), kat, "Total_Sales"))
    with hoger:
        bet = ett_land["Betalsätt"].value_counts().rename_axis("Betalsätt").reset_index(name="Ordrar")
        bet = bet.sort_values("Ordrar")
        fig = px.bar(bet, x="Ordrar", y="Betalsätt", orientation="h", color="Betalsätt",
                     color_discrete_map=BETALSATT_FARG, title=f"Hur betalar man i {land}?",
                     text=bet["Ordrar"].map(lambda v: f"{v} ordrar"))
        fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>")
        visa(liggande_staplar(snygga_till(fig, 320), bet, "Ordrar"))

    svarsruta(f"I <b>{land}</b> köper man mest <b>{kat.iloc[-1]['Kategori'].lower()}</b> "
              f"och betalar oftast med <b>{bet.iloc[-1]['Betalsätt'].lower()}</b>.")

# ---------------------------------------------------------------------------
# Flik: Tänk om … – vad händer med vinsten om vi sätter ett tak för rabatten?
# ---------------------------------------------------------------------------
with flikar[3]:
    rubrik("🧪", "Tänk om vi gav mindre rabatt?",
           "Välj vilka kunder som ska få ett tak för rabatten och dra i reglaget. Se direkt hur mycket mer vi hade tjänat. "
           "Det här är en prognos, så den räknar på all data och påverkas inte av datumvalet "
           "(men däremot av filtren för region och kundgrupp).")

    # En prognos ska bygga på så mycket data som möjligt, så vi använder alla datum ("bas")
    # i stället för bara den valda perioden ("df")
    prognos = bas
    prognos_marginal = prognos["Profit"].sum() / prognos["Total_Sales"].sum() * 100

    vanster, hoger = st.columns([1, 2])
    with vanster:
        tak_grupper = st.multiselect("Vilka kundgrupper?", list(KUNDGRUPPER.values()), default=["Företag"])
        tak = st.slider("Högsta tillåtna rabatt", min_value=0, max_value=30, value=10, step=5, format="%d %%")

    # Räkna om varje order: om kunden ingår och rabatten är högre än taket, sänk den till taket
    ny_rabatt = prognos["Discount_Percent"].where(~prognos["Kundgrupp"].isin(tak_grupper),
                                             prognos["Discount_Percent"].clip(upper=tak))
    # Ny försäljning = antal × pris × (1 − rabatt). Det vi slipper ge i rabatt blir extra vinst.
    ny_forsaljning = prognos["Quantity"] * prognos["Unit_Price"] * (1 - ny_rabatt / 100)
    extra = ny_forsaljning - prognos["Total_Sales"]
    ny_vinst = prognos["Profit"] + extra
    berorda = int((ny_rabatt < prognos["Discount_Percent"]).sum())
    ny_marginal = ny_vinst.sum() / ny_forsaljning.sum() * 100

    with hoger:
        a, b, c = st.columns(3)
        a.metric("📈 Vinst med rabatttak", pengar(ny_vinst.sum()), delta=f"+{pengar(extra.sum())}",
                 delta_description="mot idag")
        b.metric("🎯 Ny vinstmarginal", procent(ny_marginal),
                 delta=f"{ny_marginal - prognos_marginal:+.1f} procentenheter".replace(".", ","))
        c.metric("🧾 Ordrar som påverkas", tal(berorda), help="Ordrar där rabatten var högre än taket")

    # Diagram: vinst idag jämfört med vinst med rabatttak, per kundgrupp
    jamfor_vinst = pd.DataFrame({"Kundgrupp": prognos["Kundgrupp"], "Idag": prognos["Profit"], "Med rabatttak": ny_vinst})
    jamfor_vinst = jamfor_vinst.groupby("Kundgrupp").sum().reset_index().melt(
        id_vars="Kundgrupp", var_name="Läge", value_name="Vinst")
    fig = px.bar(jamfor_vinst, x="Kundgrupp", y="Vinst", color="Läge", barmode="group",
                 color_discrete_map={"Idag": GRA, "Med rabatttak": BLA},
                 title="Vinst per kundgrupp: idag jämfört med rabatttak")
    fig.update_traces(marker_cornerradius=4, hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}<extra></extra>")
    fig.update_layout(bargroupgap=0.08)
    visa(snygga_till(fig, pengar_y=True).update_xaxes(title=None))

    svarsruta(f"Med max <b>{tak} % rabatt</b> för {', '.join(tak_grupper).lower() or 'ingen kundgrupp'} "
              f"hade vinsten blivit <b>{pengar(extra.sum())} högre</b> ({berorda} ordrar påverkas).")
    st.caption("⚠️ Förenkling: vi antar att kunderna hade köpt exakt lika mycket även med lägre rabatt. "
               "I verkligheten kan en del kunder välja att inte köpa.")

# ---------------------------------------------------------------------------
# Fråga 1: Varför tjänar vi minst på företagskunder?
# ---------------------------------------------------------------------------
with flikar[4]:
    rubrik("1️⃣", "Varför tjänar vi minst på företagskunder?")

    grupper = summera(df, "Kundgrupp")
    stor_rabatt = (df["Discount_Percent"] > 10).groupby(df["Kundgrupp"]).mean() * 100
    grupper["Ordrar med >10 % rabatt (%)"] = grupper["Kundgrupp"].map(stor_rabatt)

    # Två diagram bredvid varandra: rabatt till vänster, vinstmarginal till höger
    vanster, hoger = st.columns(2)
    for kolumn, matt_namn, titel in [
        (vanster, "Ordrar med >10 % rabatt (%)", "Hur ofta får gruppen stor rabatt (över 10 %)?"),
        (hoger, "Marginal (%)", "Hur stor del av försäljningen blir vinst?"),
    ]:
        with kolumn:
            fig = px.bar(grupper, x="Kundgrupp", y=matt_namn, color="Kundgrupp",
                         color_discrete_map=KUNDGRUPP_FARG, title=titel, text=grupper[matt_namn].map(procent))
            fig.update_traces(textposition="outside", cliponaxis=False, showlegend=False,
                              textfont=dict(color=TEXT, size=14), marker_cornerradius=4,
                              hovertemplate="%{x}: %{text}<extra></extra>")
            snygga_till(fig, 340)
            fig.update_yaxes(range=[0, grupper[matt_namn].max() * 1.25], showticklabels=False, title=None)
            fig.update_xaxes(title=None)
            visa(fig)
    visa_tabell(grupper)

    if not grupper.empty:
        hogst = grupper.sort_values("Ordrar med >10 % rabatt (%)").iloc[-1]
        svarsruta(f"<b>{hogst['Kundgrupp']}</b> får oftast stor rabatt "
                  f"({procent(hogst['Ordrar med >10 % rabatt (%)'])} av ordrarna) och har en vinstmarginal på "
                  f"{procent(hogst['Marginal (%)'])}. Mer rabatt = mindre kvar i vinst. "
                  f"Testa själv i fliken <b>🧪 Tänk om …</b>")

# ---------------------------------------------------------------------------
# Fråga 2: Kostar frakten mer i vissa regioner?
# ---------------------------------------------------------------------------
with flikar[5]:
    rubrik("2️⃣", "Kostar frakten mer i vissa delar av världen?",
           "Vad det kostar i genomsnitt att skicka en order till kunden.")

    frakt = summera(df, "Region").sort_values("Frakt per order")
    fig = px.bar(frakt, x="Frakt per order", y="Region", orientation="h", color="Region",
                 color_discrete_map=REGION_FARG, title="Fraktkostnad per order",
                 text=frakt["Frakt per order"].map(pengar_exakt))
    fig.update_traces(hovertemplate="%{y}: %{text} per order<extra></extra>")
    visa(liggande_staplar(snygga_till(fig), frakt, "Frakt per order"))
    visa_tabell(frakt)

    billigast, dyrast = frakt.iloc[0], frakt.iloc[-1]
    svarsruta(f"Att skicka en order till <b>{dyrast['Region']}</b> kostar i snitt "
              f"<b>{pengar_exakt(dyrast['Frakt per order'])}</b>, mot <b>{pengar_exakt(billigast['Frakt per order'])}</b> "
              f"till <b>{billigast['Region']}</b>.")

# ---------------------------------------------------------------------------
# Fråga 3: Köper man olika saker i olika delar av världen?
# ---------------------------------------------------------------------------
with flikar[6]:
    rubrik("3️⃣", "Köper man olika saker i olika delar av världen?",
           "Varje rad visar hur regionens försäljning fördelas på kategorierna (raden blir 100 %). Ljusare ruta = större andel.")

    mix = pd.crosstab(df["Region"], df["Kategori"], values=df["Total_Sales"],
                      aggfunc="sum", normalize="index") * 100
    mix = mix[[k for k in KATEGORIER.values() if k in mix.columns]]   # samma kolumnordning varje gång
    if "Möbler" in mix.columns:
        mix = mix.sort_values("Möbler", ascending=False)   # regionerna som köper mest möbler överst
    fig = px.imshow(mix, text_auto=".0f", color_continuous_scale=BLA_SKALA, aspect="auto",
                    labels=dict(x="Kategori", y="Region", color="Andel (%)"))
    fig.update_traces(hovertemplate="%{y} – %{x}: %{z:.1f} %<extra></extra>", textfont_size=16, xgap=3, ygap=3)
    snygga_till(fig, 380)
    fig.update_xaxes(side="top", title=None, showgrid=False)
    fig.update_yaxes(title=None, showgrid=False)
    fig.update_layout(coloraxis_colorbar=dict(thickness=10, outlinewidth=0, ticksuffix=" %"))
    visa(fig)
    visa_tabell(mix.reset_index())

    if "Teknik" in mix.columns:
        teknik = mix["Teknik"].sort_values()
        svarsruta(f"<b>{teknik.index[-1]}</b> köper mest teknik ({procent(teknik.iloc[-1])}), "
                  f"<b>{teknik.index[0]}</b> minst ({procent(teknik.iloc[0])}).")

# ---------------------------------------------------------------------------
# Fråga 4: Betalar man på olika sätt i olika delar av världen?
# ---------------------------------------------------------------------------
with flikar[7]:
    rubrik("4️⃣", "Betalar man på olika sätt i olika delar av världen?",
           "Varje stapel är en region (100 %), uppdelad på hur ordrarna betalades.")

    betal = (pd.crosstab(df["Region"], df["Betalsätt"], normalize="index") * 100).reset_index()
    betal = betal.melt(id_vars="Region", var_name="Betalsätt", value_name="Andel (%)")
    fig = px.bar(betal, x="Andel (%)", y="Region", color="Betalsätt", orientation="h",
                 color_discrete_map=BETALSATT_FARG, category_orders={"Betalsätt": list(BETALSATT.values())},
                 text=betal["Andel (%)"].map(lambda v: f"{v:.0f} %"))
    fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(color="#fff", size=13),
                      marker_line_width=2, marker_line_color="#0b0e14",   # tunn mörk kant mellan bitarna
                      hovertemplate="%{y}<br>%{fullData.name}: %{x:.1f} %<extra></extra>")
    snygga_till(fig, 420)
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", showgrid=False, title=None)
    fig.update_yaxes(title=None)
    visa(fig)
    visa_tabell(betal)

    kort = betal[betal["Betalsätt"] == "Kreditkort"].sort_values("Andel (%)")
    if not kort.empty:
        svarsruta(f"Kreditkort är vanligast i <b>{kort.iloc[-1]['Region']}</b> "
                  f"({procent(kort.iloc[-1]['Andel (%)'])}) och minst vanligt i "
                  f"<b>{kort.iloc[0]['Region']}</b> ({procent(kort.iloc[0]['Andel (%)'])}).")
