"""GEMENSAM DASHBOARD: gruppens analys av e-handelsdatan på en enda sida.

Det här är startfilen. Den innehåller nästan ingen egen kod, utan sätter bara ihop
delarna i rätt ordning:

  1. sidans inställningar och utseende   (stil.py)
  2. datan                               (data.py)
  3. filtren och sidopanelen             (ui/filter.py, ui/sidopanel.py)
  4. rubrik, KPI-kort och snabböversikt  (ui/oversikt.py)
  5. flikarna                            (ui/trender.py, ui/produkter.py … ui/tank_om.py)
  6. tabellen längst ner                 (ui/oversikt.py)

Uträkningarna finns i berakningar.py och diagrammen i diagram.py. Se README.md för
en beskrivning av alla filer.

Starta så här (från projektmappen):
    pip install -r requirements.txt
    streamlit run dashboard_app.py
"""
import streamlit as st

import stil
from data import CSV_FIL, hamta_data
from ui import betalning, filter, geografi, oversikt, produkter, rabatter, sidopanel, tank_om, trender

# 1. Sidans inställningar (måste komma först) och CSS:en
st.set_page_config(page_title="E-handel – gemensam dashboard", page_icon="📊", layout="wide")
stil.lagg_till_css()

# 2. Läs in datan. Saknas filen visas ett felmeddelande och sidan stannar här.
try:
    alla = hamta_data()
except FileNotFoundError:
    st.error(f"Hittar inte datafilen: {CSV_FIL}")
    st.stop()

# 3. Filtren: fyll i startvärden, räkna ut urvalet som gäller just nu och rita sidopanelen
filter.forbered()
urval = filter.las_urval(alla)
sidopanel.visa(urval)

# 4. Rubriken, och sedan KPI-korten och snabböversikten.
# Ger filtren inga ordrar alls visas ett meddelande i stället, och sidan stannar här.
oversikt.visa_sidrubrik()
if urval.df.empty:
    oversikt.visa_tomt_urval(urval)
    st.stop()
oversikt.visa_kpi_kort(urval)
oversikt.visa_snabboversikt(urval)

# 5. Flikarna. Varje flik har en egen fil i mappen ui med en funktion som heter visa_flik.
# key + bind="query-params" gör att vald flik ligger kvar när man klickar i ett diagram,
# och att fliken syns i adressen (?flik=…).
st.write("")   # lite luft före flikarna
FLIKAR = {
    "📈 Försäljning & trender": trender,
    "🛋️ Produkter & kategorier": produkter,
    "🌍 Geografi & kunder": geografi,
    "💳 Betalning": betalning,
    "🏷️ Rabatter & förlust": rabatter,
    "🧪 Tänk om …": tank_om,
}
for flik, del_ in zip(st.tabs(list(FLIKAR), key="flik", bind="query-params"), FLIKAR.values()):
    with flik:
        del_.visa_flik(urval)

# 6. Tabellen med hela urvalet längst ner
oversikt.visa_tabell(urval)
