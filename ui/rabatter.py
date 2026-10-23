"""FLIK: RABATTER & FÖRLUSTORDRAR

  - Vinstmarginal per rabattnivå (Wissams diagram)
  - Vem får rabatterna?
  - Förlustordrar (Alyoshs flik): fyra nyckeltal, andel per ordervärde och per kategori,
    och de produkter som har flest förlustordrar
"""
import streamlit as st

import berakningar
import diagram
from formatering import pengar, pengar_exakt, procent, tal
from ui.komponenter import forklaring, kort, rubrik, visa


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    df = urval.df

    rubrik("🏷️", "Rabatter", "Hur mycket rabatterna påverkar vinsten, och vem som får dem.")
    vanster, hoger = st.columns(2)

    # --- Vinstmarginal per rabattnivå ---
    with vanster, kort("📉", "Vinstmarginal per rabattnivå"):
        per_rabatt = berakningar.marginal_per_rabatt(df)
        visa(diagram.marginal_per_rabatt(per_rabatt), "rabatt_marginal")
        forsta, sista = per_rabatt.iloc[0], per_rabatt.iloc[-1]
        forklaring(
            "Hur många procent av försäljningen som blir vinst, beroende på hur stor rabatt kunden fick.",
            f"Vid {forsta['Rabatt']} rabatt är marginalen <b>{procent(forsta['Marginal'])}</b>, "
            f"vid {sista['Rabatt']} bara <b>{procent(sista['Marginal'])}</b>." if len(per_rabatt) > 1 else None)

    # --- Hur ofta ges varje rabatt, och till vem? ---
    with hoger, kort("👥", "Vem får rabatterna?"):
        antal, nivaer = berakningar.rabatt_per_kundgrupp(df)
        visa(diagram.rabatt_per_kundgrupp(antal, nivaer), "rabatt_kundgrupp")
        stor = berakningar.per_kundgrupp(df, "Stor rabatt")
        forklaring(
            "Hur många ordrar som fått varje rabattnivå, uppdelat på kundgrupp.",
            f"<b>{stor.idxmax()}</b> får oftast mer än 10 % rabatt ({procent(stor.max())} av deras ordrar), "
            f"mot {procent(stor.min())} för {stor.idxmin().lower()}." if len(stor) > 1 else None)

    # --- Förlustordrar ---
    rubrik("⚠️", "Förlustordrar",
           "En order går med förlust när det kostar mer att köpa in och skicka varan än kunden betalar.")
    forlust, lonsamma = df[df["Förlust"]], df[~df["Förlust"]]
    if forlust.empty:
        st.success("Inga ordrar i urvalet gick med förlust. 🎉")
        return
    frakt_forlust, frakt_lonsam = berakningar.frakt_andel_median(df)

    # Fyra nyckeltal om förlustordrarna. Texten under talen är bara en upplysning, inte en
    # förändring: grå och utan pil. height="stretch" gör att alla fyra korten blir lika höga.
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

    # --- Andel förlustordrar per ordervärde ---
    with vanster, kort("💲", "Andel förlustordrar per ordervärde"):
        visa(diagram.forlust_per_ordervarde(berakningar.forlust_per_ordervarde(df)), "forlust_varde")
        sma = df["Total_Sales"] < 50
        andel_sma = (forlust["Total_Sales"] < 50).mean() * 100
        hur_manga = "Alla" if andel_sma == 100 else procent(andel_sma)   # "alla" låter bättre än "100,0 %"
        forklaring(
            "Hur stor andel av ordrarna som gick med förlust, uppdelat efter hur mycket ordern var värd.",
            f"<b>{hur_manga}</b> av förlustordrarna är värda under $50. "
            f"Frakten tar {procent(frakt_forlust)} av beloppet på en förlustorder, mot {procent(frakt_lonsam)} "
            "på en lönsam." if sma.any() and not lonsamma.empty else None)

    # --- Andel förlustordrar per kategori ---
    with hoger, kort("🛋️", "Andel förlustordrar per kategori"):
        per_kat = berakningar.forlust_per_kategori(df)
        visa(diagram.forlust_per_kategori(per_kat), "forlust_kategori")
        forklaring(
            "Hur stor andel av ordrarna i varje kategori som gick med förlust.",
            f"<b>{per_kat.index[-1]}</b> drabbas mest ({procent(per_kat.iloc[-1])} av ordrarna). Där är varorna "
            "billiga, så frakten äter upp vinsten.")

    # --- Produkterna med flest förlustordrar (en tabell som man fäller ut) ---
    with st.expander("📋 Produkterna med flest förlustordrar"):
        st.dataframe(berakningar.flest_forlustordrar(forlust).round(0), hide_index=True, width="stretch",
                     column_config={"Product_Name": "Produkt", "Förlorat": st.column_config.NumberColumn(format="$%d")})
