"""STIL: sidans utseende (CSS = instruktioner för hur sidan ska se ut).

Färgtemat för knappar, filter och bakgrund ligger i .streamlit/config.toml.
Här finns resten: typsnitt, KPI-korten, rubrikerna, förklaringsrutorna och periodkortet
i sidopanelen. Färgerna hämtas från installningar.py, så att CSS:en och diagrammen matchar.
"""
import streamlit as st

from installningar import AXEL, BLA, GRA, KORT, TEXT, TEXT_SVAG


def lagg_till_css():
    # Lägger in CSS:en på sidan. Körs en gång högst upp i dashboard_app.py.
    st.markdown(f"""
<style>
/* Mjukare, modernare typsnitt och lite mer luft */
html, body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
.block-container {{ padding-top: 3.6rem; max-width: 1400px; }}   /* luft så att KPI-korten inte hamnar under verktygsraden */

/* Sidans rubrik */
.sidrubrik {{ font-size: 2.1rem; font-weight: 750; color: {TEXT}; letter-spacing: -0.02em; line-height: 1.2; }}
.sidrubrik-under {{ color: {TEXT_SVAG}; font-size: 1.0rem; margin: 4px 0 18px 0; }}

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

/* Förklaringen under varje diagram: vad det visar, hur man läser det och vad vi ser */
.forklaring {{
    display: flex; flex-direction: column; gap: 6px; margin: 2px 0 6px 0;
    background: {KORT}; border-left: 3px solid {BLA}; border-radius: 10px;
    padding: 12px 14px; font-size: 0.92rem; line-height: 1.45; color: {TEXT_SVAG};
}}
.forklaring-etikett {{ color: {TEXT}; font-weight: 600; }}
.forklaring-slutsats {{ color: {TEXT}; padding-top: 6px; border-top: 1px solid {AXEL}; }}

/* Punktlistan i snabböversiktens kort */
.punkt {{ color: {TEXT}; }}
.punkt-titel {{ font-weight: 700; font-size: 1.05rem; margin-bottom: 6px; }}
.punkt ul {{ margin: 0; padding-left: 1.1rem; color: {TEXT_SVAG}; }}
.punkt li {{ margin: 4px 0; }}
.punkt b {{ color: {TEXT}; }}

/* Kortet i sidopanelen som visar vilka perioder som jämförs */
.period-ruta {{
    background: linear-gradient(180deg, #161c27 0%, #11161f 100%); border: 1px solid {AXEL};
    border-radius: 14px; padding: 12px 14px; margin: 2px 0 10px 0; font-size: 0.92rem; color: {TEXT};
}}
.period-rad {{ display: flex; gap: 10px; align-items: flex-start; padding: 5px 0; }}
.period-etikett {{ color: {TEXT_SVAG}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }}
.prick {{ width: 10px; height: 10px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }}
.prick.bla {{ background: {BLA}; box-shadow: 0 0 8px {BLA}; }}
.prick.gra {{ background: {GRA}; }}

/* Flikarna lite större och tydligare */
button[role="tab"] p, div[role="tab"] p {{ font-size: 1.0rem; }}
</style>
""", unsafe_allow_html=True)
