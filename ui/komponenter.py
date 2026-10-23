"""KOMPONENTER: byggstenarna som alla flikar använder.

Ett diagram visas alltid på samma sätt: i ett kort med rubrik, sedan diagrammet och
sist en förklaring. Funktionerna här gör att alla kort ser likadana ut i hela dashboarden.
"""
from functools import partial   # skickar med extra värden till en funktion som körs vid klick

import streamlit as st

from formatering import html_text


def visa(fig, namn, vid_klick=None):
    # Visar ett diagram på sidan, utan Plotlys verktygsrad (enklare för användaren).
    # Med vid_klick går det att klicka i diagrammet: då körs den funktionen. Nyckeln får ett nytt
    # nummer efter varje klick, så att diagrammet glömmer det gamla klicket.
    nyckel = f"{namn}_{st.session_state['klick_nr']}"
    klick = dict(on_select=partial(vid_klick, nyckel), selection_mode="points") if vid_klick else {}
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False}, key=nyckel, **klick)


def rubrik(ikon, titel, undertitel="", liten=False):
    # En rubrik med ikon och en kort förklaring under. liten=True används inne i korten.
    stil = ' style="margin-top:4px;font-size:1.1rem"' if liten else ""
    st.markdown(f'<div class="avsnitt"{stil}><span class="avsnitt-ikon">{ikon}</span>{titel}</div>'
                + (f'<div class="avsnitt-under">{html_text(undertitel)}</div>' if undertitel else ""),
                unsafe_allow_html=True)


def kort(ikon, titel, undertitel=""):
    # Ett kort med ram runt. Varje diagram ligger i ett eget kort: rubrik, diagram och förklaring.
    # height="stretch" gör att korten bredvid varandra blir lika höga (det högsta bestämmer).
    # Används med "with": allt som står inne i with-blocket hamnar i kortet.
    ruta = st.container(border=True, height="stretch")
    with ruta:
        rubrik(ikon, titel, undertitel, liten=True)
    return ruta


def forklaring(vad, slutsats=None):
    # Förklaringen under varje diagram (samma idé som i Wissams dashboard):
    # vad diagrammet visar och vad vi kan se i urvalet just nu.
    rader = [f'<div><span class="forklaring-etikett">ℹ️ Vad visar diagrammet?</span> {vad}</div>']
    if slutsats:
        rader.append(f'<div class="forklaring-slutsats">💡 {slutsats}</div>')
    st.markdown(f'<div class="forklaring">{html_text("".join(rader))}</div>', unsafe_allow_html=True)


def punktkort(ikon, titel, punkter):
    # Ett litet kort med en rubrik och en punktlista (används i snabböversikten).
    # Samma sorts kort som diagrammen ligger i, så att alla rutor ser likadana ut.
    lista = "".join(f"<li>{punkt}</li>" for punkt in punkter)
    with st.container(border=True, height="stretch"):
        st.markdown(html_text(f'<div class="punkt"><div class="punkt-titel">{ikon} {titel}</div><ul>{lista}</ul></div>'),
                    unsafe_allow_html=True)
