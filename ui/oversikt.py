"""ÖVERSIKT: det som står ovanför och under flikarna.

  - sidans rubrik
  - de tio KPI-korten, med pilar när man jämför perioder (från Wissams dashboard)
  - snabböversikten "Det viktigaste i urvalet" (idé från Alyoshs del)
  - tabellen med hela urvalet längst ner, som går att ladda ner (från Wissams dashboard)
"""
import streamlit as st

from berakningar import summera
from formatering import forandring, pengar, pengar_exakt, period_text, procent, procentenheter, steg_text, tal
from installningar import ALLA_LANDER
from ui.filter import valj_land
from ui.komponenter import punktkort, rubrik

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


def visa_sidrubrik():
    # Sidans rubrik, högst upp ovanför KPI-korten
    st.markdown('<div class="sidrubrik">📊 E-commerce Customer Sales Dashboard</div>'
                '<div class="sidrubrik-under">Global e-handel 2023–2025 · försäljning, produkter, kunder och betalning '
                '· belopp i USD</div>', unsafe_allow_html=True)


def visa_tomt_urval(urval):
    # Visas i stället för resten av sidan när filtren inte ger några ordrar alls
    if urval.land:
        st.warning(f"{urval.land} har inga ordrar som matchar dina val. Välj en längre period eller ett annat land.")
        st.button("✕ Visa alla länder", on_click=valj_land, args=(ALLA_LANDER,), key="alla_lander_tom")
    else:
        st.warning("Inga ordrar matchar dina val. Välj en längre period eller ändra filtren.")


def visa_kpi_kort(urval):
    # Tio KPI-kort i två rader. Med jämförelse visar varje kort en pil med förändringen.
    nu, forut = urval.nu, urval.forut
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
        st.caption(f"🔵 {period_text(urval.period)} jämfört med ⚪ {period_text(urval.jamfor_period)}. "
                   "Pilen visar förändringen. Håll musen över ⓘ för att se siffran för jämförelseperioden.")
    else:
        st.caption(f"🔵 {period_text(urval.period)}. Slå på ⚖️ Jämför under 📅 Datum i panelen till vänster "
                   "för att se pilar med förändringen mot en annan period.")


def visa_snabboversikt(urval):
    # Tre kort med toppar och dalar: försäljning, mest vinst och minst vinst
    df, nu, serie_nu = urval.df, urval.nu, urval.serie_nu
    per_produkt = summera(df, "Product_Name")
    per_kategori = summera(df, "Kategori")
    per_land = summera(df, "Land")
    per_kundgrupp = summera(df, "Kundgrupp")

    rubrik("🔎", "Det viktigaste i urvalet", "Toppar och dalar för den period och de filter du har valt.")
    s1, s2, s3 = st.columns(3)
    with s1:
        topp_steg = serie_nu["Försäljning"].idxmax()
        storst_grupp = per_kundgrupp["Försäljning"].idxmax()
        punktkort("📈", "Försäljning", [
            f"Bästa {urval.steg}: <b>{steg_text(topp_steg, urval.frekvens)}</b> "
            f"({pengar(serie_nu.loc[topp_steg, 'Försäljning'])})",
            f"Största marknad: <b>{per_land['Försäljning'].idxmax()}</b> "
            f"({pengar(per_land['Försäljning'].max())})",
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


def visa_tabell(urval):
    # Tabell med hela urvalet och en knapp för att ladda ner det som en CSV-fil
    tabell = urval.df.drop(columns=["Landskod", "Datum"])   # kolumner som bara behövs inne i koden
    st.write("")
    with st.expander(f"📋 Visa urvalet som tabell ({tal(len(urval.df))} ordrar)"):
        st.dataframe(tabell, width="stretch", hide_index=True)
        st.download_button("⬇️ Ladda ner urvalet (CSV)", tabell.to_csv(index=False).encode("utf-8"),
                           file_name="urval_e_handel.csv", mime="text/csv")
