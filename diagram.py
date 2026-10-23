"""DIAGRAM: alla diagram och kartor i dashboarden.

Varje funktion tar emot färdigräknade siffror (från berakningar.py) och ger tillbaka
en Plotly-figur. Funktionerna visar inte figuren själva – det gör ui-filerna med visa().
Vill man ändra hur ett diagram ser ut (färger, höjd, text på staplarna) gör man det här.

Ordningen följer flikarna i dashboarden.
"""
import pandas as pd
import plotly.express as px         # gör interaktiva diagram och kartor
import plotly.graph_objects as go   # används när diagrammen behöver byggas del för del

from formatering import (pengar, pengar_exakt, period_text, procent, procent_andring, procentenheter, steg_text,
                         tal)
from installningar import (AXEL, BETALSATT_FARG, BLA, BLA_SKALA, GRA, KATEGORI_FARG, KATEGORIER, KORT,
                           KUNDGRUPP_FARG, KUNDGRUPPER, MANADER, MATT_FARG, REGION_FARG, ROD, TEXT, TEXT_SVAG,
                           RUTNAT)


# ===========================================================================
# GEMENSAMT UTSEENDE (används av alla diagram)
# ===========================================================================

def genomskinlig(farg, alfa):
    # "#3987e5" -> "rgba(57,135,229,0.15)": samma färg men genomskinlig, t.ex. för ytan under en linje
    r, g, b = (int(farg[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def snygga_till(fig, hojd=380, pengar_x=False, pengar_y=False):
    # Samma utseende på alla diagram: mörk stil, diskret rutnät, svenska tal
    fig.update_layout(
        height=hojd,
        margin=dict(l=10, r=10, t=40, b=10),
        separators=", ",                    # decimalkomma och mellanslag mellan tusental
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=TEXT_SVAG, size=13),
        title=dict(x=0, xanchor="left", font=dict(color=TEXT, size=15)),   # rubriken till vänster
        # förklaringen (vilken färg är vad) uppe till höger, så att den inte krockar med axeltexterna
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right",
                    title=None, font=dict(color=TEXT_SVAG)),
        hoverlabel=dict(bgcolor=KORT, bordercolor=AXEL, font=dict(color=TEXT, size=14)),
        paper_bgcolor="rgba(0,0,0,0)",      # genomskinlig bakgrund, så att sidans mörka färg syns
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.35,                        # smalare staplar med luft emellan
    )
    # Diskreta rutnätslinjer och axlar, så att datan står i fokus.
    # automargin gör plats för axeltexterna så att de inte klipps av.
    fig.update_xaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_x else "", tickfont=dict(color=TEXT_SVAG), title=None)
    fig.update_yaxes(gridcolor=RUTNAT, linecolor=AXEL, zeroline=False, tickformat=",.0f", automargin=True,
                     tickprefix="$" if pengar_y else "", tickfont=dict(color=TEXT_SVAG), title=None)
    return fig


def svenska_datum(fig, x, frekvens):
    # Svenska datum på tidsaxeln: högst cirka 8 etiketter så att de inte trängs
    etiketter = x[::max(1, len(x) // 8)]
    fig.update_xaxes(showgrid=False, tickvals=etiketter,
                     ticktext=[f"{MANADER[d.month - 1]} {d.year}" if frekvens == "MS"
                               else f"{d.day} {MANADER[d.month - 1]}" for d in etiketter],
                     hoverformat=" ")   # dölj den engelska rubriken i rutan, datumet står redan på svenska


def jamforelse_staplar(nu_varden, jmf_varden, format_, farg_karta, som_procentenheter=False, hojd=300):
    # Liggande staplar för t.ex. kundgrupper eller kategorier.
    # Utan jämförelse: en stapel per sak i sin egen färg.
    # Med jämförelse: blå stapel = vald period, grå = jämförelseperioden, och förändringen skrivs ut.
    tabell = pd.DataFrame({"Namn": nu_varden.index, "Nu": nu_varden.values}).sort_values("Nu")
    if jmf_varden is None:
        fig = px.bar(tabell, x="Nu", y="Namn", orientation="h", color="Namn", color_discrete_map=farg_karta,
                     text=tabell["Nu"].map(format_))
        fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>", textposition="outside",
                          cliponaxis=False, showlegend=False, textfont=dict(color=TEXT, size=13))
        bredd = tabell["Nu"].max() * 1.25   # plats till höger så att talen vid staplarna inte klipps av
    else:
        tabell["Innan"] = tabell["Namn"].map(jmf_varden).fillna(0)
        if som_procentenheter:
            andring = (tabell["Nu"] - tabell["Innan"]).map(procentenheter)
        else:
            andring = ((tabell["Nu"] / tabell["Innan"].where(tabell["Innan"] > 0) - 1) * 100).map(procent_andring)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=tabell["Namn"], x=tabell["Innan"], orientation="h", name="Jämförelse",
                             marker_color=GRA, customdata=tabell["Innan"].map(format_),
                             hovertemplate="%{y}<br>⚪ Jämförelse: %{customdata}<extra></extra>"))
        fig.add_trace(go.Bar(y=tabell["Namn"], x=tabell["Nu"], orientation="h", name="Vald period",
                             marker_color=BLA, text=tabell["Nu"].map(format_) + "  (" + andring.fillna("–") + ")",
                             textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
                             hovertemplate="%{y}<br>🔵 Vald period: %{text}<extra></extra>"))
        fig.update_layout(barmode="group", bargroupgap=0.1, legend=dict(traceorder="reversed"))
        bredd = max(tabell["Nu"].max(), tabell["Innan"].max()) * 1.9
    snygga_till(fig, hojd)
    fig.update_traces(marker_cornerradius=4)
    fig.update_xaxes(range=[0, bredd], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(tabell["Namn"]))
    return fig


def staplad_andel(tabell, kolumn, farger, hojd=320):
    # Liggande 100 %-staplar: en rad per region, uppdelad efter t.ex. kategori eller betalsätt.
    # tabell kommer från berakningar.andel_per_region().
    lang = tabell.reset_index().melt(id_vars="Region", var_name=kolumn, value_name="Andel")
    fig = px.bar(lang, x="Andel", y="Region", color=kolumn, orientation="h", color_discrete_map=farger,
                 category_orders={kolumn: list(tabell.columns)}, text=lang["Andel"].map(lambda v: f"{v:.0f} %"))
    # textangle=0: talen står alltid rakt. Får ett tal inte plats i sin del döljs det (uniformtext nedan).
    fig.update_traces(hovertemplate="%{y} · %{fullData.name}: %{x:.1f} %<extra></extra>", textangle=0,
                      textposition="inside", insidetextanchor="middle", textfont=dict(color="#ffffff", size=12))
    snygga_till(fig, hojd)
    fig.update_layout(barmode="stack", uniformtext_minsize=10, uniformtext_mode="hide", bargap=0.3)
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", showgrid=False)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(tabell.index))
    return fig


# ===========================================================================
# FLIK: FÖRSÄLJNING & TRENDER
# ===========================================================================

def utveckling_over_tid(serie_nu, serie_jmf, matt, frekvens, period, jamfor_period, flytt):
    # Linjediagram över tid för ett mått (försäljning, vinst, marginal eller ordrar).
    # Den valda perioden är en färgad linje, jämförelsen en streckad grå linje ovanpå samma datum.
    farg = MATT_FARG[matt]
    prefix = "$" if matt in ("Försäljning", "Vinst") else ""
    suffix = " %" if matt == "Marginal" else ""
    siffror = ".1f" if matt == "Marginal" else ",.0f"

    x = serie_nu.index
    fig = go.Figure()
    # Jämförelsen ritas först (streckad grå linje) så att den valda perioden hamnar ovanpå
    if serie_jmf is not None:
        fig.add_trace(go.Scatter(
            x=x, y=serie_jmf[matt], name=f"Jämförelse ({period_text(jamfor_period)})",
            mode="lines", line=dict(color=GRA, width=2, dash="dash"), connectgaps=True,
            customdata=[steg_text(d - pd.Timedelta(flytt), frekvens) for d in x],
            hovertemplate="⚪ %{customdata}: " + prefix + "%{y:" + siffror + "}" + suffix + "<extra></extra>"))
    # Den valda perioden: linje i måttets färg med fylld yta under
    fig.add_trace(go.Scatter(
        x=x, y=serie_nu[matt], name=f"Vald period ({period_text(period)})",
        mode="lines+markers" if len(x) <= 60 else "lines", connectgaps=True,
        line=dict(color=farg, width=3, shape="spline" if frekvens == "MS" else "linear", smoothing=0.5),
        marker=dict(size=7), fill="tozeroy", fillcolor=genomskinlig(farg, 0.15),
        customdata=[steg_text(d, frekvens) for d in x],
        hovertemplate="🔵 %{customdata}: " + prefix + "%{y:" + siffror + "}" + suffix + "<extra></extra>"))
    snygga_till(fig, hojd=380, pengar_y=prefix == "$")
    fig.update_layout(hovermode="x unified", legend=dict(traceorder="reversed"))
    svenska_datum(fig, x, frekvens)
    fig.update_yaxes(rangemode="tozero", ticksuffix=suffix)
    return fig


def forsaljning_per_ar(ar):
    # Staplar med försäljning (blå) och vinst (turkos) bredvid varandra för varje år
    fig = px.bar(ar, x="År", y=["Försäljning", "Vinst"], barmode="group", color_discrete_map=MATT_FARG)
    fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside", cliponaxis=False,
                      textfont=dict(color=TEXT, size=13), marker_cornerradius=4,
                      hovertemplate="%{x} – %{fullData.name}: $%{y:,.0f}<extra></extra>")
    snygga_till(fig, 340, pengar_y=True)
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(range=[0, ar["Försäljning"].max() * 1.18])   # plats för talen ovanför staplarna
    return fig


# ===========================================================================
# FLIK: PRODUKTER & KATEGORIER
# ===========================================================================

def topp_produkter(topp, matt):
    # Liggande staplar för de största produkterna, färgade efter kategori (störst överst)
    fig = px.bar(topp, x=matt, y="Product_Name", orientation="h", color="Kategori",
                 color_discrete_map=KATEGORI_FARG, text=topp[matt].map(pengar),
                 category_orders={"Kategori": list(KATEGORIER.values())})
    fig.update_traces(hovertemplate="%{y}: %{text}<extra></extra>", textposition="outside", cliponaxis=False,
                      textfont=dict(color=TEXT, size=13), marker_cornerradius=4)
    snygga_till(fig, 360)
    fig.update_xaxes(range=[0, topp[matt].max() * 1.25], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(topp["Product_Name"][::-1]))
    return fig


def produkt_over_tid(serie, frekvens):
    # Försäljning och vinst över tid för en enda produkt (två linjer)
    fig = go.Figure()
    for namn in ["Försäljning", "Vinst"]:
        fig.add_trace(go.Scatter(x=serie.index, y=serie[namn], name=namn, mode="lines+markers",
                                 line=dict(color=MATT_FARG[namn], width=3), marker=dict(size=6),
                                 customdata=[steg_text(d, frekvens) for d in serie.index],
                                 hovertemplate=namn + " %{customdata}: $%{y:,.0f}<extra></extra>"))
    snygga_till(fig, 300, pengar_y=True)
    fig.update_layout(hovermode="x unified")
    svenska_datum(fig, serie.index, frekvens)
    return fig


# ===========================================================================
# FLIK: GEOGRAFI & KUNDER
# ===========================================================================

def varldskarta(lander, matt, valt_land, med_jamforelse):
    # Världskarta där varje land färgas efter måttet. lander kommer från berakningar.per_land().
    # Förändring visas med två färger: blått = ökning, rött = minskning, grått = oförändrat.
    # Övriga mått visas från mörkblått (lite) till ljusblått (mycket).
    if matt == "Förändring (%)":
        # Ett land som gått från nästan inget till lite kan öka med flera tusen procent och göra
        # alla andra länder grå. Därför slutar färgskalan vid ±100 %.
        tak = min(100, max(10, lander["Förändring (%)"].abs().quantile(0.9)))
        farger = dict(color_continuous_scale=[[0, ROD], [0.5, "#383835"], [1, BLA]], range_color=[-tak, tak])
    else:
        farger = dict(color_continuous_scale=BLA_SKALA)

    # Texten om jämförelsen i rutan som visas när man håller musen över ett land
    lander = lander.assign(Jämförelse="")
    if med_jamforelse:
        lander["Jämförelse"] = [f"<br>⚪ Jämförelse: {pengar(i)} ({procent_andring(f)})" if pd.notna(i)
                                else "<br>⚪ Jämförelse: ingen försäljning"
                                for i, f in zip(lander["Innan"], lander["Förändring (%)"])]

    karta = px.choropleth(lander, locations="Landskod", color=matt, projection="natural earth",
                          custom_data=["Land", "Region", "Försäljning", "Vinst", "Marginal (%)", "Ordrar",
                                       "Jämförelse"], **farger)
    karta.update_traces(marker_line_color="rgba(11,14,20,0.9)", marker_line_width=0.6,
                        hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                                      "Försäljning: $%{customdata[2]:,.0f}<br>Vinst: $%{customdata[3]:,.0f}<br>"
                                      "Marginal: %{customdata[4]:.1f} %<br>Ordrar: %{customdata[5]}%{customdata[6]}"
                                      "<br><i>Klicka för att filtrera</i><extra></extra>")
    # Det valda landet får en tjock vit kant, så att man ser vilket land som är valt
    if valt_land:
        vald_kod = lander.loc[lander["Land"] == valt_land, "Landskod"].iloc[0]
        karta.add_trace(go.Choropleth(locations=[vald_kod], z=[1], showscale=False, hoverinfo="skip",
                                      colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                      marker_line_color="#ffffff", marker_line_width=2.5))
    karta.update_geos(
        showframe=False, showcoastlines=False, showcountries=True, countrycolor="rgba(255,255,255,0.08)",
        showland=True, landcolor="#1a202b", showocean=False, bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85],   # klipp bort Antarktis så att kartan blir större
    )
    snygga_till(karta, hojd=480)
    karta.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar=dict(
        title=dict(text=matt, font=dict(color=TEXT_SVAG)), thickness=10, len=0.6, outlinewidth=0,
        tickformat=",.0f", tickprefix="$" if matt in ("Försäljning", "Vinst") else "",
        ticksuffix=" %" if "%" in matt else "", tickfont=dict(color=TEXT_SVAG)))
    return karta


def topplista_lander(visas, valt_land):
    # Liggande staplar för länderna med mest försäljning. Varje land har sin regions färg.
    # Är ett land valt lyser det, och övriga dämpas.
    farg = [genomskinlig(REGION_FARG[region], 1 if valt_land in (None, land) else 0.3)
            for land, region in zip(visas["Land"], visas["Region"])]
    fig = go.Figure(go.Bar(
        y=visas["Land"], x=visas["Försäljning"], orientation="h", marker_color=farg,
        marker_cornerradius=4, text=visas["Försäljning"].map(pengar), textposition="outside",
        cliponaxis=False, textfont=dict(color=TEXT, size=13),
        customdata=visas[["Plats", "Region", "Marginal (%)"]].values,
        hovertemplate="<b>%{y}</b> · nr %{customdata[0]} · %{customdata[1]}<br>"
                      "Försäljning: %{text}<br>Marginal: %{customdata[2]:.1f} %<br>"
                      "<i>Klicka för att filtrera</i><extra></extra>"))
    snygga_till(fig, 360)
    fig.update_xaxes(range=[0, visas["Försäljning"].max() * 1.3], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return fig


def frakt_per_region(frakt):
    # Liggande staplar: hur stor del av försäljningen som går till frakt i varje region
    fig = go.Figure(go.Bar(
        y=frakt["Region"], x=frakt["Andel"], orientation="h", marker_cornerradius=4,
        marker_color=[REGION_FARG[region] for region in frakt["Region"]],
        text=[f"{procent(a)}  ·  {pengar_exakt(s)} per order" for a, s in zip(frakt["Andel"], frakt["Snitt"])],
        textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
        hovertemplate="%{y}: %{text}<extra></extra>"))
    snygga_till(fig, 300)
    fig.update_xaxes(range=[0, frakt["Andel"].max() * 1.9], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return fig


# ===========================================================================
# FLIK: BETALNING
# ===========================================================================

def betalsatt_cirkel(antal):
    # Ringdiagram med andelen ordrar per betalsätt, och antalet ordrar i mitten
    betalsatt = list(antal.index)
    fig = go.Figure(go.Pie(
        labels=betalsatt, values=antal, hole=0.55, sort=False, direction="clockwise",
        marker=dict(colors=[BETALSATT_FARG[b] for b in betalsatt], line=dict(color="#0b0e14", width=2)),
        texttemplate="%{percent:.0%}", textfont=dict(color="#ffffff", size=14),
        hovertemplate="%{label}: %{percent:.1%} (%{value} ordrar)<extra></extra>"))
    snygga_till(fig, 340)
    # Antal ordrar i mitten av cirkeln, och förklaringen av färgerna till höger
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="v", y=0.5, yanchor="middle", x=1.02, xanchor="left"),
                      annotations=[dict(text=f"<b>{tal(antal.sum())}</b><br>ordrar", showarrow=False,
                                        font=dict(color=TEXT, size=16), x=0.5, y=0.5, xref="paper", yref="paper")])
    return fig


# ===========================================================================
# FLIK: RABATTER & FÖRLUSTORDRAR
# ===========================================================================

def marginal_per_rabatt(per_rabatt):
    # Stående staplar: vinstmarginalen för varje rabattnivå
    fig = go.Figure(go.Bar(
        x=per_rabatt["Rabatt"], y=per_rabatt["Marginal"], marker_color=MATT_FARG["Marginal"],
        marker_cornerradius=4, text=per_rabatt["Marginal"].map(procent), textposition="outside",
        cliponaxis=False, textfont=dict(color=TEXT, size=13), customdata=per_rabatt["Ordrar"],
        hovertemplate="%{x} rabatt: marginal %{text} (%{customdata} ordrar)<extra></extra>"))
    snygga_till(fig, 320)
    fig.update_xaxes(type="category", showgrid=False, title="Rabatt")
    fig.update_yaxes(range=[0, max(per_rabatt["Marginal"].max(), 1) * 1.2], ticksuffix=" %")
    return fig


def rabatt_per_kundgrupp(antal, nivaer):
    # Staplade staplar: hur många ordrar som fått varje rabattnivå, uppdelat på kundgrupp
    fig = px.bar(antal, x="Rabatt", y="Ordrar", color="Kundgrupp", color_discrete_map=KUNDGRUPP_FARG,
                 category_orders={"Rabatt": nivaer, "Kundgrupp": list(KUNDGRUPPER.values())})
    fig.update_traces(marker_cornerradius=3,
                      hovertemplate="%{x} rabatt · %{fullData.name}: %{y} ordrar<extra></extra>")
    snygga_till(fig, 320)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category", showgrid=False, title="Rabatt")
    return fig


def forlust_per_ordervarde(per_klass):
    # Stående röda staplar: andel förlustordrar för varje storlek på ordern
    fig = go.Figure(go.Bar(
        x=per_klass.index.astype(str), y=per_klass.values, marker_color=ROD, marker_cornerradius=4,
        text=[f"{v:.0f} %" for v in per_klass.values], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT, size=13), hovertemplate="%{x}: %{text} går med förlust<extra></extra>"))
    snygga_till(fig, 320)
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(range=[0, max(per_klass.max() * 1.25, 10)], showticklabels=False, showgrid=False)
    return fig


def forlust_per_kategori(per_kat):
    # Liggande staplar: andel förlustordrar i varje kategori, i kategorins färg
    fig = go.Figure(go.Bar(
        y=per_kat.index, x=per_kat.values, orientation="h", marker_cornerradius=4,
        marker_color=[KATEGORI_FARG[k] for k in per_kat.index], text=[procent(v) for v in per_kat.values],
        textposition="outside", cliponaxis=False, textfont=dict(color=TEXT, size=13),
        hovertemplate="%{y}: %{text} av ordrarna går med förlust<extra></extra>"))
    snygga_till(fig, 320)
    fig.update_xaxes(range=[0, max(per_kat.max(), 1) * 1.3], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return fig
