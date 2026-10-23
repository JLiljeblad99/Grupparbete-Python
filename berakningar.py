"""BERÄKNINGAR: alla uträkningar på datan.

Här räknas allt ut som diagrammen och KPI-korten visar: summor, marginaler, perioder,
tidsserier och prognoser. Funktionerna tar emot en tabell (DataFrame) och ger tillbaka
siffror eller en ny tabell. Ingen av dem ritar något eller visar något på sidan,
så de går att testa och ändra utan att röra utseendet.

Ordningen följer flikarna i dashboarden, så det är lätt att hitta rätt uträkning.
"""
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from installningar import ALLA_NAMN, BETALSATT, VARDEGRANSER, VARDEKLASSER


# ===========================================================================
# GRUNDLÄGGANDE UTRÄKNINGAR (används i flera flikar)
# ===========================================================================

def summera(data, gruppera_pa):
    # Försäljning, vinst, ordrar, sålda enheter och marginal för varje grupp (t.ex. per kategori)
    tabell = data.groupby(gruppera_pa).agg(
        Försäljning=("Total_Sales", "sum"),
        Vinst=("Profit", "sum"),
        Ordrar=("Order_ID", "nunique"),
        Antal=("Quantity", "sum"),
    )
    # Vinstmarginal = hur stor del av försäljningen som blir vinst, i procent
    tabell["Marginal"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    return tabell


def nyckeltal(data):
    # De viktigaste siffrorna för en period (samma tio KPI:er som i Wissams dashboard,
    # men med frakt per order från Johans del i stället för produkter per order)
    if data is None:
        return None
    ordrar = data["Order_ID"].nunique()
    forsaljning, vinst = data["Total_Sales"].sum(), data["Profit"].sum()
    return {
        "Försäljning": forsaljning,
        "Vinst": vinst,
        "Marginal": vinst / forsaljning * 100,
        "Ordrar": ordrar,
        "Antal": data["Quantity"].sum(),
        "Snittorder": forsaljning / ordrar,
        "Vinst per order": vinst / ordrar,
        "Rabatt": data["Discount_Percent"].mean(),
        "Frakt": data["Shipping_Cost"].mean(),
        "Förlust": data.loc[data["Förlust"], "Order_ID"].nunique() / ordrar * 100,
    }


# ===========================================================================
# PERIODER: snabbval och jämförelse (som i Google Ads)
# ===========================================================================

def manader_bakat(dag, antal):
    # Flyttar ett datum ett antal månader bakåt, t.ex. 1 okt -> 1 jul om antal = 3
    return (pd.Timestamp(dag) - pd.DateOffset(months=antal)).date()


def snabbval_period(val, forsta_dag, sista_dag):
    # Räknar ut start- och slutdatum för ett snabbval, t.ex. "Senaste 30 dagarna".
    # Datan slutar 31 dec 2025, så "senaste", "denna månad" osv. räknas från datans sista dag.
    dag = sista_dag
    manad_start = dag.replace(day=1)
    kvartal_start = date(dag.year, 3 * ((dag.month - 1) // 3) + 1, 1)
    perioder = {
        "Senaste 7 dagarna": (dag - timedelta(days=6), dag),
        "Senaste 30 dagarna": (dag - timedelta(days=29), dag),
        "Senaste 90 dagarna": (dag - timedelta(days=89), dag),
        "Denna månad": (manad_start, dag),
        "Förra månaden": (manader_bakat(manad_start, 1), manad_start - timedelta(days=1)),
        "Detta kvartal": (kvartal_start, dag),
        "Förra kvartalet": (manader_bakat(kvartal_start, 3), kvartal_start - timedelta(days=1)),
        "I år": (date(dag.year, 1, 1), dag),
        "Förra året": (date(dag.year - 1, 1, 1), date(dag.year - 1, 12, 31)),
        "Hela perioden": (forsta_dag, sista_dag),
    }
    start, slut = perioder[val]
    return max(start, forsta_dag), min(slut, sista_dag)   # håll oss inom datans datum


def jamforelse_for(val, per):
    # Räknar ut jämförelseperioden automatiskt utifrån den valda perioden
    start, slut = per
    langd = (slut - start).days + 1
    if val == "Föregående period":
        # lika många dagar, precis före den valda perioden
        return (start - timedelta(days=langd), start - timedelta(days=1))
    # "Samma period förra året": samma datum, ett år tidigare
    return ((pd.Timestamp(start) - pd.DateOffset(years=1)).date(),
            (pd.Timestamp(slut) - pd.DateOffset(years=1)).date())


def valj_frekvens(langd):
    # Hur detaljerade diagrammen över tid ska vara beror på hur lång period man valt:
    # kort period = en punkt per dag, mellanlång = per vecka, lång = per månad.
    # Ger tillbaka (pandas-förkortning, ord som används i texterna).
    if langd <= 45:
        return "D", "dag"
    if langd <= 210:
        return "7D", "vecka"
    return "MS", "månad"


def tidsserie(data, period, frekvens, forskjutning=timedelta(0)):
    # Summerar nyckeltalen per dag/vecka/månad i den valda perioden.
    # "forskjutning" används för jämförelsen: dess datum flyttas fram så att de hamnar
    # ovanpå den valda periodens datum (dag 1 mot dag 1, dag 2 mot dag 2 osv.), som i Google Ads.
    start, slut = period
    datum = data["Order_Date"] + pd.Timedelta(forskjutning)
    if frekvens == "MS":
        # Varje order hamnar på första dagen i sin månad
        steg = pd.date_range(pd.Timestamp(start).replace(day=1), pd.Timestamp(slut), freq="MS")
        punkt = datum.dt.to_period("M").dt.to_timestamp()
    else:
        # Räkna dagar från periodens start. Per vecka: dag 0–6 = vecka 1, dag 7–13 = vecka 2 osv.
        langd_steg = 1 if frekvens == "D" else 7
        steg = pd.date_range(pd.Timestamp(start), pd.Timestamp(slut), freq=f"{langd_steg}D")
        dagar = (datum - pd.Timestamp(start)).dt.days // langd_steg * langd_steg
        punkt = pd.Timestamp(start) + pd.to_timedelta(dagar, unit="D")
    serie = data.assign(Punkt=punkt).groupby("Punkt").agg(
        Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"), Ordrar=("Order_ID", "nunique"),
        Antal=("Quantity", "sum"), Rabatt=("Discount_Percent", "mean"), Frakt=("Shipping_Cost", "mean"),
        Förlustordrar=("Förlust", "sum"))
    # Dagar/veckor utan ordrar: 0 i försäljning, vinst och ordrar. Snitt och andelar lämnas tomma,
    # annars ser det ut som att t.ex. frakten var gratis och marginalen 0 just den dagen.
    serie = serie.reindex(steg)
    summor = ["Försäljning", "Vinst", "Ordrar", "Antal", "Förlustordrar"]
    serie[summor] = serie[summor].fillna(0)
    har_ordrar = serie["Ordrar"].where(serie["Ordrar"] > 0)
    serie["Marginal"] = serie["Vinst"] / serie["Försäljning"].where(serie["Försäljning"] > 0) * 100
    serie["Snittorder"] = serie["Försäljning"] / har_ordrar
    serie["Vinst per order"] = serie["Vinst"] / har_ordrar
    serie["Förlust"] = serie["Förlustordrar"] / har_ordrar * 100
    return serie


# ===========================================================================
# URVALET: det som filtren i sidopanelen har valt ut
# ===========================================================================

def i_period(data, per):
    # Plockar ut ordrarna mellan två datum (båda dagarna räknas med)
    return data[(data["Datum"] >= per[0]) & (data["Datum"] <= per[1])]


def eller_inget(data):
    # En tom tabell blir None, så att resten av koden bara behöver kolla "is None"
    return None if data is None or data.empty else data


def bara_landet(data, land):
    # Om man har valt ett land: behåll bara det landets ordrar
    if data is None or land is None:
        return data
    return data[data["Land"] == land]


@dataclass
class Urval:
    # Allt som flikarna behöver veta om det man har valt, samlat på ett ställe.
    # Flikarna får ett Urval och läser t.ex. urval.df (ordrarna) och urval.period.
    alla: pd.DataFrame              # alla ordrar i datan, utan filter
    bas: pd.DataFrame               # region, kundgrupp och kategori filtrerade, men alla datum och länder
    period: tuple                   # vald period: (första dag, sista dag)
    jamfor_period: tuple | None     # jämförelseperioden, eller None om man inte jämför
    regioner: list                  # valda regioner (alla om filtret är tomt)
    kundgrupper: list               # valda kundgrupper
    kategorier: list                # valda kategorier
    land: str | None                # valt land, eller None för alla länder
    df_alla_lander: pd.DataFrame    # vald period, alla länder (används av kartan och topplistan)
    jmf_alla_lander: pd.DataFrame | None
    df: pd.DataFrame                # vald period och valt land: det som nästan alla diagram visar
    jmf: pd.DataFrame | None        # samma sak för jämförelseperioden (None om den saknas)
    langd: int                      # antal dagar i vald period
    frekvens: str                   # "D", "7D" eller "MS": en punkt per dag, vecka eller månad
    steg: str                       # "dag", "vecka" eller "månad"
    flytt: timedelta                # hur långt jämförelsen flyttas för att hamna ovanpå vald period
    nu: dict | None = None          # nyckeltalen för vald period
    forut: dict | None = None       # nyckeltalen för jämförelseperioden
    serie_nu: pd.DataFrame | None = None    # nyckeltalen per dag/vecka/månad
    serie_jmf: pd.DataFrame | None = None


def skapa_urval(alla, period, jamfor_period, regioner, kundgrupper, kategorier, land):
    # Filtrerar datan efter allt man har valt och räknar ut det som flera flikar behöver
    regioner = regioner or ALLA_NAMN["region"]          # tom lista = alla
    kundgrupper = kundgrupper or ALLA_NAMN["kundgrupp"]
    kategorier = kategorier or ALLA_NAMN["kategori"]

    # Behåll bara de ordrar som matchar region, kundgrupp och kategori (alla datum)
    bas = alla[alla["Region"].isin(regioner) & alla["Kundgrupp"].isin(kundgrupper)
               & alla["Kategori"].isin(kategorier)]

    # Alla länder i vald period och i jämförelseperioden – används av kartan och topplistan.
    # Jämförelsen blir None om den är avstängd eller saknar data (t.ex. före 2023).
    df_alla_lander = i_period(bas, period)
    jmf_alla_lander = eller_inget(i_period(bas, jamfor_period)) if jamfor_period else None
    df = bara_landet(df_alla_lander, land)
    jmf = eller_inget(bara_landet(jmf_alla_lander, land))

    langd = (period[1] - period[0]).days + 1
    frekvens, steg = valj_frekvens(langd)
    flytt = (period[0] - jamfor_period[0]) if jmf is not None else timedelta(0)
    urval = Urval(alla, bas, period, jamfor_period, regioner, kundgrupper, kategorier, land,
                  df_alla_lander, jmf_alla_lander, df, jmf, langd, frekvens, steg, flytt)

    # Nyckeltal och tidsserier går bara att räkna ut om det finns ordrar i urvalet
    if not df.empty:
        urval.nu, urval.forut = nyckeltal(df), nyckeltal(jmf)
        urval.serie_nu = tidsserie(df, period, frekvens)
        urval.serie_jmf = tidsserie(jmf, period, frekvens, flytt) if jmf is not None else None
    return urval


# ===========================================================================
# FLIK: FÖRSÄLJNING & TRENDER
# ===========================================================================

def per_ar(df):
    # Försäljning, vinst och marginal för varje år. Året blir text, så att axeln visar "2023" och inte "2 023".
    ar = summera(df, df["Order_Date"].dt.year.rename("År")).reset_index()
    ar["År"] = ar["År"].astype(str)
    return ar


# ===========================================================================
# FLIK: PRODUKTER & KATEGORIER
# ===========================================================================

def med_kategori(produkter, df):
    # Lägger till kolumnen Kategori i en tabell med produkter (Product_Name)
    produkter["Kategori"] = produkter["Product_Name"].map(df.groupby("Product_Name")["Kategori"].first())
    return produkter


def topp_produkter(df, matt, antal=10):
    # De produkter som har mest försäljning eller vinst (matt), med kategori
    topp = summera(df, "Product_Name").nlargest(antal, matt).reset_index()
    return med_kategori(topp, df)


def produkttabell(df, sortering):
    # Alla produkter i urvalet, sorterade efter försäljning, vinst eller marginal, och avrundade för tabellen
    produkter = summera(df, "Product_Name").sort_values(sortering, ascending=False).reset_index()
    produkter = med_kategori(produkter, df)
    produkter = produkter.round({"Försäljning": 0, "Vinst": 0, "Marginal": 1})
    produkter["Vinst"] += 0.0   # avrundning kan ge "-0"; att lägga till 0.0 gör om det till vanlig 0
    return produkter


# ===========================================================================
# FLIK: GEOGRAFI & KUNDER
# ===========================================================================

def per_land(df_alla_lander, jmf_alla_lander):
    # Försäljning, vinst, marginal och ordrar för varje land. Med jämförelse också försäljningen
    # i jämförelseperioden ("Innan") och hur mycket den har förändrats i procent.
    tabell = df_alla_lander.groupby(["Land", "Landskod", "Region"], as_index=False).agg(
        Ordrar=("Order_ID", "nunique"), Försäljning=("Total_Sales", "sum"), Vinst=("Profit", "sum"))
    tabell["Marginal (%)"] = tabell["Vinst"] / tabell["Försäljning"] * 100
    tabell["Innan"], tabell["Förändring (%)"] = float("nan"), float("nan")
    if jmf_alla_lander is not None:
        tabell["Innan"] = tabell["Landskod"].map(jmf_alla_lander.groupby("Landskod")["Total_Sales"].sum())
        tabell["Förändring (%)"] = (tabell["Försäljning"] / tabell["Innan"] - 1) * 100
    return tabell


def topplista_lander(lander, valt_land, antal=10):
    # Länderna sorterade efter försäljning med placering (1, 2, 3 …).
    # Ger tillbaka (alla länder, de som ska visas i diagrammet). Det valda landet visas alltid.
    topp = lander.sort_values("Försäljning", ascending=False).reset_index(drop=True)
    topp["Plats"] = topp.index + 1
    visas = topp.head(antal)
    if valt_land and valt_land not in set(visas["Land"]):
        visas = pd.concat([visas, topp[topp["Land"] == valt_land]])
    return topp, visas.iloc[::-1]   # störst överst i diagrammet


def per_kundgrupp(data, vad):
    # Försäljning, vinstmarginal eller andel ordrar med mer än 10 % rabatt ("Stor rabatt"), per kundgrupp
    if data is None:
        return None
    grupp = data.groupby("Kundgrupp")
    if vad == "Försäljning":
        return grupp["Total_Sales"].sum()
    if vad == "Vinstmarginal":
        return grupp["Profit"].sum() / grupp["Total_Sales"].sum() * 100
    return (data["Discount_Percent"] > 10).groupby(data["Kundgrupp"]).mean() * 100


def frakt_per_region(df):
    # Fraktkostnad per region: total, snitt per order och andel av försäljningen (lägst andel först)
    frakt = df.groupby("Region").agg(Frakt=("Shipping_Cost", "sum"), Försäljning=("Total_Sales", "sum"),
                                     Snitt=("Shipping_Cost", "mean"))
    frakt["Andel"] = frakt["Frakt"] / frakt["Försäljning"] * 100
    return frakt.sort_values("Andel").reset_index()


def andel_per_region(data, kolumn, ordning, varde=None):
    # Hur varje region fördelar sig på t.ex. kategorier, i procent (varje rad blir 100 %).
    # varde=None räknar antal ordrar, annars summan av den kolumnen (t.ex. Total_Sales).
    # ordning = i vilken ordning delarna ska stå (samma ordning som färgerna).
    tabell = pd.crosstab(data["Region"], data[kolumn], values=data[varde] if varde else None,
                         aggfunc="sum" if varde else None, normalize="index") * 100
    ordning = [namn for namn in ordning if namn in tabell.columns]
    return tabell[ordning].sort_values(ordning[0])   # mest av den första överst


# ===========================================================================
# FLIK: BETALNING
# ===========================================================================

def per_betalsatt(data, matt):
    # Vinstmarginal eller snittordervärde för varje betalsätt
    if data is None:
        return None
    grupp = data.groupby("Betalsätt")
    if matt == "Vinstmarginal":
        return grupp["Profit"].sum() / grupp["Total_Sales"].sum() * 100
    return grupp["Total_Sales"].mean()


def antal_per_betalsatt(df):
    # Antal ordrar per betalsätt, i samma ordning som överallt (så att färgerna stämmer)
    antal = df["Betalsätt"].value_counts()
    betalsatt = [b for b in BETALSATT.values() if b in antal.index]
    return antal[betalsatt]


# ===========================================================================
# FLIK: RABATTER & FÖRLUSTORDRAR
# ===========================================================================

def marginal_per_rabatt(df):
    # Försäljning, vinst och marginal för varje rabattnivå, med en etikett som "10 %"
    per_rabatt = summera(df, "Discount_Percent").reset_index()
    per_rabatt["Rabatt"] = per_rabatt["Discount_Percent"].astype(int).astype(str) + " %"
    return per_rabatt


def rabatt_per_kundgrupp(df):
    # Hur många ordrar varje kundgrupp har fått på varje rabattnivå.
    # Ger tillbaka (tabellen, rabattnivåerna i ordning som "0 %", "5 %" …).
    antal = df.groupby(["Discount_Percent", "Kundgrupp"]).size().reset_index(name="Ordrar")
    antal["Rabatt"] = antal["Discount_Percent"].astype(int).astype(str) + " %"
    nivaer = [f"{int(r)} %" for r in sorted(df["Discount_Percent"].unique())]
    return antal, nivaer


def frakt_andel_median(df):
    # Hur stor del av ordervärdet som går till frakt (mittenvärdet, påverkas inte av extremvärden),
    # för förlustordrar och för lönsamma ordrar
    frakt_andel = df["Shipping_Cost"] / df["Total_Sales"] * 100
    return frakt_andel[df["Förlust"]].median(), frakt_andel[~df["Förlust"]].median()


def forlust_per_ordervarde(df):
    # Andel förlustordrar (i procent) för varje storlek på ordern, t.ex. "Under $25"
    klass = pd.cut(df["Total_Sales"], VARDEGRANSER, labels=VARDEKLASSER)
    return (df["Förlust"].groupby(klass, observed=False).mean() * 100).fillna(0)


def forlust_per_kategori(df):
    # Andel förlustordrar (i procent) i varje kategori, minst först
    return (df["Förlust"].groupby(df["Kategori"]).mean() * 100).sort_values()


def flest_forlustordrar(forlust, antal=10):
    # De produkter som har flest förlustordrar, och hur mycket de förlorade tillsammans
    return forlust.groupby(["Product_Name", "Kategori"]).agg(
        Förlustordrar=("Order_ID", "nunique"), Förlorat=("Profit", "sum")).sort_values(
        "Förlustordrar", ascending=False).head(antal).reset_index()


# ===========================================================================
# FLIK: TÄNK OM … – prognoser
# ===========================================================================

def rabatttak(prognos, tak_grupper, tak):
    # Idé 1 (Johan): vad hade hänt om de valda kundgrupperna aldrig fått mer rabatt än taket?
    # Ger tillbaka (extra vinst, antal ordrar som påverkas, ny vinstmarginal).
    # Räkna om varje order: om kunden ingår och rabatten är högre än taket, sänk den till taket
    ny_rabatt = prognos["Discount_Percent"].where(~prognos["Kundgrupp"].isin(tak_grupper),
                                                  prognos["Discount_Percent"].clip(upper=tak))
    # Det vi slipper ge i rabatt (antal × pris × sänkt rabatt) blir extra försäljning och lika mycket extra vinst
    extra = (prognos["Quantity"] * prognos["Unit_Price"] * (prognos["Discount_Percent"] - ny_rabatt) / 100).sum()
    berorda = int((ny_rabatt < prognos["Discount_Percent"]).sum())
    ny_marginal = (prognos["Profit"].sum() + extra) / (prognos["Total_Sales"].sum() + extra) * 100
    return extra, berorda, ny_marginal


def fraktavgift(prognos, grans):
    # Idé 2 (Alyosh): vad hade hänt om ordrar under gränsen själva fick betala frakten?
    # Ger tillbaka (ny vinst per order, extra vinst, förlustordrar före, förlustordrar efter, vilka som påverkas).
    berorda = prognos["Total_Sales"] < grans
    ny_vinst = prognos["Profit"] + prognos["Shipping_Cost"].where(berorda, 0)   # frakten blir ingen kostnad för oss
    extra = ny_vinst.sum() - prognos["Profit"].sum()
    forlust_innan, forlust_efter = int((prognos["Profit"] < 0).sum()), int((ny_vinst < 0).sum())
    return ny_vinst, extra, forlust_innan, forlust_efter, berorda
