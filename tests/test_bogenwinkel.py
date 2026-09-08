"""Boegen mit krummem Winkel: 66 Grad statt 90.

Auf der Trasse kommen Richtungswechsel vor, die kein 90er sind - 66 Grad, 71,
was der Verlauf hergibt. Gezeichnet werden sie auf der Isometrie trotzdem wie
eine rechtwinklige Ecke, weil ein 66-Grad-Knick auf kein Achsenraster passt.
Die Zahl daneben sagt, was es wirklich ist.

Der Punkt, an dem es weh tut, ist nicht die Beschriftung, sondern der Abzug:
der Schenkel ab Eckpunkt ist **R * tan(Winkel/2)**. Bei 90 Grad ist tan(45) = 1
und damit genau R - nur deshalb konnte im Code frueher der Radius stehen. Bei
66 Grad sind es 0,649 * R. Wer den Bogen als 90er eintraegt, saegt sein Rohr je
Bogenseite zu kurz: DN 600 um 320 mm, bei zwei Boegen an einem Rohr um 640 mm.
Genau das halten diese Tests fest.
"""
import json
import math
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd

import streamlit_app as app
from modules.calculations import PipeCalculator
from modules.utils import Visualizer

DATA = Path(__file__).resolve().parent.parent / "data" / "pipe_dimensions.json"


class TestBogenwinkel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DATA, encoding="utf-8") as f:
            cls.df = pd.DataFrame(json.load(f))
        cls.calc = PipeCalculator(cls.df)

    def _R(self, dn):
        return float(self.df[self.df["DN"] == dn].iloc[0]["Radius_BA3"])

    def _route(self, winkel=None, dn=600):
        bogen = {"Bauteil": "Bogen 90", "Richtung": "N"}
        if winkel is not None:
            bogen["Winkel"] = winkel
        return self.calc.build_spool(
            [{"Bauteil": "Rohr", "Mass (mm)": 8000},
             bogen,
             {"Bauteil": "Rohr", "Mass (mm)": 6000}],
            dn, "PN 16", dir_start="O", count_ends=False)

    # ---------------------------------------------------------- Baulaenge ---
    def test_ohne_winkel_bleibt_alles_wie_vorher(self):
        """Ein Bogen ohne Angabe ist ein 90er - der Normalfall darf sich durch
        diese Aenderung um keinen Millimeter verschieben."""
        R = self._R(600)
        self.assertAlmostEqual(
            self.calc.part_length("Bogen 90", 600), R, places=6)
        self.assertAlmostEqual(
            self.calc.part_length("Bogen 90", 600, winkel=90), R, places=6)

    def test_flacherer_bogen_hat_kuerzeren_schenkel(self):
        """R * tan(33 Grad) = 594 mm statt 914 mm bei DN 600."""
        R = self._R(600)
        L = self.calc.part_length("Bogen 90", 600, winkel=66)
        self.assertAlmostEqual(L, R * math.tan(math.radians(33.0)), places=6)
        self.assertAlmostEqual(L, 593.6, places=1)

    def test_der_unterschied_landet_in_der_saegelaenge(self):
        """Das ist der eigentliche Zweck: das Rohr wird laenger, weil weniger
        abgezogen wird. 320 mm je Bogenseite bei DN 600."""
        a = self._route(winkel=None)
        b = self._route(winkel=66)
        s_a = [c["Saegelaenge (mm)"] for c in a["cut_rows"]]
        s_b = [c["Saegelaenge (mm)"] for c in b["cut_rows"]]
        for vorher, nachher in zip(s_a, s_b):
            self.assertAlmostEqual(nachher - vorher, 320, delta=1.0)

    def test_winkel_ausserhalb_wird_gemeldet(self):
        """Ein Bogen von 0 oder 200 Grad ist keiner - lieber melden als still
        etwas rechnen, das niemand nachvollzieht."""
        for falsch in (0, 180, 200, -30):
            sp = self.calc.build_spool(
                [{"Bauteil": "Rohr", "Mass (mm)": 8000},
                 {"Bauteil": "Bogen 90", "Richtung": "N", "Winkel": falsch},
                 {"Bauteil": "Rohr", "Mass (mm)": 6000}],
                600, "PN 16", dir_start="O", count_ends=False)
            self.assertTrue(
                any("Bogenwinkel" in w for w in sp["warnings"]),
                "Winkel %s haette gemeldet werden muessen" % falsch)

    def test_nach_der_meldung_wird_mit_90_gerechnet(self):
        sp = self.calc.build_spool(
            [{"Bauteil": "Rohr", "Mass (mm)": 8000},
             {"Bauteil": "Bogen 90", "Richtung": "N", "Winkel": 200},
             {"Bauteil": "Rohr", "Mass (mm)": 6000}],
            600, "PN 16", dir_start="O", count_ends=False)
        normal = self._route(winkel=None)
        self.assertEqual([c["Saegelaenge (mm)"] for c in sp["cut_rows"]],
                         [c["Saegelaenge (mm)"] for c in normal["cut_rows"]])

    # ------------------------------------------------------------ Blatt -----
    def test_die_zeichnung_zeigt_den_echten_winkel(self):
        """Der Ecke sieht man den Richtungswechsel nicht an - sie ist auf der
        Achse gezeichnet. Darum muss die Zahl daneben stimmen."""
        fig = Visualizer.plot_spool(self._route(winkel=66), "",
                                    ballons=True, modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertTrue([t for t in texte if t.endswith("66°")],
                        "kein 66-Grad-Ballon gefunden: %s" % texte)
        self.assertFalse([t for t in texte if t.endswith("90°")])

    def test_ohne_angabe_steht_weiter_90_auf_dem_blatt(self):
        fig = Visualizer.plot_spool(self._route(winkel=None), "",
                                    ballons=True, modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertTrue([t for t in texte if t.endswith("90°")])

    # ------------------------------------------------------- Stueckliste ----
    def test_stueckliste_nennt_den_winkel(self):
        """Einen 66-Grad-Bogen kauft man nicht als 90er - auf der Liste muss
        stehen, was gebraucht wird."""
        pos = [m["Position"] for m in self._route(winkel=66)["mto"]]
        self.assertIn("Bogen 66 Grad DN600", pos)
        self.assertNotIn("Bogen 90 DN600", pos)

    def test_ohne_winkel_heisst_es_weiter_bogen_90(self):
        pos = [m["Position"] for m in self._route(winkel=None)["mto"]]
        self.assertIn("Bogen 90 DN600", pos)

    def test_jeder_bogen_bekommt_eine_positionsnummer(self):
        """Ohne Positionsnummer haengt am Ballon nichts - und in der
        erweiterten Stueckliste fehlt die Zeile."""
        for w in (None, 66):
            sp = self._route(winkel=w)
            boegen = [i for i in sp["items"] if i["part"] == "Bogen 90"]
            self.assertTrue(boegen)
            for it in boegen:
                self.assertIsNotNone(it["pos"], "Winkel %s ohne Position" % w)

    # ------------------------------------------------------- Versprung ------
    def test_der_versprung_bleibt_unberuehrt(self):
        """Die Spalte Winkel gehoerte vorher dem Versprung. Der muss weiter
        genauso rechnen wie bisher."""
        sp = self.calc.build_spool(
            [{"Bauteil": "Rohr", "Mass (mm)": 3000},
             {"Bauteil": "Versprung", "Mass (mm)": 800, "Seite (mm)": 600,
              "Winkel": 45},
             {"Bauteil": "Rohr", "Mass (mm)": 2000}],
            300, "PN 16", dir_start="O", count_ends=False)
        self.assertEqual(sp["warnings"], [])
        v = [i for i in sp["items"] if i["part"] == "Versprung"][0]
        self.assertEqual(v["vers"]["winkel"], 45)


class TestSpalteEinblenden(unittest.TestCase):
    """Wann die Winkelspalte in der Tabelle auftaucht.

    Die meisten Boegen sind 90er - eine dauernd sichtbare Winkelspalte kostet
    auf dem Handy nur Breite. Sie kommt darum ueber "Alle Spalten zeigen"
    dazu. Steht aber irgendwo ein Winkel drin, muss sie bleiben: ein Wert, der
    die Saegelaenge veraendert, darf nicht aus dem Blick verschwinden.
    """

    def test_leere_spalte_bleibt_ausgeblendet(self):
        d = pd.DataFrame([{"Bauteil": "Bogen 90", "Winkel": None}])
        self.assertFalse(app._hat_werte(d, "Winkel"))

    def test_eingetragener_winkel_blendet_sie_ein(self):
        d = pd.DataFrame([{"Bauteil": "Bogen 90", "Winkel": None},
                          {"Bauteil": "Bogen 90", "Winkel": 66}])
        self.assertTrue(app._hat_werte(d, "Winkel"))

    def test_fehlende_spalte_ist_kein_fehler(self):
        """Eine Route aus einer aelteren Fassung kennt die Spalte nicht."""
        self.assertFalse(app._hat_werte(pd.DataFrame([{"Bauteil": "Rohr"}]),
                                        "Winkel"))


if __name__ == "__main__":
    unittest.main()
