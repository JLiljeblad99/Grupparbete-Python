"""FLIK: FÖRSÄLJNING & TRENDER

  - Utveckling över tid (Johans tidsdiagram, med jämförelsen ovanpå)
  - Försäljning och vinst per år (Alyoshs årsdiagram)
"""
import streamlit as st

import berakningar
import diagram
from formatering import forandring, pengar, procent, procentenheter, steg_text, tal
from ui.komponenter import forklaring, kort, visa


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    nu, forut, serie_nu = urval.nu, urval.forut, urval.serie_nu

    # --- Utveckling över tid ---
    with kort("📈", "Utveckling över tid", "Välj vad diagrammet ska visa."):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal", "Ordrar"],
                                    default="Försäljning", key="tid_matt",
                                    label_visibility="collapsed") or "Försäljning"
        fig = diagram.utveckling_over_tid(serie_nu, urval.serie_jmf, matt, urval.frekvens,
                                          urval.period, urval.jamfor_period, urval.flytt)
        visa(fig, "tid")

        # Slutsatsen: förändringen mot jämförelseperioden, eller den bästa punkten om man inte jämför
        format_ = {"Försäljning": pengar, "Vinst": pengar, "Marginal": procent, "Ordrar": tal}[matt]
        if forut:
            andring = (procentenheter(nu[matt] - forut[matt]) if matt == "Marginal"
                       else forandring(nu[matt], forut[matt]) or "–")
            slutsats = (f"{matt} i vald period: <b>{format_(nu[matt])}</b>, mot {format_(forut[matt])} "
                        f"i jämförelseperioden – en förändring på <b>{andring}</b>.")
        else:
            basta = serie_nu[matt].idxmax()
            slutsats = (f"Högst var det under <b>{steg_text(basta, urval.frekvens)}</b> "
                        f"({format_(serie_nu.loc[basta, matt])}).")
        forklaring(
            f"Hur {matt.lower()} har utvecklats i den period du valt. Varje punkt är en {urval.steg}.",
            slutsats)

    # --- Försäljning och vinst per år ---
    with kort("📅", "Försäljning och vinst per år"):
        ar = berakningar.per_ar(urval.df)
        visa(diagram.forsaljning_per_ar(ar), "per_ar")
        if len(ar) >= 2:
            sista, forra = ar.iloc[-1], ar.iloc[-2]
            slutsats = (f"<b>{sista['År']}</b> sålde vi för {pengar(sista['Försäljning'])}, "
                        f"<b>{forandring(sista['Försäljning'], forra['Försäljning'])}</b> jämfört med {forra['År']}. "
                        f"Marginalen var {procent(sista['Marginal'])} mot {procent(forra['Marginal'])}.")
        else:
            slutsats = "Välj en period som täcker flera år (t.ex. <b>Hela perioden</b>) för att jämföra åren."
        forklaring(
            "Den totala försäljningen (blå) och vinsten (turkos) för varje år i perioden.",
            slutsats)
