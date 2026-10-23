"""FLIK: TÄNK OM … – två prognoser

  - Idé 1 (Johan): tänk om vi gav mindre rabatt?
  - Idé 2 (Alyosh): tänk om små ordrar fick betala sin egen frakt?

Uträkningarna finns i berakningar.py (rabatttak och fraktavgift).
"""
import streamlit as st

import berakningar
from formatering import pengar, procent, procentenheter, tal
from installningar import KUNDGRUPPER
from ui.komponenter import forklaring, kort


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    st.markdown("Här kan du testa två idéer för att öka vinsten. Prognoserna räknar på **alla datum** "
                "(så mycket data som möjligt), men följer filtren för region, land, kundgrupp och kategori.")
    prognos = berakningar.bara_landet(urval.bas, urval.land)
    nuvarande_vinst = prognos["Profit"].sum()
    nuvarande_marginal = nuvarande_vinst / prognos["Total_Sales"].sum() * 100

    # --- Idé 1: tak för rabatten ---
    with kort("🏷️", "Tänk om vi gav mindre rabatt?",
              "Välj vilka kunder som ska få ett tak för rabatten och dra i reglaget."):
        vanster, hoger = st.columns([1, 2])
        with vanster:
            tak_grupper = st.multiselect("Vilka kundgrupper?", list(KUNDGRUPPER.values()), default=["Företag"])
            tak = st.slider("Högsta tillåtna rabatt", min_value=0, max_value=30, value=10, step=5, format="%d %%")
        extra, berorda, ny_marginal = berakningar.rabatttak(prognos, tak_grupper, tak)
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
        ny_vinst, extra, forlust_innan, forlust_efter, berorda = berakningar.fraktavgift(prognos, grans)
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
            f"Om ordrar under <b>${grans}</b> betalade sin egen frakt hade vinsten blivit <b>{pengar(extra)} högre</b>, "
            f"och förlustordrarna hade gått från {tal(forlust_innan)} till <b>{tal(forlust_efter)}</b>. "
            "Förenkling: vi antar att kunderna hade köpt lika mycket ändå.")
