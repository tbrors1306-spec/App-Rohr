"""Referenz- und Lerninhalte für das Fallnaht-Schweißen (Stovepipe) mit
zellulose-umhüllten Elektroden (E6010 / E7010 / E8010 – Handelsname z. B. CEL 70).

Alle Zahlen sind Richtwerte aus Handbüchern und der Praxis (API 1104 / ISO 13847).
Die freigegebene WPS des Projekts hat immer Vorrang.
"""

# --------------------------------------------------------------------- Text --
CEL_OVERVIEW = """
**Fallnaht / Stovepipe** ist das klassische Baustellen-Verfahren für Rundnähte an
Fernleitungen: Elektrodenhandschweißen (E, SMAW) in **Fallposition** (5G / PG),
also von 12 Uhr nach 6 Uhr abwärts, meist von zwei Schweißern gleichzeitig.

**Zellulose-Elektrode (E xx10):** Die Umhüllung enthält viel organisches Material.
Beim Abbrennen entsteht ein kräftiger, gasreicher Lichtbogen (H₂, CO, CO₂) mit
**tiefem Einbrand** und **schnell erstarrender, dünner Schlacke** – dadurch lässt
sich zügig fallend schweißen und der Wurzelspalt gut überbrücken.

**Polarität:** Gleichstrom. Das klassische E 6010 / FOX CEL läuft **DC+**. Die
höherfesten Pipeline-Grades (**Böhler FOX CEL 70 / 75 / 80 / 90**) sind für **beide
Polaritäten** ausgelegt – hier gilt laut Datenblatt: **Wurzel DC− (Minuspol,
Herstellerempfehlung)**, Heiß-, Füll- und Decklage **DC+**. DC− an der Wurzel bringt
weniger Wärme ins Rohr → weichere, spaltüberbrückende Wurzel mit weniger
Durchbrand und weniger innerer Wurzelkerbe. **Immer nach freigegebener WPS** –
Polarität ist eine wesentliche Variable.

| Vorteile | Nachteile |
|---|---|
| Sehr schnell, hohe Nahtleistung | Hoher diffusibler Wasserstoff → Kaltrissgefahr |
| Tiefer Einbrand, spaltüberbrückend | Vorwärmen + Zwischenlagen-Kontrolle nötig |
| Wenig Ausrüstung, windunempfindlicher als MAG | Für X70/X80 und dickwandig nur mit strenger Kontrolle |
| Wurzel von innen sichtbar sauber | Elektroden feuchte-empfindlich (nicht wie basisch rücktrocknen!) |

Üblich bis **X60 (L415)**; auf X70 möglich, aber nicht erste Wahl. Für Füll- und
Decklagen wird bei dickeren Wänden oft auf basisch (E7018) oder Fülldraht gewechselt,
weil die Rissneigung der Zellulose-Elektrode dort steigt.
"""

CEL_STORAGE = """
**Zellulose-Elektroden brauchen einen Rest an Feuchte in der Umhüllung** (Herstellerangabe,
oft 3–5 %). Deshalb gilt – anders als bei basischen Elektroden:

- **Nicht im Rücktrockenofen backen.** Zu trocken = schlechtes Zündverhalten, Spritzer,
  Poren, teils höhere Rissneigung.
- Original verpackt und trocken bei Raumtemperatur lagern; angebrochene Pakete zeitnah
  verbrauchen.
- Leicht feucht gewordene Elektroden nur nach Herstellerfreigabe mild rekonditionieren
  (z. B. ca. 70 °C). Verklebte, aufgequollene oder abgeplatzte Umhüllung → aussortieren.
- Kerndraht darf nicht rosten – rostige Enden abknipsen.
"""

CEL_SAFETY = """
- **Stromschlag:** DC-Leerlaufspannung 50–90 V. Trockene Handschuhe, isolierter Stand,
  Werkstück sauber erden.
- **Rauch/Gase:** In Rohrgräben und im Rohr schlechte Luft – für Absaugung/Frischluft sorgen.
- **UV/IR:** Zwei Schweißer über Kreuz – gegenseitige Blendung, Schweißvorhänge nutzen.
- **Graben:** Verbau / Grabensicherung, Rohr gegen Abrollen sichern, Fluchtweg frei halten.
- **Brand:** Umhüllung glüht ab, heiße Stummel – Eimer statt Boden.
"""

# ---------------------------------------------------------- Nahtvorbereitung --
# key: (Richtwert, Erklärung / Wirkung)
CEL_JOINT = {
    "Öffnungswinkel gesamt": ("60°",
        "Je Flanke 30°. Enger Spalt spart Fülllagen über tausende Nähte. "
        "Zu eng → Bindefehler an den Flanken, zu weit → viel Füllvolumen und Verzug."),
    "Steg / Land (root face)": ("1,6 mm (Bereich 0,8–1,6 mm)",
        "Stehende Kante an der Wurzel. Zu klein → Durchbrand / großes Keyhole; "
        "zu groß → mangelnder Wurzeleinbrand, Bindefehler."),
    "Wurzelspalt / Gap (root opening)": ("1,6 mm (Bereich 1,6–2,4 mm)",
        "Abstand der Stege. Steuert die Keyhole-Größe. Zu groß → Durchhang / Fenster; "
        "zu klein → keine durchgehende Wurzel."),
    "Kantenversatz Hi-Lo (innen)": ("max. 1,6 mm",
        "Höhenversatz der Innenkanten. Sonst einseitige Wurzelkerbe und Bindefehler. "
        "Mit Innen-/Außenspanner (line-up clamp) ausrichten."),
    "Blanke Fügezone": ("je 25 mm metallisch blank",
        "Rost, Beschichtung, Farbe, Fett, Feuchte vor dem Heften restlos entfernen – "
        "sonst Poren und Wasserstoff."),
}
# API 1104 heißt bei Rohrleitungsschweißern „the sixteenth-inch code": fast jedes
# kritische Maß ist 1/16" = 1,6 mm.

# ------------------------------------------------------------------- Lagen ----
# Reihenfolge, Technik, Elektrode, Strom-Tendenz, Zweck / Hinweise
CEL_PASSES = [
    {
        "Lage": "Wurzel (root / stringer)",
        "Elektrode": "2,5 oder 3,25 mm",
        "Strom": "niedrig–mittel",
        "Technik": "Ziehen (drag), kurzer Lichtbogen, Umhüllung berührt beide Kanten. "
                   "Gleichmäßiges Keyhole ca. 4–5 mm halten; öffnet es zu weit → Rod "
                   "vom Keyhole wegkippen oder kurz absetzen.",
        "Zweck": "Durchgehende, wurzelseitig glatte Bindung. Innen-Spanner erst lösen, "
                 "wenn ≥ 50–100 % der Wurzel fertig sind (je nach WPS / Restraint).",
    },
    {
        "Lage": "Heißlage (hot pass)",
        "Elektrode": "3,25 oder 4,0 mm",
        "Strom": "höchster Wert",
        "Technik": "Schnell, heiß, flache Raupe. **Sofort nach der Wurzel** schweißen, "
                   "solange die Wurzel noch warm ist (Zwischenlagentemperatur halten).",
        "Zweck": "Schmilzt Wurzelfehler, Poren und Schlackenreste ein; beugt "
                 "'wagon tracks' (Längsschlacke neben der Wurzel) und Wasserstoffrissen vor.",
    },
    {
        "Lage": "Fülllagen (fill)",
        "Elektrode": "4,0 (–5,0) mm",
        "Strom": "mittel",
        "Technik": "Strichraupen oder leichtes Pendeln, jede Lage vollständig entschlacken, "
                   "bei Bedarf Anschlüsse verschleifen. Flanken sauber ausschmelzen.",
        "Zweck": "Querschnitt auffüllen. Anzahl nach Wandstärke (Faustwert unten).",
    },
    {
        "Lage": "Decklage (cap)",
        "Elektrode": "4,0 (–5,0) mm",
        "Strom": "mittel",
        "Technik": "Gleichmäßiges Pendeln, an den Nahträndern kurz stehen bleiben "
                   "(kein Einbrandkerben), 1–2 mm Überhöhung, Übergang flach.",
        "Zweck": "Endkontur, Nahtüberhöhung und Randkerbfreiheit nach Abnahmekriterien.",
    },
]

# ------------------------------------------------------------- Elektrodenwinkel
CEL_ANGLES = {
    "Arbeitswinkel (work angle)":
        "In der Fuge mittig, also ~90° zur Rohroberfläche / Winkelhalbierende der V-Fuge. "
        "In steilen Positionen (3–6 Uhr) 5–10° zur schon geschweißten Seite kippen, um "
        "Wurzelkerben zu vermeiden.",
    "Schleppwinkel Wurzel (drag/travel angle)":
        "Elektrode fast senkrecht zur Rohrachse, 5–15° schleppend (entgegen der "
        "Laufrichtung). Am 3-Uhr-Punkt bis ~30° – der genaue Wert hängt von Stromstärke "
        "und Rohrverhalten ab.",
    "Schleppwinkel Heiß-/Füll-/Decklage":
        "10–20° schleppend, etwas flacher als die Wurzel.",
    "Lichtbogenlänge":
        "Sehr kurz – 'drag rod': Umhüllungskante schleift auf dem Werkstück, Kernstab "
        "fast aufliegend. Langer Lichtbogen = Poren + Spritzer.",
    "Laufrichtung / Uhrzeit":
        "Immer 12 → 6 Uhr (fallend). Zwei Schweißer je eine Rohrhälfte. Start knapp "
        "vor 12 Uhr (nicht exakt am Scheitel), Wechsel der Körperhaltung bei ~3 Uhr.",
    "Neu ansetzen (restart)":
        "Zünden ~10 mm vor dem Kraterende, zurück zum Krater fahren, kurz auffüllen, "
        "dann weiter – vermeidet Zündporen und Bindefehler.",
}

# -------------------------------------------------------- Strom-Richtwerte ----
# Ampere, Zellulose E6010 / E8010-Klasse. Polaritaet: Wurzel DC-, sonst DC+
# (Pipeline-Grades wie FOX CEL 70), klassisches E6010 durchgehend DC+.
CEL_AMPERAGE = [
    {"Elektrode Ø": '2,5 mm (3/32")', "Wurzel": "40–75 A",  "Heißlage": "55–90 A",   "Füll / Deck": "50–85 A"},
    {"Elektrode Ø": '3,25 mm (1/8")', "Wurzel": "70–115 A", "Heißlage": "120–160 A", "Füll / Deck": "90–140 A"},
    {"Elektrode Ø": '4,0 mm (5/32")', "Wurzel": "–",         "Heißlage": "140–185 A", "Füll / Deck": "110–175 A"},
    {"Elektrode Ø": '5,0 mm (3/16")', "Wurzel": "–",         "Heißlage": "–",          "Füll / Deck": "140–215 A"},
]
CEL_AMPERAGE_NOTE = (
    "**Spannweite in der Tabelle:** unteres Ende = Wurzel sichern, dünne Wand, weiter "
    "Spalt oder Abschnitt Richtung 6 Uhr / Überkopf; oberes Ende = dicke Wand, enger "
    "Spalt, mehr Abschmelzleistung, Abschnitt um 12 Uhr. Beim Fallnahtschweißen wird der "
    "Strom relativ hoch eingestellt und von 12 → 6 Uhr nur wenig verändert – die "
    "Feinabstimmung läuft über Brenngeschwindigkeit und Elektrodenhaltung, nicht über "
    "große Stromsprünge.\n\n"
    "**Spannung:** Beim E-Handschweißen wird die Spannung nicht am Gerät eingestellt – "
    "sie ergibt sich aus der Lichtbogenlänge. Zellulose läuft mit hoher "
    "Lichtbogenspannung, typisch **26–40 V**; diesen Wert für die Streckenenergie-"
    "Rechnung verwenden.\n\n"
    "Grober Startwert: ~**30–40 A je mm Kerndraht** (z. B. 3,25 mm → rund 100–130 A), "
    "dann nach Nahtbild feinjustieren.\n\n"
    "**Polarität:** Bei den Pipeline-Grades (FOX CEL 70/75/80/90) die **Wurzel auf "
    "DC−** (Elektrode an Minus), Heiß-/Füll-/Decklage auf **DC+**. Klassisches E 6010 "
    "durchgehend DC+. Maßgeblich ist die WPS."
)

# -------------------------------------------- Strom <-> Wurzelspalt / Keyhole --
# Richtwerte Wurzelstrom (fallend) je Elektrodendurchmesser und Spaltweite.
# Grundregel: enger Spalt -> mehr Strom, weiter Spalt -> weniger Strom.
CEL_CURRENT_GAP = [
    {"Elektrode Ø": '2,5 mm (3/32")',
     "Spalt eng ~1,5 mm": "60–75 A", "Spalt normal ~1,6–2,4 mm": "45–65 A",
     "Spalt weit >2,4 mm": "40–55 A", "Keyhole-Ziel": "~3–4 mm"},
    {"Elektrode Ø": '3,25 mm (1/8")',
     "Spalt eng ~1,5 mm": "95–115 A", "Spalt normal ~1,6–2,4 mm": "80–100 A",
     "Spalt weit >2,4 mm": "70–90 A", "Keyhole-Ziel": "~4–5 mm"},
    {"Elektrode Ø": '4,0 mm (5/32")',
     "Spalt eng ~1,5 mm": "130–150 A", "Spalt normal ~1,6–2,4 mm": "110–135 A",
     "Spalt weit >2,4 mm": "95–120 A", "Keyhole-Ziel": "~5–6 mm"},
]
CEL_CURRENT_GAP_NOTE = (
    "**Faustregel:** enger Spalt / dicker Steg → **mehr Strom** (sonst kein "
    "Wurzeleinbrand). Weiter Spalt / dünner Steg → **weniger Strom** (sonst "
    "Durchbrand). Allein die Fit-up kann den Strombedarf um **± 25 A** verschieben. "
    "Der Steg (feather edge) wirkt wie zusätzlicher Spalt.\n\n"
    "Der **Strom ist nicht die Stellgröße – das Keyhole ist es.** Strom grob nach "
    "Tabelle wählen, dann über Brenngeschwindigkeit und Elektrodenhaltung ein "
    "gleichmäßiges Keyhole halten. Bei DC− fühlt sich der Lichtbogen weicher an; "
    "nicht nach der Anzeige, nach dem Keyhole regeln."
)
CEL_KEYHOLE = {
    "Gutes Keyhole": "Kleines, gleichmäßiges Loch vor dem Bad, ~1× bis knapp über "
                     "Elektrodendurchmesser. Bleibt über die ganze Wurzel gleich groß.",
    "Keyhole wird zu groß": "Strom zu hoch / zu langsam / Spalt hat sich geöffnet. "
                            "Abhilfe: Tempo raus, Strom 5–10 A runter, Elektrode kurz "
                            "vom Keyhole wegkippen; bei Bedarf absetzen und neu "
                            "ansetzen (Back-step).",
    "Keyhole schließt sich / verschwindet": "Strom zu niedrig / zu schnell / Spalt zu "
                            "eng / Steg zu dick. Abhilfe: langsamer, Strom 5–10 A "
                            "hoch, Lichtbogen fester in die Wurzelkante drücken.",
    "Keyhole eiert / unregelmäßig": "Ungleiche Fit-up (Hi-Lo, wechselnder Spalt) oder "
                            "unruhige Hand. Fit-up prüfen, sonst gleichmäßig ziehen "
                            "und die Größe über das Tempo ausgleichen.",
}

CEL_HOTPASS_TIMING = (
    "**Zeit Wurzel → Heißlage ist eine wesentliche WPS-Variable** (API 1104 § 5.4.2.8) "
    "– der genaue Wert steht in eurer WPS. Praxis-Richtwerte:\n\n"
    "- **Heißlage innerhalb ~15 min** nach der Wurzel, solange die Wurzel noch über "
    "Vorwärm-/Zwischenlagentemperatur ist.\n"
    "- Erste **Fülllage innerhalb ~30 min** nach der Heißlage.\n"
    "- Vorher **Wurzel komplett entschlacken und schleifen** (Schlackenzeilen / "
    "'wagon tracks' raus) – sonst Einschlüsse und Wasserstoffrisse.\n"
    "- Reißt das Zeitfenster (Schichtende, Regen, fehlende Elektroden): Naht "
    "**nicht offen liegen lassen** – nach WPS abdecken oder abbrechen und "
    "dokumentieren."
)

CEL_WEATHER = (
    "**Wind:** Zellulose ist windunempfindlicher als MAG (kein Schutzgas), trotzdem "
    "ab ~stärkerem Wind Schweißvorhang / Zelt – sonst Poren und Kaltstellen.\n\n"
    "**Nässe:** Nicht auf nassem oder betautem Rohr schweißen. Fuge und je 75 mm "
    "daneben trocknen; das Vorwärmen dient auch dazu, Restfeuchte auszutreiben.\n\n"
    "**Kälte:** Bei niedriger Umgebungstemperatur Vorwärmtemperatur höher ansetzen "
    "(reale Bauteiltemperatur zählt). Elektroden warm und trocken transportieren."
)

# -------------------------------------------- Führungstechnik / Raupenform ----
# Elektrodenführung je Lage (Fallnaht). Grundregel: Wurzel ziehen, nicht pendeln.
CEL_TRAVEL = [
    {"Lage": "Wurzel",
     "Technik": "Ziehen (Drag) – durchgehend",
     "Bewegung": "keine Seitwärtsbewegung; Lichtbogen auf der Vorderkante des Bades, "
                 "Tempo so, dass das Keyhole gleich groß bleibt",
     "Ausweichtechnik": "in schwierigen Abschnitten kurzer Whip (1–2× Ø vor, kurze "
                        "Pause, zurück ins Bad). Kein breites Pendeln – lässt Luft/"
                        "Schlacke rein (Poren, wagon tracks)."},
    {"Lage": "Heißlage",
     "Technik": "Ziehen oder leichter Whip",
     "Bewegung": "flach und schnell, meist Strichraupe; heiß genug, um die Wurzel "
                 "wieder aufzuschmelzen",
     "Ausweichtechnik": "leichtes Zickzack, wenn die Wurzel breit ist"},
    {"Lage": "Fülllagen",
     "Technik": "Strichraupen (mehrere nebeneinander) oder Whip & Pause",
     "Bewegung": "Pendelbreite ≤ ~3 × Elektroden-Ø; bei dicker Wand lieber 2–3 "
                 "schmale Strichraupen als eine breite Pendelraupe",
     "Ausweichtechnik": "Halbmond bei mittlerer Breite"},
    {"Lage": "Decklage",
     "Technik": "Halbmond (Sichel), Zickzack oder J-Technik",
     "Bewegung": "an jedem Nahtrand kurz stehen bleiben (Kerbfreiheit), gleichmäßig, "
                 "1–2 mm Überhöhung; Pendelbreite = Fuge + ~1,5 mm je Seite",
     "Ausweichtechnik": "mehrere Strichraupen ('Stripper' + Decklage) statt Pendeln"},
]

# Führung je Uhrposition (5G fallend, 12 -> 6 Uhr)
CEL_CLOCK_TECHNIQUE = {
    "12:00 Scheitel (flach)":
        "Elektrode fast senkrecht, zügiger Drag. Füll-/Decklage darf hier am "
        "breitesten pendeln.",
    "1:30":
        "Leichter Schleppwinkel, weiter Drag; Bewegung noch klein.",
    "3:00 Flanke (senkrecht)":
        "Mehr Schleppwinkel. Kleine Halbmond-/Seitwärtsbewegung, um beide Kanten zu "
        "benetzen. Auf Einbrandkerbe an der unteren Flanke achten – Elektrode leicht "
        "zur schon geschweißten (oberen) Seite kippen.",
    "4:30":
        "Das Bad will absacken: Bewegung kleiner, Lichtbogen kürzer, Tempo etwas "
        "raus, Strom eher am unteren Ende.",
    "6:00 Sohle (überkopfnah)":
        "Am schwersten. Engster Lichtbogen, kleine kontrollierte Bewegung (kurzer "
        "Whip oder kleine Kreise), nicht stehen bleiben. Hier laufen die beiden "
        "Schweißer zusammen – sauber einbinden.",
}

CEL_PATTERN_GLOSSARY = {
    "Strichraupe (Drag)": "Gerade gezogen, keine Seitwärtsbewegung. Tiefster, "
                          "schmalster Einbrand – Standard für Wurzel und schmale Lagen.",
    "Whip / Schritttechnik": "Elektrode 1–2 × Ø aus dem Bad nach vorn, kurze Pause "
                             "(Bad friert an), zurück auf die Vorderkante. Steuert "
                             "Wärme und Profil in Zwangslage.",
    "Halbmond (Sichel)": "Fortlaufende ⌒-Bögen quer zur Naht. Für glatte Füll- und "
                         "Decklagen.",
    "Zickzack (seitlich)": "/\\/\\ von Kante zu Kante, an den Rändern kurz stehen "
                           "bleiben. Füll-/Decklage.",
    "Kringel / Kreise": "Kleine Schleifen. Gut in Zwangslage (4–6 Uhr) und zum "
                        "kontrollierten Auffüllen.",
    "J-Technik": "Whip-Variante zum Kappen – gerade runter, dann Haken. Gibt eine "
                 "gleichmäßige Decklage mit sauberen Rändern.",
    "Randpause (toe pause)": "Kein eigenes Muster, sondern die Regel: an den "
                             "Nahträndern jeweils kurz anhalten – verhindert "
                             "Einbrandkerben.",
}

# ----------------------------------------------------------- Vorwärmen --------
CEL_PREHEAT = [
    {"Fall": "Dünnwandig, niedriger CE, > 5 °C", "Vorwärmen": "min. 20 °C / handwarm",
     "Zweck": "Feuchte von der Fuge treiben"},
    {"Fall": "Standard C-Stahl bis ~X52, Wand < 12 mm", "Vorwärmen": "80–100 °C",
     "Zweck": "Wasserstoff-Abbau, Abkühlrate senken"},
    {"Fall": "X60–X70, Wand ≥ 12 mm, hoher Einspanngrad, Tie-in", "Vorwärmen": "100–150 °C",
     "Zweck": "Kaltrissvermeidung (HISC)"},
    {"Fall": "Niedrige Umgebungstemp., Wind, Nässe", "Vorwärmen": "+25–50 °C Aufschlag",
     "Zweck": "reale Bauteiltemperatur absichern"},
]
CEL_INTERPASS_NOTE = (
    "**Zwischenlagentemperatur** mindestens = Vorwärmtemperatur, **Maximum ~250 °C** "
    "(sonst leiden Zähigkeit/Festigkeit). **Heißlage sofort** nach der Wurzel legen – die "
    "Wurzel nicht unter die Vorwärmtemperatur abkühlen lassen (typ. Grenze ~100–120 °C). "
    "Rundum messen (Temperaturmesskreide / Anlegefühler), ~75 mm neben der Fuge."
)

# ------------------------------------------------------------- Wandstärke -----
CEL_PASS_COUNT = (
    "Faustwerte Lagenzahl: Wand ≤ 5 mm → Wurzel + Heißlage + Deck (3). "
    "6–10 mm → + 1 Fülllage (4). 11–16 mm → 2–3 Fülllagen (5–6). "
    "> 16 mm → entsprechend mehr; ab hier meist basisch/Fülldraht für Füll+Deck."
)

# ---------------------------------------------------------------- Fehler ------
CEL_DEFECTS = [
    {"Fehlerbild": "Innere Wurzelkerbe (IU)",
     "Ursache": "Strom zu hoch, zu schnell, falscher Winkel, Spalt zu weit, Hi-Lo",
     "Abhilfe": "Strom runter, gleichmäßiges Keyhole, Winkel zur kalten Seite, Hi-Lo richten"},
    {"Fehlerbild": "Hohlkehle / 'wagon tracks' (Längsschlacke neben Wurzel)",
     "Ursache": "Heißlage zu spät oder zu kalt, Wurzel nicht entschlackt, Verunreinigung",
     "Abhilfe": "Heißlage sofort und heiß, Wurzel bürsten/schleifen, Fuge sauber"},
    {"Fehlerbild": "Durchbrand / Fenster / Durchhang",
     "Ursache": "Spalt zu weit, Steg zu klein, Strom zu hoch, zu langsam, Keyhole zu groß",
     "Abhilfe": "Fuge nacharbeiten, Strom/Tempo anpassen, Keyhole klein halten"},
    {"Fehlerbild": "Poren / Zündporen",
     "Ursache": "Lichtbogen zu lang, Feuchte/Rost/Farbe, Wind, Polarität nicht nach WPS, schlechter Restart",
     "Abhilfe": "Kurzer Lichtbogen (drag), blank schleifen, Windschutz, Polarität nach WPS (Wurzel meist DC−, sonst DC+), Back-step-Restart"},
    {"Fehlerbild": "Bindefehler an der Flanke",
     "Ursache": "Strom zu niedrig, zu schnell, Lichtbogen nicht in die Flanke geführt, zu enge Fuge",
     "Abhilfe": "Strom hoch, an den Flanken kurz stehen, Fugenwinkel prüfen"},
    {"Fehlerbild": "Schlackeneinschluss",
     "Ursache": "Lage nicht entschlackt, Strom zu niedrig, unruhige Raupe, Kerben",
     "Abhilfe": "Jede Lage komplett entschlacken/schleifen, Strom/Technik anpassen"},
    {"Fehlerbild": "Randkerbe an der Decklage",
     "Ursache": "Am Nahtrand zu schnell, Strom hoch, langer Lichtbogen",
     "Abhilfe": "An den Rändern kurz halten, Strom runter, kurzer Lichtbogen"},
    {"Fehlerbild": "Risse (Wasserstoff / Krater)",
     "Ursache": "Keine/zu geringe Vorwärmung, Heißlage zu spät, hoher Einspanngrad, Krater offen",
     "Abhilfe": "Vorwärmen + Zwischenlagentemp. halten, Heißlage sofort, Krater auffüllen"},
]

# -------------------------------------------------------------- Ablauf --------
CEL_SEQUENCE = [
    "Fugenform prüfen: Winkel 60°, Steg ~1,6 mm, je 25 mm blank geschliffen.",
    "Rohr aufstellen, Innen-/Außenspanner setzen, Spalt ~1,6 mm und Hi-Lo ≤ 1,6 mm einstellen.",
    "Rundum auf Solltemperatur vorwärmen und messen (Kreide/Fühler, ~75 mm neben der Fuge).",
    "Wurzel fallend 12 → 6 Uhr, zwei Schweißer, Ziehtechnik, Keyhole ~4–5 mm halten.",
    "Innenspanner erst lösen, wenn die Wurzel nach WPS weit genug fertig ist (≥ 50–100 %).",
    "Wurzel entschlacken/bürsten. Heißlage SOFORT, heiß und schnell.",
    "Fülllagen legen, jede Lage vollständig entschlacken, Anschlüsse verschleifen.",
    "Decklage pendeln, Randkerben vermeiden, 1–2 mm Überhöhung.",
    "Sicht- und Maßprüfung, dann NDT nach WPS (RT / AUT).",
]

# ------------------------------------------------ Elektrodenwinkel: Bänder ---
# Richtwert-Schleppwinkel (Grad, von der Senkrechten, schleppend) je Uhrposition.
DRAG_BANDS = {
    "12:00 (Scheitel)": (5, 15),
    "1:30":             (5, 18),
    "3:00 (Flanke)":    (10, 30),
    "4:30":             (10, 25),
    "6:00 (Sohle)":     (5, 20),
}
WORK_ANGLE_NOTE = (
    "Arbeitswinkel: in der Fuge **mittig** (0°) führen. Nur in den steilen Positionen "
    "(3–6 Uhr) 5–10° zur **bereits geschweißten** Seite kippen, um eine einseitige "
    "Wurzelkerbe zu vermeiden. Über ~12° wird es unsauber."
)

# ------------------------------------------------------ EWM Pico 350 (cel) ---
EWM_PICO350 = {
    "Bauart": "MMA-Inverter, Gleichstrom (DC), 3 × 400 V",
    "Schweißstrom": "10 – 350 A",
    "Einschaltdauer (40 °C)": "350 A / 35 %   ·   280 A / 60 %   ·   230 A / 100 %",
    "Leerlaufspannung": "95 V",
    "Kennlinien / Funktionen": "MMA-Kennlinie „Cel“, Hotstart, Arcforce, Antistick, PF-Puls (Steiglage)",
}

EWM_PICO350_SETUP = """
**Betriebsart / Kennlinie:** MMA wählen, Lichtbogen-Kennlinie **„Cel“** – speziell für
zellulose-umhüllte Elektroden (harter, druckvoller Lichtbogen, wenig Kleben, tiefer Einbrand).

**Polung:** Nach Datenblatt / WPS. Klassisches E 6010 = **DC+**. Bei den Pipeline-Grades
(FOX CEL 70/75/80/90) läuft die **Wurzel auf DC− (Elektrode an Minus)**, die
Heiß-/Füll-/Decklage auf **DC+** – d. h. am Gerät zwischen Wurzel- und Fülllagen die
Klemmen tauschen. Immer die freigegebene WPS beachten.

**Strom / Einschaltdauer:** Die ganze Fallnaht liegt im Dauerbetrieb – selbst die Heißlage
mit 4 mm (~150–185 A) bleibt unter 230 A = **100 % ED**. ED nur bei sehr langen, heißen
Nähten am Stück beachten.

**Hotstart** (Zündstromspitze): für Zellulose **kräftig** einstellen, damit die Elektrode
ohne Kleben zündet. Richtwert: Hotstart-Strom deutlich über Schweißstrom, Hotstart-Zeit
kurz (Bruchteil einer Sekunde). Genaue Skala und Grenzen im Gerätehandbuch.

**Arcforce** (dynamische Stromanhebung bei kurzem Lichtbogen): bei Zellulose **hoch** –
hält den kurzen „drag“-Lichtbogen stabil, verhindert Kleben, treibt den Einbrand.
Zum Vergleich: Rutil mittel, basisch niedrig–mittel.

**Antistick:** **ein** lassen – senkt den Strom ab, wenn die Elektrode doch festklebt
(schützt Elektrode und Trafo).

**PF-Puls / Steiglagenfunktion:** nur für **Steignähte / Zwangslagen**. Für die reine
**Fallnaht aus** lassen.

**Leitungen:** kurze, ausreichend dicke Schweiß- und Masseleitungen, Masseklemme nah an
der Naht, Kontaktflächen blank – sonst Spannungsabfall und unruhiger Lichtbogen.
"""

# --------------------------------------- RT-Auswertung: ISO 6520-1 Nummern ---
RT_DEFECTS = [
    {"Nr. (ISO 6520-1)": "100 / 1001", "Bezeichnung (DE)": "Riss / Mikroriss", "EN": "crack / micro-crack",
     "Im Röntgenfilm": "scharfe, dunkle, unregelmäßige Linie, oft verzweigt",
     "Typische Ursache (Fallnaht)": "Wasserstoff (keine Vorwärmung, Heißlage zu spät), hoher Einspanngrad"},
    {"Nr. (ISO 6520-1)": "1024", "Bezeichnung (DE)": "Endkraterriss", "EN": "crater crack",
     "Im Röntgenfilm": "stern-/sichelförmiger Riss am Nahtende",
     "Typische Ursache (Fallnaht)": "Krater nicht aufgefüllt, zu schnelles Absetzen"},
    {"Nr. (ISO 6520-1)": "2011", "Bezeichnung (DE)": "Pore (Gaspore)", "EN": "gas pore",
     "Im Röntgenfilm": "runder, scharf begrenzter dunkler Fleck",
     "Typische Ursache (Fallnaht)": "langer Lichtbogen, Feuchte/Rost/Farbe, Wind, feuchte Elektrode"},
    {"Nr. (ISO 6520-1)": "2013", "Bezeichnung (DE)": "Porennest", "EN": "clustered (localised) porosity",
     "Im Röntgenfilm": "Gruppe von Poren auf engem Raum",
     "Typische Ursache (Fallnaht)": "punktuelle Verunreinigung, schlechter Wiederansatz"},
    {"Nr. (ISO 6520-1)": "2014", "Bezeichnung (DE)": "Porenzeile", "EN": "linear porosity",
     "Im Röntgenfilm": "Poren in einer Linie, meist längs der Naht",
     "Typische Ursache (Fallnaht)": "Verunreinigung im Spalt, Zugluft an der Wurzel"},
    {"Nr. (ISO 6520-1)": "2016", "Bezeichnung (DE)": "Wurmloch / Schlauchpore", "EN": "worm-hole / elongated cavity",
     "Im Röntgenfilm": "längliche, teils verzweigte dunkle Hohlform",
     "Typische Ursache (Fallnaht)": "starke Gasentwicklung, feuchte Elektrode, verunreinigte Fuge"},
    {"Nr. (ISO 6520-1)": "516", "Bezeichnung (DE)": "Wurzelporosität / Schwammbildung", "EN": "root porosity / hollow bead",
     "Im Röntgenfilm": "Kette feiner Poren in der Wurzelmitte",
     "Typische Ursache (Fallnaht)": "Heißlage zu spät, Verunreinigung, feuchte Elektrode"},
    {"Nr. (ISO 6520-1)": "301 / 3011", "Bezeichnung (DE)": "Schlackeneinschluss / Schlackenzeile ('wagon tracks')", "EN": "slag inclusion / linear slag",
     "Im Röntgenfilm": "unregelmäßig begrenzte dunkle Flächen, oft parallel beidseits der Wurzel",
     "Typische Ursache (Fallnaht)": "Lage nicht entschlackt, Kerben, Strom zu niedrig"},
    {"Nr. (ISO 6520-1)": "401", "Bezeichnung (DE)": "Bindefehler", "EN": "lack of fusion",
     "Im Röntgenfilm": "gerade, scharf begrenzte dunkle Linie an Flanke oder zwischen Lagen",
     "Typische Ursache (Fallnaht)": "Strom zu niedrig, zu schnell, Lichtbogen nicht in die Flanke, Hi-Lo"},
    {"Nr. (ISO 6520-1)": "4011 / 4012 / 4013", "Bezeichnung (DE)": "Flanken- / Lagen- / Wurzelbindefehler", "EN": "sidewall / inter-run / root LOF",
     "Im Röntgenfilm": "wie 401, die Lage im Querschnitt zeigt die Stelle",
     "Typische Ursache (Fallnaht)": "wie 401, je nach Lage"},
    {"Nr. (ISO 6520-1)": "402 / 4021", "Bezeichnung (DE)": "Ungenügende Durchschweißung / Wurzelfehler", "EN": "incomplete / lack of penetration",
     "Im Röntgenfilm": "durchgehender oder unterbrochener dunkler Streifen genau in der Nahtmitte (Wurzel)",
     "Typische Ursache (Fallnaht)": "Steg zu groß, Spalt zu klein, Strom zu niedrig, Keyhole verloren"},
    {"Nr. (ISO 6520-1)": "5011 / 5012", "Bezeichnung (DE)": "Randkerbe – durchgehend / unterbrochen", "EN": "continuous / intermittent undercut",
     "Im Röntgenfilm": "dunkles Band direkt am Nahtübergang der Decklage",
     "Typische Ursache (Fallnaht)": "am Nahtrand zu schnell, Strom hoch, langer Lichtbogen"},
    {"Nr. (ISO 6520-1)": "5013", "Bezeichnung (DE)": "Schrumpfkerbe / Wurzelkerbe (außen)", "EN": "shrinkage groove",
     "Im Röntgenfilm": "dunkle Rille beidseits der Wurzelraupe",
     "Typische Ursache (Fallnaht)": "Schrumpfung, Heißlage fehlt oder zu spät"},
    {"Nr. (ISO 6520-1)": "5014", "Bezeichnung (DE)": "Wurzelkerbe innen (IU – internal undercut)", "EN": "root undercut",
     "Im Röntgenfilm": "dunkles Band am Übergang Wurzel → Grundwerkstoff, wurzelseitig",
     "Typische Ursache (Fallnaht)": "Strom zu hoch, zu schnell, falscher Winkel, Spalt weit"},
    {"Nr. (ISO 6520-1)": "504", "Bezeichnung (DE)": "Wurzelüberhöhung / Durchhang der Wurzel", "EN": "excess penetration",
     "Im Röntgenfilm": "hellerer (dünnerer) Bereich in Nahtmitte – mehr Material innen",
     "Typische Ursache (Fallnaht)": "Spalt/Keyhole zu groß, Strom hoch, zu langsam"},
    {"Nr. (ISO 6520-1)": "509 / 510", "Bezeichnung (DE)": "Durchhang / Durchbrand", "EN": "sagging / burn-through",
     "Im Röntgenfilm": "örtlich sehr helle Stelle bzw. Loch (Materialverlust)",
     "Typische Ursache (Fallnaht)": "Spalt zu weit, Steg zu klein, Strom hoch, zu langsam"},
    {"Nr. (ISO 6520-1)": "507", "Bezeichnung (DE)": "Kantenversatz (Hi-Lo)", "EN": "linear misalignment",
     "Im Röntgenfilm": "Dichtesprung quer zur Naht, einseitig versetzte Wurzel",
     "Typische Ursache (Fallnaht)": "Rohre beim Heften nicht fluchtend gespannt"},
    {"Nr. (ISO 6520-1)": "515", "Bezeichnung (DE)": "Wurzelrückfall (Rückfall / 'suck-back')", "EN": "root concavity",
     "Im Röntgenfilm": "hellerer Streifen in Nahtmitte – Wurzel liegt unter der Rohrinnenwand",
     "Typische Ursache (Fallnaht)": "Heißlage zu heiß / zu spät, Spalt groß, Wurzel zu dünn geschweißt"},
    {"Nr. (ISO 6520-1)": "517", "Bezeichnung (DE)": "Schlechter Wiederansatz", "EN": "poor restart",
     "Im Röntgenfilm": "örtliche Pore / Bindefehler / Kerbe an der Ansatzstelle",
     "Typische Ursache (Fallnaht)": "kein Back-step, kalter Ansatz"},
    {"Nr. (ISO 6520-1)": "601 / 602", "Bezeichnung (DE)": "Zündstelle / Spritzer", "EN": "stray arc / spatter",
     "Im Röntgenfilm": "kleiner heller oder dunkler Punkt neben der Naht",
     "Typische Ursache (Fallnaht)": "Zünden neben der Fuge, Arcforce/Lichtbogen zu lang"},
]
RT_NOTE = (
    "Nummern nach **ISO 6520-1** (Einteilung der Unregelmäßigkeiten in Schmelzschweißungen). "
    "Bewertungsgruppen **B / C / D** nach **ISO 5817**. Zulässigkeitsgrenzen für die "
    "Durchstrahlungsprüfung (RT) an Rohrleitungen nach **API 1104** bzw. **ISO 10675-1** – "
    "welche Gruppe und welche Norm gelten, steht in der WPS bzw. im Prüfplan. "
    "„Hell“ = mehr Strahlung durchgelassen (weniger Werkstoff), „dunkel“ = weniger "
    "(Hohlraum / Einschluss)."
)
