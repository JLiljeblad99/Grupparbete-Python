"""FLIK: PRODUKTER & KATEGORIER

  - Kategorier (klickbara: filtrerar hela sidan)
  - Topp 10 produkter, färgade efter kategori
  - Tabell med alla produkter (Alyoshs klickbara tabell)
  - Detaljer för den produkt man klickar på
"""
from functools import partial

import streamlit as st

import berakningar
import diagram
from formatering import pengar, procent, tal
from installningar import KATEGORI_FARG
from ui.filter import nar_stapel_klickas
from ui.komponenter import forklaring, kort, visa


def visa_flik(urval):
    # Ritar hela fliken. urval = det som filtren har valt ut (se berakningar.Urval).
    df, jmf, nu = urval.df, urval.jmf, urval.nu
    per_kategori = berakningar.summera(df, "Kategori")
    vanster, hoger = st.columns(2)

    # --- Kategorier (ett klick på en stapel filtrerar hela sidan på den kategorin) ---
    with vanster, kort("🛋️", "Kategorier", "Klicka på en kategori för att filtrera hela sidan."):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinst", "Marginal"], default="Försäljning",
                                    key="kategori_matt", label_visibility="collapsed") or "Försäljning"
        format_ = procent if matt == "Marginal" else pengar
        jmf_kategori = berakningar.summera(jmf, "Kategori")[matt] if jmf is not None else None
        fig = diagram.jamforelse_staplar(per_kategori[matt], jmf_kategori, format_, KATEGORI_FARG,
                                         som_procentenheter=matt == "Marginal")
        visa(fig, "kategorier", partial(nar_stapel_klickas, "kategori"))
        storst, hogst = per_kategori["Försäljning"].idxmax(), per_kategori["Marginal"].idxmax()
        forklaring(
            f"{matt} för varje produktkategori.",
            f"<b>{storst}</b> står för {procent(per_kategori.loc[storst, 'Försäljning'] / nu['Försäljning'] * 100)} "
            f"av försäljningen, men <b>{hogst}</b> har högst marginal ({procent(per_kategori.loc[hogst, 'Marginal'])}).")

    # --- Topp 10 produkter ---
    with hoger, kort("🏆", "Topp 10 produkter"):
        matt = st.segmented_control("Visa", ["Försäljning", "Vinst"], default="Försäljning",
                                    key="produkt_matt", label_visibility="collapsed") or "Försäljning"
        topp = berakningar.topp_produkter(df, matt)
        visa(diagram.topp_produkter(topp, matt), "topp_produkter")
        forklaring(
            f"De tio produkter som har dragit in mest {matt.lower()}. Färgen visar vilken kategori produkten hör till.",
            f"Etta är <b>{topp['Product_Name'].iloc[0]}</b> med {pengar(topp[matt].iloc[0])}.")

    # --- Produkttabellen: klicka på en rad för att se produkten nedanför ---
    with kort("🏷️", "Alla produkter", "Klicka på en rad för att se produkten över tid."):
        sortering = st.segmented_control("Sortera efter", ["Försäljning", "Vinst", "Marginal"],
                                         default="Försäljning", key="produkt_sortering") or "Försäljning"
        produkter = berakningar.produkttabell(df, sortering)
        # Klickbar tabell. key innehåller filtren och sorteringen, så att valet nollställs när de ändras
        # (annars skulle rad nummer 3 plötsligt betyda en annan produkt).
        vald_rad = st.dataframe(
            produkter, hide_index=True, width="stretch", height=390,
            on_select="rerun", selection_mode="single-row",
            key=f"produkter_{'_'.join(urval.kategorier)}_{sortering}_{len(df)}",
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
            "Alla produkter i urvalet med försäljning, vinst, marginal, antal ordrar och sålda enheter.")

    # --- Detaljer för vald produkt ---
    rader = vald_rad.selection.rows                     # valda radnummer (tom lista = inget valt)
    vald_produkt = produkter.loc[rader[0] if rader else 0, "Product_Name"]   # inget valt -> översta produkten
    df_produkt = df[df["Product_Name"] == vald_produkt]
    with kort("🔍", vald_produkt, f"Kategori: {df_produkt['Kategori'].iloc[0]}."
              + ("" if rader else " Visar produkten överst i listan – klicka på en rad för att välja en annan.")):
        produkt = berakningar.nyckeltal(df_produkt)
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("💰 Försäljning", pengar(produkt["Försäljning"]), height="stretch")
        p2.metric("📈 Vinst", pengar(produkt["Vinst"]), height="stretch")
        p3.metric("🎯 Vinstmarginal", procent(produkt["Marginal"]), height="stretch")
        p4.metric("📦 Sålda enheter", tal(produkt["Antal"]), height="stretch")
        serie = berakningar.tidsserie(df_produkt, urval.period, urval.frekvens)
        visa(diagram.produkt_over_tid(serie, urval.frekvens), "produkt_tid")
        forklaring(
            f"Försäljning (blå) och vinst (turkos) för {vald_produkt} per {urval.steg} i den valda perioden.")
