"""FLIK: BETALNING

  - Lönsamhet per betalsätt (vinstmarginal eller snittordervärde)
  - Betalsätt i vald region eller valt land (Johans fråga 4): ett cirkeldiagram som följer filtren
"""
import streamlit as st

import berakningar
import diagram
from formatering import pengar_exakt, procent, tal
from installningar import BETALSATT_FARG, REGIONER
from ui.komponenter import forklaring, kort, visa


def plats_text(urval):
    # Var urvalet gäller, t.ex. "Spanien", "Europa", "Europa och Sydamerika" eller "alla regioner"
    regioner = urval.regioner
    if urval.land:
        return urval.land
    if len(regioner) == len(REGIONER):
        return "alla regioner"
    return " och ".join([", ".join(regioner[:-1]), regioner[-1]] if len(regioner) > 1 else regioner)


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    df, jmf = urval.df, urval.jmf
    vanster, hoger = st.columns(2)

    # --- Vad är varje betalsätt värt? ---
    # Hur stor andel av ordrarna som betalas på varje sätt visas i cirkeldiagrammet bredvid,
    # så här visas bara vinstmarginal och snittordervärde.
    with vanster, kort("💳", "Lönsamhet per betalsätt"):
        alternativ = ["Vinstmarginal", "Snittordervärde"]
        if st.session_state.get("betal_matt") not in alternativ + [None]:
            st.session_state.pop("betal_matt")   # t.ex. ett gammalt val som inte finns längre
        matt = st.segmented_control("Visa", alternativ, default="Vinstmarginal", key="betal_matt",
                                    label_visibility="collapsed") or "Vinstmarginal"
        format_ = procent if matt == "Vinstmarginal" else pengar_exakt
        betal = berakningar.per_betalsatt(df, matt)
        fig = diagram.jamforelse_staplar(betal, berakningar.per_betalsatt(jmf, matt), format_, BETALSATT_FARG,
                                         som_procentenheter=matt == "Vinstmarginal", hojd=340)
        visa(fig, "betalsatt")
        if matt == "Vinstmarginal":
            slutsats = (f"Skillnaden i marginal mellan betalsätten är bara {tal(betal.max() - betal.min(), 1)} "
                        "procentenheter, så betalsättet påverkar nästan inte vinsten.")
        else:
            slutsats = (f"Störst ordrar har <b>{betal.idxmax().lower()}</b> ({pengar_exakt(betal.max())}), "
                        f"minst <b>{betal.idxmin().lower()}</b> ({pengar_exakt(betal.min())}).")
        forklaring(
            {"Vinstmarginal": "Hur stor del av försäljningen som blir vinst för varje betalsätt.",
             "Snittordervärde": "Hur mycket en order är värd i genomsnitt för varje betalsätt."}[matt],
            slutsats if len(betal) > 1 else None)

    # --- Betalsätt i den region/det land man har valt ---
    plats = plats_text(urval)
    with hoger, kort("🌐", f"Betalsätt i {plats}",
                     "Välj region eller land i panelen till vänster, så visar diagrammet bara det."):
        antal = berakningar.antal_per_betalsatt(df)
        visa(diagram.betalsatt_cirkel(antal), "betalsatt_cirkel")
        andel = antal / antal.sum() * 100
        forklaring(
            f"Hur ordrarna i {plats} fördelar sig på de fyra betalsätten. Hela cirkeln är 100 %.",
            f"I {plats} betalar flest med <b>{andel.idxmax().lower()}</b> ({procent(andel.max())}), "
            f"minst med <b>{andel.idxmin().lower()}</b> ({procent(andel.min())})." if len(andel) > 1 else None)
