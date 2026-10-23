"""FILTER: håller reda på vad man har valt i sidopanelen och i diagrammen.

Streamlit kör om hela sidan vid varje klick. Det man har valt sparas därför i
st.session_state (sidans minne), och funktionerna här läser och ändrar det minnet.

Filtren finns i två uppsättningar:
  - utkastet (datumväljaren och "utkast_..."): det man håller på att välja i panelen till vänster
  - det som gäller ("vald_..." och "filter_..."): det som sidan faktiskt visar
Utkastet börjar gälla först när man klickar på Uppdatera. En tom lista betyder "alla".
Klickar man i ett diagram ändras båda direkt.
"""
import streamlit as st

from berakningar import jamforelse_for, skapa_urval, snabbval_period
from data import datumgranser, land_till_region
from installningar import ALLA_LANDER, ALLA_NAMN, KOD_TILL_LAND, STANDARD_JAMFOR, STANDARD_SNABBVAL

FILTER = ["region", "land", "kundgrupp", "kategori"]

# Valen i flikarna (t.ex. vad kartan ska visa). De nollställs också när man klickar på "Återställ allt".
FLIKARNAS_VAL = ["tid_matt", "kategori_matt", "produkt_matt", "karta_matt", "grupp_matt", "betal_matt",
                 "produkt_sortering"]


# ===========================================================================
# STARTVÄRDEN
# ===========================================================================

def standardvarden():
    # Hur allt ser ut när man öppnar sidan (och efter "Återställ allt"): hela perioden och alla filter
    forsta, sista = datumgranser()
    period = snabbval_period(STANDARD_SNABBVAL, forsta, sista)
    return {
        "snabbval": STANDARD_SNABBVAL, "period_datum": period, "jamfor_pa": False,
        "jamfor_val": STANDARD_JAMFOR, "jamfor_datum": jamforelse_for(STANDARD_JAMFOR, period),
        "utkast_region": [], "utkast_land": ALLA_LANDER, "utkast_kundgrupp": [], "utkast_kategori": [],
        "vald_period": period, "vald_jamforelse": None,
        "filter_region": [], "filter_land": ALLA_LANDER, "filter_kundgrupp": [], "filter_kategori": [],
    }


def forbered():
    # Fyller i startvärdena i sidans minne första gången sidan öppnas (finns de redan händer inget)
    for nyckel, varde in standardvarden().items():
        st.session_state.setdefault(nyckel, varde)
    st.session_state.setdefault("klick_nr", 0)


# ===========================================================================
# PERIODER I PANELEN
# ===========================================================================

def som_period(valt):
    # Kalendern ger (första dag, sista dag). Har man bara hunnit klicka på första dagen
    # finns ingen sista dag än – då blir svaret None (ingen färdig period).
    if isinstance(valt, (tuple, list)):
        return (valt[0], valt[1]) if len(valt) == 2 else None
    return (valt, valt)


def utkast_period():
    # Perioden i kalendern just nu (eller den som gäller, om man bara hunnit klicka på första dagen)
    return som_period(st.session_state["period_datum"]) or st.session_state["vald_period"]


def utkast_jamforelse(per):
    # Jämförelseperioden i panelen just nu, eller None om jämförelsen är avstängd
    if not st.session_state.get("jamfor_pa"):
        return None
    val = st.session_state.get("jamfor_val", STANDARD_JAMFOR)
    if val != "Anpassat":
        return jamforelse_for(val, per)
    return som_period(st.session_state.get("jamfor_datum")) or st.session_state["vald_jamforelse"]


# ===========================================================================
# DET HÄR KÖRS AUTOMATISKT NÄR MAN ÄNDRAR NÅGOT I SIDOPANELEN
# ===========================================================================

def nar_snabbval_andras():
    # Man valde t.ex. "Senaste 30 dagarna": fyll i kalendern med de datumen
    if st.session_state["snabbval"] != "Anpassat":
        st.session_state["period_datum"] = snabbval_period(st.session_state["snabbval"], *datumgranser())


def nar_kalendern_andras():
    # Man valde egna datum i kalendern: visa "Anpassat" i listan med snabbval
    st.session_state["snabbval"] = "Anpassat"


def nar_jamfor_kalendern_andras():
    # Man valde egna datum för jämförelsen: visa "Anpassat" i jämförelselistan
    st.session_state["jamfor_val"] = "Anpassat"


def satt_land(namn, typ):
    # Väljer ett land (eller "Alla länder") och håller regionen i takt med det: väljer man USA sätts
    # regionen till Nordamerika, och går man tillbaka till alla länder kommer de regioner man hade
    # valt innan tillbaka. typ = "utkast" (panelen) eller "filter" (det som gäller på sidan).
    sparade = f"{typ}_regioner_fore_land"
    if namn == ALLA_LANDER:
        st.session_state[f"{typ}_region"] = st.session_state.pop(sparade, [])
    else:
        if sparade not in st.session_state:   # spara regionerna bara första gången
            st.session_state[sparade] = st.session_state[f"{typ}_region"]
        st.session_state[f"{typ}_region"] = [land_till_region()[namn]]
    st.session_state[f"{typ}_land"] = namn


def nar_land_valjs():
    # Man valde ett land i listan i panelen. Det börjar gälla när man klickar på Uppdatera.
    satt_land(st.session_state["utkast_land"], "utkast")


def tillampa():
    # Körs när man klickar på Uppdatera: allt man har valt i panelen börjar gälla på hela sidan
    per = utkast_period()
    st.session_state["vald_period"], st.session_state["vald_jamforelse"] = per, utkast_jamforelse(per)
    for namn in FILTER:
        st.session_state[f"filter_{namn}"] = st.session_state[f"utkast_{namn}"]
    if "utkast_regioner_fore_land" in st.session_state:
        st.session_state["filter_regioner_fore_land"] = st.session_state["utkast_regioner_fore_land"]
    else:
        st.session_state.pop("filter_regioner_fore_land", None)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


def har_vantande_andringar():
    # True om man har ändrat något i panelen som inte gäller än (då behöver man klicka på Uppdatera)
    def samma(namn):
        utkast, galler = st.session_state[f"utkast_{namn}"], st.session_state[f"filter_{namn}"]
        if namn == "land":
            return utkast == galler
        # tom lista och alla valda betyder samma sak
        return set(utkast or ALLA_NAMN[namn]) == set(galler or ALLA_NAMN[namn])
    per = utkast_period()
    return (per != st.session_state["vald_period"] or utkast_jamforelse(per) != st.session_state["vald_jamforelse"]
            or not all(samma(namn) for namn in FILTER))


def aterstall():
    # Körs när man klickar på "Återställ allt": hela perioden och alla regioner, länder, kundgrupper
    # och kategorier. Det gäller direkt, utan att man behöver klicka på Uppdatera.
    for nyckel in list(standardvarden()) + ["utkast_regioner_fore_land", "filter_regioner_fore_land"] + FLIKARNAS_VAL:
        st.session_state.pop(nyckel, None)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


# ===========================================================================
# KLICK I DIAGRAMMEN: filtrerar sidan direkt (och ändrar filtren i panelen)
# ===========================================================================

def valj_land(namn):
    # Ett klick på ett land gäller direkt, både på sidan och i panelen
    for typ in ("filter", "utkast"):
        satt_land(namn, typ)
    st.session_state["klick_nr"] += 1   # diagrammen glömmer gamla klick


def nar_land_klickas(nyckel):
    # Körs när man klickar på ett land på kartan (ger landskoden) eller i topplistan (ger namnet).
    # Klickar man på samma land igen tas filtret bort.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    varde = punkter[0].get("location") or punkter[0].get("y")
    namn = KOD_TILL_LAND.get(varde, varde)
    if namn in land_till_region():
        valj_land(ALLA_LANDER if st.session_state["filter_land"] == namn else namn)


def nar_stapel_klickas(filter_namn, nyckel):
    # Körs när man klickar på en stapel för en kundgrupp eller kategori: filtrerar hela sidan på den
    # direkt (och ändrar filtret i panelen). Klickar man på samma igen visas alla.
    punkter = st.session_state[nyckel]["selection"]["points"]
    if not punkter:
        return
    namn = punkter[0].get("y")
    if namn in ALLA_NAMN[filter_namn]:
        nytt = [] if st.session_state[f"filter_{filter_namn}"] == [namn] else [namn]
        st.session_state[f"filter_{filter_namn}"], st.session_state[f"utkast_{filter_namn}"] = nytt, list(nytt)
    st.session_state["klick_nr"] += 1


# ===========================================================================
# URVALET SOM GÄLLER JUST NU
# ===========================================================================

def las_urval(alla):
    # Läser filtren som gäller just nu ur sidans minne och räknar ut urvalet (se berakningar.Urval)
    land = st.session_state["filter_land"]
    return skapa_urval(
        alla, st.session_state["vald_period"], st.session_state["vald_jamforelse"],
        st.session_state["filter_region"], st.session_state["filter_kundgrupp"],
        st.session_state["filter_kategori"], None if land == ALLA_LANDER else land)
