"""INSTÄLLNINGAR: färger, svenska namn och standardval.

Här finns bara fasta värden (konstanter), ingen kod som räknar eller ritar något.
Alla andra filer hämtar sina färger och namn härifrån, så att samma sak ser likadan
ut i hela dashboarden. Vill man byta en färg eller ett namn räcker det att ändra här.
"""

# ===========================================================================
# FÄRGER
# ===========================================================================

# Fasta färger som används i hela dashboarden. Samma sak har alltid samma färg, i alla flikar.
# Färgerna är anpassade för mörk bakgrund och går att skilja åt även för färgblinda.
BLA, ORANGE, TURKOS, GUL, LILA = "#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9"
GRA = "#898781"   # jämförelseperioden är alltid grå
ROD = "#d03b3b"   # används bara för förlust och minskning, så att rött alltid betyder "dåligt"

# Diagrammens "ram": textfärg, svagare text, rutnät, axlar och bakgrund till hjälprutor
TEXT, TEXT_SVAG, RUTNAT, AXEL, KORT = "#e8eaf0", "#a3a8b4", "#232a36", "#2f3746", "#151a23"

# Skala från mörkblått (lite) till ljusblått (mycket). På mörk bakgrund lyser "mycket" starkast.
BLA_SKALA = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]

# Färg för varje mått: försäljning är alltid blå, vinst turkos (grön = pengar in), marginal lila
MATT_FARG = {"Försäljning": BLA, "Vinst": TURKOS, "Marginal": LILA, "Ordrar": GUL}


# ===========================================================================
# SVENSKA NAMN
# ===========================================================================

# Datan är på engelska. Här översätter vi till svenska så att alla förstår.
REGIONER = {
    "Europe": "Europa",
    "North America": "Nordamerika",
    "Asia Pacific": "Asien & Stillahavet",
    "South America": "Sydamerika",
    "Middle East & Africa": "Mellanöstern & Afrika",
}
KUNDGRUPPER = {
    "Consumer": "Privatpersoner",
    "Corporate": "Företag",
    "Home Office": "Småföretag",
}
BETALSATT = {
    "Credit Card": "Kreditkort",
    "PayPal": "PayPal",
    "Cash on Delivery": "Betala vid leverans",
    "Bank Transfer": "Banköverföring",
}
KATEGORIER = {
    "Furniture": "Möbler",
    "Technology": "Teknik",
    "Clothing & Accessories": "Kläder",
    "Office Supplies": "Kontorsmaterial",
}
# Svenskt namn + landskod (koden behövs för att kartan ska veta var landet ligger)
LANDER = {
    "Argentina": ("Argentina", "ARG"), "Australia": ("Australien", "AUS"),
    "Brazil": ("Brasilien", "BRA"), "Canada": ("Kanada", "CAN"),
    "China": ("Kina", "CHN"), "Colombia": ("Colombia", "COL"),
    "France": ("Frankrike", "FRA"), "Germany": ("Tyskland", "DEU"),
    "India": ("Indien", "IND"), "Italy": ("Italien", "ITA"),
    "Japan": ("Japan", "JPN"), "Mexico": ("Mexiko", "MEX"),
    "Nigeria": ("Nigeria", "NGA"), "Saudi Arabia": ("Saudiarabien", "SAU"),
    "South Africa": ("Sydafrika", "ZAF"), "South Korea": ("Sydkorea", "KOR"),
    "Spain": ("Spanien", "ESP"), "UAE": ("Förenade Arabemiraten", "ARE"),
    "United Kingdom": ("Storbritannien", "GBR"), "United States": ("USA", "USA"),
}
KOD_TILL_LAND = {kod: namn for namn, kod in LANDER.values()}   # t.ex. "MEX" -> "Mexiko"

MANADER = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
MANADER_LANGA = ["januari", "februari", "mars", "april", "maj", "juni",
                 "juli", "augusti", "september", "oktober", "november", "december"]

# Koppla varje region, kundgrupp osv. till sin fasta färg. Samma ordning överallt:
# första saken i en grupp är blå, den andra orange, den tredje turkos osv.
REGION_FARG = dict(zip(REGIONER.values(), [BLA, ORANGE, TURKOS, GUL, LILA]))
KUNDGRUPP_FARG = dict(zip(KUNDGRUPPER.values(), [BLA, ORANGE, TURKOS]))
BETALSATT_FARG = dict(zip(BETALSATT.values(), [BLA, ORANGE, TURKOS, GUL]))
KATEGORI_FARG = dict(zip(KATEGORIER.values(), [BLA, ORANGE, TURKOS, GUL]))

# Gränserna för ordervärde som förlustordrarna delas in efter. float("inf") = "allt över 250".
VARDEGRANSER = [0, 25, 50, 100, 250, float("inf")]
VARDEKLASSER = ["Under $25", "$25–50", "$50–100", "$100–250", "Över $250"]


# ===========================================================================
# FILTER OCH STANDARDVAL I SIDOPANELEN
# ===========================================================================

ALLA_LANDER = "Alla länder"   # första valet i land-filtret

# Alla namn som går att välja i filtren. En tom lista i ett filter betyder "alla de här".
ALLA_NAMN = {"region": list(REGIONER.values()), "kundgrupp": list(KUNDGRUPPER.values()),
             "kategori": list(KATEGORIER.values())}

# Snabbvalen för datum och jämförelse, som i Google Ads
SNABBVAL = ["Senaste 7 dagarna", "Senaste 30 dagarna", "Senaste 90 dagarna", "Denna månad",
            "Förra månaden", "Detta kvartal", "Förra kvartalet", "I år", "Förra året",
            "Hela perioden", "Anpassat"]
JAMFOR_VAL = ["Föregående period", "Samma period förra året", "Anpassat"]
STANDARD_SNABBVAL = "Hela perioden"   # en översikt ska visa allt från början
STANDARD_JAMFOR = "Samma period förra året"
