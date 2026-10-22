"""PROTOTYP: interaktivt interface för delen Geografi, kunder och betalning.

Det här är en webbsida (byggd med Streamlit) som ger en snabb översikt på en enda sida:
  - välj period och jämför med en annan period (som i Google Ads)
  - nyckeltal: försäljning, vinst, marginal, ordrar och frakt per order
  - en världskarta – klicka på ett land så visar ALLA diagram bara det landet
  - försäljning, vinst eller ordrar över tid
  - fyra översiktskort: kundgrupper, vad som köps, hur man betalar och topplista över länder
  - "Tänk om ...": en prognos för vad som händer om vi ger mindre rabatt

Starta så här (från projektmappen):
    pip install -r requirements.txt
    streamlit run johan_geografi_kunder_betalning/geografi_kunder_betalning_prototyp_app.py

Då öppnas sidan automatiskt i webbläsaren. Det mörka färgtemat ligger i
.streamlit/config.toml i samma mapp och gäller bara den här appen.

Om valutan: datan säger inte vilken valuta det är. Eftersom det är en global
webbutik antar vi amerikanska dollar (USD), som är vanligast i internationell handel.
"""
from datetime import date, timedelta
from functools import partial   # skickar med extra värden till en funktion som körs vid klick

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
BLA, ORANGE, TURKOS, GUL, GRA = "#3987e5", "#d95926", "#199e70", "#c98500", "#898781"

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
MANADER_LANGA = ["januari", "februari", "mars", "april", "maj", "juni",
                 "juli", "augusti", "september", "oktober", "november", "december"]

# Koppla varje region, kundgrupp osv. till sin fasta färg
KUNDGRUPP_FARG = dict(zip(KUNDGRUPPER.values(), [BLA, ORANGE, TURKOS]))
BETALSATT_FARG = dict(zip(BETALSATT.values(), [BLA, ORANGE, TURKOS, GUL]))
KATEGORI_FARG = dict(zip(KATEGORIER.values(), [BLA, ORANGE, TURKOS, GUL]))


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


def procentenheter(varde):
    # Skillnaden mellan två procenttal: 33,1 % mot 30,4 % -> "+2,7 %-enh." (procentenheter)
    return f"{varde:+.1f} %-enh.".replace(".", ",", 1)


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
    return procent_andring((nu / forut - 1) * 100) if forut else None


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


def visa(fig, namn=None, vid_klick=None):
    # Visar ett diagram på sidan, utan Plotlys verktygsrad (enklare för användaren).
    # Med vid_klick går det att klicka i diagrammet: då körs den funktionen. Nyckeln får ett nytt
    # nummer efter varje klick, så att diagrammet glömmer det gamla klicket.
    klick = {}
    if vid_klick:
        nyckel = f"{namn}_{st.session_state['klick_nr']}"
        klick = dict(key=nyckel, on_select=partial(vid_klick, nyckel), selection_mode="points")
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False}, **klick)


def svarsruta(text):
    # En markerad ruta med svaret på en fråga, skrivet i klartext
    st.markdown(f'<div class="svar"><span class="svar-ikon">💡</span><div>{text}</div></div>',
                unsafe_allow_html=True)


def rubrik(ikon, titel, undertitel="", liten=False):
    # En snygg rubrik med ikon och en kort förklaring under. liten=True används inne i korten.
    stil = ' style="margin-top:4px;font-size:1.1rem"' if liten else ""
    st.markdown(f'<div class="avsnitt"{stil}><span class="avsnitt-ikon">{ikon}</span>{titel}</div>'
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


ALLA_LANDER = "Alla länder"   # första valet i land-filtret

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
                   "senaste_period", "senaste_jamfor", "filter_region", "filter_kundgrupp", "filter_land", "regioner_fore_land",
                   "tid_matt", "grupp_matt"]:
        st.session_state.pop(nyckel, None)


# --- Datumväljaren: EN knapp högst upp på sidan som öppnar en ruta, som i Google Ads och GA4 ---

LAND_TILL_REGION = dict(zip(alla["Land"], alla["Region"]))   # t.ex. "USA" -> "Nordamerika"


def valj_land(namn):
    # Väljer ett land (eller "Alla länder") och håller region-filtret i takt med det:
    # väljer man USA sätts regionen till Nordamerika, och går man tillbaka till alla länder
    # kommer de regioner man hade valt innan tillbaka.
    if namn == ALLA_LANDER:
        st.session_state["filter_region"] = st.session_state.pop("regioner_fore_land", list(REGIONER.values()))
    else:
        if "regioner_fore_land" not in st.session_state:   # spara regionerna bara första gången
            st.session_state["regioner_fore_land"] = st.session_state.get("filter_region", list(REGIONER.values()))
        st.session_state["filter_region"] = [LAND_TILL_REGION[namn]]
    st.session_state["filter_land"] = namn
    st.session_state["klick_nr"] = st.session_state.get("klick_nr", 0) + 1   # diagrammen glömmer gamla klick


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

    # Varna om en märkbar del (mer än 5 %) av jämförelsen ligger före datans början – då blir den
    # inte rättvis. En enstaka dag gör inget: datan börjar 2 jan 2023, så "förra året" saknar bara 1 jan.
    if jamfor_period and (FORSTA_DAG - jamfor_period[0]).days > 0.05 * ((jamfor_period[1] - jamfor_period[0]).days + 1):
        st.warning(f"Jämförelseperioden börjar före {datum_text(FORSTA_DAG)}, när datan saknas. "
                   "Jämförelsen blir därför missvisande – välj en kortare period.")

    # Startvärden för filtren. De sätts här (och inte i själva listorna) så att ett klick
    # på kartan eller i ett diagram kan ändra filtret – då hänger panelen och diagrammen ihop.
    st.session_state.setdefault("filter_region", list(REGIONER.values()))
    st.session_state.setdefault("filter_kundgrupp", list(KUNDGRUPPER.values()))

    st.markdown("### 🎛️ Filter")
    valda_regioner = st.multiselect("🌍 Region", list(REGIONER.values()), key="filter_region")

    # Land: bara länderna i de regioner man har valt (väljer man Nordamerika går bara Kanada, Mexiko
    # och USA att välja). Väljer man ett land sätts regionen till landets region (se valj_land).
    # Ändras också när man klickar på ett land på kartan eller i topplistan.
    land_alternativ = [ALLA_LANDER] + sorted(land for land, region in LAND_TILL_REGION.items()
                                             if region in valda_regioner)
    nu_land = st.session_state.get("filter_land")
    if nu_land not in land_alternativ or (nu_land != ALLA_LANDER and LAND_TILL_REGION[nu_land] not in valda_regioner):
        # t.ex. om man själv har valt bort landets region – då visas alla länder i regionerna man valt
        st.session_state["filter_land"] = ALLA_LANDER
        st.session_state.pop("regioner_fore_land", None)
    st.selectbox("📍 Land", land_alternativ, key="filter_land", on_change=lambda: valj_land(st.session_state["filter_land"]),
                 help="Visar länderna i de regioner du har valt. Välj ett land här, eller klicka på ett land "
                      "på kartan – de hänger ihop. Regionen ändras automatiskt till landets region.")

    valda_kundgrupper = st.multiselect(
        "👥 Kundgrupp", list(KUNDGRUPPER.values()), key="filter_kundgrupp",
        help="**Privatpersoner** = vanliga konsumenter. **Företag** = större företag. "
             "**Småföretag** = små företag och folk som driver firma hemifrån (heter \"Home Office\" i datan).")
    st.button("↺ Återställ allt", on_click=aterstall, width="stretch")

# Behåll bara de ordrar som matchar region och kundgrupp
bas = alla[alla["Region"].isin(valda_regioner) & alla["Kundgrupp"].isin(valda_kundgrupper)]


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
# 5. KLICK PÅ ETT LAND: filtrerar alla diagram på sidan
# ===========================================================================

KOD_TILL_LAND = {kod: namn for namn, kod in LANDER.values()}   # t.ex. "MEX" -> "Mexiko"
st.session_state.setdefault("klick_nr", 0)


def nar_land_klickas(nyckel):
    # Körs när man klickar på ett land på kartan (ger landskoden) eller i topplistan (ger namnet).
    # Klickar man på samma land igen tas filtret bort.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    varde = punkter[0].get("location") or punkter[0].get("y")
    namn = KOD_TILL_LAND.get(varde, varde)
    # Klicket ändrar land- och region-filtret i panelen till vänster, så att de alltid visar samma sak
    if namn in LAND_TILL_REGION:
        valj_land(ALLA_LANDER if st.session_state.get("filter_land") == namn else namn)


def nar_kundgrupp_klickas(nyckel):
    # Körs när man klickar på en stapel i kundgruppsdiagrammet: filtrerar hela sidan på den kundgruppen
    # (och ändrar kundgruppsfiltret i panelen). Klickar man på samma igen visas alla kundgrupper.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    grupp = punkter[0].get("y")
    alla_grupper = list(KUNDGRUPPER.values())
    if grupp in alla_grupper:
        st.session_state["filter_kundgrupp"] = alla_grupper if st.session_state.get("filter_kundgrupp") == [grupp] else [grupp]
    st.session_state["klick_nr"] += 1


valt_land = None if st.session_state["filter_land"] == ALLA_LANDER else st.session_state["filter_land"]


def bara_landet(data):
    # Om man har klickat på ett land: behåll bara det landets ordrar
    if data is None or valt_land is None:
        return data
    return data[data["Land"] == valt_land]


df = bara_landet(df_alla_lander)    # det som alla diagram (utom kartan och topplistan) visar
jmf = eller_inget(bara_landet(jmf_alla_lander))

with st.sidebar:
    if jamfor_period and jmf_alla_lander is None and not df_alla_lander.empty:
        st.warning("Det finns ingen data för jämförelseperioden. Välj en annan period.")
    st.divider()
    st.download_button("⬇️ Ladda ner urvalet (CSV)",
                       df.drop(columns=["Landskod", "Datum"]).to_csv(index=False).encode("utf-8"),
                       file_name="urval_geografi_kunder_betalning.csv", width="stretch")

# Om filtren inte ger några ordrar alls: visa ett meddelande och stoppa här
if df.empty:
    if valt_land:
        st.warning(f"{valt_land} har inga ordrar som matchar dina val. Välj en längre period eller ett annat land.")
        st.button("✕ Visa alla länder", on_click=valj_land, args=(ALLA_LANDER,), key="alla_lander_tom")
    else:
        st.warning("Inga ordrar matchar dina val. Välj minst en region och en kundgrupp, eller en längre period.")
    st.stop()


# ===========================================================================
# 6. RUBRIKRUTAN
# ===========================================================================

# Små "etiketter" under rubriken som visar vad man har valt just nu
def filter_text(valda, alla_namn, ord_):
    # "Alla kundgrupper", "Företag, Småföretag" eller "3 av 5 regioner"
    if len(valda) == len(alla_namn):
        return f"Alla {ord_}"
    return ", ".join(valda) if len(valda) <= 2 else f"{len(valda)} av {len(alla_namn)} {ord_}"


chips = [f"🔵 {period_text(period)}"]
if jmf is not None:
    chips.append(f"⚪ Jämförs med {period_text(jamfor_period)}")
chips += [f"📍 {valt_land}" if valt_land else "🌍 Alla länder",
          f"🗺️ {filter_text(valda_regioner, REGIONER, 'regioner')}",
          f"👥 {filter_text(valda_kundgrupper, KUNDGRUPPER, 'kundgrupper')}",
          "💵 Belopp i USD"]
chips_html = "".join(f'<span class="chip">{text}</span>' for text in chips)

st.markdown(
    '<div class="hero"><span class="etikett">PROTOTYP</span>'
    '<h1>🌍 Geografi, kunder &amp; betalning</h1>'
    '<p>Utforska var vi säljer, vem som köper och hur kunderna betalar. Välj datum och filter i panelen '
    'till vänster, och <b>klicka på ett land på kartan</b> för att se bara det landet.</p>'
    f'<div class="chips">{chips_html}</div></div>',
    unsafe_allow_html=True,
)

# När ett land är valt: visa det tydligt, med en knapp för att gå tillbaka till alla länder
if valt_land:
    text_kolumn, knapp_kolumn = st.columns([4, 1], vertical_alignment="center")
    region = df["Region"].iloc[0]
    text_kolumn.markdown(f'<div class="avsnitt" style="margin-top:0">📍 {valt_land} '
                         f'<span class="avsnitt-under">· {region} · alla diagram visar bara det här landet</span></div>',
                         unsafe_allow_html=True)
    knapp_kolumn.button("✕ Visa alla länder", on_click=valj_land, args=(ALLA_LANDER,), width="stretch",
                        key="alla_lander_topp")


# ===========================================================================
# 7. NYCKELTAL MED SMÅ TRENDDIAGRAM
# ===========================================================================

def nyckeltal(data):
    # De viktigaste siffrorna för en period
    if data is None:
        return None
    forsaljning, vinst = data["Total_Sales"].sum(), data["Profit"].sum()
    return {"Försäljning": forsaljning, "Vinst": vinst, "Marginal": vinst / forsaljning * 100,
            "Ordrar": len(data), "Frakt": data["Shipping_Cost"].mean()}


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
        Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"), Ordrar=("Order_ID", "count"),
        Frakt=("Shipping_Cost", "mean"))
    # Dagar/veckor utan ordrar: 0 i försäljning, vinst och ordrar. Frakt per order och marginal
    # lämnas tomma, annars ser det ut som att frakten var gratis och marginalen 0 just den dagen.
    serie = serie.reindex(steg)
    summor = ["Försäljning", "Vinst", "Ordrar"]
    serie[summor] = serie[summor].fillna(0)
    serie["Marginal"] = serie["Vinst"] / serie["Försäljning"].where(serie["Försäljning"] > 0) * 100
    return serie


serie_nu = tidsserie(df)
FLYTT = (start - jamfor_period[0]) if jmf is not None else timedelta(0)
serie_jmf = tidsserie(jmf, FLYTT) if jmf is not None else None

def trend(kol):
    # Värdena till det lilla trenddiagrammet i ett kort (dagar utan ordrar hoppas över)
    varden = serie_nu[kol].dropna().round(1).tolist()
    return varden if len(varden) > 1 else None


# Ett kort per nyckeltal: (rubrik, nyckeltal, hur talet skrivs, typ av litet diagram, förklaring)
NYCKELTAL = [
    ("💰 Försäljning", "Försäljning", pengar, "area", ""),
    ("📈 Vinst", "Vinst", pengar, "area", ""),
    ("🎯 Vinstmarginal", "Marginal", procent, "line",
     "Hur stor del av försäljningen som blir vinst. Pilen visar skillnaden i procentenheter."),
    ("📦 Ordrar", "Ordrar", tal, "bar", ""),
    ("🚚 Frakt per order", "Frakt", pengar_exakt, "line", "Vad det kostar i genomsnitt att skicka en order till kunden."),
]
for kolumn, (etikett, namn, format_, diagram, forklaring) in zip(st.columns(5), NYCKELTAL):
    if forut is None:
        delta = None
    elif namn == "Marginal":
        delta = procentenheter(nu[namn] - forut[namn])   # för marginalen visas skillnaden i procentenheter
    else:
        delta = forandring(nu[namn], forut[namn])
    # Hjälptexten (ⓘ): förklaring + siffran för jämförelseperioden. Korten är för smala för att
    # visa jämförelsesiffran bredvid pilen, därför ligger den här.
    hjalp = [forklaring] if forklaring else []
    if forut:
        hjalp.append(f"⚪ Jämförelseperioden: **{format_(forut[namn])}**")
    kolumn.metric(etikett, format_(nu[namn]), delta=delta, help="  \n".join(hjalp) or None,
                  delta_color="inverse" if namn == "Frakt" else "normal",   # lägre frakt är bättre: minskning = grön
                  chart_data=trend(namn), chart_type=diagram)
if forut:
    st.caption(f"🔵 {period_text(period)} jämfört med ⚪ {period_text(jamfor_period)}. "
               "Pilen visar förändringen. Håll musen över ⓘ för att se siffran för jämförelseperioden. "
               f"De små diagrammen visar utvecklingen per {STEG}.")
else:
    st.caption(f"De små diagrammen i korten visar utvecklingen per {STEG}. "
               "Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster för att se hur det har förändrats.")


# ===========================================================================
# 8. VÄRLDSKARTAN – klicka på ett land för att filtrera hela sidan
# ===========================================================================

rubrik("🗺️", "Världskarta",
       "Håll musen över ett land för att se siffrorna. <b>Klicka på ett land</b> så visar alla diagram bara det landet – "
       "klicka igen för att se alla länder.")

alternativ = ["Försäljning", "Vinst", "Marginal (%)", "Ordrar"]
if jmf_alla_lander is not None:
    alternativ.append("Förändring (%)")   # bara när man jämför: hur mycket varje land ökat/minskat
matt = st.segmented_control("Vad ska kartan visa?", alternativ, default="Försäljning",
                            label_visibility="collapsed")
matt = matt if matt in alternativ else "Försäljning"   # om man klickar bort valet, visa försäljning

# Kartan visar alltid alla länder i urvalet, även när ett land är valt
per_land = df_alla_lander.groupby(["Land", "Landskod", "Region"], as_index=False).agg(
    Ordrar=("Order_ID", "count"),
    Försäljning=("Total_Sales", "sum"),
    Vinst=("Profit", "sum"),
)
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
    # alla andra länder grå. Därför slutar färgskalan vid ±100 % (det exakta talet syns när man
    # håller musen över landet).
    tak = min(100, max(10, per_land["Förändring (%)"].abs().quantile(0.9)))
    farger = dict(color_continuous_scale=[[0, "#e66767"], [0.5, "#383835"], [1, BLA]],
                  range_color=[-tak, tak])
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
snygga_till(karta, hojd=500)
karta.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar=dict(
    title=dict(text=matt, font=dict(color=TEXT_SVAG)), thickness=10, len=0.6, outlinewidth=0,
    tickformat=",.0f", tickprefix="$" if matt in ("Försäljning", "Vinst") else "",
    ticksuffix=" %" if "%" in matt else "", tickfont=dict(color=TEXT_SVAG)))

visa(karta, "karta", nar_land_klickas)   # ett klick på ett land filtrerar hela sidan


# ===========================================================================
# 9. TIDSDIAGRAM: utvecklingen i den valda perioden, med jämförelsen ovanpå
# ===========================================================================

rubrik("📈", "Utveckling över tid",
       f"Varje punkt är en {STEG} i perioden du valt."
       + (" Den streckade grå linjen är jämförelseperioden, lagd ovanpå så att första dagen jämförs med första dagen."
          if serie_jmf is not None else " Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster för att se en jämförelse här."))

tid_matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Ordrar"], default="Försäljning",
                                key="tid_matt", label_visibility="collapsed") or "Försäljning"
prefix = "" if tid_matt == "Ordrar" else "$"   # ordrar är antal, inte pengar

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
# 10. ÖVERSIKT: fyra kort som fungerar både för alla länder och för ett valt land
# ===========================================================================

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
        bredd = tabell["Nu"].max() * 1.22   # plats till höger så att talen vid staplarna inte klipps av
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
    fig.update_xaxes(range=[0, bredd], showgrid=False, showticklabels=False, title=None)
    fig.update_yaxes(showgrid=False, title=None)
    return fig


plats = f"i {valt_land}" if valt_land else "i urvalet"
rubrik("🔎", f"Översikt {plats}", "Fyra snabba svar: vem köper, vad köps, hur man betalar och var vi säljer mest.")

vanster, hoger = st.columns(2)

# --- Kort 1: Kundgrupper (fråga 1: varför tjänar vi minst på företagskunder?) ---
with vanster.container(border=True):
    rubrik("👥", "Kundgrupper", "Vem köper – och vem får stora rabatter? Klicka på en kundgrupp för att filtrera.",
           liten=True)
    grupp_matt = st.segmented_control("Visa", ["Försäljning", "Vinstmarginal", "Stor rabatt"],
                                      default="Försäljning", key="grupp_matt",
                                      label_visibility="collapsed") or "Försäljning"

    def per_kundgrupp(data, vad):
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
    fig = jamforelse_staplar(per_kundgrupp(df, grupp_matt), per_kundgrupp(jmf, grupp_matt), format_,
                             KUNDGRUPP_FARG, som_procentenheter=grupp_matt != "Försäljning")
    # Klick på en kundgrupp filtrerar hela sidan och ändrar kundgruppsfiltret i panelen
    visa(fig, "kundgrupper", nar_kundgrupp_klickas)
    rabatt = per_kundgrupp(df, "Stor rabatt").sort_values()
    marginal = per_kundgrupp(df, "Vinstmarginal")
    if len(rabatt) > 1:
        st.markdown(f"💡 **{rabatt.index[-1]}** får oftast stor rabatt ({procent(rabatt.iloc[-1])} av ordrarna) "
                    f"och har en vinstmarginal på {procent(marginal[rabatt.index[-1]])}. Mer rabatt = mindre vinst.")

# --- Kort 2: Vad köps? (fråga 3) ---
with hoger.container(border=True):
    rubrik("🛋️", "Vad köps?", "Hur stor del av försäljningen varje kategori står för.", liten=True)
    andel_kategori = lambda data: (None if data is None else
                                   data.groupby("Kategori")["Total_Sales"].sum() / data["Total_Sales"].sum() * 100)
    kategorier = andel_kategori(df)
    visa(jamforelse_staplar(kategorier, andel_kategori(jmf), procent, KATEGORI_FARG, som_procentenheter=True))
    st.markdown(f"💡 Mest säljs **{kategorier.idxmax().lower()}** ({procent(kategorier.max())} av försäljningen), "
                f"minst **{kategorier.idxmin().lower()}** ({procent(kategorier.min())}).")

vanster, hoger = st.columns(2)

# --- Kort 3: Hur betalar man? (fråga 4) ---
with vanster.container(border=True):
    rubrik("💳", "Hur betalar man?", "Hur stor del av ordrarna som betalas på varje sätt.", liten=True)
    andel_betalsatt = lambda data: None if data is None else data["Betalsätt"].value_counts(normalize=True) * 100
    betalsatt = andel_betalsatt(df)
    visa(jamforelse_staplar(betalsatt, andel_betalsatt(jmf), procent, BETALSATT_FARG, som_procentenheter=True))
    st.markdown(f"💡 Vanligast är **{betalsatt.idxmax().lower()}** ({procent(betalsatt.max())} av ordrarna).")

# --- Kort 4: Länder – topplista (var säljer vi mest?) ---
with hoger.container(border=True):
    rubrik("🏆", "Länder med mest försäljning",
           "Klicka på ett land här eller på kartan för att filtrera hela sidan.", liten=True)
    topp = per_land.sort_values("Försäljning", ascending=False).reset_index(drop=True)
    topp["Plats"] = topp.index + 1
    visas = topp.head(8)
    if valt_land and valt_land not in set(visas["Land"]):
        visas = pd.concat([visas, topp[topp["Land"] == valt_land]])   # visa alltid det valda landet
    visas = visas.iloc[::-1]   # störst överst
    # Det valda landet lyser blått, övriga är dämpade. Utan valt land är alla blå.
    farg = [BLA if (valt_land is None or land == valt_land) else "#2b3f5c" for land in visas["Land"]]
    fig = go.Figure(go.Bar(
        y=visas["Land"], x=visas["Försäljning"], orientation="h", marker_color=farg,
        marker_cornerradius=4, text=visas["Försäljning"].map(pengar), textposition="outside",
        cliponaxis=False, textfont=dict(color=TEXT, size=13),
        customdata=visas[["Plats", "Region", "Marginal (%)"]].values,
        hovertemplate="<b>%{y}</b> · nr %{customdata[0]} · %{customdata[1]}<br>"
                      "Försäljning: %{text}<br>Marginal: %{customdata[2]:.1f} %<br>"
                      "<i>Klicka för att filtrera</i><extra></extra>"))
    snygga_till(fig, 300)
    fig.update_xaxes(range=[0, visas["Försäljning"].max() * 1.3], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False)
    visa(fig, "topplista", nar_land_klickas)
    if valt_land:
        plats_nr = int(topp.loc[topp["Land"] == valt_land, "Plats"].iloc[0])
        st.markdown(f"💡 **{valt_land}** är nummer **{plats_nr}** av {len(topp)} länder i försäljning.")
    else:
        st.markdown(f"💡 Störst är **{topp['Land'].iloc[0]}** med {pengar(topp['Försäljning'].iloc[0])}.")


# ===========================================================================
# 11. TÄNK OM … – en prognos för vad som händer om vi ger mindre rabatt
# ===========================================================================

st.write("")
with st.expander("🧪 Tänk om vi gav mindre rabatt? – öppna för att testa en prognos"):
    st.markdown("Välj vilka kunder som ska få ett tak för rabatten och dra i reglaget. "
                "Det här är en prognos, så den räknar på **alla datum** – men följer filtren för region, "
                "kundgrupp och valt land.")

    # En prognos ska bygga på så mycket data som möjligt, så vi använder alla datum ("bas")
    # i stället för bara den valda perioden
    prognos = bara_landet(bas)
    prognos_marginal = prognos["Profit"].sum() / prognos["Total_Sales"].sum() * 100

    vanster, hoger = st.columns([1, 2])
    with vanster:
        tak_grupper = st.multiselect("Vilka kundgrupper?", list(KUNDGRUPPER.values()), default=["Företag"])
        tak = st.slider("Högsta tillåtna rabatt", min_value=0, max_value=30, value=10, step=5, format="%d %%")

    # Räkna om varje order: om kunden ingår och rabatten är högre än taket, sänk den till taket
    ny_rabatt = prognos["Discount_Percent"].where(~prognos["Kundgrupp"].isin(tak_grupper),
                                                  prognos["Discount_Percent"].clip(upper=tak))
    # Det vi slipper ge i rabatt (antal × pris × sänkt rabatt) blir extra försäljning och lika mycket extra vinst
    extra = prognos["Quantity"] * prognos["Unit_Price"] * (prognos["Discount_Percent"] - ny_rabatt) / 100
    ny_forsaljning = prognos["Total_Sales"] + extra
    ny_vinst = prognos["Profit"] + extra
    berorda = int((ny_rabatt < prognos["Discount_Percent"]).sum())
    ny_marginal = ny_vinst.sum() / ny_forsaljning.sum() * 100

    with hoger:
        a, b, c = st.columns(3)
        a.metric("📈 Vinst med rabatttak", pengar(ny_vinst.sum()), delta=f"+{pengar(extra.sum())}",
                 delta_description="mot idag")
        b.metric("🎯 Ny vinstmarginal", procent(ny_marginal),
                 delta=procentenheter(ny_marginal - prognos_marginal))
        c.metric("🧾 Ordrar som påverkas", tal(berorda), help="Ordrar där rabatten var högre än taket")

    svarsruta(f"Med max <b>{tak} % rabatt</b> för {', '.join(tak_grupper).lower() or 'ingen kundgrupp'} "
              f"hade vinsten blivit <b>{pengar(extra.sum())} högre</b> ({berorda} ordrar påverkas).")
    st.caption("⚠️ Förenkling: vi antar att kunderna hade köpt exakt lika mycket även med lägre rabatt. "
               "I verkligheten kan en del kunder välja att inte köpa.")
