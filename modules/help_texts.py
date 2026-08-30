"""Zentrale Kurz-Erklärungen für jede Funktion der App.

Konvention (bitte für neue Tools beibehalten):
  * Jedes Werkzeug bekommt einen Eintrag in HELP mit einem eindeutigen Schlüssel.
  * Direkt unter der Überschrift des Tools wird `render_tool_help("<key>")` aufgerufen.
  * "what"   – 1–3 Sätze: Was rechnet das Tool, wofür braucht man es (laienverständlich).
  * "fields" – dict {Feldname: Erklärung} für jedes Eingabefeld.
  * "result" – optional: Was bedeuten die Ergebniswerte.
"""

import streamlit as st

HELP = {
    # ----------------------------------------------------------------- Säge --
    "saege": {
        "title": "Smarte Säge",
        "what": (
            "Rechnet aus dem gewünschten Fertigmaß einer Rohrverbindung (Anschluss zu "
            "Anschluss bzw. Mitte zu Mitte) die reine Sägelänge des geraden Rohrstücks "
            "aus. Dazu werden alle Bauteile, Schweißspalte und Dichtungen abgezogen. "
            "Schnitte lassen sich in einer Liste sammeln und auf Stangenlängen "
            "optimieren."
        ),
        "fields": {
            "Bezeichnung / Spool": "Freier Name für den Schnitt (z. B. \"Strang A - 01\"). Nur zur Wiedererkennung in der Liste.",
            "Schnittmaß (Roh)": "Das gewünschte Fertigmaß der Verbindung in mm, bevor Bauteile abgezogen werden.",
            "Spalt (mm)": "Luftspalt pro Schweißnaht (Wurzelspalt), der beim Heften frei bleibt. Wird je Bauteil einmal abgezogen.",
            "Dichtungen": "Anzahl der Flanschdichtungen in dieser Verbindung.",
            "Dicke": "Dicke einer einzelnen Dichtung in mm.",
            "Typ / DN / Anzahl / Winkel": "Bauteil, das mitgerechnet wird (Bogen, Flansch, T-Stück, Reduzierung). DN = Größe, Anzahl = Stückzahl, Winkel nur bei Zuschnitt-Bögen. \"Bauteil dazu\" nimmt es in die Abzugsliste auf.",
        },
        "result": (
            "Sägelänge (Z) = das Maß, auf das das gerade Rohr gesägt wird. "
            "\"Negativmaß\" bedeutet: die Bauteile sind länger als das Sollmaß – so nicht "
            "baubar. Optional lassen sich Schweißnaht-Schrumpfung kompensieren und der "
            "Verschnitt auf Stangenlängen minimieren."
        ),
    },

    # ------------------------------------------------------------- Geometrie --
    "geo_2d": {
        "title": "2D-Etage (S-Schlag)",
        "what": (
            "Zwei Bögen versetzen die Leitung parallel in einer Ebene (Etage / "
            "Doppelbogen). Berechnet die schräge Verbindungslänge und den Rohr-Zuschnitt "
            "zwischen den Bögen."
        ),
        "fields": {
            "Nennweite": "Rohrgröße (DN). Bestimmt den Bogenradius, der vom Zuschnitt abgezogen wird.",
            "Versprung (H)": "Wie weit die Leitung seitlich versetzt wird (mm), gemessen senkrecht zur ursprünglichen Richtung.",
            "Fittings (°)": "Winkel der beiden Bögen, üblich 45°.",
        },
        "result": (
            "Zuschnitt (Rohr) = Sägelänge des Passstücks zwischen den Bögen. "
            "Etagenlänge = schräges Achsmaß Bogenmitte–Bogenmitte. "
            "Benötigter Platz = Baulänge in Laufrichtung. \"An Säge\" übernimmt den "
            "Zuschnitt in die Smarte Säge."
        ),
    },
    "geo_3d": {
        "title": "3D-Raum-Etage (Rolling Offset)",
        "what": (
            "Wie die 2D-Etage, aber der Versatz geht gleichzeitig zur Seite und in die "
            "Höhe (räumlich). Berechnet Zuschnitt, Rohrweg und die nötige Lage der Bögen."
        ),
        "fields": {
            "Nennweite": "Rohrgröße (DN), für den Bogen-Abzug.",
            "Roll (Seite)": "Seitlicher Versatz in mm.",
            "Set (Höhe)": "Höhenversatz in mm.",
            "Fitting Typ (°)": "Winkel der verwendeten Bögen (z. B. 45°).",
        },
        "result": (
            "Zuschnitt (Rohr) = Sägelänge des schrägen Passstücks. "
            "Rohrweg (Mitte) = Achsmaß der Schräge. "
            "Benötigte Baulänge (Run) = Länge in Laufrichtung. Die 3D-Vorschau zeigt die "
            "Lage im Raum."
        ),
    },
    "geo_bogen": {
        "title": "Standard-Bogen",
        "what": (
            "Die klassischen Maße eines Rohrbogens: der Vorbau (Abzugsmaß fürs Sägen) "
            "und die Abwicklungslängen außen / Mitte / innen zum Anreißen."
        ),
        "fields": {
            "Nennweite": "Rohrgröße (DN). Legt Bogenradius und Rohr-Außendurchmesser fest.",
            "Winkel (°)": "Bogenwinkel, z. B. 90° oder 45°.",
        },
        "result": (
            "Vorbau (Z-Maß) = so viel wird pro Bogenseite von der Rohrlänge abgezogen. "
            "Rücken / Mitte / Bauch = Länge der Außen-, Mittel- und Innenkontur über den "
            "Bogen – zum Anzeichnen von Falten- oder Segmentschnitten."
        ),
    },
    "geo_segment": {
        "title": "Segment-Bogen (Lobster Back)",
        "what": (
            "Ein Bogen, aus mehreren geraden Rohrstücken mit schrägen (Gehrungs-)Schnitten "
            "zusammengeschweißt – wenn kein fertiger Bogen verfügbar ist. Die Zeichnung "
            "zeigt den fertigen Bogen mit allen Nähten, darunter stehen die Anreißmaße."
        ),
        "fields": {
            "Nennweite": "Rohrgröße (DN) – bestimmt den Außendurchmesser.",
            "Bogenradius R": "Radius von der Bogenmitte bis zur Rohrachse (mm).",
            "Anzahl Segmente": "Wie viele gerade Stücke der Bogen hat. Mehr = glatter, aber mehr Nähte. Die 2 Endstücke sind halbe Segmente, damit die Anschlüsse gerade sind.",
            "Gesamtwinkel (°)": "Winkel, den der ganze Bogen macht (z. B. 90°).",
        },
        "result": (
            "**Sägeblatt-Neigung** = so schräg wird das Sägeblatt für jede Schnittfläche "
            "gestellt. **Knick je Naht** = wie stark die Rohrachse an jeder Schweißnaht "
            "abknickt (doppelte Sägeblatt-Neigung). **Rücken / Achse / Bauch** = "
            "Abwicklungslängen an der Außen-, Mittel- und Innenseite zum Anreißen der "
            "Schnitte am Rohr."
        ),
    },
    "geo_stutzen": {
        "title": "Stutzen-Abwicklung (Sattelschnitt)",
        "what": (
            "Erzeugt eine 1:1-Schablone, um ein Abzweigrohr (Stutzen) passend auf ein "
            "größeres Hauptrohr zu schneiden, sowie die Ausschnittkurve für das "
            "Hauptrohr. Gilt für rechtwinklig und mittig aufgesetzte Stutzen (Set-on)."
        ),
        "fields": {
            "Hauptrohr DN": "Größe des durchgehenden Rohrs.",
            "Stutzen DN": "Größe des Abzweigs (muss kleiner/gleich Hauptrohr sein).",
            "Stationen (Umfangsteilung)": "In wie viele Punkte der Stutzenumfang für die Anreißtabelle unterteilt wird – mehr = feiner.",
        },
        "result": (
            "Stutzen-Umfang = Maßband-Länge rundum. Größter Abtrag h = tiefste Stelle, "
            "die weggeschnitten wird. Linke Kurve/Tabelle = Schablone für den Stutzen "
            "(Umfangsmaß s ↔ Abtrag h). Rechte Kurve = Ausschnitt fürs Hauptrohr."
        ),
    },
    "geo_spalt": {
        "title": "Spalt-Ausgleich (Keilspalt)",
        "what": (
            "Wenn zwei Rohrenden nicht plan-parallel zusammenpassen – der Spalt ist "
            "oben/unten oder links/rechts unterschiedlich – berechnet dieses Tool den "
            "Korrekturschnitt, um die Enden wieder parallel zu bekommen."
        ),
        "fields": {
            "Nennweite": "Rohrgröße (DN); der Außendurchmesser bestimmt den Umfang.",
            "12 / 3 / 6 / 9 Uhr": "Gemessener Spalt an den vier Uhrzeit-Positionen in mm (z. B. mit Fühlerlehre).",
        },
        "result": (
            "Klaffen = Kippwinkel der Stoßfläche. Max. Spalt = größte Differenz. "
            "Ausrichtung = wo der Spalt am größten ist. Die Anreißtabelle "
            "(Maßband / Abtrag) wird um den Umfang angezeichnet und die Abtragstiefe "
            "übertragen, dann nachschneiden."
        ),
    },

    # -------------------------------------------------------------- Schweißen --
    "weld_az": {
        "title": "a- / z-Maß der Kehlnaht",
        "what": "Rechnet zwischen den zwei üblichen Angaben für die Größe einer Kehlnaht um.",
        "fields": {
            "Bekannt": "Wähle, ob du das z-Maß (Schenkellänge an der Kante) oder das a-Maß (Höhe des eingeschriebenen Dreiecks, \"Nahtdicke\") kennst.",
            "z bzw. a (mm)": "Der bekannte Wert.",
        },
        "result": "Beide Maße. Formel a = z/√2 ≈ 0,707 · z, gilt für die gleichschenklige Kehlnaht (90°).",
    },

    # ---------------------------------------------------------------- Rechner --
    "fc_tri": {
        "title": "Trigonometrie / Dreiecksrechner",
        "what": (
            "Löst Dreiecke – für alle \"ich habe zwei Maße, brauche das dritte\"-Fälle "
            "im Feld (Steigungen, Diagonalen, Winkel)."
        ),
        "fields": {
            "Dreieckstyp": "Rechtwinklig (ein 90°-Winkel) oder Schräg (Kosinussatz, kein rechter Winkel).",
            "a / b / c / α (rechtwinklig)": "Häkchen bei den zwei bekannten Größen setzen. a = Kathete an α, b = Kathete gegenüber α, c = Hypotenuse (längste Seite), α = Winkel in Grad.",
            "a, b, γ (schräg)": "Zwei Seiten und der von ihnen eingeschlossene Winkel; alternativ alle drei Seiten a, b, c.",
        },
        "result": "Alle fehlenden Seiten und Winkel sowie die Fläche.",
    },
    "fc_circle": {
        "title": "Kreisteiler / Lochbild",
        "what": (
            "Teilt einen Kreis in gleiche Teile – für Lochbilder (Flanschbohrungen) oder "
            "um einen Rohrumfang gleichmäßig zu markieren."
        ),
        "fields": {
            "Vorgabe": "Ob du den Durchmesser (Teil-/Lochkreis) oder den gemessenen Umfang eingibst.",
            "Ø bzw. Umfang (mm)": "Der Zahlenwert dazu.",
            "Anzahl Teile / Löcher": "In wie viele gleiche Abschnitte geteilt wird (mindestens 2).",
        },
        "result": (
            "Winkelschritt, Bogenmaß je Teil, Sehnenmaß (Stechzirkel-Einstellung zum "
            "Abschlagen), Maß zur gegenüberliegenden Seite, Koordinatentabelle und eine "
            "Lochbild-Zeichnung."
        ),
    },

    # -------------------------------------------------------------- Fallnaht --
    "fallnaht": {
        "title": "Fallnaht / Stovepipe (Cellulose)",
        "what": (
            "Lern- und Nachschlagemodul für das fallende Elektrodenhandschweißen von "
            "Rohr-Rundnähten mit zellulose-umhüllten Elektroden (E xx10, z. B. \"CEL 70\"). "
            "Erklärt Nahtvorbereitung, Elektrodenhaltung, Stromstärken, Lagenaufbau, "
            "Vorwärmen und typische Fehler – mit Zeichnungen."
        ),
        "fields": {
            "② Nahtvorbereitung": "Schieberegler für Öffnungswinkel, Steg (Land), Wurzelspalt, Hi-Lo und Wandstärke – die Querschnittzeichnung passt sich an, darunter die Richtwerte mit Wirkung jedes Werts.",
            "③ Elektrodenhaltung": "Uhrposition wählen und Schlepp- / Arbeitswinkel schieben – das Bild zeigt die Haltung, darunter kommt die Bewertung (im Richtwert / zu steil / zu flach).",
            "④ Strom & Lagen": "Ampere-Tabelle nach Elektrodendurchmesser und Lage; Schieber für Fülllagen und Wandstärke zeigen den Lagenaufbau als Skizze.",
            "⑤ Gerät (EWM Pico 350)": "Gerätedaten und empfohlene Einstellungen (Kennlinie Cel, Polung, Hotstart, Arcforce, Antistick, Puls) für dieses Schweißgerät.",
            "⑦ Fehler & RT-Auswertung": "Tabelle A: Fehler mit Ursache/Abhilfe. Tabelle B: offizielle Benennung + Nummer nach ISO 6520-1 zum Auswerten von Röntgen-Protokollen.",
        },
        "result": (
            "Reines Wissensmodul – keine Berechnung. Dient als Einweisung und "
            "Gedächtnisstütze; verbindlich ist immer die WPS des Projekts."
        ),
    },

    # ----------------------------------------------------- Schweißen Phase 2 --
    "weld_prep": {
        "title": "Nahtvorbereitung",
        "what": (
            "Zeigt für die gewählte Nahtart die üblichen Fugenmaße (Winkel, Steg, "
            "Wurzelspalt) und den Naht-Querschnitt. Der Querschnitt wird im Reiter "
            "\"Zusatzwerkstoff\" für die Mengenrechnung weiterverwendet."
        ),
        "fields": {
            "Nahtart": "I-Stoß, V-, HV-, DV-(X-)Naht oder Kehlnaht – setzt sinnvolle Startwerte.",
            "Wandstärke / Blechdicke": "Materialdicke an der Fuge.",
            "Öffnungs-/Flankenwinkel": "Gesamter Öffnungswinkel der V/X-Naht bzw. Flankenwinkel bei HV.",
            "Steg / Land": "Stehende Kante an der Wurzel.",
            "Wurzelspalt": "Abstand der Bauteile an der Wurzel.",
            "z-Maß (nur Kehlnaht)": "Schenkellänge der Kehlnaht.",
        },
        "result": "Naht-Querschnitt A in mm² und Fugenbreite; bei Kehlnaht das a-Maß.",
    },
    "weld_preheat": {
        "title": "Vorwärmen (EN 1011-2 B) / PWHT",
        "what": (
            "Berechnet die Vorwärm- und Zwischenlagentemperatur nach EN 1011-2, "
            "Methode B, aus Kohlenstoffäquivalent, Bauteildicke, Wasserstoffgehalt "
            "und Streckenenergie. Darunter PWHT-Richtwerte je Werkstoff."
        ),
        "fields": {
            "CET": "Kohlenstoffäquivalent – direkt eingeben oder aus den Legierungsanteilen (C, Mn, Mo, Cr, Cu, Ni) berechnen lassen.",
            "Kombinierte Dicke d": "Summe der Blechdicken an der Fuge – bestimmt den Wärmeabfluss.",
            "Zusatz / Wasserstoff HD": "Elektroden-/Drahttyp → diffusibler Wasserstoff in ml/100 g.",
            "Streckenenergie Q": "Aus dem Reiter ⚡ Streckenenergie (kJ/mm).",
        },
        "result": (
            "Empfohlene Vorwärm-/Zwischenlagentemperatur in °C. Warnung, wenn Eingaben "
            "außerhalb des Modellbereichs liegen (z. B. Zellulose-Wasserstoff). "
            "PWHT-Tabelle: Glühtemperatur und Haltezeit je Werkstoffgruppe."
        ),
    },

    # ----------------------------------------------------- Geometrie Phase 3 --
    "geo_stutzen_schraeg": {
        "title": "Stutzen schräg / außermittig",
        "what": (
            "Wie die Stutzen-Abwicklung, aber der Stutzen darf schräg angestellt "
            "(Anstellwinkel β) und/oder seitlich versetzt (e) sein. Der Sattelschnitt "
            "wird dadurch unsymmetrisch."
        ),
        "fields": {
            "Hauptrohr DN / Stutzen DN": "Rohrgrößen (Außendurchmesser).",
            "Anstellwinkel β": "Neigung der Stutzenachse aus der Senkrechten, 0–70°.",
            "Seitlicher Versatz e": "Abstand der Stutzenachse von der Hauptrohrachse (mm).",
            "Stationen": "Feinheit der Anreißtabelle.",
        },
        "result": "Schablonenkurve (Umfangsmaß s ↔ Abtrag h) und Hauptrohr-Ausschnitt, jetzt seitenabhängig – Schablone lagerichtig auflegen.",
    },
    "geo_verschneidung": {
        "title": "Rohr-Verschneidung (gleicher Ø)",
        "what": (
            "Zwei Rohre mit gleichem Durchmesser, die sich unter einem Winkel treffen "
            "(T-Stück, Lateral, Y). Bei gleichem Ø ist der Schnitt eine ebene Gehrung – "
            "beide Rohre werden gleich geschnitten."
        ),
        "fields": {
            "Nennweite": "Größe beider Rohre.",
            "Fall": "Abzweig/Lateral (ein Rohr eingeschweißt) oder Y symmetrisch (beide Rohre gleich zur Mittelachse).",
            "Winkel zwischen den Rohrachsen": "90° = rechtwinkliger Abzweig, < 90° = Lateral/Y.",
            "Stationen": "Feinheit der Schablone.",
        },
        "result": "Gehrungswinkel je Rohr, Abtrag von der Ferse (0) zur Zunge (max) und die Anreißtabelle.",
    },
    "geo_reduzierung": {
        "title": "Reduzierung – Abwicklung",
        "what": (
            "Flachmuster eines Reduzierstücks (Kegelstumpf) zum Anreißen auf Blech. "
            "Konzentrisch: exakter Kreisringsektor. Exzentrisch (eine Seite gerade): "
            "Abwicklung per Triangulation mit wahren Längen je Station."
        ),
        "fields": {
            "großes / kleines Ø": "Außendurchmesser der beiden Enden (aus DN oder direkt).",
            "Baulänge L": "Axiale Länge des Reduzierstücks.",
            "Bauart": "konzentrisch (mittig) oder exzentrisch (eine Mantellinie gerade).",
            "Stationen": "Nur exzentrisch: Anzahl Teilungen für die Triangulation.",
        },
        "result": (
            "Konzentrisch: Mantellinie, Sektorwinkel, Innen-/Außenradius, Bogenlängen "
            "→ direkt aufreißen. Exzentrisch: Tabelle der wahren Längen (Elementlinie + "
            "Diagonale) zum dreieckweisen Übertragen."
        ),
    },
    "geo_passstueck": {
        "title": "Passstück 3D",
        "what": (
            "Aus dem im Raum vermessenen Achsversatz zwischen zwei Anschlüssen das "
            "Verbindungsstück ermitteln: gerade, wenn die Achsen fluchten, sonst mit "
            "zwei gleichen Bögen (Rolling Offset)."
        ),
        "fields": {
            "Lauf ΔX": "Abstand in Richtung der ersten Rohrachse.",
            "Seite ΔY / Höhe ΔZ": "Seitlicher und höhenmäßiger Versatz des zweiten Anschlusses.",
            "Bogenwinkel": "Winkel der verwendeten Bögen (z. B. 45°).",
        },
        "result": "Wahrer Achsversatz, Raumdiagonale, Rohrweg Mitte-Mitte, Verdrehung (Roll) und die verbleibende gerade Länge.",
    },
    "geo_dehnung": {
        "title": "Dehnungsausgleicher",
        "what": (
            "Berechnet die Wärmedehnung einer Leitung und schätzt die nötige "
            "Schenkellänge eines L-, Z- oder U-Bogens (Lyra) zur Aufnahme – "
            "Vorauslegung nach Guided-Cantilever."
        ),
        "fields": {
            "Werkstoff / α": "Wärmeausdehnungskoeffizient (Stahl ≈ 12, Austenit ≈ 16,5 · 10⁻⁶/K).",
            "Leitungslänge L": "Länge zwischen den Festpunkten (m).",
            "Temperaturhub ΔT": "Differenz Betriebs- zu Montagetemperatur (K).",
            "DN / E-Modul / zul. Spannung Sa": "Rohrgröße, Elastizitätsmodul und zulässiger Spannungsbereich.",
            "Form": "U-Bogen (wirksamster), Z-Bogen oder L-Bogen.",
        },
        "result": (
            "Wärmedehnung ΔL und Richtwert für die Schenkellänge. **Ersetzt keine "
            "Flexibilitäts-/Spannungsanalyse** der Rohrklasse."
        ),
    },

    # ---------------------------------------------------- Smart Data Phase 4 --
    "sd_schedule": {
        "title": "Rohrmaße / Schedule",
        "what": (
            "Nachschlagetabelle nach ASME B36.10M: zu einer Nennweite der "
            "Außendurchmesser und je Schedule (Sch10, STD, XS, Sch160, XXS) die "
            "Wandstärke und der daraus folgende Innendurchmesser."
        ),
        "fields": {
            "Nennweite (NPS)": "Zollgröße; DN und Außen-Ø werden dazu angezeigt.",
        },
        "result": "Tabelle Schedule → Wand (mm) → Innen-Ø (mm). Grundlage für Gewicht, Volumen und Druck.",
    },

    # ---------------------------------------------------------- Vorrichten --
    "sd_lifting": {
        "title": "Hebezeug / Anschlagmittel",
        "what": (
            "Rechnet aus dem Gewicht (aus Rohrmaßen oder direkt) die Last je "
            "Anschlagstrang in Abhängigkeit vom Neigungswinkel – zur Auswahl von "
            "Ketten, Rundschlingen und Schäkeln."
        ),
        "fields": {
            "Gewicht": "Aus OD/Wand/Länge berechnet oder direkt in kg.",
            "Anzahl Stränge": "1–4. Bei 3 oder 4 Strängen zählen praktisch nur 2 als tragend.",
            "Neigungswinkel β": "Winkel der Stränge zur Senkrechten. Größer = deutlich höhere Strangkraft.",
        },
        "result": "Gesamtlast (kN), Last je Strang (kN und kg), Anzahl tragender Stränge und der Neigungsbeiwert 1/cos β.",
    },
    "sd_pnclass": {
        "title": "PN ↔ Class",
        "what": (
            "Grobe Gegenüberstellung europäischer Druckstufen (PN) und "
            "ASME-Class-Stufen mit dem ungefähren zulässigen Druck bei "
            "Raumtemperatur."
        ),
        "fields": {},
        "result": (
            "Orientierungstabelle. PN und Class sind nicht baugleich – Lochbild, "
            "Dichtfläche und Schrauben müssen zusammenpassen. Zulässiger Druck sinkt "
            "mit der Temperatur (Druck-Temperatur-Rating der Norm)."
        ),
    },

    # ------------------------------------------------------------- Smart Data --
    "smartdata": {
        "title": "Smart Data (Nachschlagewerte)",
        "what": (
            "Zeigt Nachschlage-Werte zur eingestellten Rohrgröße und Druckstufe "
            "(oben in der Seitenleiste unter \"Einstellungen\" wählbar): Gewichte, "
            "Flanschmaße, Dichtung, Schrauben und Drehmomente."
        ),
        "fields": {
            "Wandstärke (mm)": "Rohrwanddicke für die Gewichts- und Volumenrechnung.",
            "Rohrlänge (m)": "Länge, für die Gewicht und Füllmenge berechnet werden.",
            "Typ / U-Scheibe / Geschmiert / Dichtung": "Flanschverbindungsart (Fest-Fest, Fest-Los, Fest-Blind), ob Unterlegscheiben verwendet werden, ob die Schraube geschmiert ist (MoS2) und die Dichtungsdicke – daraus ergeben sich Schraubenlänge und Anzugsmoment.",
        },
        "result": (
            "Leergewicht / Füllgewicht / Füllvolumen (für Transport und Druckprobe), "
            "Flansch-Blattdicke und Lochkreis, Bohrungsanzahl, sowie Bolzenlänge, "
            "Schlüsselweite und Drehmoment (trocken / geschmiert)."
        ),
    },
}


def render_tool_help(key: str, expanded: bool = False):
    """Klappbare Kurz-Erklärung für ein Tool. Direkt unter dessen Überschrift aufrufen."""
    h = HELP.get(key)
    if not h:
        return
    with st.expander(f"ℹ️ {h['title']} – kurz erklärt", expanded=expanded):
        st.markdown(h["what"])
        if h.get("fields"):
            st.markdown("**Eingabefelder:**")
            for name, desc in h["fields"].items():
                st.markdown(f"- **{name}** — {desc}")
        if h.get("result"):
            st.markdown(f"**Ergebnis:** {h['result']}")
