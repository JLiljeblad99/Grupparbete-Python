"""FLIK: GEOGRAFI & KUNDER

  - Världskarta (Johans klickbara karta)
  - Länder med mest försäljning (klickbar topplista)
  - Kundgrupper (klickbara)
  - Fraktkostnad per region (Johans fråga 2)
  - Vad köps i olika delar av världen? (Johans fråga 3)
"""
from functools import partial

import streamlit as st

import berakningar
import diagram
from formatering import pengar, procent
from installningar import KATEGORI_FARG, KUNDGRUPP_FARG
from ui.filter import nar_land_klickas, nar_stapel_klickas
from ui.komponenter import forklaring, kort, visa


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    df, jmf, valt_land = urval.df, urval.jmf, urval.land

    # Kartan och topplistan visar alltid alla länder i urvalet, även när ett land är valt
    lander = berakningar.per_land(urval.df_alla_lander, urval.jmf_alla_lander)

    # --- Världskartan: ett klick på ett land filtrerar hela sidan ---
    with kort("🗺️", "Världskarta", "Klicka på ett land så visar alla diagram bara det landet – "
                                    "klicka igen för att se alla länder."):
        alternativ = ["Försäljning", "Vinst", "Marginal (%)", "Ordrar"]
        if urval.jmf_alla_lander is not None:
            alternativ.append("Förändring (%)")   # bara när man jämför: hur mycket varje land ökat/minskat
        if st.session_state.get("karta_matt") not in alternativ + [None]:
            st.session_state.pop("karta_matt")    # t.ex. "Förändring" när jämförelsen har stängts av
        matt = st.segmented_control("Vad ska kartan visa?", alternativ, default="Försäljning", key="karta_matt",
                                    label_visibility="collapsed") or "Försäljning"
        karta = diagram.varldskarta(lander, matt, valt_land, med_jamforelse=urval.jmf_alla_lander is not None)
        visa(karta, "karta", nar_land_klickas)
        storst = lander.loc[lander["Försäljning"].idxmax()]
        forklaring(
            f"{matt} i varje land vi säljer till. Grå länder har inga ordrar i urvalet.",
            f"Störst är <b>{storst['Land']}</b> med {pengar(storst['Försäljning'])} "
            f"(marginal {procent(storst['Marginal (%)'])}).")

    vanster, hoger = st.columns(2)

    # --- Topplista över länder (klickbar) ---
    with vanster, kort("🏆", "Länder med mest försäljning", "Klicka på ett land för att filtrera hela sidan."):
        topp, visas = berakningar.topplista_lander(lander, valt_land)
        visa(diagram.topplista_lander(visas, valt_land), "topplista", nar_land_klickas)
        if valt_land:
            plats_nr = int(topp.loc[topp["Land"] == valt_land, "Plats"].iloc[0])
            slutsats = f"<b>{valt_land}</b> är nummer <b>{plats_nr}</b> av {len(topp)} länder i försäljning."
        else:
            topp3 = topp.head(3)["Försäljning"].sum() / topp["Försäljning"].sum() * 100
            slutsats = f"De tre största länderna står för <b>{procent(topp3)}</b> av försäljningen."
        forklaring(
            "De tio länder där kunderna har handlat för mest pengar. Färgen visar landets region.",
            slutsats)

    # --- Kundgrupper (ett klick på en stapel filtrerar hela sidan på den kundgruppen) ---
    with hoger, kort("👥", "Kundgrupper", "Vem köper – och vem får stora rabatter? Klicka för att filtrera."):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinstmarginal", "Stor rabatt"],
                                    default="Försäljning", key="grupp_matt",
                                    label_visibility="collapsed") or "Försäljning"
        format_ = pengar if matt == "Försäljning" else procent
        fig = diagram.jamforelse_staplar(berakningar.per_kundgrupp(df, matt), berakningar.per_kundgrupp(jmf, matt),
                                         format_, KUNDGRUPP_FARG, som_procentenheter=matt != "Försäljning", hojd=310)
        visa(fig, "kundgrupper", partial(nar_stapel_klickas, "kundgrupp"))
        rabatt = berakningar.per_kundgrupp(df, "Stor rabatt").sort_values()
        marginal = berakningar.per_kundgrupp(df, "Vinstmarginal")
        forklaring(
            {"Försäljning": "Hur mycket varje kundgrupp har köpt för.",
             "Vinstmarginal": "Hur stor del av varje kundgrupps köp som blir vinst.",
             "Stor rabatt": "Hur stor andel av varje kundgrupps ordrar som fått mer än 10 % rabatt."}[matt],
            f"<b>{rabatt.index[-1]}</b> får oftast stor rabatt ({procent(rabatt.iloc[-1])} av ordrarna) och har "
            f"en vinstmarginal på {procent(marginal[rabatt.index[-1]])}. Mer rabatt = mindre vinst."
            if len(rabatt) > 1 else None)

    vanster, hoger = st.columns(2)

    # --- Frakt per region ---
    with vanster, kort("🚚", "Fraktkostnad per region"):
        frakt = berakningar.frakt_per_region(df)
        visa(diagram.frakt_per_region(frakt), "frakt")
        dyrast, billigast = frakt.iloc[-1], frakt.iloc[0]
        forklaring(
            "Hur stor del av försäljningen som går till frakt i varje region, och vad frakten kostar per order.",
            f"I <b>{dyrast['Region']}</b> går {procent(dyrast['Andel'])} av försäljningen till frakt, mot "
            f"{procent(billigast['Andel'])} i {billigast['Region']}." if len(frakt) > 1 else None)

    # --- Produktmix per region ---
    with hoger, kort("🧭", "Vad köps i olika delar av världen?"):
        mix = berakningar.andel_per_region(df, "Kategori", KATEGORI_FARG, varde="Total_Sales")
        visa(diagram.staplad_andel(mix, "Kategori", KATEGORI_FARG, hojd=300), "produktmix")
        forklaring(
            "Hur försäljningen i varje region fördelar sig på de fyra kategorierna. Varje rad blir 100 %.",
            f"Mest möbler köper <b>{mix['Möbler'].idxmax()}</b> ({procent(mix['Möbler'].max())}), "
            f"mest teknik <b>{mix['Teknik'].idxmax()}</b> ({procent(mix['Teknik'].max())})."
            if {"Möbler", "Teknik"} <= set(mix.columns) and len(mix) > 1 else None)
