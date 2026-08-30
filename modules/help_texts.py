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
            "Typ / DN / Anzahl / Winkel": "Bauteil, das mitgerechnet wird (Bogen, Flansch, T-Stück, Reduzierung). DN = Größe, Anzahl = Stückzahl, Winkel nur beim Bogen (90° = Standard-BA3). \"Bauteil dazu\" nimmt es in die Abzugsliste auf.",
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
            "Benötigte Baulänge (Run) = Länge in Laufrichtung. "
            "Verdrehung (Roll) = um welchen Winkel die Bögen aus der Senkrechten "
            "gedreht eingebaut werden. Die 3D-Vorschau zeigt die Lage im Raum."
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
    "sd_fittings": {
        "title": "Fitting-Einbaumaße",
        "what": (
            "Sammeltabelle der Einbau- und Abzugsmaße aller Formteile über alle DN – "
            "genau die Zahlen, die die Smarte Säge pro Bauteil abzieht, hier zum "
            "Durchblättern und Ausdrucken. Die Flansch-Spalte richtet sich nach der "
            "in der Seitenleiste gewählten Druckstufe."
        ),
        "fields": {
            "Bogenwinkel": "Stellt die Vorbau-Spalte auf einen beliebigen Bogenwinkel "
                           "(Vorbau = R·tan(Winkel/2)); 90° = Bogenradius.",
        },
        "result": (
            "Je DN: Ø außen, Bogenradius, Vorbau (Z-Maß) für den gewählten Winkel, "
            "Flansch-Blattdicke, T-Stück-Einbaumaß und Baulänge einer konzentrischen "
            "Reduzierung. Vorbau = Abzug pro Bogenseite, Flansch b = Abzug pro Flansch."
        ),
    },

    # ------------------------------------------------------------- Smart Data --
    "smartdata": {
        "title": "Smart Data (Nachschlagewerte)",
        "what": (
            "Nachschlage-Werte zur eingestellten Rohrgröße und Druckstufe (oben in der "
            "Seitenleiste unter \"Einstellungen\" wählbar): Flanschmaße, Dichtung, "
            "Schrauben und Drehmomente (EN 1092-1)."
        ),
        "fields": {
            "Wandstärke (mm)": "Rohrwanddicke – geht in die Dichtungs- und Bolzenlängen-Rechnung ein.",
            "Typ / U-Scheibe / Geschmiert / Dichtung": "Flanschverbindungsart (Fest-Fest, Fest-Los, Fest-Blind), ob Unterlegscheiben verwendet werden, ob die Schraube geschmiert ist (MoS2) und die Dichtungsdicke – daraus ergeben sich Schraubenlänge und Anzugsmoment.",
        },
        "result": (
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
