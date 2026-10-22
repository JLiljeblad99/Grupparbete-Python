"""GEMENSAM DASHBOARD: gruppens tre dashboards ihopslagna till en enda sida.

Allt bygger på samma data: archive/global_ecommerce_sales.csv (2 000 ordrar, 2023–2025).
Från varje del har vi tagit de tydligaste diagrammen och de mest användbara funktionerna:
  - Wissam (wissam_kpi_dashboard):           tio KPI-kort, rabattdiagrammet, en förklaring under
                                             varje diagram, tabell och nedladdning av urvalet
  - Alyosh (alya_forsaljning_produkter):     försäljning per år, kategorier, produkttabellen,
                                             snabböversikten, förlustordrar och "Tänk om" för frakten
  - Johan (johan_geografi_kunder_betalning): period + jämförelse, världskartan, kundgrupper, betalsätt,
                                             klickbara diagram och "Tänk om" för rabatterna

Starta så här (från projektmappen):
    pip install -r requirements.txt
    streamlit run gemensam_dashboard/dashboard_app.py

Det mörka färgtemat ligger i .streamlit/config.toml i samma mapp som den här filen.

Om valutan: datan säger inte vilken valuta det är. Eftersom det är en global
webbutik antar vi amerikanska dollar (USD), som är vanligast i internationell handel.
"""
from datetime import date, timedelta
from functools import partial   # skickar med extra värden till en funktion som körs vid klick
from pathlib import Path        # hjälper till att hitta filer på datorn

import pandas as pd                 # läser och räknar på datan
import plotly.express as px         # gör interaktiva diagram och kartor
import plotly.graph_objects as go   # används när diagrammen behöver byggas del för del
import streamlit as st              # bygger webbsidan
from plotly.subplots import make_subplots   # flera cirkeldiagram bredvid varandra

# Datan ligger i mappen archive i projektmappen. Path(__file__).parent är den här mappen
# (gemensam_dashboard), och .parent en gång till går upp till projektmappen.
CSV_FIL = Path(__file__).parent.parent / "archive" / "global_ecommerce_sales.csv"
NUMERISKA_KOLUMNER = ["Quantity", "Unit_Price", "Discount_Percent", "Total_Sales", "Shipping_Cost", "Profit"]


# ===========================================================================
# 1. INSTÄLLNINGAR: färger och svenska namn
# ===========================================================================

# Fasta färger som används i hela dashboarden. Samma sak har alltid samma färg, i alla flikar.
# Färgerna är anpassade för mörk bakgrund och går att skilja åt även för färgblinda.
BLA, ORANGE, TURKOS, GUL, LILA = "#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9"
GRA = "#898781"   # jämförelseperioden är alltid grå
ROD = "#d03b3b"   # används bara för förlust och minskning, så att rött alltid betyder "dåligt"

# Diagrammens "ram": textfärg, svagare text, rutnät, axlar och bakgrund till hjälprutor
TEXT, TEXT_SVAG, RUTNAT, AXEL, KORT = "#e8eaf0", "#a3a8b4", "#232a36", "#2f3746", "#151a23"

# Skala från mörkblått (lite) till ljusblått (mycket). På mörk bakgrund lyser "mycket" starkast.
BLA_SKALA = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]

# Färg för varje mått: försäljning är alltid blå, vinst turkos (grön = pengar in), marginal lila
MATT_FARG = {"Försäljning": BLA, "Vinst": TURKOS, "Marginal": LILA, "Ordrar": GUL}

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
MANADER_LANGA = ["januari", "februari", "mars", "april", "maj", "juni",
                 "juli", "augusti", "september", "oktober", "november", "december"]

# Koppla varje region, kundgrupp osv. till sin fasta färg. Samma ordning överallt:
# första saken i en grupp är blå, den andra orange, den tredje turkos osv.
REGION_FARG = dict(zip(REGIONER.values(), [BLA, ORANGE, TURKOS, GUL, LILA]))
KUNDGRUPP_FARG = dict(zip(KUNDGRUPPER.values(), [BLA, ORANGE, TURKOS]))
BETALSATT_FARG = dict(zip(BETALSATT.values(), [BLA, ORANGE, TURKOS, GUL]))
KATEGORI_FARG = dict(zip(KATEGORIER.values(), [BLA, ORANGE, TURKOS, GUL]))

# Gränserna för ordervärde som förlustordrarna delas in efter. float("inf") = "allt över 250".
VARDEGRANSER = [0, 25, 50, 100, 250, float("inf")]
VARDEKLASSER = ["Under $25", "$25–50", "$50–100", "$100–250", "Över $250"]


# ===========================================================================
# 2. DATA
# ===========================================================================

@st.cache_data   # sparar datan i minnet, så att sidan inte läser filen på nytt vid varje klick
def hamta_data():
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


def summera(data, gruppera_pa):
    """Försäljning, vinst, ordrar, sålda enheter och marginal för varje grupp."""
    tabell = data.groupby(gruppera_pa).agg(
        Försäljning=("Total_Sales", "sum"),
        Vinst=("Profit", "sum"),
        Ordrar=("Order_ID", "nunique"),
        Antal=("Quantity", "sum"),
    )
    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent
    tabell["Marginal"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    return tabell


# ===========================================================================
# 3. HJÄLPFUNKTIONER: tal, datum och färger
# ===========================================================================

def tal(varde, decimaler=0):
    # Svenskt sätt: 484559.3 -> "484 559". Mellanslaget är "hårt" så att talet aldrig delas på två rader.
    return f"{varde:,.{decimaler}f}".replace(",", " ").replace(".", ",")


def pengar(varde, decimaler=0):
    # Belopp i dollar: 137006.2 -> "$137 006". Minustecknet hamnar före $: -953 -> "-$953".
    return f"-${tal(-varde, decimaler)}" if varde < 0 else f"${tal(varde, decimaler)}"


def pengar_exakt(varde):
    # Belopp med cent, för små belopp: 12.345 -> "$12,35"
    return pengar(varde, 2)


def procent(varde):
    # Procent med en decimal: 33.84 -> "33,8 %"
    return f"{tal(varde, 1)} %"


def procent_andring(varde):
    # Som procent(), men alltid med + eller - framför: 12.34 -> "+12,3 %"
    return ("+" if varde >= 0 else "") + procent(varde)


def procentenheter(varde):
    # Skillnaden mellan två procenttal: 33,1 % mot 30,4 % -> "+2,7 %-enh." (procentenheter)
    return ("+" if varde >= 0 else "") + f"{tal(varde, 1)} %-enh."


def forandring(nu, forut):
    # Hur mycket något har ändrats i procent, t.ex. "+12,0 %". None om det inte går att räkna.
    # abs() gör att en vinst som går från -100 till +50 räknas som en ökning, inte en minskning.
    return procent_andring((nu - forut) / abs(forut) * 100) if forut else None


def datum_text(dag):
    # Skriver ett datum på svenska: 2023-01-02 -> "2 jan 2023"
    return f"{dag.day} {MANADER[dag.month - 1]} {dag.year}"


def period_text(period):
    return f"{datum_text(period[0])} – {datum_text(period[1])}"


def genomskinlig(farg, alfa):
    # "#3987e5" -> "rgba(57,135,229,0.15)": samma färg men genomskinlig, t.ex. för ytan under en linje
    r, g, b = (int(farg[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def html_text(text):
    # "$" kan av misstag tolkas som en matteformel på sidan. &#36; är samma tecken skrivet som HTML.
    return text.replace("$", "&#36;")


# ===========================================================================
# 4. HJÄLPFUNKTIONER: diagram, rubriker och förklaringar
# ===========================================================================

def snygga_till(fig, hojd=380, pengar_x=False, pengar_y=False):
    # Samma utseende på alla diagram: mörk stil, diskret rutnät, svenska tal
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
        paper_bgcolor="rgba(0,0,0,0)",      # genomskinlig bakgrund, så att sidans mörka färg syns
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.35,                        # smalare staplar med luft emellan
    )
    # Diskreta rutnätslinjer och axlar, så att datan står i fokus.
    # automargin gör plats för axeltexterna så att de inte klipps av.
    fig.update_xaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_x else "", tickfont=dict(color=TEXT_SVAG), title=None)
    fig.update_yaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_y else "", tickfont=dict(color=TEXT_SVAG), title=None)
    return fig


def visa(fig, namn, vid_klick=None):
    # Visar ett diagram på sidan, utan Plotlys verktygsrad (enklare för användaren).
    # Med vid_klick går det att klicka i diagrammet: då körs den funktionen. Nyckeln får ett nytt
    # nummer efter varje klick, så att diagrammet glömmer det gamla klicket.
    nyckel = f"{namn}_{st.session_state['klick_nr']}"
    klick = dict(on_select=partial(vid_klick, nyckel), selection_mode="points") if vid_klick else {}
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False}, key=nyckel, **klick)


def rubrik(ikon, titel, undertitel="", liten=False):
    # En rubrik med ikon och en kort förklaring under. liten=True används inne i korten.
    stil = ' style="margin-top:4px;font-size:1.1rem"' if liten else ""
    st.markdown(f'<div class="avsnitt"{stil}><span class="avsnitt-ikon">{ikon}</span>{titel}</div>'
                + (f'<div class="avsnitt-under">{html_text(undertitel)}</div>' if undertitel else ""),
                unsafe_allow_html=True)


def kort(ikon, titel, undertitel=""):
    # Ett kort med ram runt. Varje diagram ligger i ett eget kort: rubrik, diagram och förklaring.
    # height="stretch" gör att korten bredvid varandra blir lika höga (det högsta bestämmer).
    ruta = st.container(border=True, height="stretch")
    with ruta:
        rubrik(ikon, titel, undertitel, liten=True)
    return ruta


def forklaring(vad, hur, slutsats=None):
    # Förklaringen under varje diagram (samma idé som i Wissams dashboard):
    # vad diagrammet visar, hur man läser det och vad vi kan se i urvalet just nu.
    rader = [f'<div><span class="forklaring-etikett">ℹ️ Vad visar diagrammet?</span> {vad}</div>',
             f'<div><span class="forklaring-etikett">👉 Så läser du det:</span> {hur}</div>']
    if slutsats:
        rader.append(f'<div class="forklaring-slutsats">💡 {slutsats}</div>')
    st.markdown(f'<div class="forklaring">{html_text("".join(rader))}</div>', unsafe_allow_html=True)


def punktkort(ikon, titel, punkter):
    # Ett litet kort med en rubrik och en punktlista (används i snabböversikten).
    # Samma sorts kort som diagrammen ligger i, så att alla rutor ser likadana ut.
    lista = "".join(f"<li>{punkt}</li>" for punkt in punkter)
    with st.container(border=True, height="stretch"):
        st.markdown(html_text(f'<div class="punkt"><div class="punkt-titel">{ikon} {titel}</div><ul>{lista}</ul></div>'),
                    unsafe_allow_html=True)


def jamforelse_staplar(nu_varden, jmf_varden, format_, farg_karta, som_procentenheter=False, hojd=300):
    # Liggande staplar för t.ex. kundgrupper eller kategorier.
    # Utan jämförelse: en stapel per sak i sin egen färg.
    # Med jämförelse: blå stapel = vald period, grå = jämförelseperioden, och förändringen skrivs ut.
    tabell = pd.DataFrame({"Namn": nu_varden.index, "Nu": nu_varden.values}).sort_values("Nu")
    if jmf_varden is None:
        fig = px.bar(tabell, x="Nu", y="Namn", orientation="h", color="Namn", color_discrete_map=farg_karta,
                     text=tabell["Nu"].map(format_))
        fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>", textposition="outside",
                          cliponaxis=False, showlegend=False, textfont=dict(color=TEXT, size=13))
        bredd = tabell["Nu"].max() * 1.25   # plats till höger så att talen vid staplarna inte klipps av
    else:
        tabell["Innan"] = tabell["Namn"].map(jmf_varden).fillna(0)
        if som_procentenheter:
            andring = (tabell["Nu"] - tabell["Innan"]).map(procentenheter)
        else:
            andring = ((tabell["Nu"] / tabell["Innan"].where(tabell["Innan"] > 0) - 1) * 100).map(procent_andring)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=tabell["Namn"], x=tabell["Innan"], orientation="h", name="Jämförelse",
                             marker_color=GRA, customdata=tabell["Innan"].map(format_),
                             hovertemplate="%{y}<br>⚪ Jämförelse: %{customdata}<extra></extra>"))
        fig.add_trace(go.Bar(y=tabell["Namn"], x=tabell["Nu"], orientation="h", name="Vald period",
                             marker_color=BLA, text=tabell["Nu"].map(format_) + "  (" + andring.fillna("–") + ")",
                             textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
                             hovertemplate="%{y}<br>🔵 Vald period: %{text}<extra></extra>"))
        fig.update_layout(barmode="group", bargroupgap=0.1, legend=dict(traceorder="reversed"))
        bredd = max(tabell["Nu"].max(), tabell["Innan"].max()) * 1.9
    snygga_till(fig, hojd)
    fig.update_traces(marker_cornerradius=4)
    fig.update_xaxes(range=[0, bredd], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(tabell["Namn"]))
    return fig


def staplad_andel(data, kolumn, farger, varde=None, hojd=320):
    # Liggande 100 %-staplar: en rad per region, uppdelad efter t.ex. kategori eller betalsätt.
    # varde=None räknar antal ordrar, annars summan av den kolumnen (t.ex. Total_Sales).
    tabell = pd.crosstab(data["Region"], data[kolumn], values=data[varde] if varde else None,
                         aggfunc="sum" if varde else None, normalize="index") * 100
    ordning = [namn for namn in farger if namn in tabell.columns]   # samma ordning som färgerna
    tabell = tabell[ordning].sort_values(ordning[0])                # mest av den första överst
    lang = tabell.reset_index().melt(id_vars="Region", var_name=kolumn, value_name="Andel")
    fig = px.bar(lang, x="Andel", y="Region", color=kolumn, orientation="h", color_discrete_map=farger,
                 category_orders={kolumn: ordning}, text=lang["Andel"].map(lambda v: f"{v:.0f} %"))
    # textangle=0: talen står alltid rakt. Får ett tal inte plats i sin del döljs det (uniformtext nedan).
    fig.update_traces(hovertemplate="%{y} · %{fullData.name}: %{x:.1f} %<extra></extra>", textangle=0,
                      textposition="inside", insidetextanchor="middle", textfont=dict(color="#ffffff", size=12))
    snygga_till(fig, hojd)
    fig.update_layout(barmode="stack", uniformtext_minsize=10, uniformtext_mode="hide", bargap=0.3)
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", showgrid=False)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(tabell.index))
    return fig, tabell


# ===========================================================================
# 5. SIDANS UTSEENDE (CSS = instruktioner för hur sidan ska se ut)
# ===========================================================================

st.set_page_config(page_title="E-handel – gemensam dashboard", page_icon="📊", layout="wide")

st.markdown(f"""
<style>
/* Mjukare, modernare typsnitt och lite mer luft */
html, body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
.block-container {{ padding-top: 3.6rem; max-width: 1400px; }}   /* luft så att KPI-korten inte hamnar under verktygsraden */

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

/* Förklaringen under varje diagram: vad det visar, hur man läser det och vad vi ser */
.forklaring {{
    display: flex; flex-direction: column; gap: 6px; margin: 2px 0 6px 0;
    background: {KORT}; border-left: 3px solid {BLA}; border-radius: 10px;
    padding: 12px 14px; font-size: 0.92rem; line-height: 1.45; color: {TEXT_SVAG};
}}
.forklaring-etikett {{ color: {TEXT}; font-weight: 600; }}
.forklaring-slutsats {{ color: {TEXT}; padding-top: 6px; border-top: 1px solid {AXEL}; }}

/* Punktlistan i snabböversiktens kort */
.punkt {{ color: {TEXT}; }}
.punkt-titel {{ font-weight: 700; font-size: 1.05rem; margin-bottom: 6px; }}
.punkt ul {{ margin: 0; padding-left: 1.1rem; color: {TEXT_SVAG}; }}
.punkt li {{ margin: 4px 0; }}
.punkt b {{ color: {TEXT}; }}

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
button[role="tab"] p, div[role="tab"] p {{ font-size: 1.0rem; }}
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# 6. SIDOPANELEN: period, jämförelse och filter
# ===========================================================================

try:
    alla = hamta_data()
except FileNotFoundError:
    st.error(f"Hittar inte datafilen: {CSV_FIL}")
    st.stop()

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


ALLA_LANDER = "Alla länder"   # första valet i land-filtret

SNABBVAL = ["Senaste 7 dagarna", "Senaste 30 dagarna", "Senaste 90 dagarna", "Denna månad",
            "Förra månaden", "Detta kvartal", "Förra kvartalet", "I år", "Förra året",
            "Hela perioden", "Anpassat"]
JAMFOR_VAL = ["Föregående period", "Samma period förra året", "Anpassat"]
STANDARD_SNABBVAL = "Hela perioden"   # en översikt ska visa allt från början
STANDARD_PERIOD = snabbval_period(STANDARD_SNABBVAL)
STANDARD_JAMFOR = "Samma period förra året"
LAND_TILL_REGION = dict(zip(alla["Land"], alla["Region"]))   # t.ex. "USA" -> "Nordamerika"

# Filtren finns i två uppsättningar:
#   - utkastet (datumväljaren och "utkast_..."): det man håller på att välja i panelen till vänster
#   - det som gäller ("vald_..." och "filter_..."): det som sidan faktiskt visar
# Utkastet börjar gälla först när man klickar på Apply. En tom lista betyder "alla".
STANDARD = {
    "snabbval": STANDARD_SNABBVAL, "period_datum": STANDARD_PERIOD, "jamfor_pa": False,
    "jamfor_val": STANDARD_JAMFOR, "jamfor_datum": jamforelse_for(STANDARD_JAMFOR, STANDARD_PERIOD),
    "utkast_region": [], "utkast_land": ALLA_LANDER, "utkast_kundgrupp": [], "utkast_kategori": [],
    "vald_period": STANDARD_PERIOD, "vald_jamforelse": None,
    "filter_region": [], "filter_land": ALLA_LANDER, "filter_kundgrupp": [], "filter_kategori": [],
}
FILTER = ["region", "land", "kundgrupp", "kategori"]
ALLA_NAMN = {"region": list(REGIONER.values()), "kundgrupp": list(KUNDGRUPPER.values()),
             "kategori": list(KATEGORIER.values())}
for nyckel, varde in STANDARD.items():
    st.session_state.setdefault(nyckel, varde)
st.session_state.setdefault("klick_nr", 0)


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


def utkast_period():
    # Perioden i kalendern just nu (eller den som gäller, om man bara hunnit klicka på första dagen)
    return som_period(st.session_state["period_datum"]) or st.session_state["vald_period"]


def utkast_jamforelse(per):
    # Jämförelseperioden i panelen just nu, eller None om jämförelsen är avstängd
    if not st.session_state.get("jamfor_pa"):
        return None
    val = st.session_state.get("jamfor_val", STANDARD_JAMFOR)
    if val != "Anpassat":
        return jamforelse_for(val, per)
    return som_period(st.session_state.get("jamfor_datum")) or st.session_state["vald_jamforelse"]


def satt_land(namn, typ):
    # Väljer ett land (eller "Alla länder") och håller regionen i takt med det: väljer man USA sätts
    # regionen till Nordamerika, och går man tillbaka till alla länder kommer de regioner man hade
    # valt innan tillbaka. typ = "utkast" (panelen) eller "filter" (det som gäller på sidan).
    sparade = f"{typ}_regioner_fore_land"
    if namn == ALLA_LANDER:
        st.session_state[f"{typ}_region"] = st.session_state.pop(sparade, [])
    else:
        if sparade not in st.session_state:   # spara regionerna bara första gången
            st.session_state[sparade] = st.session_state[f"{typ}_region"]
        st.session_state[f"{typ}_region"] = [LAND_TILL_REGION[namn]]
    st.session_state[f"{typ}_land"] = namn


def nar_land_valjs():
    # Man valde ett land i listan i panelen. Det börjar gälla när man klickar på Apply.
    satt_land(st.session_state["utkast_land"], "utkast")


def tillampa():
    # Körs när man klickar på Apply: allt man har valt i panelen börjar gälla på hela sidan
    per = utkast_period()
    st.session_state["vald_period"], st.session_state["vald_jamforelse"] = per, utkast_jamforelse(per)
    for namn in FILTER:
        st.session_state[f"filter_{namn}"] = st.session_state[f"utkast_{namn}"]
    if "utkast_regioner_fore_land" in st.session_state:
        st.session_state["filter_regioner_fore_land"] = st.session_state["utkast_regioner_fore_land"]
    else:
        st.session_state.pop("filter_regioner_fore_land", None)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


def har_vantande_andringar():
    # True om man har ändrat något i panelen som inte gäller än (då behöver man klicka på Apply)
    def samma(namn):
        utkast, galler = st.session_state[f"utkast_{namn}"], st.session_state[f"filter_{namn}"]
        if namn == "land":
            return utkast == galler
        # tom lista och alla valda betyder samma sak
        return set(utkast or ALLA_NAMN[namn]) == set(galler or ALLA_NAMN[namn])
    per = utkast_period()
    return (per != st.session_state["vald_period"] or utkast_jamforelse(per) != st.session_state["vald_jamforelse"]
            or not all(samma(namn) for namn in FILTER))


def aterstall():
    # Körs när man klickar på "Återställ allt": hela perioden och alla regioner, länder, kundgrupper
    # och kategorier. Det gäller direkt, utan att man behöver klicka på Apply.
    for nyckel in list(STANDARD) + ["utkast_regioner_fore_land", "filter_regioner_fore_land", "tid_matt",
                                    "kategori_matt", "produkt_matt", "karta_matt", "grupp_matt", "betal_matt",
                                    "produkt_sortering"]:
        st.session_state.pop(nyckel, None)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


# Det som gäller på sidan just nu. En tom lista betyder "alla".
period, jamfor_period = st.session_state["vald_period"], st.session_state["vald_jamforelse"]
start, slut = period
langd = (slut - start).days + 1
valda_regioner = st.session_state["filter_region"] or ALLA_NAMN["region"]
valda_kundgrupper = st.session_state["filter_kundgrupp"] or ALLA_NAMN["kundgrupp"]
valda_kategorier = st.session_state["filter_kategori"] or ALLA_NAMN["kategori"]
valt_land = None if st.session_state["filter_land"] == ALLA_LANDER else st.session_state["filter_land"]

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
                    st.session_state["jamfor_datum"] = jamforelse_for(jamfor_val, utkast_period())
                st.markdown("**⚪ Jämförelseperiod**")
                st.date_input("Jämförelseperiod", key="jamfor_datum", min_value=date(2015, 1, 1),
                              max_value=SISTA_DAG, format="YYYY-MM-DD",
                              on_change=nar_jamfor_kalendern_andras, label_visibility="collapsed")
        st.caption(f"Datan går från {datum_text(FORSTA_DAG)} till {datum_text(SISTA_DAG)}. "
                   "Klicka på **Apply** i panelen när du är klar, så uppdateras sidan.")

    # Varna om en märkbar del (mer än 5 %) av jämförelsen ligger före datans början – då blir den
    # inte rättvis. En enstaka dag gör inget: datan börjar 2 jan 2023, så "förra året" saknar bara 1 jan.
    if jamfor_period and (FORSTA_DAG - jamfor_period[0]).days > 0.05 * ((jamfor_period[1] - jamfor_period[0]).days + 1):
        st.warning(f"Jämförelseperioden börjar före {datum_text(FORSTA_DAG)}, när datan saknas. "
                   "Jämförelsen blir därför missvisande – välj en kortare period.")

    st.markdown("### 🎛️ Filter")
    st.multiselect("🌍 Region", ALLA_NAMN["region"], key="utkast_region", placeholder="Alla regioner")

    # Land: bara länderna i de regioner man har valt (väljer man Nordamerika går bara Kanada, Mexiko
    # och USA att välja). Väljer man ett land sätts regionen till landets region (se satt_land).
    utkast_regioner = st.session_state["utkast_region"] or ALLA_NAMN["region"]
    land_alternativ = [ALLA_LANDER] + sorted(land for land, region in LAND_TILL_REGION.items()
                                             if region in utkast_regioner)
    if st.session_state["utkast_land"] not in land_alternativ:
        # t.ex. om man själv har valt bort landets region – då visas alla länder i regionerna man valt
        st.session_state["utkast_land"] = ALLA_LANDER
        st.session_state.pop("utkast_regioner_fore_land", None)
    st.selectbox("📍 Land", land_alternativ, key="utkast_land", on_change=nar_land_valjs,
                 help="Visar länderna i de regioner du har valt. Regionen ändras automatiskt till landets region. "
                      "Du kan också klicka på ett land på kartan.")
    st.multiselect(
        "👥 Kundgrupp", ALLA_NAMN["kundgrupp"], key="utkast_kundgrupp", placeholder="Alla kundgrupper",
        help="**Privatpersoner** = vanliga konsumenter. **Företag** = större företag. "
             "**Småföretag** = små företag och folk som driver firma hemifrån (heter \"Home Office\" i datan).")
    st.multiselect("🛒 Kategori", ALLA_NAMN["kategori"], key="utkast_kategori", placeholder="Alla kategorier")

    # Apply: allt man har valt ovanför börjar gälla. Knappen lyser blått när det finns något att tillämpa.
    vantar = har_vantande_andringar()
    if vantar:
        st.info("Du har ändrat något som inte gäller än. Klicka på **Apply** för att uppdatera sidan.", icon="✏️")
    st.button("✓ Apply", on_click=tillampa, type="primary" if vantar else "secondary", width="stretch")
    st.button("↺ Återställ allt", on_click=aterstall, width="stretch",
              help="Hela perioden och alla regioner, länder, kundgrupper och kategorier. Gäller direkt.")
    st.caption("💡 Klickar du på ett land, en kundgrupp eller en kategori i ett diagram filtreras sidan direkt.")

# Behåll bara de ordrar som matchar region, kundgrupp och kategori (alla datum)
bas = alla[alla["Region"].isin(valda_regioner) & alla["Kundgrupp"].isin(valda_kundgrupper)
           & alla["Kategori"].isin(valda_kategorier)]


def i_period(data, per):
    # Plockar ut ordrarna mellan två datum (båda dagarna räknas med)
    return data[(data["Datum"] >= per[0]) & (data["Datum"] <= per[1])]


def eller_inget(data):
    # En tom tabell blir None, så att resten av koden bara behöver kolla "is None"
    return None if data is None or data.empty else data


# Alla länder i vald period och i jämförelseperioden – används av kartan och topplistan.
# Jämförelsen blir None om den är avstängd eller saknar data (t.ex. före 2023).
df_alla_lander = i_period(bas, period)
jmf_alla_lander = eller_inget(i_period(bas, jamfor_period)) if jamfor_period else None


# ===========================================================================
# 7. KLICK I DIAGRAMMEN: filtrerar sidan direkt (och ändrar filtren i panelen)
# ===========================================================================

KOD_TILL_LAND = {kod: namn for namn, kod in LANDER.values()}   # t.ex. "MEX" -> "Mexiko"


def valj_land(namn):
    # Ett klick på ett land gäller direkt, både på sidan och i panelen
    for typ in ("filter", "utkast"):
        satt_land(namn, typ)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


def nar_land_klickas(nyckel):
    # Körs när man klickar på ett land på kartan (ger landskoden) eller i topplistan (ger namnet).
    # Klickar man på samma land igen tas filtret bort.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    varde = punkter[0].get("location") or punkter[0].get("y")
    namn = KOD_TILL_LAND.get(varde, varde)
    if namn in LAND_TILL_REGION:
        valj_land(ALLA_LANDER if st.session_state["filter_land"] == namn else namn)


def nar_stapel_klickas(filter_namn, nyckel):
    # Körs när man klickar på en stapel för en kundgrupp eller kategori: filtrerar hela sidan på den
    # direkt (och ändrar filtret i panelen). Klickar man på samma igen visas alla.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    namn = punkter[0].get("y")
    if namn in ALLA_NAMN[filter_namn]:
        nytt = [] if st.session_state[f"filter_{filter_namn}"] == [namn] else [namn]
        st.session_state[f"filter_{filter_namn}"], st.session_state[f"utkast_{filter_namn}"] = nytt, list(nytt)
    st.session_state["klick_nr"] += 1


def bara_landet(data):
    # Om man har valt ett land: behåll bara det landets ordrar
    if data is None or valt_land is None:
        return data
    return data[data["Land"] == valt_land]


df = bara_landet(df_alla_lander)    # det som alla diagram (utom kartan och topplistan) visar
jmf = eller_inget(bara_landet(jmf_alla_lander))

if jamfor_period and jmf_alla_lander is None and not df_alla_lander.empty:
    st.sidebar.warning("Det finns ingen data för jämförelseperioden. Välj en annan period.")

# Om filtren inte ger några ordrar alls: visa ett meddelande och stoppa här
if df.empty:
    if valt_land:
        st.warning(f"{valt_land} har inga ordrar som matchar dina val. Välj en längre period eller ett annat land.")
        st.button("✕ Visa alla länder", on_click=valj_land, args=(ALLA_LANDER,), key="alla_lander_tom")
    else:
        st.warning("Inga ordrar matchar dina val. Välj en längre period eller ändra filtren.")
    st.stop()


# ===========================================================================
# 8. NYCKELTAL: tio KPI-kort högst upp, med pilar när man jämför perioder
# ===========================================================================

def nyckeltal(data):
    # De viktigaste siffrorna för en period (samma tio KPI:er som i Wissams dashboard,
    # men med frakt per order från Johans del i stället för produkter per order)
    if data is None:
        return None
    ordrar = data["Order_ID"].nunique()
    forsaljning, vinst = data["Total_Sales"].sum(), data["Profit"].sum()
    return {
        "Försäljning": forsaljning,
        "Vinst": vinst,
        "Marginal": vinst / forsaljning * 100,
        "Ordrar": ordrar,
        "Antal": data["Quantity"].sum(),
        "Snittorder": forsaljning / ordrar,
        "Vinst per order": vinst / ordrar,
        "Rabatt": data["Discount_Percent"].mean(),
        "Frakt": data["Shipping_Cost"].mean(),
        "Förlust": data.loc[data["Förlust"], "Order_ID"].nunique() / ordrar * 100,
    }


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
    # Summerar nyckeltalen per dag/vecka/månad i den valda perioden.
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
        Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"), Ordrar=("Order_ID", "nunique"),
        Antal=("Quantity", "sum"), Rabatt=("Discount_Percent", "mean"), Frakt=("Shipping_Cost", "mean"),
        Förlustordrar=("Förlust", "sum"))
    # Dagar/veckor utan ordrar: 0 i försäljning, vinst och ordrar. Snitt och andelar lämnas tomma,
    # annars ser det ut som att t.ex. frakten var gratis och marginalen 0 just den dagen.
    serie = serie.reindex(steg)
    summor = ["Försäljning", "Vinst", "Ordrar", "Antal", "Förlustordrar"]
    serie[summor] = serie[summor].fillna(0)
    har_ordrar = serie["Ordrar"].where(serie["Ordrar"] > 0)
    serie["Marginal"] = serie["Vinst"] / serie["Försäljning"].where(serie["Försäljning"] > 0) * 100
    serie["Snittorder"] = serie["Försäljning"] / har_ordrar
    serie["Vinst per order"] = serie["Vinst"] / har_ordrar
    serie["Förlust"] = serie["Förlustordrar"] / har_ordrar * 100
    return serie


serie_nu = tidsserie(df)
FLYTT = (start - jamfor_period[0]) if jmf is not None else timedelta(0)
serie_jmf = tidsserie(jmf, FLYTT) if jmf is not None else None


def steg_text(dag):
    # Hur en punkt beskrivs i text, t.ex. "3 okt 2025", "veckan från 3 okt 2025" eller "oktober 2025"
    if FREKVENS == "MS":
        return f"{MANADER_LANGA[dag.month - 1]} {dag.year}"
    text = datum_text(dag.date())
    return f"veckan från {text}" if FREKVENS == "7D" else text


def svenska_datum(fig, x):
    # Svenska datum på tidsaxeln: högst cirka 8 etiketter så att de inte trängs
    etiketter = x[::max(1, len(x) // 8)]
    fig.update_xaxes(showgrid=False, tickvals=etiketter,
                     ticktext=[f"{MANADER[d.month - 1]} {d.year}" if FREKVENS == "MS"
                               else f"{d.day} {MANADER[d.month - 1]}" for d in etiketter],
                     hoverformat=" ")   # dölj den engelska rubriken i rutan, datumet står redan på svenska


# Ett kort per nyckeltal:
# (rubrik, nyckeltal, hur talet skrivs, visa skillnaden i procentenheter?, är lägre bättre?, förklaring)
KPI_KORT = [
    ("💰 Försäljning", "Försäljning", pengar, False, False, "Summan av vad kunderna har betalat (Total_Sales)."),
    ("📈 Vinst", "Vinst", pengar, False, False,
     "Det som blir kvar till företaget när kostnaderna är betalda (Profit)."),
    ("🎯 Vinstmarginal", "Marginal", procent, True, False,
     "Hur stor del av försäljningen som blir vinst. Pilen visar skillnaden i procentenheter."),
    ("🧾 Ordrar", "Ordrar", tal, False, False, "Antal ordrar."),
    ("📦 Sålda produkter", "Antal", tal, False, False, "Antal sålda enheter (Quantity)."),
    ("🛍️ Snittordervärde", "Snittorder", pengar_exakt, False, False,
     "Försäljning delat med antal ordrar (kallas AOV)."),
    ("💵 Vinst per order", "Vinst per order", pengar_exakt, False, False, "Vinst delat med antal ordrar."),
    ("🏷️ Snittrabatt", "Rabatt", procent, True, True,
     "Genomsnittlig rabatt per order. Lägre rabatt ger högre marginal, så en minskning visas i grönt."),
    ("🚚 Frakt per order", "Frakt", pengar_exakt, False, True,
     "Vad det kostar i genomsnitt att skicka en order till kunden. En minskning visas i grönt."),
    ("⚠️ Förlustordrar", "Förlust", procent, True, True,
     "Andel ordrar där vinsten blev negativ. En minskning visas i grönt."),
]
for rad in (KPI_KORT[:5], KPI_KORT[5:]):
    for kolumn, (etikett, namn, format_, enheter, lagre_bast, beskrivning) in zip(st.columns(5), rad):
        if forut is None:
            delta = None
        elif enheter:
            delta = procentenheter(nu[namn] - forut[namn])   # för procenttal visas skillnaden i procentenheter
        else:
            delta = forandring(nu[namn], forut[namn])
        # Hjälptexten (ⓘ): förklaring + siffran för jämförelseperioden
        hjalp = beskrivning + (f"  \n⚪ Jämförelseperioden: **{format_(forut[namn])}**" if forut else "")
        kolumn.metric(etikett, format_(nu[namn]), delta=delta, help=hjalp, height="stretch",
                      delta_color="inverse" if lagre_bast else "normal")
if forut:
    st.caption(f"🔵 {period_text(period)} jämfört med ⚪ {period_text(jamfor_period)}. "
               "Pilen visar förändringen. Håll musen över ⓘ för att se siffran för jämförelseperioden.")
else:
    st.caption(f"🔵 {period_text(period)}. Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster "
               "för att se pilar med förändringen mot en annan period.")


# ===========================================================================
# 9. SNABBÖVERSIKT: det viktigaste i urvalet (idé från Alyoshs del)
# ===========================================================================

per_produkt = summera(df, "Product_Name")
per_kategori = summera(df, "Kategori")
per_land_urval = summera(df, "Land")
per_kundgrupp = summera(df, "Kundgrupp")

rubrik("🔎", "Det viktigaste i urvalet", "Toppar och dalar för den period och de filter du har valt.")
s1, s2, s3 = st.columns(3)
with s1:
    topp_steg = serie_nu["Försäljning"].idxmax()
    storst_grupp = per_kundgrupp["Försäljning"].idxmax()
    punktkort("📈", "Försäljning", [
        f"Bästa {STEG}: <b>{steg_text(topp_steg)}</b> ({pengar(serie_nu.loc[topp_steg, 'Försäljning'])})",
        f"Största marknad: <b>{per_land_urval['Försäljning'].idxmax()}</b> "
        f"({pengar(per_land_urval['Försäljning'].max())})",
        f"Största kundgrupp: <b>{storst_grupp}</b> "
        f"({procent(per_kundgrupp.loc[storst_grupp, 'Försäljning'] / nu['Försäljning'] * 100)} av försäljningen)",
    ])
with s2:
    bast_p, bast_k = per_produkt["Vinst"].idxmax(), per_kategori["Vinst"].idxmax()
    hogst_k = per_kategori["Marginal"].idxmax()
    punktkort("🏆", "Drar in mest vinst", [
        f"Produkt: <b>{bast_p}</b> ({pengar(per_produkt.loc[bast_p, 'Vinst'])})",
        f"Kategori: <b>{bast_k}</b> ({pengar(per_kategori.loc[bast_k, 'Vinst'])})",
        f"Högst marginal: <b>{hogst_k}</b> ({procent(per_kategori.loc[hogst_k, 'Marginal'])})",
    ])
with s3:
    samst_p, samst_k = per_produkt["Vinst"].idxmin(), per_kategori["Marginal"].idxmin()
    punktkort("⚠️", "Drar in minst vinst", [
        f"Produkt: <b>{samst_p}</b> ({pengar(per_produkt.loc[samst_p, 'Vinst'])})",
        f"Lägst marginal: <b>{samst_k}</b> ({procent(per_kategori.loc[samst_k, 'Marginal'])})",
        f"Förlustordrar: <b>{tal(df['Förlust'].sum())}</b> ({procent(nu['Förlust'])} av ordrarna)",
    ])


# ===========================================================================
# 10. FLIK: FÖRSÄLJNING & TRENDER
# ===========================================================================

def visa_trender():
    # --- Utveckling över tid (Johans tidsdiagram, med jämförelsen ovanpå) ---
    with kort("📈", "Utveckling över tid", "Välj vad diagrammet ska visa."):
        tid_matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal", "Ordrar"],
                                        default="Försäljning", key="tid_matt",
                                        label_visibility="collapsed") or "Försäljning"
        farg = MATT_FARG[tid_matt]
        prefix = "$" if tid_matt in ("Försäljning", "Vinst") else ""
        suffix = " %" if tid_matt == "Marginal" else ""
        siffror = ".1f" if tid_matt == "Marginal" else ",.0f"

        x = serie_nu.index
        tid = go.Figure()
        # Jämförelsen ritas först (streckad grå linje) så att den valda perioden hamnar ovanpå
        if serie_jmf is not None:
            tid.add_trace(go.Scatter(
                x=x, y=serie_jmf[tid_matt], name=f"Jämförelse ({period_text(jamfor_period)})",
                mode="lines", line=dict(color=GRA, width=2, dash="dash"), connectgaps=True,
                customdata=[steg_text(d - pd.Timedelta(FLYTT)) for d in x],
                hovertemplate="⚪ %{customdata}: " + prefix + "%{y:" + siffror + "}" + suffix + "<extra></extra>"))
        # Den valda perioden: linje i måttets färg med fylld yta under
        tid.add_trace(go.Scatter(
            x=x, y=serie_nu[tid_matt], name=f"Vald period ({period_text(period)})",
            mode="lines+markers" if len(x) <= 60 else "lines", connectgaps=True,
            line=dict(color=farg, width=3, shape="spline" if FREKVENS == "MS" else "linear", smoothing=0.5),
            marker=dict(size=7), fill="tozeroy", fillcolor=genomskinlig(farg, 0.15),
            customdata=[steg_text(d) for d in x],
            hovertemplate="🔵 %{customdata}: " + prefix + "%{y:" + siffror + "}" + suffix + "<extra></extra>"))
        snygga_till(tid, hojd=380, pengar_y=prefix == "$")
        tid.update_layout(hovermode="x unified", legend=dict(traceorder="reversed"))
        # Svenska datum på axeln: högst cirka 8 etiketter så att de inte trängs
        svenska_datum(tid, x)
        tid.update_yaxes(rangemode="tozero", ticksuffix=suffix)
        visa(tid, "tid")

        # Slutsatsen: förändringen mot jämförelseperioden, eller den bästa punkten om man inte jämför
        format_ = {"Försäljning": pengar, "Vinst": pengar, "Marginal": procent, "Ordrar": tal}[tid_matt]
        if forut:
            andring = (procentenheter(nu[tid_matt] - forut[tid_matt]) if tid_matt == "Marginal"
                       else forandring(nu[tid_matt], forut[tid_matt]) or "–")
            slutsats = (f"{tid_matt} i vald period: <b>{format_(nu[tid_matt])}</b>, mot {format_(forut[tid_matt])} "
                        f"i jämförelseperioden – en förändring på <b>{andring}</b>.")
        else:
            basta = serie_nu[tid_matt].idxmax()
            slutsats = (f"Högst var det under <b>{steg_text(basta)}</b> "
                        f"({format_(serie_nu.loc[basta, tid_matt])}).")
        forklaring(
            f"Hur {tid_matt.lower()} har utvecklats i den period du valt. Varje punkt är en {STEG}.",
            "En stigande linje betyder att det går bättre. "
            + ("Den streckade grå linjen är jämförelseperioden, lagd ovanpå så att första dagen jämförs "
               "med första dagen." if serie_jmf is not None else
               "Slå på ⚖️ Jämför i panelen till vänster för att se en jämförelse som en streckad linje."),
            slutsats)

    # --- Försäljning och vinst per år (Alyoshs årsdiagram) ---
    with kort("📅", "Försäljning och vinst per år"):
        ar = summera(df, df["Order_Date"].dt.year.rename("År")).reset_index()
        ar["År"] = ar["År"].astype(str)   # text, så att axeln visar "2023" och inte "2 023"
        fig = px.bar(ar, x="År", y=["Försäljning", "Vinst"], barmode="group", color_discrete_map=MATT_FARG)
        fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside", cliponaxis=False,
                          textfont=dict(color=TEXT, size=13), marker_cornerradius=4,
                          hovertemplate="%{x} – %{fullData.name}: $%{y:,.0f}<extra></extra>")
        snygga_till(fig, 340, pengar_y=True)
        fig.update_xaxes(type="category", showgrid=False)
        fig.update_yaxes(range=[0, ar["Försäljning"].max() * 1.18])   # plats för talen ovanför staplarna
        visa(fig, "per_ar")
        if len(ar) >= 2:
            sista, forra = ar.iloc[-1], ar.iloc[-2]
            slutsats = (f"<b>{sista['År']}</b> sålde vi för {pengar(sista['Försäljning'])}, "
                        f"<b>{forandring(sista['Försäljning'], forra['Försäljning'])}</b> jämfört med {forra['År']}. "
                        f"Marginalen var {procent(sista['Marginal'])} mot {procent(forra['Marginal'])}.")
        else:
            slutsats = "Välj en period som täcker flera år (t.ex. <b>Hela perioden</b>) för att jämföra åren."
        forklaring(
            "Den totala försäljningen (blå) och vinsten (turkos) för varje år i perioden.",
            "Jämför staplarna år för år. Om perioden bara täcker en del av ett år räknas bara den delen, "
            "så välj hela år för en rättvis jämförelse.",
            slutsats)


# ===========================================================================
# 11. FLIK: PRODUKTER & KATEGORIER
# ===========================================================================

def visa_produkter():
    vanster, hoger = st.columns(2)

    # --- Kategorier (klickbara: filtrerar hela sidan) ---
    with vanster, kort("🛋️", "Kategorier", "Klicka på en kategori för att filtrera hela sidan."):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal"], default="Försäljning",
                                    key="kategori_matt", label_visibility="collapsed") or "Försäljning"
        format_ = procent if matt == "Marginal" else pengar
        jmf_kategori = summera(jmf, "Kategori")[matt] if jmf is not None else None
        fig = jamforelse_staplar(per_kategori[matt], jmf_kategori, format_, KATEGORI_FARG,
                                 som_procentenheter=matt == "Marginal")
        visa(fig, "kategorier", partial(nar_stapel_klickas, "kategori"))
        storst, hogst = per_kategori["Försäljning"].idxmax(), per_kategori["Marginal"].idxmax()
        forklaring(
            f"{matt} för varje produktkategori.",
            "Längst stapel = störst. Byt mellan försäljning, vinst och marginal med knapparna ovanför."
            + (" Grå stapel = jämförelseperioden, och förändringen står inom parentes." if jmf is not None else ""),
            f"<b>{storst}</b> står för {procent(per_kategori.loc[storst, 'Försäljning'] / nu['Försäljning'] * 100)} "
            f"av försäljningen, men <b>{hogst}</b> har högst marginal ({procent(per_kategori.loc[hogst, 'Marginal'])}).")

    # --- Topp 10 produkter, färgade efter kategori ---
    with hoger, kort("🏆", "Topp 10 produkter"):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinst"], default="Försäljning",
                                    key="produkt_matt", label_visibility="collapsed") or "Försäljning"
        topp = per_produkt.nlargest(10, matt).reset_index()
        topp["Kategori"] = topp["Product_Name"].map(df.groupby("Product_Name")["Kategori"].first())
        fig = px.bar(topp, x=matt, y="Product_Name", orientation="h", color="Kategori",
                     color_discrete_map=KATEGORI_FARG, text=topp[matt].map(pengar),
                     category_orders={"Kategori": list(KATEGORIER.values())})
        fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>", textposition="outside", cliponaxis=False,
                          textfont=dict(color=TEXT, size=13), marker_cornerradius=4)
        snygga_till(fig, 360)
        fig.update_xaxes(range=[0, topp[matt].max() * 1.25], showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(topp["Product_Name"][::-1]))
        visa(fig, "topp_produkter")
        forklaring(
            f"De tio produkter som har dragit in mest {matt.lower()}. Färgen visar vilken kategori produkten hör till.",
            "Störst överst. Färgerna är samma som i kategoridiagrammet till vänster.",
            f"Etta är <b>{topp['Product_Name'].iloc[0]}</b> med {pengar(topp[matt].iloc[0])}.")

    # --- Produkttabellen (Alyoshs klickbara tabell) ---
    with kort("🏷️", "Alla produkter", "Klicka på en rad för att se produkten över tid."):
        sortering = st.segmented_control("Sortera efter", ["Försäljning", "Vinst", "Marginal"],
                                         default="Försäljning", key="produkt_sortering") or "Försäljning"
        produkter = per_produkt.sort_values(sortering, ascending=False).reset_index()
        produkter["Kategori"] = produkter["Product_Name"].map(df.groupby("Product_Name")["Kategori"].first())
        produkter = produkter.round({"Försäljning": 0, "Vinst": 0, "Marginal": 1})
        produkter["Vinst"] += 0.0   # avrundning kan ge "-0"; att lägga till 0.0 gör om det till vanlig 0
        # Klickbar tabell. key innehåller filtren och sorteringen, så att valet nollställs när de ändras
        # (annars skulle rad nummer 3 plötsligt betyda en annan produkt).
        vald_rad = st.dataframe(
            produkter, hide_index=True, width="stretch", height=390,
            on_select="rerun", selection_mode="single-row",
            key=f"produkter_{'_'.join(valda_kategorier)}_{sortering}_{len(df)}",
            column_order=["Product_Name", "Kategori", "Försäljning", "Vinst", "Marginal", "Ordrar", "Antal"],
            column_config={
                # ProgressColumn = en stapel i cellen, så att man ser storleksordningen direkt
                "Product_Name": st.column_config.TextColumn("Produkt"),
                "Kategori": st.column_config.TextColumn(width="small"),
                "Försäljning": st.column_config.ProgressColumn(
                    "Försäljning ($)", format="localized", min_value=0, max_value=float(produkter["Försäljning"].max())),
                "Vinst": st.column_config.ProgressColumn(
                    "Vinst ($)", format="localized", min_value=0, max_value=float(max(produkter["Vinst"].max(), 1))),
                "Marginal": st.column_config.ProgressColumn(
                    "Marginal (%)", format="%.1f", min_value=0, max_value=float(max(produkter["Marginal"].max(), 1))),
                "Ordrar": st.column_config.NumberColumn(width="small"),
                "Antal": st.column_config.NumberColumn("Sålda", width="small", help="Antal sålda enheter"),
            },
        )
        forklaring(
            "Alla produkter i urvalet med försäljning, vinst, marginal, antal ordrar och sålda enheter.",
            "Staplarna i cellerna visar storleksordningen. Sortera med knapparna ovanför och klicka på en "
            "rad för att se den produkten i diagrammet nedanför.")

    # --- Detaljer för vald produkt ---
    rader = vald_rad.selection.rows                     # valda radnummer (tom lista = inget valt)
    vald_produkt = produkter.loc[rader[0] if rader else 0, "Product_Name"]   # inget valt -> översta produkten
    df_produkt = df[df["Product_Name"] == vald_produkt]
    with kort("🔍", vald_produkt, f"Kategori: {df_produkt['Kategori'].iloc[0]}."
              + ("" if rader else " Visar produkten överst i listan – klicka på en rad för att välja en annan.")):
        produkt = nyckeltal(df_produkt)
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("💰 Försäljning", pengar(produkt["Försäljning"]), height="stretch")
        p2.metric("📈 Vinst", pengar(produkt["Vinst"]), height="stretch")
        p3.metric("🎯 Vinstmarginal", procent(produkt["Marginal"]), height="stretch")
        p4.metric("📦 Sålda enheter", tal(produkt["Antal"]), height="stretch")
        serie = tidsserie(df_produkt)
        fig = go.Figure()
        for namn in ["Försäljning", "Vinst"]:
            fig.add_trace(go.Scatter(x=serie.index, y=serie[namn], name=namn, mode="lines+markers",
                                     line=dict(color=MATT_FARG[namn], width=3), marker=dict(size=6),
                                     customdata=[steg_text(d) for d in serie.index],
                                     hovertemplate=namn + " %{customdata}: $%{y:,.0f}<extra></extra>"))
        snygga_till(fig, 300, pengar_y=True)
        fig.update_layout(hovermode="x unified")
        svenska_datum(fig, serie.index)
        visa(fig, "produkt_tid")
        forklaring(
            f"Försäljning (blå) och vinst (turkos) för {vald_produkt} per {STEG} i den valda perioden.",
            "Avståndet mellan linjerna är det som går åt till kostnader. Ju närmare linjerna ligger, "
            "desto lönsammare är produkten.")


# ===========================================================================
# 12. FLIK: GEOGRAFI & KUNDER
# ===========================================================================

def visa_geografi():
    # --- Världskartan (Johans klickbara karta) ---
    with kort("🗺️", "Världskarta", "Klicka på ett land så visar alla diagram bara det landet – "
                                    "klicka igen för att se alla länder."):
        alternativ = ["Försäljning", "Vinst", "Marginal (%)", "Ordrar"]
        if jmf_alla_lander is not None:
            alternativ.append("Förändring (%)")   # bara när man jämför: hur mycket varje land ökat/minskat
        if st.session_state.get("karta_matt") not in alternativ + [None]:
            st.session_state.pop("karta_matt")    # t.ex. "Förändring" när jämförelsen har stängts av
        matt = st.segmented_control("Vad ska kartan visa?", alternativ, default="Försäljning", key="karta_matt",
                                    label_visibility="collapsed") or "Försäljning"

        # Kartan visar alltid alla länder i urvalet, även när ett land är valt
        per_land = df_alla_lander.groupby(["Land", "Landskod", "Region"], as_index=False).agg(
            Ordrar=("Order_ID", "nunique"), Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"))
        per_land["Marginal (%)"] = per_land["Vinst"] / per_land["Försäljning"] * 100

        # Försäljningen i jämförelseperioden för varje land, och hur mycket den har förändrats.
        # Texten används i rutan som visas när man håller musen över landet.
        per_land["Förändring (%)"], per_land["Jämförelse"] = float("nan"), ""
        if jmf_alla_lander is not None:
            innan = per_land["Landskod"].map(jmf_alla_lander.groupby("Landskod")["Total_Sales"].sum())
            per_land["Förändring (%)"] = (per_land["Försäljning"] / innan - 1) * 100
            per_land["Jämförelse"] = [f"<br>⚪ Jämförelse: {pengar(i)} ({procent_andring(f)})" if pd.notna(i)
                                      else "<br>⚪ Jämförelse: ingen försäljning"
                                      for i, f in zip(innan, per_land["Förändring (%)"])]

        # Förändring visas med två färger: blått = ökning, rött = minskning, grått = oförändrat.
        # Övriga mått visas från mörkblått (lite) till ljusblått (mycket).
        if matt == "Förändring (%)":
            # Ett land som gått från nästan inget till lite kan öka med flera tusen procent och göra
            # alla andra länder grå. Därför slutar färgskalan vid ±100 %.
            tak = min(100, max(10, per_land["Förändring (%)"].abs().quantile(0.9)))
            farger = dict(color_continuous_scale=[[0, ROD], [0.5, "#383835"], [1, BLA]], range_color=[-tak, tak])
        else:
            farger = dict(color_continuous_scale=BLA_SKALA)

        karta = px.choropleth(per_land, locations="Landskod", color=matt, projection="natural earth",
                              custom_data=["Land", "Region", "Försäljning", "Vinst", "Marginal (%)", "Ordrar",
                                           "Jämförelse"], **farger)
        karta.update_traces(marker_line_color="rgba(11,14,20,0.9)", marker_line_width=0.6,
                            hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                                          "Försäljning: $%{customdata[2]:,.0f}<br>Vinst: $%{customdata[3]:,.0f}<br>"
                                          "Marginal: %{customdata[4]:.1f} %<br>Ordrar: %{customdata[5]}%{customdata[6]}"
                                          "<br><i>Klicka för att filtrera</i><extra></extra>")
        # Det valda landet får en tjock vit kant, så att man ser vilket land som är valt
        if valt_land:
            vald_kod = per_land.loc[per_land["Land"] == valt_land, "Landskod"].iloc[0]
            karta.add_trace(go.Choropleth(locations=[vald_kod], z=[1], showscale=False, hoverinfo="skip",
                                          colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                          marker_line_color="#ffffff", marker_line_width=2.5))
        karta.update_geos(
            showframe=False, showcoastlines=False, showcountries=True, countrycolor="rgba(255,255,255,0.08)",
            showland=True, landcolor="#1a202b", showocean=False, bgcolor="rgba(0,0,0,0)",
            lataxis_range=[-58, 85],   # klipp bort Antarktis så att kartan blir större
        )
        snygga_till(karta, hojd=480)
        karta.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar=dict(
            title=dict(text=matt, font=dict(color=TEXT_SVAG)), thickness=10, len=0.6, outlinewidth=0,
            tickformat=",.0f", tickprefix="$" if matt in ("Försäljning", "Vinst") else "",
            ticksuffix=" %" if "%" in matt else "", tickfont=dict(color=TEXT_SVAG)))
        visa(karta, "karta", nar_land_klickas)   # ett klick på ett land filtrerar hela sidan

        storst = per_land.loc[per_land["Försäljning"].idxmax()]
        forklaring(
            f"{matt} i varje land vi säljer till. Grå länder har inga ordrar i urvalet.",
            "Ju ljusare blå, desto mer. " + ("Vid Förändring betyder blått ökning och rött minskning. "
                                             if jmf_alla_lander is not None else "")
            + "Håll musen över ett land för att se alla siffror.",
            f"Störst är <b>{storst['Land']}</b> med {pengar(storst['Försäljning'])} "
            f"(marginal {procent(storst['Marginal (%)'])}).")

    vanster, hoger = st.columns(2)

    # --- Topplista över länder (klickbar) ---
    with vanster, kort("🏆", "Länder med mest försäljning", "Klicka på ett land för att filtrera hela sidan."):
        topp = per_land.sort_values("Försäljning", ascending=False).reset_index(drop=True)
        topp["Plats"] = topp.index + 1
        visas = topp.head(10)
        if valt_land and valt_land not in set(visas["Land"]):
            visas = pd.concat([visas, topp[topp["Land"] == valt_land]])   # visa alltid det valda landet
        visas = visas.iloc[::-1]   # störst överst
        # Varje land har sin regions färg. Är ett land valt lyser det, och övriga dämpas.
        farg = [genomskinlig(REGION_FARG[region], 1 if valt_land in (None, land) else 0.3)
                for land, region in zip(visas["Land"], visas["Region"])]
        fig = go.Figure(go.Bar(
            y=visas["Land"], x=visas["Försäljning"], orientation="h", marker_color=farg,
            marker_cornerradius=4, text=visas["Försäljning"].map(pengar), textposition="outside",
            cliponaxis=False, textfont=dict(color=TEXT, size=13),
            customdata=visas[["Plats", "Region", "Marginal (%)"]].values,
            hovertemplate="<b>%{y}</b> · nr %{customdata[0]} · %{customdata[1]}<br>"
                          "Försäljning: %{text}<br>Marginal: %{customdata[2]:.1f} %<br>"
                          "<i>Klicka för att filtrera</i><extra></extra>"))
        snygga_till(fig, 360)
        fig.update_xaxes(range=[0, visas["Försäljning"].max() * 1.3], showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False)
        visa(fig, "topplista", nar_land_klickas)
        if valt_land:
            plats_nr = int(topp.loc[topp["Land"] == valt_land, "Plats"].iloc[0])
            slutsats = f"<b>{valt_land}</b> är nummer <b>{plats_nr}</b> av {len(topp)} länder i försäljning."
        else:
            topp3 = topp.head(3)["Försäljning"].sum() / topp["Försäljning"].sum() * 100
            slutsats = f"De tre största länderna står för <b>{procent(topp3)}</b> av försäljningen."
        forklaring(
            "De tio länder där kunderna har handlat för mest pengar. Färgen visar landets region.",
            "Längst stapel = viktigast marknad. Håll musen över en stapel för att se marginalen.",
            slutsats)

    # --- Kundgrupper (klickbara) ---
    with hoger, kort("👥", "Kundgrupper", "Vem köper – och vem får stora rabatter? Klicka för att filtrera."):
        grupp_matt = st.segmented_control("Visa", ["Försäljning", "Vinstmarginal", "Stor rabatt"],
                                          default="Försäljning", key="grupp_matt",
                                          label_visibility="collapsed") or "Försäljning"

        def per_grupp(data, vad):
            # Försäljning, vinstmarginal eller andel ordrar med mer än 10 % rabatt, per kundgrupp
            if data is None:
                return None
            grupp = data.groupby("Kundgrupp")
            if vad == "Försäljning":
                return grupp["Total_Sales"].sum()
            if vad == "Vinstmarginal":
                return grupp["Profit"].sum() / grupp["Total_Sales"].sum() * 100
            return (data["Discount_Percent"] > 10).groupby(data["Kundgrupp"]).mean() * 100

        format_ = pengar if grupp_matt == "Försäljning" else procent
        fig = jamforelse_staplar(per_grupp(df, grupp_matt), per_grupp(jmf, grupp_matt), format_,
                                 KUNDGRUPP_FARG, som_procentenheter=grupp_matt != "Försäljning", hojd=310)
        visa(fig, "kundgrupper", partial(nar_stapel_klickas, "kundgrupp"))
        rabatt = per_grupp(df, "Stor rabatt").sort_values()
        marginal = per_grupp(df, "Vinstmarginal")
        forklaring(
            {"Försäljning": "Hur mycket varje kundgrupp har köpt för.",
             "Vinstmarginal": "Hur stor del av varje kundgrupps köp som blir vinst.",
             "Stor rabatt": "Hur stor andel av varje kundgrupps ordrar som fått mer än 10 % rabatt."}[grupp_matt],
            "Privatpersoner = vanliga konsumenter, Företag = större företag, Småföretag = små företag och "
            "folk som driver firma hemifrån. Byt mått med knapparna ovanför.",
            f"<b>{rabatt.index[-1]}</b> får oftast stor rabatt ({procent(rabatt.iloc[-1])} av ordrarna) och har "
            f"en vinstmarginal på {procent(marginal[rabatt.index[-1]])}. Mer rabatt = mindre vinst."
            if len(rabatt) > 1 else None)

    vanster, hoger = st.columns(2)

    # --- Frakt per region (Johans fråga 2) ---
    with vanster, kort("🚚", "Fraktkostnad per region"):
        frakt = df.groupby("Region").agg(Frakt=("Shipping_Cost", "sum"), Försäljning=("Total_Sales", "sum"),
                                         Snitt=("Shipping_Cost", "mean"))
        frakt["Andel"] = frakt["Frakt"] / frakt["Försäljning"] * 100
        frakt = frakt.sort_values("Andel").reset_index()
        fig = go.Figure(go.Bar(
            y=frakt["Region"], x=frakt["Andel"], orientation="h", marker_cornerradius=4,
            marker_color=[REGION_FARG[region] for region in frakt["Region"]],
            text=[f"{procent(a)}  ·  {pengar_exakt(s)} per order" for a, s in zip(frakt["Andel"], frakt["Snitt"])],
            textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
            hovertemplate="%{y}: %{text}<extra></extra>"))
        snygga_till(fig, 300)
        fig.update_xaxes(range=[0, frakt["Andel"].max() * 1.9], showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False)
        visa(fig, "frakt")
        dyrast, billigast = frakt.iloc[-1], frakt.iloc[0]
        forklaring(
            "Hur stor del av försäljningen som går till frakt i varje region, och vad frakten kostar per order.",
            "Längre stapel = dyrare frakt i förhållande till vad kunderna köper för.",
            f"I <b>{dyrast['Region']}</b> går {procent(dyrast['Andel'])} av försäljningen till frakt, mot "
            f"{procent(billigast['Andel'])} i {billigast['Region']}." if len(frakt) > 1 else None)

    # --- Produktmix per region (Johans fråga 3) ---
    with hoger, kort("🧭", "Vad köps i olika delar av världen?"):
        fig, mix = staplad_andel(df, "Kategori", KATEGORI_FARG, varde="Total_Sales", hojd=300)
        visa(fig, "produktmix")
        forklaring(
            "Hur försäljningen i varje region fördelar sig på de fyra kategorierna. Varje rad blir 100 %.",
            "Jämför färgernas bredd mellan raderna. Bred blå del = mycket möbler.",
            f"Mest möbler köper <b>{mix['Möbler'].idxmax()}</b> ({procent(mix['Möbler'].max())}), "
            f"mest teknik <b>{mix['Teknik'].idxmax()}</b> ({procent(mix['Teknik'].max())})."
            if {"Möbler", "Teknik"} <= set(mix.columns) and len(mix) > 1 else None)


# ===========================================================================
# 13. FLIK: BETALNING
# ===========================================================================

def visa_betalning():
    # --- Hur betalar man? (Johans kort) ---
    with kort("💳", "Hur betalar kunderna?"):
        matt = st.segmented_control("Visa", ["Andel av ordrarna", "Vinstmarginal", "Snittordervärde"],
                                    default="Andel av ordrarna", key="betal_matt",
                                    label_visibility="collapsed") or "Andel av ordrarna"

        def per_betalsatt(data):
            if data is None:
                return None
            if matt == "Andel av ordrarna":
                return data["Betalsätt"].value_counts(normalize=True) * 100
            grupp = data.groupby("Betalsätt")
            if matt == "Vinstmarginal":
                return grupp["Profit"].sum() / grupp["Total_Sales"].sum() * 100
            return grupp["Total_Sales"].mean()

        format_ = pengar_exakt if matt == "Snittordervärde" else procent
        betal = per_betalsatt(df)
        fig = jamforelse_staplar(betal, per_betalsatt(jmf), format_, BETALSATT_FARG,
                                 som_procentenheter=matt != "Snittordervärde", hojd=300)
        visa(fig, "betalsatt")
        marginal = df.groupby("Betalsätt")["Profit"].sum() / df.groupby("Betalsätt")["Total_Sales"].sum() * 100
        andel = df["Betalsätt"].value_counts(normalize=True) * 100
        forklaring(
            {"Andel av ordrarna": "Hur stor del av ordrarna som betalas på varje sätt.",
             "Vinstmarginal": "Hur stor del av försäljningen som blir vinst för varje betalsätt.",
             "Snittordervärde": "Hur mycket en order är värd i genomsnitt för varje betalsätt."}[matt],
            "Längst stapel = störst. Byt mått med knapparna ovanför.",
            f"Vanligast är <b>{andel.idxmax().lower()}</b> ({procent(andel.max())} av ordrarna). Skillnaden i "
            f"marginal mellan betalsätten är bara {tal(marginal.max() - marginal.min(), 1)} procentenheter, "
            "så betalsättet påverkar nästan inte vinsten." if len(andel) > 1 else None)

    # --- Betalsätt per region (Johans fråga 4): ett cirkeldiagram per region ---
    with kort("🌐", "Betalsätt i olika delar av världen"):
        antal = pd.crosstab(df["Region"], df["Betalsätt"])          # antal ordrar per region och betalsätt
        mix = antal.div(antal.sum(axis=1), axis=0) * 100            # samma sak i procent (varje region = 100 %)
        regioner = [r for r in REGIONER.values() if r in antal.index]
        betalsatt = [b for b in BETALSATT.values() if b in antal.columns]
        fig = make_subplots(rows=1, cols=len(regioner), specs=[[{"type": "domain"}] * len(regioner)],
                            subplot_titles=regioner, horizontal_spacing=0.02)
        for nr, region in enumerate(regioner, start=1):
            fig.add_trace(go.Pie(
                labels=betalsatt, values=antal.loc[region, betalsatt], name=region, hole=0.5, sort=False,
                direction="clockwise", marker=dict(colors=[BETALSATT_FARG[b] for b in betalsatt],
                                                   line=dict(color="#0b0e14", width=2)),
                texttemplate="%{percent:.0%}", textfont=dict(color="#ffffff", size=12),
                hovertemplate=f"<b>{region}</b><br>" + "%{label}: %{percent:.1%} (%{value} ordrar)<extra></extra>"),
                row=1, col=nr)
        snygga_till(fig, 330)
        # Förklaringen av färgerna under cirklarna, så att den inte krockar med regionernas namn
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", y=-0.05, yanchor="top", x=0.5, xanchor="center"))
        fig.update_annotations(font=dict(color=TEXT, size=14))   # regionernas namn ovanför cirklarna
        visa(fig, "betalsatt_region")
        forklaring(
            "Hur ordrarna i varje region fördelar sig på de fyra betalsätten. Varje cirkel är en region och blir 100 %.",
            "Jämför hur stor del av cirklarna som har samma färg. Stor blå del = många betalar med kreditkort. "
            "Håll musen över en del för att se antalet ordrar.",
            f"Kreditkort är vanligast i <b>{mix['Kreditkort'].idxmax()}</b> ({procent(mix['Kreditkort'].max())}), "
            f"betala vid leverans i <b>{mix['Betala vid leverans'].idxmax()}</b> "
            f"({procent(mix['Betala vid leverans'].max())})."
            if {"Kreditkort", "Betala vid leverans"} <= set(mix.columns) and len(mix) > 1 else None)


# ===========================================================================
# 14. FLIK: RABATTER & FÖRLUSTORDRAR
# ===========================================================================

def visa_rabatter_forlust():
    rubrik("🏷️", "Rabatter", "Hur mycket rabatterna påverkar vinsten, och vem som får dem.")
    vanster, hoger = st.columns(2)

    # --- Vinstmarginal per rabattnivå (Wissams diagram) ---
    with vanster, kort("📉", "Vinstmarginal per rabattnivå"):
        per_rabatt = summera(df, "Discount_Percent").reset_index()
        per_rabatt["Rabatt"] = per_rabatt["Discount_Percent"].astype(int).astype(str) + " %"
        fig = go.Figure(go.Bar(
            x=per_rabatt["Rabatt"], y=per_rabatt["Marginal"], marker_color=MATT_FARG["Marginal"],
            marker_cornerradius=4, text=per_rabatt["Marginal"].map(procent), textposition="outside",
            cliponaxis=False, textfont=dict(color=TEXT, size=13), customdata=per_rabatt["Ordrar"],
            hovertemplate="%{x} rabatt: marginal %{text} (%{customdata} ordrar)<extra></extra>"))
        snygga_till(fig, 320)
        fig.update_xaxes(type="category", showgrid=False, title="Rabatt")
        fig.update_yaxes(range=[0, max(per_rabatt["Marginal"].max(), 1) * 1.2], ticksuffix=" %")
        visa(fig, "rabatt_marginal")
        forsta, sista = per_rabatt.iloc[0], per_rabatt.iloc[-1]
        forklaring(
            "Hur många procent av försäljningen som blir vinst, beroende på hur stor rabatt kunden fick.",
            "Lägre stapel = en mindre del av försäljningen blir vinst.",
            f"Vid {forsta['Rabatt']} rabatt är marginalen <b>{procent(forsta['Marginal'])}</b>, "
            f"vid {sista['Rabatt']} bara <b>{procent(sista['Marginal'])}</b>." if len(per_rabatt) > 1 else None)

    # --- Hur ofta ges varje rabatt, och till vem? ---
    with hoger, kort("👥", "Vem får rabatterna?"):
        antal = df.groupby(["Discount_Percent", "Kundgrupp"]).size().reset_index(name="Ordrar")
        antal["Rabatt"] = antal["Discount_Percent"].astype(int).astype(str) + " %"
        nivaer = [f"{int(r)} %" for r in sorted(df["Discount_Percent"].unique())]
        fig = px.bar(antal, x="Rabatt", y="Ordrar", color="Kundgrupp", color_discrete_map=KUNDGRUPP_FARG,
                     category_orders={"Rabatt": nivaer, "Kundgrupp": list(KUNDGRUPPER.values())})
        fig.update_traces(marker_cornerradius=3,
                          hovertemplate="%{x} rabatt · %{fullData.name}: %{y} ordrar<extra></extra>")
        snygga_till(fig, 320)
        fig.update_layout(barmode="stack")
        fig.update_xaxes(type="category", showgrid=False, title="Rabatt")
        visa(fig, "rabatt_kundgrupp")
        stor = (df["Discount_Percent"] > 10).groupby(df["Kundgrupp"]).mean() * 100
        forklaring(
            "Hur många ordrar som fått varje rabattnivå, uppdelat på kundgrupp.",
            "Hög stapel = vanlig rabatt. Färgerna visar vilka kunder som fått rabatten.",
            f"<b>{stor.idxmax()}</b> får oftast mer än 10 % rabatt ({procent(stor.max())} av deras ordrar), "
            f"mot {procent(stor.min())} för {stor.idxmin().lower()}." if len(stor) > 1 else None)

    # --- Förlustordrar (Alyoshs flik) ---
    rubrik("⚠️", "Förlustordrar",
           "En order går med förlust när det kostar mer att köpa in och skicka varan än kunden betalar.")
    forlust, lonsamma = df[df["Förlust"]], df[~df["Förlust"]]
    if forlust.empty:
        st.success("Inga ordrar i urvalet gick med förlust. 🎉")
        return

    # Hur stor del av ordervärdet som går till frakt (mittenvärdet, påverkas inte av extremvärden)
    frakt_andel = df["Shipping_Cost"] / df["Total_Sales"] * 100
    frakt_forlust, frakt_lonsam = frakt_andel[df["Förlust"]].median(), frakt_andel[~df["Förlust"]].median()

    # Texten under talen är bara en upplysning, inte en förändring: grå och utan pil.
    # height="stretch" gör att alla fyra korten blir lika höga.
    info = dict(delta_color="off", delta_arrow="off", height="stretch")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🧾 Förlustordrar", tal(len(forlust)), delta=f"{procent(len(forlust) / len(df) * 100)} av alla", **info)
    k2.metric("💸 Förlorat totalt", pengar(forlust["Profit"].sum()),
              delta=f"{pengar_exakt(forlust['Profit'].mean())} per förlustorder", **info,
              help="Summan av vinsten för alla förlustordrar (negativ = förlust).")
    k3.metric("🛍️ Snittorder", pengar(forlust["Total_Sales"].mean()),
              delta=f"lönsamma: {pengar(lonsamma['Total_Sales'].mean())}" if not lonsamma.empty else None, **info,
              help="Genomsnittligt ordervärde för förlustordrarna, jämfört med de lönsamma ordrarna.")
    k4.metric("🚚 Frakten tar", procent(frakt_forlust),
              delta=f"lönsamma: {procent(frakt_lonsam)}" if not lonsamma.empty else None, **info,
              help="Hur stor del av ordervärdet som går till frakt (mittenvärdet).")

    vanster, hoger = st.columns(2)
    with vanster, kort("💲", "Andel förlustordrar per ordervärde"):
        klass = pd.cut(df["Total_Sales"], VARDEGRANSER, labels=VARDEKLASSER)
        per_klass = (df["Förlust"].groupby(klass, observed=False).mean() * 100).fillna(0)
        fig = go.Figure(go.Bar(
            x=per_klass.index.astype(str), y=per_klass.values, marker_color=ROD, marker_cornerradius=4,
            text=[f"{v:.0f} %" for v in per_klass.values], textposition="outside", cliponaxis=False,
            textfont=dict(color=TEXT, size=13), hovertemplate="%{x}: %{text} går med förlust<extra></extra>"))
        snygga_till(fig, 320)
        fig.update_xaxes(type="category", showgrid=False)
        fig.update_yaxes(range=[0, max(per_klass.max() * 1.25, 10)], showticklabels=False, showgrid=False)
        visa(fig, "forlust_varde")
        sma = df["Total_Sales"] < 50
        andel_sma = (forlust["Total_Sales"] < 50).mean() * 100
        hur_manga = "Alla" if andel_sma == 100 else procent(andel_sma)   # "alla" låter bättre än "100,0 %"
        forklaring(
            "Hur stor andel av ordrarna som gick med förlust, uppdelat efter hur mycket ordern var värd.",
            "Hög röd stapel = många förlustordrar i den storleken.",
            f"<b>{hur_manga}</b> av förlustordrarna är värda under $50. "
            f"Frakten tar {procent(frakt_forlust)} av beloppet på en förlustorder, mot {procent(frakt_lonsam)} "
            "på en lönsam." if sma.any() and not lonsamma.empty else None)

    with hoger, kort("🛋️", "Andel förlustordrar per kategori"):
        per_kat = (df["Förlust"].groupby(df["Kategori"]).mean() * 100).sort_values()
        fig = go.Figure(go.Bar(
            y=per_kat.index, x=per_kat.values, orientation="h", marker_cornerradius=4,
            marker_color=[KATEGORI_FARG[k] for k in per_kat.index], text=[procent(v) for v in per_kat.values],
            textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
            hovertemplate="%{y}: %{text} av ordrarna går med förlust<extra></extra>"))
        snygga_till(fig, 320)
        fig.update_xaxes(range=[0, max(per_kat.max(), 1) * 1.3], showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False)
        visa(fig, "forlust_kategori")
        forklaring(
            "Hur stor andel av ordrarna i varje kategori som gick med förlust.",
            "Längre stapel = fler förlustordrar. Färgerna är samma som för kategorierna i resten av dashboarden.",
            f"<b>{per_kat.index[-1]}</b> drabbas mest ({procent(per_kat.iloc[-1])} av ordrarna). Där är varorna "
            "billiga, så frakten äter upp vinsten.")

    with st.expander("📋 Produkterna med flest förlustordrar"):
        topp = forlust.groupby(["Product_Name", "Kategori"]).agg(
            Förlustordrar=("Order_ID", "nunique"), Förlorat=("Profit", "sum")).sort_values(
            "Förlustordrar", ascending=False).head(10).reset_index()
        st.dataframe(topp.round(0), hide_index=True, width="stretch",
                     column_config={"Product_Name": "Produkt", "Förlorat": st.column_config.NumberColumn(format="$%d")})


# ===========================================================================
# 15. FLIK: TÄNK OM … – två prognoser (Johans rabatttak och Alyoshs fraktavgift)
# ===========================================================================

def visa_tank_om():
    st.markdown("Här kan du testa två idéer för att öka vinsten. Prognoserna räknar på **alla datum** "
                "(så mycket data som möjligt), men följer filtren för region, land, kundgrupp och kategori.")
    prognos = bara_landet(bas)
    nuvarande_vinst = prognos["Profit"].sum()
    nuvarande_marginal = nuvarande_vinst / prognos["Total_Sales"].sum() * 100

    # --- Idé 1: tak för rabatten ---
    with kort("🏷️", "Tänk om vi gav mindre rabatt?",
              "Välj vilka kunder som ska få ett tak för rabatten och dra i reglaget."):
        vanster, hoger = st.columns([1, 2])
        with vanster:
            tak_grupper = st.multiselect("Vilka kundgrupper?", list(KUNDGRUPPER.values()), default=["Företag"])
            tak = st.slider("Högsta tillåtna rabatt", min_value=0, max_value=30, value=10, step=5, format="%d %%")
        # Räkna om varje order: om kunden ingår och rabatten är högre än taket, sänk den till taket
        ny_rabatt = prognos["Discount_Percent"].where(~prognos["Kundgrupp"].isin(tak_grupper),
                                                      prognos["Discount_Percent"].clip(upper=tak))
        # Det vi slipper ge i rabatt (antal × pris × sänkt rabatt) blir extra försäljning och lika mycket extra vinst
        extra = (prognos["Quantity"] * prognos["Unit_Price"] * (prognos["Discount_Percent"] - ny_rabatt) / 100).sum()
        berorda = int((ny_rabatt < prognos["Discount_Percent"]).sum())
        ny_marginal = (nuvarande_vinst + extra) / (prognos["Total_Sales"].sum() + extra) * 100
        with hoger:
            a, b, c = st.columns(3)
            a.metric("📈 Vinst med rabatttak", pengar(nuvarande_vinst + extra), delta=f"+{pengar(extra)}",
                     delta_description="mot idag", height="stretch")
            b.metric("🎯 Ny vinstmarginal", procent(ny_marginal), delta=procentenheter(ny_marginal - nuvarande_marginal),
                     height="stretch")
            c.metric("🧾 Ordrar som påverkas", tal(berorda), delta=f"{procent(berorda / len(prognos) * 100)} av alla",
                     delta_color="off", delta_arrow="off", height="stretch",
                     help="Ordrar där rabatten var högre än taket")
        forklaring(
            "Hur mycket vinsten hade ökat om de valda kundgrupperna aldrig fått mer rabatt än taket.",
            "Dra i reglaget och välj kundgrupper. Siffrorna räknas om direkt.",
            f"Med max <b>{tak} % rabatt</b> för {', '.join(tak_grupper).lower() or 'ingen kundgrupp'} hade vinsten "
            f"blivit <b>{pengar(extra)} högre</b> ({tal(berorda)} ordrar påverkas). Förenkling: vi antar att kunderna "
            "hade köpt lika mycket även med lägre rabatt.")

    # --- Idé 2: små ordrar betalar sin egen frakt ---
    with kort("🚚", "Tänk om små ordrar fick betala sin egen frakt?",
              "Ordrar under gränsen betalar själva för frakten. Se direkt vad som händer med vinsten."):
        vanster, hoger = st.columns([1, 2])
        with vanster:
            grans = st.slider("Ordrar under det här beloppet betalar frakten", min_value=0, max_value=100,
                              value=50, step=5, format="$%d")
        berorda = prognos["Total_Sales"] < grans
        ny_vinst = prognos["Profit"] + prognos["Shipping_Cost"].where(berorda, 0)   # frakten blir ingen kostnad för oss
        extra = ny_vinst.sum() - nuvarande_vinst
        forlust_innan, forlust_efter = int((prognos["Profit"] < 0).sum()), int((ny_vinst < 0).sum())
        with hoger:
            a, b, c = st.columns(3)
            a.metric("📈 Ny vinst", pengar(ny_vinst.sum()), delta=f"+{pengar(extra)}", delta_description="mot idag",
                     height="stretch")
            b.metric("🧾 Förlustordrar kvar", tal(forlust_efter), delta=f"{tal(forlust_efter - forlust_innan)} st",
                     delta_color="inverse", height="stretch", help="Färre förlustordrar visas i grönt, eftersom det är bra.")
            c.metric("🛍️ Påverkas", tal(berorda.sum()), delta=f"{procent(berorda.mean() * 100)} av alla",
                     delta_color="off", delta_arrow="off", height="stretch",
                     help="Antal ordrar som är värda mindre än gränsen")
        forklaring(
            "Hur vinsten och antalet förlustordrar hade ändrats om små ordrar själva fick betala frakten.",
            "Dra i reglaget för att ändra gränsen. Siffrorna räknas om direkt.",
            f"Om ordrar under <b>${grans}</b> betalade sin egen frakt hade vinsten blivit <b>{pengar(extra)} högre</b>, "
            f"och förlustordrarna hade gått från {tal(forlust_innan)} till <b>{tal(forlust_efter)}</b>. "
            "Förenkling: vi antar att kunderna hade köpt lika mycket ändå.")


# ===========================================================================
# 16. FLIKARNA OCH TABELLEN LÄNGST NER
# ===========================================================================

st.write("")   # lite luft före flikarna
# key + on_change="rerun" gör att vald flik ligger kvar när man klickar i ett diagram
flikar = st.tabs(["📈 Försäljning & trender", "🛋️ Produkter & kategorier", "🌍 Geografi & kunder",
                  "💳 Betalning", "🏷️ Rabatter & förlust", "🧪 Tänk om …"], key="flik", bind="query-params")
for flik, visa_flik in zip(flikar, [visa_trender, visa_produkter, visa_geografi, visa_betalning,
                                    visa_rabatter_forlust, visa_tank_om]):
    with flik:
        visa_flik()

# Tabell med hela urvalet och en knapp för att ladda ner det (från Wissams dashboard)
st.write("")
with st.expander(f"📋 Visa urvalet som tabell ({tal(len(df))} ordrar)"):
    st.dataframe(df.drop(columns=["Landskod", "Datum"]), width="stretch", hide_index=True)
    st.download_button("⬇️ Ladda ner urvalet (CSV)", df.drop(columns=["Landskod", "Datum"]).to_csv(index=False).encode("utf-8"),
                       file_name="urval_e_handel.csv", mime="text/csv")
