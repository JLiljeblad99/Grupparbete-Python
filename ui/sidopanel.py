"""SIDOPANELEN: datum, jämförelse och filter till vänster på sidan.

Här ritas bara panelen. Vad som händer när man ändrar något (t.ex. klickar på Uppdatera)
står i filter.py.
"""
from datetime import date

import streamlit as st

from data import datumgranser, land_till_region
from formatering import datum_text, period_text, tal
from installningar import ALLA_LANDER, ALLA_NAMN, JAMFOR_VAL, SNABBVAL
from ui import filter


def visa(urval):
    # Ritar hela sidopanelen. urval behövs för att visa vilken period som gäller just nu.
    forsta_dag, sista_dag = datumgranser()
    period, jamfor_period, langd = urval.period, urval.jamfor_period, urval.langd

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
                st.radio("Snabbval", SNABBVAL, key="snabbval", on_change=filter.nar_snabbval_andras,
                         label_visibility="collapsed")

            # Höger: kalendern för perioden, och jämförelsen under den
            with kalender_kolumn:
                st.markdown("**🔵 Period**")
                st.date_input("Period", key="period_datum", min_value=forsta_dag, max_value=sista_dag,
                              format="YYYY-MM-DD", on_change=filter.nar_kalendern_andras,
                              label_visibility="collapsed")
                if filter.som_period(st.session_state["period_datum"]) is None:
                    st.caption("👆 Klicka på sista dagen i kalendern.")

                st.toggle("⚖️ Jämför med en annan period", key="jamfor_pa")
                if st.session_state["jamfor_pa"]:
                    jamfor_val = st.selectbox("Jämför med", JAMFOR_VAL, key="jamfor_val")
                    # Om man inte valt egna datum räknas jämförelsens datum ut automatiskt
                    if jamfor_val != "Anpassat":
                        st.session_state["jamfor_datum"] = filter.jamforelse_for(jamfor_val, filter.utkast_period())
                    st.markdown("**⚪ Jämförelseperiod**")
                    st.date_input("Jämförelseperiod", key="jamfor_datum", min_value=date(2015, 1, 1),
                                  max_value=sista_dag, format="YYYY-MM-DD",
                                  on_change=filter.nar_jamfor_kalendern_andras, label_visibility="collapsed")
            st.caption(f"Datan går från {datum_text(forsta_dag)} till {datum_text(sista_dag)}. "
                       "Klicka på **Uppdatera** i panelen när du är klar.")

        # Varna om en märkbar del (mer än 5 %) av jämförelsen ligger före datans början – då blir den
        # inte rättvis. En enstaka dag gör inget: datan börjar 2 jan 2023, så "förra året" saknar bara 1 jan.
        if jamfor_period and (forsta_dag - jamfor_period[0]).days > 0.05 * ((jamfor_period[1] - jamfor_period[0]).days + 1):
            st.warning(f"Jämförelseperioden börjar före {datum_text(forsta_dag)}, när datan saknas. "
                       "Jämförelsen blir därför missvisande – välj en kortare period.")

        st.markdown("### 🎛️ Filter")
        st.multiselect("🌍 Region", ALLA_NAMN["region"], key="utkast_region", placeholder="Alla regioner")

        # Land: bara länderna i de regioner man har valt (väljer man Nordamerika går bara Kanada, Mexiko
        # och USA att välja). Väljer man ett land sätts regionen till landets region (se filter.satt_land).
        utkast_regioner = st.session_state["utkast_region"] or ALLA_NAMN["region"]
        land_alternativ = [ALLA_LANDER] + sorted(land for land, region in land_till_region().items()
                                                 if region in utkast_regioner)
        if st.session_state["utkast_land"] not in land_alternativ:
            # t.ex. om man själv har valt bort landets region – då visas alla länder i regionerna man valt
            st.session_state["utkast_land"] = ALLA_LANDER
            st.session_state.pop("utkast_regioner_fore_land", None)
        st.selectbox("📍 Land", land_alternativ, key="utkast_land", on_change=filter.nar_land_valjs,
                     help="Visar länderna i de regioner du har valt. Regionen ändras automatiskt till landets region. "
                          "Du kan också klicka på ett land på kartan.")
        st.multiselect(
            "👥 Kundgrupp", ALLA_NAMN["kundgrupp"], key="utkast_kundgrupp", placeholder="Alla kundgrupper",
            help="**Privatpersoner** = vanliga konsumenter. **Företag** = större företag. "
                 "**Småföretag** = små företag och folk som driver firma hemifrån (heter \"Home Office\" i datan).")
        st.multiselect("🛒 Kategori", ALLA_NAMN["kategori"], key="utkast_kategori", placeholder="Alla kategorier")

        # Uppdatera: allt man har valt ovanför börjar gälla. Knappen lyser blått när det finns något att tillämpa.
        vantar = filter.har_vantande_andringar()
        st.button("✓ Uppdatera", on_click=filter.tillampa, type="primary" if vantar else "secondary", width="stretch")
        st.button("↺ Återställ allt", on_click=filter.aterstall, width="stretch",
                  help="Hela perioden och alla regioner, länder, kundgrupper och kategorier. Gäller direkt.")
        st.caption("💡 Klickar du på ett land, en kundgrupp eller en kategori i ett diagram filtreras sidan direkt.")

    # Varning om jämförelseperioden inte har några ordrar alls (hamnar längst ner i panelen)
    if jamfor_period and urval.jmf_alla_lander is None and not urval.df_alla_lander.empty:
        st.sidebar.warning("Det finns ingen data för jämförelseperioden. Välj en annan period.")
