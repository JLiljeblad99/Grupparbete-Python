"""PROTOTYP: interaktivt interface för delarna Försäljning & trender samt Produkter & kategorier.

Det här är en webbsida (byggd med Streamlit) där man kan utforska datan själv:
  - se de viktigaste siffrorna direkt högst upp, jämfört med året innan
  - se försäljning, vinst och marginal över tid
  - klicka på en kategori och en produkt för att se mer
  - förstå varför vissa ordrar går med förlust, och testa "Tänk om ..."

Starta så här (från projektmappen):
    python -m streamlit run alya_forsaljning_produkter/app.py

Då öppnas sidan i webbläsaren. Stäng med Ctrl+C i terminalen.
Stilen (mörkt tema, färger, rubrikruta, kort och svarsrutor) är samma som i Johans del,
så att delarna passar ihop när vi slår ihop dem.

Om valutan: datan säger inte vilken valuta det är. Precis som i Johans del antar vi
amerikanska dollar (USD).
"""
from pathlib import Path   # hjälper oss att bygga sökvägar till filer

import pandas as pd             # läser och räknar på datan
import plotly.express as px     # gör interaktiva diagram (hovra, klicka)
import streamlit as st          # bygger webbsidan

# Här ligger datan: Grupparbete-Python/archive/global_ecommerce_sales.csv
# __file__ = den här filen. .parent = mappen den ligger i. .parent igen = ett steg upp.
CSV_FIL = Path(__file__).parent.parent / "archive" / "global_ecommerce_sales.csv"


# ===========================================================================
# 1. INSTÄLLNINGAR: färger och svenska namn (samma som i Johans del)
# ===========================================================================

# Fasta färger. Samma sak har alltid samma färg i alla diagram.
# Färgerna är anpassade för mörk bakgrund och går att skilja åt även för färgblinda.
BLA, ORANGE, TURKOS, GUL = "#3987e5", "#d95926", "#199e70", "#c98500"
GRA = "#898781"
ROD = "#d03b3b"   # används bara för förlust, så att rött alltid betyder "dåligt"

# Diagrammens "ram": textfärg, svagare text, rutnät, axlar och bakgrund till hjälprutor
TEXT, TEXT_SVAG, RUTNAT, AXEL, KORT = "#e8eaf0", "#a3a8b4", "#232a36", "#2f3746", "#151a23"

# Datan är på engelska. Här översätter vi kategorierna till svenska (samma namn som Johan använder).
KATEGORIER = {
    "Furniture": "Möbler",
    "Technology": "Teknik",
    "Clothing & Accessories": "Kläder",
    "Office Supplies": "Kontorsmaterial",
}
# zip parar ihop två listor: (Möbler, BLA), (Teknik, ORANGE) ... och dict gör en ordbok av paren.
KATEGORI_FARG = dict(zip(KATEGORIER.values(), [BLA, ORANGE, TURKOS, GUL]))

# Färg för varje mått i linjediagrammen
MATT_FARG = {"Försäljning": BLA, "Vinst": ORANGE, "Marginal (%)": TURKOS}

# Koder som pandas använder för tidsperioder: "M" = månad, "Q" = kvartal, "Y" = år
PERIODKODER = {"Månad": "M", "Kvartal": "Q", "År": "Y"}

# Hur datumet skrivs i hover-rutan: "2025-06", "2025 kv 2" eller "2025"
HOVERFORMAT = {"Månad": "%Y-%m", "Kvartal": "%Y kv %q", "År": "%Y"}

MANADER = ["januari", "februari", "mars", "april", "maj", "juni",
           "juli", "augusti", "september", "oktober", "november", "december"]

# Gränserna för ordervärde som vi delar in ordrarna efter i fliken om förlustordrar.
# float("inf") = oändligt, alltså "allt över 250".
VARDEGRANSER = [0, 25, 50, 100, 250, float("inf")]
VARDEKLASSER = ["Under $25", "$25–50", "$50–100", "$100–250", "Över $250"]


# ===========================================================================
# 2. HJÄLPFUNKTIONER
# ===========================================================================

@st.cache_data   # sparar datan i minnet, så att sidan inte läser filen på nytt vid varje klick
def hamta_data():
    df = pd.read_csv(CSV_FIL)
    # Gör om datum-texten till riktiga datum. errors="coerce" = ogiltiga datum blir "saknas" i stället för en krasch.
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    # Ta bort trasiga rader där datum, försäljning eller vinst saknas
    df = df.dropna(subset=["Order_Date", "Total_Sales", "Profit"])
    # Svenska kategorinamn i en egen kolumn
    df["Kategori"] = df["Product_Category"].map(KATEGORIER)
    return df


def summera(df, gruppera_pa):
    """Räknar ut försäljning, vinst, ordrar, antal och marginal för varje grupp."""
    # groupby = dela upp tabellen i grupper. gruppera_pa kan vara ett kolumnnamn ("Kategori")
    # eller en egen uträknad kolumn (t.ex. året för varje order).
    tabell = df.groupby(gruppera_pa).agg(
        Försäljning=("Total_Sales", "sum"),   # summan av försäljningen
        Vinst=("Profit", "sum"),              # summan av vinsten
        Ordrar=("Order_ID", "nunique"),       # antal unika ordrar
        Antal=("Quantity", "sum"),            # antal sålda enheter
    )
    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    return tabell


def over_tid(df, tidsupplosning):
    """Summerar per månad, kvartal eller år."""
    # to_period gör om varje datum till sin period (2025-06-14 -> 2025 Q2),
    # to_timestamp gör om perioden till ett datum igen (första dagen) -> snygg tidsaxel.
    period = df["Order_Date"].dt.to_period(PERIODKODER[tidsupplosning]).dt.to_timestamp()
    return summera(df, period)


def per_ar(df):
    """Summerar per år (2023, 2024, 2025)."""
    return summera(df, df["Order_Date"].dt.year)


# --- Formatering av tal. " " är ett hårt mellanslag: det bryts aldrig, så "15 105"
# --- eller "17,1 %" hamnar aldrig på två rader.

def tal(varde, decimaler=0):
    # Svenskt sätt: 484559.3 -> "484 559"
    return f"{varde:,.{decimaler}f}".replace(",", " ").replace(".", ",")


def pengar(varde):
    # Belopp i dollar: 137006.2 -> "$137 006". Minustecknet hamnar före $: -953 -> "-$953".
    return f"-${tal(-varde)}" if varde < 0 else f"${tal(varde)}"


def procent(varde):
    # Procent med en decimal: 33.84 -> "33,8 %"
    return f"{tal(varde, 1)} %"


def procent_andring(varde):
    # Som procent(), men alltid med + eller − framför: 6.33 -> "+6,3 %"
    return ("+" if varde >= 0 else "") + procent(varde)


def forandring(nu, forut):
    # Hur mycket något har ändrats i procent, t.ex. "+6,3 %". None (inget) om det inte går att räkna.
    if forut is None or forut == 0:
        return None
    return procent_andring((nu / forut - 1) * 100)


def manadsnamn(datum):
    # 2025-06-01 -> "juni 2025". datum.month är 1–12, listan börjar på 0, därför -1.
    return f"{MANADER[datum.month - 1]} {datum.year}"


def periodnamn(datum, tidsupplosning):
    # Ett datum som text beroende på vald period: "juni 2025", "kvartal 2 2025" eller "2025"
    if tidsupplosning == "Månad":
        return manadsnamn(datum)
    if tidsupplosning == "Kvartal":
        return f"kvartal {(datum.month - 1) // 3 + 1} {datum.year}"   # // = heltalsdivision
    return str(datum.year)


# --- Diagram och rutor (samma utseende som i Johans del) ---

def snygga_till(fig, hojd=380, pengar_x=False, pengar_y=False):
    """Samma utseende på alla diagram: mörk stil, diskret rutnät, svenska tal."""
    fig.update_layout(
        height=hojd,
        margin=dict(l=10, r=10, t=40, b=10),
        separators=", ",                    # decimalkomma och mellanslag mellan tusental
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=TEXT_SVAG, size=13),
        title=dict(x=0, xanchor="left", font=dict(color=TEXT, size=15)),   # rubriken till vänster
        # förklaringen (vilken färg är vad) uppe till höger, så att den inte krockar med rubriken
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


def liggande_staplar(fig, tabell, kolumn):
    """För liggande staplar: talen står vid staplarna, så axeln och rutnätet behövs inte."""
    # textposition="outside" = talet till höger om stapeln. cliponaxis=False = talet får sticka ut.
    fig.update_traces(textposition="outside", cliponaxis=False, showlegend=False,
                      textfont=dict(color=TEXT, size=13), marker_cornerradius=4)
    # Gör x-axeln 25 % längre än största stapeln, så att talet till höger får plats
    fig.update_xaxes(range=[0, tabell[kolumn].max() * 1.25], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return fig


def visa(fig, **extra):
    """Visar ett diagram utan Plotlys verktygsrad. **extra = ev. fler inställningar, t.ex. för klick."""
    # theme=None = använd våra egna färger i stället för Streamlits standardfärger
    return st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False}, **extra)


def visa_tabell(tabell):
    """En hopfällbar ruta där man kan se siffrorna bakom diagrammet."""
    with st.expander("📋 Visa siffrorna i en tabell"):
        st.dataframe(tabell.round(1), width="stretch")


def svarsruta(text):
    """En markerad ruta med en slutsats i klartext. <b>text</b> = fetstil."""
    # unsafe_allow_html=True låter oss använda egen HTML, så att rutan kan få sin egen stil (se CSS nedan)
    st.markdown(f'<div class="svar"><span class="svar-ikon">💡</span><div>{text}</div></div>',
                unsafe_allow_html=True)


def rubrik(ikon, titel, undertitel=""):
    """En avsnittsrubrik med ikon och en kort förklaring under."""
    st.markdown(f'<div class="avsnitt"><span class="avsnitt-ikon">{ikon}</span>{titel}</div>'
                + (f'<div class="avsnitt-under">{undertitel}</div>' if undertitel else ""),
                unsafe_allow_html=True)


def punktkort(ikon, titel, punkter):
    """Ett litet kort med en rubrik och en punktlista (används i snabböversikten)."""
    # "".join(...) sätter ihop alla <li>-rader (listpunkter) till en enda text
    lista = "".join(f"<li>{punkt}</li>" for punkt in punkter)
    st.markdown(f'<div class="punkt"><div class="punkt-titel">{ikon} {titel}</div><ul>{lista}</ul></div>',
                unsafe_allow_html=True)


def linjediagram(tabell, kolumner, tidsupplosning, prefix="$"):
    """Linjediagram över tid. Första måttet (t.ex. Försäljning) får en fylld yta under linjen."""
    fig = px.line(tabell, y=kolumner, markers=True, color_discrete_map=MATT_FARG)
    # Tjockare linjer och tydliga punkter. %{fullData.name} = linjens namn, %{y:,.0f} = värdet.
    fig.update_traces(line=dict(width=3), marker=dict(size=7),
                      hovertemplate="%{fullData.name}: " + prefix + "%{y:,.0f}<extra></extra>")
    # Fylld yta under den första linjen, som i Johans tidsdiagram
    fig.data[0].update(fill="tozeroy", fillcolor="rgba(57,135,229,0.12)")
    snygga_till(fig, pengar_y=prefix == "$")
    fig.update_layout(hovermode="x unified")   # en ruta med alla linjers värden för en tidpunkt
    # Tidsaxeln: en markering per år som bara visar årtalet. Hover-rutan visar perioden.
    # range = lite luft före första och efter sista punkten (45 dagar), så att årtalet längst
    # till vänster inte krockar med talen på y-axeln.
    luft = pd.Timedelta(days=45)
    fig.update_xaxes(showgrid=False, dtick="M12", tickformat="%Y", hoverformat=HOVERFORMAT[tidsupplosning],
                     range=[tabell.index.min() - luft, tabell.index.max() + luft])
    fig.update_yaxes(rangemode="tozero")   # axeln börjar på 0, så att svängningarna inte överdrivs
    return fig


# ===========================================================================
# 3. SIDANS UTSEENDE (CSS = instruktioner för hur sidan ska se ut) – samma klasser som Johan
# ===========================================================================

CSS = f"""
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
        radial-gradient(circle at 85% 30%, rgba(25,158,112,0.35), transparent 45%),
        radial-gradient(circle at 60% 110%, rgba(217,89,38,0.30), transparent 50%),
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

/* Korten i snabböversikten (samma stil som nyckeltalskorten) */
.punkt {{
    background: linear-gradient(180deg, #161c27 0%, #11161f 100%); border: 1px solid {AXEL};
    border-radius: 16px; padding: 14px 18px; height: 100%; color: {TEXT};
}}
.punkt-titel {{ font-weight: 700; margin-bottom: 6px; }}
.punkt ul {{ margin: 0; padding-left: 1.1rem; color: {TEXT_SVAG}; }}
.punkt li {{ margin: 4px 0; }}
.punkt b {{ color: {TEXT}; }}

/* Flikarna lite större och tydligare */
button[role="tab"] p, div[role="tab"] p {{ font-size: 0.98rem; }}
</style>
"""


# ===========================================================================
# 4. SIDANS DELAR – varje funktion ritar en del av sidan.
#    De tar emot den filtrerade datan, så att gruppens gemensamma app kan anropa dem.
# ===========================================================================

def visa_hero(valda_ar, valda_kategorier, tidsupplosning):
    """Rubrikrutan högst upp, med små "chips" som visar vad man har valt just nu."""
    # min() och max() ger första och sista valda år, t.ex. "2023–2025"
    ar_text = str(min(valda_ar)) if len(valda_ar) == 1 else f"{min(valda_ar)}–{max(valda_ar)}"
    chips = [f"📅 {ar_text}",
             f"🛒 {len(valda_kategorier)} av {len(KATEGORIER)} kategorier",
             f"📊 Diagram per {tidsupplosning.lower()}",
             "💵 Belopp i USD"]
    chips_html = "".join(f'<span class="chip">{text}</span>' for text in chips)
    st.markdown(
        '<div class="hero"><span class="etikett">PROTOTYP</span>'
        '<h1>📈 Försäljning, trender &amp; produkter</h1>'
        '<p>Hur går försäljningen, och vilka produkter drar in mest? '
        'Välj år och kategorier i panelen till vänster – allt uppdateras direkt.</p>'
        f'<div class="chips">{chips_html}</div></div>',
        unsafe_allow_html=True,
    )


def visa_nyckeltal(df, tidsupplosning):
    """Fyra nyckeltalskort med jämförelse mot året innan och ett litet trenddiagram."""
    ar = per_ar(df)
    serie = over_tid(df, tidsupplosning)

    # Jämförelse: senaste året mot året innan. Går bara om minst två år är valda.
    # .iloc[-1] = sista raden (senaste året), .iloc[-2] = näst sista.
    nu = forut = None
    if len(ar) >= 2:
        nu, forut = ar.iloc[-1], ar.iloc[-2]

    def delta(kolumn):
        # Förändringen i procent, eller None om det inte finns något år att jämföra med
        return forandring(nu[kolumn], forut[kolumn]) if forut is not None else None

    def trend(kolumn):
        # Värdena till det lilla trenddiagrammet i kortet (en punkt per månad/kvartal/år)
        return serie[kolumn].round(1).tolist() if len(serie) > 1 else None

    forsaljning, vinst = df["Total_Sales"].sum(), df["Profit"].sum()
    k1, k2, k3, k4 = st.columns(4)
    # delta = pilen. delta_description = texten bredvid pilen. chart_data = det lilla diagrammet.
    jamfor = f"mot {ar.index[-2]}" if forut is not None else None   # kort text, t.ex. "mot 2024"
    k1.metric("💰 Försäljning", pengar(forsaljning), delta=delta("Försäljning"), delta_description=jamfor,
              chart_data=trend("Försäljning"), chart_type="area")
    k2.metric("📈 Vinst", pengar(vinst), delta=delta("Vinst"), delta_description=jamfor,
              chart_data=trend("Vinst"), chart_type="area")
    marginal_delta = None
    if forut is not None:
        # Marginalen är redan i procent, så där visar vi skillnaden i procentenheter
        skillnad = nu["Marginal (%)"] - forut["Marginal (%)"]
        marginal_delta = ("+" if skillnad >= 0 else "") + f"{tal(skillnad, 1)} %-enh."
    k3.metric("🎯 Vinstmarginal", procent(vinst / forsaljning * 100), delta=marginal_delta,
              delta_description=jamfor, chart_data=trend("Marginal (%)"), chart_type="line",
              help="Hur stor del av försäljningen som blir vinst. Pilen visar skillnaden i procentenheter.")
    k4.metric("📦 Ordrar", tal(df["Order_ID"].nunique()), delta=delta("Ordrar"), delta_description=jamfor,
              chart_data=trend("Ordrar"), chart_type="bar")

    if forut is not None:
        st.caption(f"Siffrorna gäller hela urvalet. Pilen visar hur {ar.index[-1]} gick jämfört med "
                   f"{ar.index[-2]}. De små diagrammen visar utvecklingen per {tidsupplosning.lower()}.")
    else:
        st.caption(f"De små diagrammen visar utvecklingen per {tidsupplosning.lower()}. "
                   "Välj minst två år i panelen till vänster för att se en jämförelse.")


def visa_snabboversikt(df):
    """Tre kort med de viktigaste punkterna: toppar och dalar, bästa och sämsta."""
    ar = per_ar(df)
    manad = over_tid(df, "Månad")
    produkter = summera(df, "Product_Name")
    kategorier = summera(df, "Kategori")

    # idxmax() = namnet på raden med störst värde, idxmin() = raden med minst värde
    topp, dipp = manad["Försäljning"].idxmax(), manad["Försäljning"].idxmin()
    punkter_forsaljning = [
        f"Toppmånad: <b>{manadsnamn(topp)}</b> ({pengar(manad.loc[topp, 'Försäljning'])})",
        f"Svagaste månad: <b>{manadsnamn(dipp)}</b> ({pengar(manad.loc[dipp, 'Försäljning'])})",
    ]
    if len(ar) > 1:   # "bästa år" säger bara något om mer än ett år är valt
        basta_ar = ar["Försäljning"].idxmax()
        punkter_forsaljning.append(f"Bästa år: <b>{basta_ar}</b> ({pengar(ar.loc[basta_ar, 'Försäljning'])})")

    bast_p, samst_p = produkter["Vinst"].idxmax(), produkter["Vinst"].idxmin()
    bast_k, samst_k = kategorier["Vinst"].idxmax(), kategorier["Marginal (%)"].idxmin()

    rubrik("🔎", "Det viktigaste just nu")
    s1, s2, s3 = st.columns(3)
    with s1:
        punktkort("📈", "Försäljning", punkter_forsaljning)
    with s2:
        punktkort("🏆", "Drar in mest vinst", [
            f"Produkt: <b>{bast_p}</b> ({pengar(produkter.loc[bast_p, 'Vinst'])})",
            f"Kategori: <b>{bast_k}</b> ({pengar(kategorier.loc[bast_k, 'Vinst'])})",
        ])
    with s3:
        punktkort("⚠️", "Drar in minst vinst", [
            f"Produkt: <b>{samst_p}</b> ({pengar(produkter.loc[samst_p, 'Vinst'])})",
            f"Kategori: <b>{samst_k}</b> (marginal {procent(kategorier.loc[samst_k, 'Marginal (%)'])})",
        ])


def visa_forsaljning_trender(df, tidsupplosning):
    """Flik: Hur ser försäljningen och vinsten ut över tid?"""
    tabell = over_tid(df, tidsupplosning)
    steg = tidsupplosning.lower()

    # --- Försäljning och vinst över tid ---
    # "en månad" men "ett kvartal" / "ett år"
    artikel = "en" if tidsupplosning == "Månad" else "ett"
    rubrik("📈", "Hur ser försäljningen och vinsten ut?",
           f"Varje punkt är {artikel} {steg} – byt mellan månad, kvartal och år i panelen till vänster. "
           "Håll musen över diagrammet för att se siffrorna.")
    visa(linjediagram(tabell, ["Försäljning", "Vinst"], tidsupplosning))

    topp, dipp = tabell["Försäljning"].idxmax(), tabell["Försäljning"].idxmin()
    svarsruta(f"Försäljningen var högst under <b>{periodnamn(topp, tidsupplosning)}</b> "
              f"({pengar(tabell.loc[topp, 'Försäljning'])}) och lägst under <b>{periodnamn(dipp, tidsupplosning)}</b> "
              f"({pengar(tabell.loc[dipp, 'Försäljning'])}). Vinsten följer försäljningen nästan exakt.")

    # --- Marginal över tid (eget diagram: procent och dollar ska inte dela samma axel) ---
    rubrik("🎯", "Vinstmarginal över tid", "Hur många procent av försäljningen som blir vinst.")
    fig = linjediagram(tabell, ["Marginal (%)"], tidsupplosning, prefix="")
    fig.update_traces(hovertemplate="Marginal: %{y:.1f} %<extra></extra>")
    fig.data[0].update(fillcolor="rgba(25,158,112,0.12)")   # turkos yta under linjen
    fig.update_yaxes(ticksuffix=" %")
    fig.update_layout(height=260, showlegend=False)
    visa(fig)
    svarsruta(f"Marginalen har legat mellan <b>{procent(tabell['Marginal (%)'].min())}</b> och "
              f"<b>{procent(tabell['Marginal (%)'].max())}</b> – alltså mycket stabil, även när försäljningen svänger.")

    # --- Per år ---
    ar = per_ar(df)
    rubrik("📅", "Försäljning och vinst per år")
    # reset_index gör året till en vanlig kolumn. Året görs om till text, så att axeln visar "2023" och inte "2 023".
    data = ar.reset_index(names="År")
    data["År"] = data["År"].astype(str)
    fig = px.bar(data, x="År", y=["Försäljning", "Vinst"], barmode="group", color_discrete_map=MATT_FARG)
    # texttemplate = talet ovanför varje stapel
    fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside", cliponaxis=False,
                      textfont=dict(color=TEXT, size=13), marker_cornerradius=4,
                      hovertemplate="%{x} – %{fullData.name}: $%{y:,.0f}<extra></extra>")
    snygga_till(fig, 360, pengar_y=True)
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(range=[0, ar["Försäljning"].max() * 1.15])   # plats för talen ovanför staplarna
    visa(fig)
    visa_tabell(ar)
    if len(ar) >= 2:
        svarsruta(f"<b>{ar.index[-1]}</b> sålde vi för {pengar(ar['Försäljning'].iloc[-1])}, "
                  f"<b>{forandring(ar['Försäljning'].iloc[-1], ar['Försäljning'].iloc[-2])}</b> jämfört med "
                  f"{ar.index[-2]}.")


def visa_produkter_kategorier(df, tidsupplosning):
    """Flik: Vilka kategorier och produkter drar in mest?"""
    # --- Kategorier: klickbart stapeldiagram ---
    rubrik("🛋️", "Vilka kategorier drar in mest?",
           "Klicka på en stapel för att bara visa den kategorins produkter längre ner.")
    # segmented_control = knappar i rad där man väljer ett alternativ (samma som Johan använder)
    matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal (%)"], default="Försäljning",
                                key="kategori_matt", label_visibility="collapsed") or "Försäljning"
    som_text = procent if "%" in matt else pengar   # välj rätt formatering för talen vid staplarna

    kategorier = summera(df, "Kategori").sort_values(matt).reset_index()
    fig = px.bar(kategorier, x=matt, y="Kategori", orientation="h", color="Kategori",
                 color_discrete_map=KATEGORI_FARG, text=kategorier[matt].map(som_text))
    fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>")
    snygga_till(fig, 300)
    liggande_staplar(fig, kategorier, matt)
    # on_select="rerun" gör diagrammet klickbart: sidan körs om och vi får veta vad som klickades
    klick = visa(fig, on_select="rerun", selection_mode="points", key="kategori_klick")
    punkter = klick.selection.points        # lista med klickade staplar (tom = inget klickat)
    vald_kategori = punkter[0]["y"] if punkter else None   # för liggande staplar är "y" kategorins namn

    storst = kategorier.iloc[-1]   # sista raden = störst efter sorteringen
    hogst_marginal = kategorier.sort_values("Marginal (%)").iloc[-1]
    andel = storst["Försäljning"] / kategorier["Försäljning"].sum() * 100
    if matt == "Marginal (%)":
        svarsruta(f"<b>{storst['Kategori']}</b> har högst marginal ({procent(storst['Marginal (%)'])}): "
                  "där blir störst del av varje såld dollar vinst.")
    else:
        svarsruta(f"<b>{storst['Kategori']}</b> drar in mest {matt.lower()} och står för {procent(andel)} av "
                  f"försäljningen. Men <b>{hogst_marginal['Kategori']}</b> har högst marginal "
                  f"({procent(hogst_marginal['Marginal (%)'])}).")
    visa_tabell(kategorier.set_index("Kategori"))

    # --- Produktlistan ---
    if vald_kategori:
        rubrik("🏷️", f"Produkter i kategorin {vald_kategori}",
               "Klicka på en rad för att se produkten över tid. Dubbelklicka i diagrammet ovan för att visa alla kategorier igen.")
        urval = df[df["Kategori"] == vald_kategori]
    else:
        rubrik("🏷️", "Alla produkter", "Klicka på en rad för att se produkten över tid.")
        urval = df

    sortering = st.segmented_control("Sortera efter", ["Försäljning", "Vinst", "Marginal (%)"],
                                     default="Försäljning", key="produkt_sortering") or "Försäljning"
    produkter = summera(urval, "Product_Name").sort_values(sortering, ascending=False).reset_index()
    # Kategorin för varje produkt: first = första värdet i gruppen (en produkt hör bara till en kategori)
    produkter["Kategori"] = produkter["Product_Name"].map(urval.groupby("Product_Name")["Kategori"].first())
    produkter = produkter.round({"Försäljning": 0, "Vinst": 0, "Marginal (%)": 1})
    # Avrundning kan ge "-0" (t.ex. -0,4 -> -0). Att lägga till 0.0 gör om -0 till vanlig 0.
    produkter["Vinst"] += 0.0
    # Kolumnerna som visas. Kategori behövs bara när alla kategorier visas.
    kolumner = ["Product_Name", "Försäljning", "Vinst", "Marginal (%)", "Ordrar", "Antal"]
    if not vald_kategori:
        kolumner.insert(1, "Kategori")   # lägg in Kategori som andra kolumn

    # Klickbar tabell. key innehåller kategori och sortering, så att valet nollställs när de ändras
    # (annars skulle rad nummer 3 plötsligt betyda en annan produkt).
    vald_rad = st.dataframe(
        produkter,
        hide_index=True, width="stretch", height=390,
        on_select="rerun", selection_mode="single-row",
        key=f"produkter_{vald_kategori}_{sortering}",
        column_order=kolumner,
        column_config={
            # ProgressColumn = en stapel i cellen, så att man ser storleksordningen direkt.
            # format="localized" = tusentalsavgränsare enligt webbläsarens språk (46 614).
            # width="small" = smal kolumn, så att hela tabellen får plats utan att man behöver scrolla i sidled.
            "Product_Name": st.column_config.TextColumn("Produkt"),
            "Kategori": st.column_config.TextColumn(width="small"),
            "Försäljning": st.column_config.ProgressColumn(
                "Försäljning ($)", format="localized", min_value=0, max_value=float(produkter["Försäljning"].max())),
            "Vinst": st.column_config.ProgressColumn(
                "Vinst ($)", format="localized", min_value=0, max_value=float(produkter["Vinst"].max())),
            "Marginal (%)": st.column_config.ProgressColumn(
                format="%.1f", min_value=0, max_value=float(produkter["Marginal (%)"].max())),
            "Ordrar": st.column_config.NumberColumn(width="small"),
            "Antal": st.column_config.NumberColumn("Sålda", width="small", help="Antal sålda enheter"),
        },
    )
    rader = vald_rad.selection.rows                     # valda radnummer (tom lista = inget valt)
    vald_produkt = produkter.loc[rader[0] if rader else 0, "Product_Name"]   # inget valt -> översta produkten

    # --- Detaljer för vald produkt ---
    df_produkt = urval[urval["Product_Name"] == vald_produkt]
    rubrik("🔍", vald_produkt,
           f"Kategori: {df_produkt['Kategori'].iloc[0]}."
           + ("" if rader else " Visar produkten överst i listan – klicka på en rad för att välja en annan."))
    forsaljning, vinst = df_produkt["Total_Sales"].sum(), df_produkt["Profit"].sum()
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("💰 Försäljning", pengar(forsaljning))
    p2.metric("📈 Vinst", pengar(vinst))
    p3.metric("🎯 Vinstmarginal", procent(vinst / forsaljning * 100))
    p4.metric("📦 Sålda enheter", tal(df_produkt["Quantity"].sum()))
    visa(linjediagram(over_tid(df_produkt, tidsupplosning), ["Försäljning", "Vinst"], tidsupplosning))


def visa_forlustordrar(df):
    """Flik: Varför går vissa ordrar med förlust – och vad kan vi göra åt det?"""
    rubrik("⚠️", "Varför går vissa ordrar med förlust?",
           "En order går med förlust när det kostar mer att köpa in och skicka varan än kunden betalar.")

    # Ny kolumn med True/False: gick ordern med förlust?
    df = df.assign(Förlust=df["Profit"] < 0)
    forlust = df[df["Förlust"]]
    lonsamma = df[~df["Förlust"]]   # ~ betyder "inte": alla ordrar som INTE gick med förlust
    if forlust.empty:
        st.success("Inga ordrar i urvalet gick med förlust. 🎉")
        return

    # Hur stor del av ordervärdet som går till frakt, för varje order
    frakt_andel = df["Shipping_Cost"] / df["Total_Sales"] * 100
    # median = mittenvärdet (hälften av ordrarna ligger under, hälften över). Påverkas inte av extremvärden.
    frakt_forlust = frakt_andel[df["Förlust"]].median()
    frakt_lonsam = frakt_andel[~df["Förlust"]].median()

    # --- Nyckeltal ---
    # Här är texten under talet bara en upplysning, inte en förändring. Därför:
    # delta_color="off" = grå i stället för grön/röd, delta_arrow="off" = ingen pil.
    info = dict(delta_color="off", delta_arrow="off")   # samma inställningar till flera kort
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🧾 Förlustordrar", tal(len(forlust)), delta=f"{procent(len(forlust) / len(df) * 100)} av alla", **info)
    k2.metric("💸 Förlorat totalt", pengar(forlust["Profit"].sum()),
              help="Summan av vinsten för alla förlustordrar (negativ = förlust).")
    k3.metric("🛍️ Snittorder", pengar(forlust["Total_Sales"].mean()),
              delta=f"lönsamma: {pengar(lonsamma['Total_Sales'].mean())}", **info,
              help="Genomsnittligt ordervärde för förlustordrarna, jämfört med de lönsamma ordrarna.")
    k4.metric("🚚 Frakten tar", procent(frakt_forlust), delta=f"lönsamma: {procent(frakt_lonsam)}", **info,
              help="Hur stor del av ordervärdet som går till frakt (mittenvärdet).")

    # --- Diagram: andel förlustordrar per ordervärde och per kategori ---
    vanster, hoger = st.columns(2)
    with vanster:
        # pd.cut delar in varje order i en "värdeklass" utifrån ordervärdet (se VARDEGRANSER högst upp)
        klass = pd.cut(df["Total_Sales"], VARDEGRANSER, labels=VARDEKLASSER)
        # mean() av True/False = andelen True. observed=False = ta med alla klasser, även tomma.
        per_klass = (df["Förlust"].groupby(klass, observed=False).mean() * 100).fillna(0).reset_index()
        per_klass.columns = ["Ordervärde", "Andel förlust (%)"]
        fig = px.bar(per_klass, x="Ordervärde", y="Andel förlust (%)", title="Andel förlustordrar per ordervärde",
                     text=per_klass["Andel förlust (%)"].map(lambda v: f"{v:.0f} %"))
        fig.update_traces(marker_color=ROD, textposition="outside", cliponaxis=False, marker_cornerradius=4,
                          textfont=dict(color=TEXT, size=13), hovertemplate="%{x}: %{text} går med förlust<extra></extra>")
        snygga_till(fig, 340)
        fig.update_yaxes(range=[0, max(per_klass["Andel förlust (%)"].max() * 1.25, 10)], showticklabels=False)
        fig.update_xaxes(showgrid=False)
        visa(fig)
    with hoger:
        per_kategori = (df["Förlust"].groupby(df["Kategori"]).mean() * 100).sort_values().reset_index()
        per_kategori.columns = ["Kategori", "Andel förlust (%)"]
        fig = px.bar(per_kategori, x="Andel förlust (%)", y="Kategori", orientation="h", color="Kategori",
                     color_discrete_map=KATEGORI_FARG, title="Andel förlustordrar per kategori",
                     text=per_kategori["Andel förlust (%)"].map(procent))
        fig.update_traces(hovertemplate="%{y}: %{text} av ordrarna går med förlust<extra></extra>")
        snygga_till(fig, 340)
        visa(liggande_staplar(fig, per_kategori, "Andel förlust (%)"))

    # Slutsats: andelen förlustordrar bland små ordrar (under $50) och hur stor del av förlustordrarna som är små
    sma = df["Total_Sales"] < 50
    sma_forlust = df.loc[sma, "Förlust"].mean() * 100 if sma.any() else 0
    andel_sma = (forlust["Total_Sales"] < 50).mean() * 100
    varst = per_kategori.iloc[-1]
    # "alla" låter bättre än "100,0 %"
    hur_manga = "Alla" if andel_sma == 100 else procent(andel_sma)
    svarsruta(f"<b>Det är de små ordrarna som går med förlust.</b> {hur_manga} av förlustordrarna "
              f"är värda under $50, och {procent(sma_forlust)} av alla ordrar under $50 går med förlust. "
              f"Frakten kostar nästan lika mycket oavsett ordervärde, så på en liten order tar den "
              f"<b>{procent(frakt_forlust)}</b> av beloppet – mot {procent(frakt_lonsam)} på en lönsam order. "
              f"Därför drabbas <b>{varst['Kategori']}</b> mest ({procent(varst['Andel förlust (%)'])} av ordrarna): "
              "där är varorna billiga.")

    # --- Jämförelse: förlustordrar mot lönsamma ordrar ---
    with st.expander("📋 Jämför förlustordrar med lönsamma ordrar"):
        jamforelse = pd.DataFrame({
            "Lönsamma ordrar": [len(lonsamma), lonsamma["Total_Sales"].mean(), lonsamma["Unit_Price"].mean(),
                                lonsamma["Quantity"].mean(), lonsamma["Shipping_Cost"].mean(), frakt_lonsam,
                                lonsamma["Discount_Percent"].mean()],
            "Förlustordrar": [len(forlust), forlust["Total_Sales"].mean(), forlust["Unit_Price"].mean(),
                              forlust["Quantity"].mean(), forlust["Shipping_Cost"].mean(), frakt_forlust,
                              forlust["Discount_Percent"].mean()],
        }, index=["Antal ordrar", "Snittordervärde ($)", "Snittpris per vara ($)", "Varor per order",
                  "Frakt per order ($)", "Frakten av ordervärdet (%)", "Snittrabatt (%)"])
        st.dataframe(jamforelse.round(1), width="stretch")
        st.caption("Frakten kostar ungefär lika mycket för båda, men förlustordrarna är mycket mindre. "
                   "Rabatten skiljer bara lite – den är inte huvudorsaken.")

    with st.expander("📋 Produkterna med flest förlustordrar"):
        topp = forlust.groupby(["Product_Name", "Kategori"]).agg(
            Förlustordrar=("Order_ID", "count"), Förlorat=("Profit", "sum")).sort_values(
            "Förlustordrar", ascending=False).head(10).reset_index()
        st.dataframe(topp.round(0), hide_index=True, width="stretch",
                     column_config={"Product_Name": "Produkt", "Förlorat": st.column_config.NumberColumn(format="$%d")})

    # --- Tänk om … (samma idé som Johans rabattreglage) ---
    rubrik("🧪", "Tänk om små ordrar fick betala sin egen frakt?",
           "Dra i reglaget: ordrar under den gränsen betalar själva för frakten. Se direkt vad som händer med vinsten.")
    vanster, hoger = st.columns([1, 2])
    with vanster:
        grans = st.slider("Ordrar under det här beloppet betalar frakten", min_value=0, max_value=100,
                          value=50, step=5, format="$%d")
    # Ordrar under gränsen: frakten betalas av kunden, så den blir inte längre en kostnad för oss
    berorda = df["Total_Sales"] < grans
    ny_vinst = df["Profit"] + df["Shipping_Cost"].where(berorda, 0)   # where = lägg bara till frakt för berörda ordrar
    extra = ny_vinst.sum() - df["Profit"].sum()
    with hoger:
        a, b, c = st.columns(3)
        a.metric("📈 Ny vinst", pengar(ny_vinst.sum()), delta=f"+{pengar(extra)}", delta_description="mot idag")
        b.metric("🧾 Förlustordrar kvar", tal((ny_vinst < 0).sum()),
                 delta=f"{tal((ny_vinst < 0).sum() - len(forlust))} st", delta_color="inverse",
                 help="inverse = färre förlustordrar visas i grönt, eftersom det är bra.")
        c.metric("🛍️ Påverkas", tal(berorda.sum()), help="Antal ordrar som är värda mindre än gränsen")
    svarsruta(f"Om ordrar under <b>${grans}</b> betalade sin egen frakt hade vinsten blivit "
              f"<b>{pengar(extra)} högre</b>, och antalet förlustordrar hade gått från {tal(len(forlust))} till "
              f"<b>{tal((ny_vinst < 0).sum())}</b>.")
    st.caption("⚠️ Förenkling: vi antar att kunderna hade köpt exakt lika mycket även om de fick betala frakten. "
               "I verkligheten kan en del kunder välja att inte köpa, eller att lägga till fler varor för att slippa avgiften.")


# ===========================================================================
# 5. MAIN – sätter ihop sidan
# ===========================================================================

def aterstall():
    # Körs när man klickar på "Återställ allt": tar bort alla val så att allt visas som från början
    for nyckel in ["filter_ar", "filter_kategori", "tidsupplosning"]:
        st.session_state.pop(nyckel, None)


def main():
    st.set_page_config(page_title="Försäljning & produkter", page_icon="📈", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)   # lägg in sidans utseende (CSS:en ovan)

    alla = hamta_data()

    # --- Sidopanelen: period och filter ---
    # (I gruppens gemensamma app används i stället den gemensamma sidopanelen.)
    with st.sidebar:
        st.markdown("### 📅 Period")
        alla_ar = sorted(alla["Order_Date"].dt.year.unique())   # t.ex. [2023, 2024, 2025]
        valda_ar = st.multiselect("År", alla_ar, default=alla_ar, key="filter_ar")
        tidsupplosning = st.segmented_control("Visa diagrammen per", ["Månad", "Kvartal", "År"],
                                              default="Kvartal", key="tidsupplosning") or "Kvartal"
        st.markdown("### 🎛️ Filter")
        valda_kategorier = st.multiselect("🛒 Kategori", list(KATEGORIER.values()),
                                          default=list(KATEGORIER.values()), key="filter_kategori")
        st.button("↺ Återställ allt", on_click=aterstall, width="stretch")

    # Behåll bara ordrar från valda år och valda kategorier. & = "och", båda villkoren måste stämma.
    df = alla[alla["Order_Date"].dt.year.isin(valda_ar) & alla["Kategori"].isin(valda_kategorier)]
    if df.empty:
        st.warning("Inga ordrar matchar dina val. Välj minst ett år och en kategori i panelen till vänster.")
        st.stop()   # avsluta här så resten av sidan inte ritas

    # --- Sidan: översikt först, sedan detaljer i flikar ---
    visa_hero(valda_ar, valda_kategorier, tidsupplosning)
    visa_nyckeltal(df, tidsupplosning)
    visa_snabboversikt(df)

    st.write("")   # lite luft före flikarna
    flik_trender, flik_produkter, flik_forlust = st.tabs(
        ["📈 Försäljning & trender", "🛋️ Produkter & kategorier", "⚠️ Förlustordrar"])
    with flik_trender:
        visa_forsaljning_trender(df, tidsupplosning)
    with flik_produkter:
        visa_produkter_kategorier(df, tidsupplosning)
    with flik_forlust:
        visa_forlustordrar(df)


# Kör main() bara när filen startas direkt (streamlit run ...).
# Om gruppens app i stället importerar funktionerna härifrån ritas ingen extra sida.
if __name__ == "__main__":
    main()
