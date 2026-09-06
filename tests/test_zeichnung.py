"""Zeichnung und Feldzettel: laufen sie durch und liegt drin, was drin sein soll?

Die Skizze pixelweise zu pruefen bringt nichts. Geprueft wird darum, dass jede
Route ohne Fehler zeichnet und dass die Zahlen im Titelblock aus der Rechnung
kommen - dort schlaegt ein Fehler tatsaechlich auf den Zettel durch.
"""
import json
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd

from modules.calculations import PipeCalculator
from modules.utils import Visualizer

DATA = Path(__file__).resolve().parent.parent / "data" / "pipe_dimensions.json"


def _z(t, m=None, r=None, d=None, ma=None, s=None, w=None):
    return {"Bauteil": t, "Mass (mm)": m, "Richtung": r, "DN": d,
            "Massart": ma, "Seite (mm)": s, "Winkel": w}


class TestZeichnung(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DATA, encoding="utf-8") as f:
            cls.df = pd.DataFrame(json.load(f))
        cls.calc = PipeCalculator(cls.df)

    def _spool(self, **kw):
        parts = [_z("Rohr", 1000), _z("Vorschweissflansch"),
                 _z("Armatur mit Flanschen", 300), _z("Vorschweissflansch"),
                 _z("Rohr", 2000), _z("Bogen 90", r="N"),
                 _z("Rohr", 1500), _z("Versprung", 800, s=600, w=45),
                 _z("Rohr", 900)]
        args = dict(dn_start=80, pn="PN 16", dir_start="O", el_start=16089,
                    x_start=-1150, y_start=2582,
                    branches=[{"An Bauteil": 5, "Art": "Anschweissstutzen",
                               "Richtung": "Hoch", "DN": 50,
                               "Abstand (mm)": 800, "Rohrlaenge (mm)": 700,
                               "Ende": "Vorschweissflansch"}])
        args.update(kw)
        return self.calc.build_spool(parts, **args)

    def test_jede_ansicht_zeichnet_ohne_fehler(self):
        sp = self._spool()
        self.assertEqual(sp["warnings"], [])
        for modus in Visualizer.MODI:
            for ms in (False, True):
                fig = Visualizer.plot_spool(sp, "Test", massstab=ms,
                                            naht_nr=True, ballons=True,
                                            modus=modus)
                self.assertIsNotNone(fig)

    def test_ansichten_zeigen_nur_ihre_beschriftung(self):
        """Der Sinn der Modi: nicht alles gleichzeitig auf dem Blatt."""
        sp = self._spool()

        def _texte(modus):
            fig = Visualizer.plot_spool(sp, "", naht_nr=True, ballons=True,
                                        modus=modus)
            return [t.get_text() for a in fig.axes for t in a.texts]

        auf = _texte("Aufmass & Saegen")
        schw = _texte("Schweissen")
        mont = _texte("Montage")
        self.assertFalse([x for x in auf if x.startswith("WF")])
        self.assertTrue([x for x in schw if x.startswith("WF")])
        self.assertFalse([x for x in schw if x.startswith("H ")])
        self.assertFalse([x for x in mont if x.startswith("WF")])
        # Aufmass hat Masse, Montage nicht
        self.assertTrue([x for x in auf if x.startswith("H ")])
        # Hoehenkoten gibt es nicht mehr auf der Zeichnung - die Hoehen
        # stehen als Z-Koordinate in der Nahtliste.
        for txt in (auf, schw, mont):
            self.assertFalse([x for x in txt if x.startswith("EL ")])

    def test_abzweig_nie_laenger_gezeichnet_als_ein_laengeres_rohr(self):
        """Ein 660er Abzweig aus drei Abschnitten darf nicht laenger aussehen
        als ein 1000er Rohr aus einem Stueck. Das war schon einmal kaputt."""
        import math as _m
        sp = self.calc.build_spool(
            [_z("Rohr", 1000), _z("Rohr", 1000)], 80, "PN 16", dir_start="O",
            count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                       "Richtung": "Hoch", "DN": 50, "Abstand (mm)": 500,
                       "Rohrlaenge (mm)": 550, "Ende": "offenes Ende"}])
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        ax = fig.axes[0]
        # Rohrlinien: die dicke ist die Kette, die duenne der Abzweig
        ketten = [l for l in ax.lines if abs(l.get_linewidth() - 3.2) < 1e-9]
        zweige = [l for l in ax.lines if abs(l.get_linewidth() - 2.4) < 1e-9]
        self.assertTrue(ketten and zweige)

        def _laenge(l):
            x, y = l.get_xdata(), l.get_ydata()
            return _m.hypot(x[1] - x[0], y[1] - y[0])

        self.assertLess(max(_laenge(l) for l in zweige),
                        max(_laenge(l) for l in ketten),
                        "Abzweig (660 mm) wird laenger gezeichnet als das "
                        "Rohr (1000 mm)")

    def test_symbole_bleiben_erkennbar_gross(self):
        """Ein Schieber zwischen zwei kurzen Flanschen darf nicht auf einen
        Punkt zusammenschrumpfen, nur weil daneben ein langes Rohr liegt."""
        sp = self.calc.build_spool(
            [_z("Rohr", 12000), _z("Vorschweissflansch"),
             _z("Armatur mit Flanschen", 300), _z("Vorschweissflansch"),
             _z("Rohr", 12000)], 80, "PN 16", dir_start="O", count_ends=False)
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        ax = fig.axes[0]
        ketten = [l for l in ax.lines if abs(l.get_linewidth() - 3.2) < 1e-9]
        xs = [v for l in ketten for v in l.get_xdata()]
        ys = [v for l in ketten for v in l.get_ydata()]
        gesamt = max(max(xs) - min(xs), max(ys) - min(ys))
        rot = [l for l in ax.lines if l.get_color() == '#b91c1c']
        self.assertTrue(rot, "keine Armaturen-/Flanschsymbole gezeichnet")
        groesste = max(max(abs(l.get_xdata()[1] - l.get_xdata()[0]),
                           abs(l.get_ydata()[1] - l.get_ydata()[0]))
                       for l in rot)
        self.assertGreater(groesste, gesamt * 0.012,
                           "Symbol zu klein - sieht aus wie ein Punkt")

    def _symbol_axes(self, part):
        """Ein Symbol allein auf einer leeren Achse - so laesst sich pruefen,
        was es zeichnet, ohne dass die halbe Route dazwischenfunkt."""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        Visualizer._part_symbol(ax, part, (-1.0, 0.0), (1.0, 0.0), (0.0, 0.0),
                                (1.0, 0.0), (0.0, 1.0), 1.0, ("F", "F"))
        return ax

    def test_jedes_bauteil_mit_symbol_zeichnet_auch_eines(self):
        """Jedes Bauteil, fuer das es ein Symbol gibt, muss es auch bekommen.

        Faellt ein Zweig der Symbolauswahl weg, zeichnet das Bauteil entweder
        gar nichts oder - schlimmer - das Symbol des Nachbarn. Auf dem Blatt
        faellt das erst auf, wenn man genau hinsieht.
        """
        for part in ("Klappe", "Demontagestueck", "Armatur geschweisst",
                     "Armatur mit Flanschen", "Blindflansch", "Reduzierung",
                     "Montagestoss"):
            ax = self._symbol_axes(part)
            gezeichnet = len(ax.lines) + len(ax.patches)
            self.assertGreater(gezeichnet, 0,
                               "%s bekommt kein Symbol" % part)

    def test_klappe_ohne_dreiecke_mit_scheibe_und_welle(self):
        """Die Klappe wird bewusst **ohne** die beiden Dreiecke gezeichnet:
        zwei Gehaeusestriche, eine Schraege als Scheibe und ein gefuellter
        Punkt fuer die Welle. Mit Dreiecken waere auf dem Blatt kein
        Unterschied zum Schieber zu sehen."""
        ax = self._symbol_axes("Klappe")
        self.assertEqual(len(ax.patches), 0,
                         "Klappe darf keine Dreiecke bekommen")
        welle = [l for l in ax.lines if l.get_marker() not in ('', 'None', None)]
        self.assertEqual(len(welle), 1, "genau ein Punkt fuer die Welle")
        striche = [l for l in ax.lines if l.get_marker() in ('', 'None', None)]
        self.assertGreaterEqual(len(striche), 3,
                                "Gehaeuse (2 Striche) und Scheibe fehlen")
        # Die Scheibe liegt schraeg: sie laeuft quer ueber das Rohr, nicht
        # laengs und nicht senkrecht wie die Gehaeusestriche.
        schraeg = [l for l in striche
                   if abs(l.get_xdata()[1] - l.get_xdata()[0]) > 1e-6
                   and abs(l.get_ydata()[1] - l.get_ydata()[0]) > 1e-6]
        self.assertTrue(schraeg, "keine schraege Scheibe gezeichnet")

    def test_schieber_behaelt_seine_dreiecke(self):
        """Umgekehrt: der Schieber wird weiter mit den beiden Dreiecken und
        Spindel samt Handrad gezeichnet - daran erkennt man ihn."""
        for part in ("Armatur geschweisst", "Armatur mit Flanschen"):
            ax = self._symbol_axes(part)
            self.assertEqual(len(ax.patches) + len([
                l for l in ax.lines if len(l.get_xdata()) > 2]), 2,
                "%s braucht zwei Dreiecke" % part)

    def test_versatz_zwei_flaechen_je_eigene_schraffur(self):
        """Der Versatz wird als **zwei rechtwinklige Dreiecke** gezeichnet -
        so, wie man ihn abwickelt und auch rechnet:

            waagerecht: Lauf und Seite      -> Hypotenuse ist der Schatten
            senkrecht:  Hoehe und Schatten  -> Hypotenuse ist das Rohr

        Kein Rechteck und keine Box: die haetten Kanten, zu denen kein Mass
        gehoert. Vier Umrisslinien reichen, zwei je Dreieck, die gemeinsame
        Schattenkante wird nur einmal gezogen.

        Beide Flaechen sind **verschieden** schraffiert - laufen die Linien
        gleich, sieht man auf dem Blatt nicht, welche Flaeche die Hoehe und
        welche die Seite zeigt. Eine geschlossene Box wird nicht gezeichnet:
        sie braucht doppelt so viele Striche, auch die verdeckten hinten.

        Ausserdem darf die Schraffur nicht bildschirmfest auf 45 Grad liegen -
        dann sieht die Flaeche aus, als laege sie quer im Raum.
        """
        import math as _m

        def _linien(sp):
            fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
            schraff, umriss = set(), 0
            for l in fig.axes[0].lines:
                x, y = l.get_xdata(), l.get_ydata()
                if len(x) != 2:
                    continue                    # Winkelzeichen, kein Umriss
                grad = round(_m.degrees(
                    _m.atan2(y[1] - y[0], x[1] - x[0])) % 180.0, 1)
                if l.get_color() == '#7c8da3':
                    schraff.add(grad)
                elif (l.get_color() == '#64748b'
                      and abs(l.get_linewidth() - 0.8) < 1e-9):
                    umriss += 1          # Umriss der Versatzflaechen
            return schraff, umriss

        def _abstand(winkel):
            a, b = sorted(winkel)
            return min(abs(b - a), 180.0 - abs(b - a))

        # Rollversatz: liegendes Rechteck + senkrechtes Dreieck
        schraff, umriss = _linien(self.calc.build_spool(
            [_z("Rohr", 1500), _z("Versprung", 500, s=400, w=45),
             _z("Rohr", 1500)], 80, "PN 16", dir_start="O", count_ends=False))
        self.assertEqual(len(schraff), 2,
                         "Hoehe und Seite brauchen je eine eigene Schraffur, "
                         "gefunden: %s" % sorted(schraff))
        self.assertGreater(_abstand(schraff), 10.0,
                           "die beiden Schraffuren sind nicht zu "
                           "unterscheiden: %s" % sorted(schraff))
        self.assertEqual(umriss, 4,
                         "zwei Dreiecke = vier Umrisslinien (die Schattenkante "
                         "gehoert beiden), gezeichnet wurden %d" % umriss)
        for g in schraff:                      # nicht bildschirmfest auf 45
            self.assertNotAlmostEqual(g, 45.0, places=1)
            self.assertNotAlmostEqual(g, 135.0, places=1)

        # Ohne Seitenversatz faellt das Rechteck weg - nur das Dreieck bleibt
        schraff2, umriss2 = _linien(self.calc.build_spool(
            [_z("Rohr", 1500), _z("Versprung", 500, w=45), _z("Rohr", 1500)],
            80, "PN 16", dir_start="O", count_ends=False))
        self.assertEqual(len(schraff2), 1,
                         "ohne Seite gibt es nur eine Flaeche")
        self.assertEqual(umriss2, 2, "ohne Seite bleibt ein Dreieck uebrig - "
                                     "Hoehe und Lauf, das Rohr ist die "
                                     "Hypotenuse")

    def test_schraffiertes_dreieck_liegt_immer_unten(self):
        """Das waagerechte Dreieck liegt **immer auf der unteren Hoehe** -
        egal ob der Versprung steigt oder faellt. Es soll unter dem Rohr
        stehen und nicht darueber schweben.

        Daraus folgt, wo die Hoehenkathete sitzt: faellt der Versatz, am
        Anfang (das Rohr geht erst runter); steigt er, am Ende (das Rohr
        laeuft erst). Genau das prueft der Test - die Schraffur des
        senkrechten Dreiecks laeuft in der Isometrie senkrecht und ist
        dadurch von der anderen zu unterscheiden.

        Die Regel hat mehrere Anlaeufe gebraucht, deshalb steht sie hier fest.
        """
        import math as _m

        def _hoehenkante_x(richtung):
            sp = self.calc.build_spool(
                [_z("Rohr", 1200),
                 _z("Versprung", 800, r=richtung, s=600, w=45),
                 _z("Rohr", 1200)], 80, "PN 16", dir_start="O",
                count_ends=False)
            self.assertEqual(sp["warnings"], [])
            fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
            ax = fig.axes[0]
            # Die Hoehenkante ist die einzige Umrisslinie, die in der Isometrie
            # senkrecht steht - Lauf und Seite liegen waagerecht und erscheinen
            # schraeg, der Schatten ebenso.
            senk = [l for l in ax.lines
                    if l.get_color() == '#64748b'
                    and abs(l.get_linewidth() - 0.8) < 1e-9
                    and len(l.get_xdata()) == 2
                    and abs(l.get_xdata()[1] - l.get_xdata()[0]) < 1e-9]
            self.assertEqual(len(senk), 1,
                             "genau eine senkrechte Kante (%s)" % richtung)
            # Der Versprung ist das Kettenstueck, dessen Richtung am staerksten
            # von der Laufrichtung abweicht.
            kette = [l for l in ax.lines
                     if abs(l.get_linewidth() - 3.2) < 1e-9
                     and len(l.get_xdata()) == 2]
            kette.sort(key=lambda l: l.get_xdata()[0])

            def _winkel(l):
                x, y = l.get_xdata(), l.get_ydata()
                return _m.degrees(_m.atan2(y[1] - y[0], x[1] - x[0]))

            lauf = _winkel(kette[0])
            schraeg = max(kette, key=lambda l: abs(_winkel(l) - lauf))
            xs = list(schraeg.get_xdata())
            return senk[0].get_xdata()[0], min(xs), max(xs)

        x, vorne, hinten = _hoehenkante_x("Runter")
        self.assertLess(x, (vorne + hinten) / 2.0,
                        "faellt der Versatz, gehoert die Hoehe an den Anfang")
        x, vorne, hinten = _hoehenkante_x("Hoch")
        self.assertGreater(x, (vorne + hinten) / 2.0,
                           "steigt der Versatz, gehoert die Hoehe ans Ende")

    def _spool_mit_stutzen(self, abstand=400):
        return self.calc.build_spool(
            [_z("Rohr", 2000)], 80, "PN 16", dir_start="O", count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                       "Richtung": "Hoch", "DN": 50,
                       "Abstand (mm)": abstand, "Rohrlaenge (mm)": 500,
                       "Ende": "Vorschweissflansch"}])

    def test_anrissmass_des_stutzens_steht_auf_der_zeichnung(self):
        """Wo genau sitzt der Stutzen auf dem Rohr? Ohne dieses Mass kann man
        ihn nicht anzeichnen.

        Es wurde bisher gerechnet und in die Saegeliste geschrieben, stand aber
        nicht auf der Skizze - wer nur das Blatt in der Hand hat, konnte den
        Stutzen nicht setzen.
        """
        sp = self._spool_mit_stutzen(400)
        self.assertEqual(sp["branches"][0]["anriss"], 400.0)
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertIn("400", texte,
                      "Anrissmass des Stutzens fehlt auf der Zeichnung")

    def test_stutzen_bekommen_ein_kettenmass(self):
        """Mehrere Stutzen auf einem Rohr werden als **Kette** bemasst:
        Punkt an Punkt, alle auf einer Linie, mit Pfeilen an jedem Messpunkt.

        Also 400 | 1200 | Rest - nicht 400 und 1600 jeweils ab Rohranfang
        (das waere die gestaffelte Bemassung) und erst recht nicht als
        Einzelmasse, die bei zwei Stutzen uebereinander liegen.
        """
        sp = self.calc.build_spool(
            [_z("Rohr", 2800)], 80, "PN 16", dir_start="O", count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                       "Richtung": "Hoch", "DN": 50, "Abstand (mm)": a,
                       "Rohrlaenge (mm)": 500, "Ende": "Vorschweissflansch"}
                      for a in (400, 1600)])
        self.assertEqual(sp["warnings"], [])
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        ax = fig.axes[0]
        texte = [t.get_text() for a_ in fig.axes for t in a_.texts]
        rest = sp["segments"][0]["len"] - 1600.0
        for erwartet in ("400", "1200", "%.0f" % rest):
            self.assertIn(erwartet, texte,
                          "Kettenabschnitt %s fehlt" % erwartet)
        self.assertNotIn("1600", texte,
                         "1600 ist das Mass ab Rohranfang - das waere die "
                         "gestaffelte Bemassung, nicht die Kette")
        # An jedem Messpunkt ein Pfeil: drei Abschnitte, also sechs Spitzen.
        self.assertGreaterEqual(len(ax.patches), 6,
                                "Masspfeile fehlen - mit Schraegstrichen ist "
                                "bei kurzen Abschnitten nicht zu sehen, "
                                "welcher zu welchem Mass gehoert")

    def test_masse_lassen_sich_ausblenden(self):
        """Schalter "Masse ausblenden": die Leitung bleibt, die Bemassung geht.

        Gedacht fuer den Blick auf die Rohrfolge allein und fuer ein Blatt zum
        Selbst-Eintragen. Die Bauteile duerfen dabei nicht mit verschwinden.
        """
        sp = self._spool_mit_stutzen(400)
        mit = Visualizer.plot_spool(sp, "", modus="Alles", masse=True)
        ohne = Visualizer.plot_spool(sp, "", modus="Alles", masse=False)

        def _texte(fig):
            return [t.get_text() for a in fig.axes for t in a.texts]

        def _kette(fig):
            return [l for l in fig.axes[0].lines
                    if abs(l.get_linewidth() - 3.2) < 1e-9]

        self.assertIn("400", _texte(mit))
        self.assertNotIn("400", _texte(ohne))
        self.assertNotIn("2000", _texte(ohne))
        self.assertTrue(_kette(ohne), "ohne Masse fehlt die Leitung selbst")
        self.assertEqual(len(_kette(mit)), len(_kette(ohne)))
        # Die Bauteilnummern bleiben: sonst steht auf dem Blatt nichts mehr,
        # woran man ein Teil festmachen kann.
        # In "Alles" gewinnt das DN-Schild, darum hier die Aufmass-Ansicht:
        # dort traegt jedes Teil seine Nummer, und die muss bleiben - sonst
        # steht auf dem Blatt nichts mehr, woran man ein Teil festmacht.
        auf = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen",
                                    masse=False)
        self.assertIn(Visualizer._teil_label(sp["items"][0]), _texte(auf),
                      "Bauteilnummern duerfen nicht mit weg")
        self.assertNotIn("400", _texte(auf))
        # Auch auf dem Feldzettel muss der Schalter durchschlagen
        blatt = Visualizer.plot_iso_blatt(sp, kopf={}, masse=False)
        self.assertNotIn("400", [t.get_text() for a in blatt.axes
                                 for t in a.texts])

    def test_kein_abschnitt_ohne_mass(self):
        """Jeder gerade Lauf ist bemasst - auch einer, der nur aus Formteilen
        besteht.

        Gesamtmasse ueber einen Lauf gibt es nicht mehr - ausser genau hier:
        ein Lauf ganz ohne Rohr waere sonst voellig unbemasst und nicht zu
        bauen. Rohre tragen ihr eigenes Mass, ein angeschweisster Flansch
        zaehlt dabei mit.
        """
        import math as _m
        for name, sp in (("Demo", self._spool()),
                         ("Bogen an Versprung", self.calc.build_spool(
                             [_z("Rohr", 2000), _z("Versprung", 800, s=600, w=45),
                              _z("Bogen 90", r="Hoch"), _z("Rohr", 1500)],
                             80, "PN 16", dir_start="O", count_ends=False))):
            fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
            texte = [t.get_text() for a_ in fig.axes for t in a_.texts]
            laid = sp["segments"]
            i0 = 0
            while i0 < len(laid):
                j0 = i0
                while (j0 + 1 < len(laid)
                       and laid[j0 + 1]["d"] == laid[i0]["d"]):
                    j0 += 1
                teile = {laid[k]["part"] for k in range(i0, j0 + 1)}
                laengen = [laid[k]["len"] for k in range(i0, j0 + 1)]
                L = sum(laengen)
                if teile != {"Versprung"} and L > 1.0:
                    kandidaten = ["%.0f" % L]
                    for k in range(i0, j0 + 1):
                        if laid[k]["part"] != "Rohr" or laid[k]["len"] <= 1.0:
                            continue
                        # Rohr allein, oder mit einem der angeschweissten
                        # Flansche daneben - welcher Flansch welchem Rohr
                        # zugeschlagen wird, entscheidet die Zeichnung.
                        nb = [laid[q]["len"] for q in (k - 1, k + 1)
                              if i0 <= q <= j0
                              and laid[q]["part"] in Visualizer._FLANSCHE]
                        kandidaten.append("%.0f" % laid[k]["len"])
                        for extra in nb:
                            kandidaten.append("%.0f" % (laid[k]["len"] + extra))
                        if len(nb) == 2:
                            kandidaten.append("%.0f" % (laid[k]["len"]
                                                        + sum(nb)))
                    self.assertTrue(
                        any(k in texte for k in kandidaten),
                        "%s: Lauf %d-%d (%s, %.0f mm) hat kein Mass"
                        % (name, i0, j0, "/".join(sorted(teile)), L))
                i0 = j0 + 1

    def test_jedes_rohr_einzeln_und_kein_gesamtmass(self):
        """Jedes Rohr bekommt sein eigenes Mass - **kein** Gesamtmass ueber den
        Lauf. Die Summe rechnet sich jeder selbst aus, auf dem Blatt hat sie
        nur Platz weggenommen. Formteile bleiben ohne Mass, ihre Baulaengen
        stehen in der Stueckliste."""
        sp = self.calc.build_spool(
            [_z("Rohr", 1000), _z("Vorschweissflansch"),
             _z("Armatur mit Flanschen", 300), _z("Vorschweissflansch"),
             _z("Rohr", 1000)], 80, "PN 16", dir_start="O", count_ends=False)
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        # Gesamtmass des Laufs (1000 + 300 + 1000) darf NICHT dastehen
        self.assertNotIn("2300", texte,
                         "Gesamtmass ueber den Lauf ist abgeschafft")
        # Jedes Rohr einzeln - und der angeschweisste Flansch gehoert dazu,
        # sonst bliebe zwischen Massende und Flanschflaeche ein ungemessenes
        # Stueck. Saegelaenge 950 + Flansch 50 = 1000.
        flansch = float(self.df[self.df["DN"] == 80]["Flansch_b_16"].iloc[0])
        for r in sp["cut_rows"]:
            erwartet = r["Saegelaenge (mm)"] + flansch
            self.assertIn("%d" % erwartet, texte,
                          "Rohr %s: Mass ohne den Flansch daran" % r["Nr"])
            self.assertNotIn("%d" % r["Saegelaenge (mm)"], texte,
                             "Rohr %s: nackte Saegelaenge statt Rohr+Flansch"
                             % r["Nr"])
        # Formteile bekommen kein Mass: die Armatur ist 300 lang
        self.assertNotIn("300", texte,
                         "die Armatur hat ein Mass bekommen - Formteile "
                         "bleiben ohne")
        # Bauteile tragen nur ihre Nummer
        for nr in ("1", "2", "3", "4", "5"):
            self.assertIn(nr, texte)

    def test_abzweigmass_liegt_beim_abzweig(self):
        """Das Abzweigmass gehoert neben den Abzweig, nicht in die Bahnen
        aussen - dort laege es quer durch alle anderen Masslinien."""
        import math as _m
        sp = self.calc.build_spool(
            [_z("Rohr", 3000), _z("Bogen 90", r="N"), _z("Rohr", 3000)],
            80, "PN 16", dir_start="O", count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                       "Richtung": "Hoch", "DN": 50, "Abstand (mm)": 1500,
                       "Rohrlaenge (mm)": 500, "Ende": "offenes Ende"}])
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        ax = fig.axes[0]
        zweige = [l for l in ax.lines if abs(l.get_linewidth() - 2.4) < 1e-9]
        self.assertTrue(zweige)
        zx = [v for l in zweige for v in l.get_xdata()]
        zy = [v for l in zweige for v in l.get_ydata()]
        mitte = (sum(zx) / len(zx), sum(zy) / len(zy))
        beschr = [t for a in fig.axes for t in a.texts
                  if t.get_text().startswith("DN50")]
        self.assertEqual(len(beschr), 1, "genau ein Mass je Abzweig")
        pos = beschr[0].get_position()
        alle_x = [v for l in ax.lines for v in l.get_xdata()]
        alle_y = [v for l in ax.lines for v in l.get_ydata()]
        span = max(max(alle_x) - min(alle_x), max(alle_y) - min(alle_y))
        self.assertLess(_m.hypot(pos[0] - mitte[0], pos[1] - mitte[1]),
                        span * 0.15,
                        "Abzweigmass steht zu weit vom Abzweig weg")

    def _ueberschneidungen(self, sp, modus):
        """Echte Textrahmen aus matplotlib vergleichen, nicht meine Schaetzung.

        Nur so faellt auf, wenn die Flaechenschaetzung zu knapp wird.
        """
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        fig = Visualizer.plot_spool(sp, "", modus=modus, naht_nr=True,
                                    ballons=True)
        c = FigureCanvasAgg(fig)
        c.draw()
        r = c.get_renderer()
        rechtecke = [(t.get_text(),) + tuple(t.get_window_extent(r).extents)
                     for ax in fig.axes for t in ax.texts if t.get_text().strip()]
        treffer = []
        for i in range(len(rechtecke)):
            for j in range(i + 1, len(rechtecke)):
                a_, b_ = rechtecke[i], rechtecke[j]
                if (a_[1] < b_[3] and a_[3] > b_[1]
                        and a_[2] < b_[4] and a_[4] > b_[2]):
                    treffer.append("%r / %r" % (a_[0], b_[0]))
        return treffer

    def test_keine_beschriftung_ueberschneidet_eine_andere(self):
        """Kernversprechen: keine Ueberschneidung von Massen oder Kennungen -
        in keiner Ansicht und bei keiner Streckenfuehrung."""
        routen = {
            "Demo": self._spool(),
            "eng": self.calc.build_spool(
                [_z("Rohr", 400), _z("Vorschweissflansch"),
                 _z("Armatur mit Flanschen", 300), _z("Armatur mit Flanschen", 250),
                 _z("Vorschweissflansch"), _z("Rohr", 400), _z("Bogen 90", r="N"),
                 _z("Rohr", 300), _z("Bogen 90", r="Hoch"), _z("Rohr", 350)],
                80, "PN 16", dir_start="O"),
            "lang": self.calc.build_spool(
                [_z("Rohr", 9000), _z("Bogen 90", r="N"), _z("Rohr", 12000),
                 _z("Bogen 90", r="Hoch"), _z("Rohr", 4000)],
                150, "PN 16", dir_start="O"),
            "viele Abzweige": self.calc.build_spool(
                [_z("Rohr", 4000), _z("Bogen 90", r="N"), _z("Rohr", 4000)],
                100, "PN 16", dir_start="O",
                branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                           "Richtung": "Hoch", "DN": 50, "Abstand (mm)": a_,
                           "Rohrlaenge (mm)": 500, "Ende": "offenes Ende"}
                          for a_ in (700, 1500, 2300, 3100)]),
        }
        for name, sp in routen.items():
            for modus in Visualizer.MODI:
                treffer = self._ueberschneidungen(sp, modus)
                self.assertEqual(
                    treffer, [],
                    "%s / %s: %d Ueberschneidung(en): %s"
                    % (name, modus, len(treffer), "; ".join(treffer[:4])))

    def test_versprung_jeder_schenkel_eigenes_mass(self):
        """Ein Versprung bekommt kein Gesamtmass, sondern jeder Schenkel sein
        eigenes - im Detail-Kasten, weil die Treppe aus Hoehe, Seite und Lauf
        isometrisch weit ausholt und auf der Route alles kreuzen wuerde."""
        sp = self.calc.build_spool(
            [_z("Rohr", 1000), _z("Versprung", 800, s=600, w=45), _z("Rohr", 900)],
            80, "PN 16", dir_start="O", count_ends=False)
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        v = sp["items"][1]["vers"]
        # Jede Kante der Versatzflaeche traegt ihr eigenes Mass, an Ort und
        # Stelle - nicht ein Gesamtmass fuer den ganzen Versprung.
        for erwartet in ("H  %.0f" % v["hoehe"], "S  %.0f" % v["seite"],
                         "L  %.0f" % v["run"]):
            self.assertIn(erwartet, texte, "%r fehlt am Versatz" % erwartet)
        # Der Rohrweg gehoert mit aufs Blatt, und zwar am Rohr: das ist das
        # Mass, das man beim Bauen tatsaechlich abgreift.
        self.assertIn("Rohrweg  %.0f" % v["travel"], texte)
        # Am Bauteil muss stehen, dass es ein Versprung ist - aus einer
        # schraffierten Flaeche allein wird das niemand ablesen.
        self.assertTrue([x for x in texte if "Versprung" in x],
                        "am Versprung steht nicht, was er ist")
        # die Masse gehoeren an den Versatz, nicht irgendwohin an den Rand
        zeich = [t for a in fig.axes for t in a.texts
                 if t.get_text().startswith(("H ", "S ", "L "))]
        self.assertEqual(len(zeich), 3)

    def _masslinien(self, fig):
        """Masslinien und ihre Hilfslinien aus der Zeichnung holen."""
        grau = {'#94a3b8', '#334155', '#475569'}
        raus = []
        for l in fig.axes[0].lines:
            if l.get_color() not in grau:
                continue
            lw = round(l.get_linewidth(), 2)
            if abs(lw - 0.9) < 1e-9 or 0.55 < lw < 0.75:
                x, y = l.get_xdata(), l.get_ydata()
                raus.append(((x[0], y[0]), (x[1], y[1])))
        return raus

    def test_masslinien_kreuzen_einander_hoechstens_vereinzelt(self):
        """Masslinien kreuzen sich nur, wo es nicht anders geht.

        Die Platzierung bewertet jede Stelle und nimmt die beste. Bei einer
        Leitung, die in sich zurueckláeuft, gibt es fuer ein langes Gesamtmass
        manchmal keine kreuzungsfreie Bahn, ohne es quer ueber das halbe Blatt
        zu schieben - dann ist eine Kreuzung das kleinere Uebel. Der Test haelt
        fest, wie viele das hoechstens sein duerfen: mehr waere ein Rueckschritt.
        """
        import math as _m

        def kreuz(o, a_, b_):
            return ((a_[0] - o[0]) * (b_[1] - o[1])
                    - (a_[1] - o[1]) * (b_[0] - o[0]))

        def schnitt(s1, s2):
            p1, p2, p3, p4 = s1[0], s1[1], s2[0], s2[1]
            d1, d2 = kreuz(p3, p4, p1), kreuz(p3, p4, p2)
            d3, d4 = kreuz(p1, p2, p3), kreuz(p1, p2, p4)
            if not (((d1 > 1e-12) != (d2 > 1e-12))
                    and ((d3 > 1e-12) != (d4 > 1e-12))):
                return None
            f = d3 / (d3 - d4) if (d3 - d4) else 0.0
            return (p3[0] + (p4[0] - p3[0]) * f, p3[1] + (p4[1] - p3[1]) * f)

        sp = self._spool()
        for modus in ("Aufmass & Saegen", "Schweissen", "Montage"):
            fig = Visualizer.plot_spool(sp, "", modus=modus, naht_nr=True,
                                        ballons=True)
            linien = self._masslinien(fig)
            if not linien:
                continue
            pk = [v for s in linien for v in (s[0], s[1])]
            tol = max(max(q[0] for q in pk) - min(q[0] for q in pk),
                      max(q[1] for q in pk) - min(q[1] for q in pk)) * 0.012
            n = 0
            for i in range(len(linien)):
                for j in range(i + 1, len(linien)):
                    q = schnitt(linien[i], linien[j])
                    if q is None:
                        continue
                    if all(_m.hypot(q[0] - e[0], q[1] - e[1]) >= tol
                           for e in (linien[i][0], linien[i][1],
                                     linien[j][0], linien[j][1])):
                        n += 1
            # Einzelmasse, Gesamtmasse und die Masse an der Offset-Box
            # bringen viele Linien aufs Blatt. Drei Kreuzungen sind der
            # gemessene Stand - mehr waere ein Rueckschritt.
            self.assertLessEqual(
                n, 3, "%s: %d Masslinien kreuzen sich - gemessen waren "
                      "hoechstens drei noetig" % (modus, n))

    def test_feldzettel_ist_a3_quer(self):
        fig = Visualizer.plot_iso_blatt(self._spool())
        b, h = fig.get_size_inches()
        self.assertAlmostEqual(b, 16.54, places=2)
        self.assertAlmostEqual(h, 11.69, places=2)
        self.assertGreater(b, h)

    def test_feldzettel_zeigt_die_zahlen_aus_der_rechnung(self):
        sp = self._spool()
        fig = Visualizer.plot_iso_blatt(
            sp, kopf={"zeichnr": "ISO-1001", "leitung": "80-PL-1001",
                      "dn": 80, "druck": "16 bar"})
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertIn("ISO-1001", texte)
        self.assertIn("%.2f m" % (sp["total_axis"] / 1000.0), texte)
        self.assertIn("%d / %d" % (sp["naehte"], sp["flanschverbindungen"]), texte)
        feld = sum(1 for n in sp["nahtliste"] if n["feld"])
        self.assertIn(str(feld), texte)

    def test_leere_titelblock_felder_werden_zu_strich(self):
        fig = Visualizer.plot_iso_blatt(self._spool(), kopf={})
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertIn("–", texte)

    def test_lange_listen_werden_angesagt_statt_abgeschnitten(self):
        """Was nicht aufs Blatt passt, muss dort stehen - nicht verschwinden."""
        parts = []
        for i in range(30):
            parts.append(_z("Rohr", 1000 + i * 10))
            parts.append(_z("Bogen 90", r="N" if i % 2 else "O"))
        sp = self.calc.build_spool(parts, 80, "PN 16", dir_start="O")
        fig = Visualizer.plot_iso_blatt(sp)
        texte = " ".join(t.get_text() for a in fig.axes for t in a.texts)
        self.assertIn("weitere Naehte", texte)

    def test_einzelnes_bauteil_zeichnet(self):
        """Kuerzeste denkbare Route - darf nicht an der Skalierung scheitern."""
        sp = self.calc.build_spool([_z("Rohr", 500)], 100, "PN 16")
        self.assertIsNotNone(Visualizer.plot_spool(sp, "einzeln"))
        self.assertIsNotNone(Visualizer.plot_iso_blatt(sp))

    def test_einfachste_route_zeichnet_das_blatt(self):
        """Ohne Abzweig, ohne Versprung - der Feldzettel muss trotzdem stehen."""
        sp = self.calc.build_spool([_z("Rohr", 1000), _z("Bogen 90", r="N"),
                                    _z("Rohr", 1000)], 100, "PN 16")
        self.assertEqual(sp["warnings"], [])
        self.assertIsNotNone(Visualizer.plot_iso_blatt(sp))


if __name__ == "__main__":
    unittest.main()
