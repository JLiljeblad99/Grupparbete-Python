"""FORMATERING: hur tal, belopp, procent och datum skrivs ut på sidan.

Alla funktioner här tar ett värde och ger tillbaka en färdig text på svenska,
t.ex. 137006.2 -> "$137 006". Ingen av dem räknar på datan eller ritar något.
"""
from installningar import MANADER, MANADER_LANGA

# Ett "hårt" mellanslag: ser ut som ett vanligt, men webbläsaren bryter aldrig raden där.
# Används mellan tusental ("484 559") och före procenttecknet ("33,8 %"), så att talen hålls ihop.
HART_MELLANSLAG = "\u00a0"


# ===========================================================================
# TAL, BELOPP OCH PROCENT
# ===========================================================================

def tal(varde, decimaler=0):
    # Svenskt sätt: 484559.3 -> "484 559". Mellanslaget är "hårt" så att talet aldrig delas på två rader.
    return f"{varde:,.{decimaler}f}".replace(",", HART_MELLANSLAG).replace(".", ",")


def pengar(varde, decimaler=0):
    # Belopp i dollar: 137006.2 -> "$137 006". Minustecknet hamnar före $: -953 -> "-$953".
    return f"-${tal(-varde, decimaler)}" if varde < 0 else f"${tal(varde, decimaler)}"


def pengar_exakt(varde):
    # Belopp med cent, för små belopp: 12.345 -> "$12,35"
    return pengar(varde, 2)


def procent(varde):
    # Procent med en decimal: 33.84 -> "33,8 %"
    return f"{tal(varde, 1)}{HART_MELLANSLAG}%"


def procent_andring(varde):
    # Som procent(), men alltid med + eller - framför: 12.34 -> "+12,3 %"
    return ("+" if varde >= 0 else "") + procent(varde)


def procentenheter(varde):
    # Skillnaden mellan två procenttal: 33,1 % mot 30,4 % -> "+2,7 %-enh." (procentenheter)
    return ("+" if varde >= 0 else "") + f"{tal(varde, 1)}{HART_MELLANSLAG}%-enh."


def forandring(nu, forut):
    # Hur mycket något har ändrats i procent, t.ex. "+12,0 %". None om det inte går att räkna.
    # abs() gör att en vinst som går från -100 till +50 räknas som en ökning, inte en minskning.
    return procent_andring((nu - forut) / abs(forut) * 100) if forut else None


# ===========================================================================
# DATUM
# ===========================================================================

def datum_text(dag):
    # Skriver ett datum på svenska: 2023-01-02 -> "2 jan 2023"
    return f"{dag.day} {MANADER[dag.month - 1]} {dag.year}"


def period_text(period):
    # En period med start och slut: "1 jan 2025 – 31 dec 2025"
    return f"{datum_text(period[0])} – {datum_text(period[1])}"


def steg_text(dag, frekvens):
    # Hur en punkt i ett tidsdiagram beskrivs i text. frekvens är "D" (dag), "7D" (vecka) eller "MS" (månad).
    # T.ex. "3 okt 2025", "veckan från 3 okt 2025" eller "oktober 2025".
    if frekvens == "MS":
        return f"{MANADER_LANGA[dag.month - 1]} {dag.year}"
    text = datum_text(dag.date())
    return f"veckan från {text}" if frekvens == "7D" else text


# ===========================================================================
# TEXT PÅ SIDAN
# ===========================================================================

def html_text(text):
    # "$" kan av misstag tolkas som en matteformel på sidan. &#36; är samma tecken skrivet som HTML.
    return text.replace("$", "&#36;")
