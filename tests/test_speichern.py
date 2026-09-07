"""Route speichern und wieder laden: kommt derselbe Job zurueck?

Gespeichert wird als JSON-Datei - auf Streamlit Cloud gehoert dem Nutzer kein
Speicher, der Server wird neu gestartet und waere wieder leer. Die Datei liegt
bei ihm und geht auch an den Kollegen weiter.

Geprueft wird nicht das Dateiformat, sondern das, worauf es ankommt: dass aus
der geladenen Route dieselbe Rechnung faellt wie aus der urspruenglichen.
"""
import json
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd

import streamlit_app as app
from modules.calculations import PipeCalculator

DATA = Path(__file__).resolve().parent.parent / "data" / "pipe_dimensions.json"


class TestSpeichern(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DATA, encoding="utf-8") as f:
            cls.df = pd.DataFrame(json.load(f))
        cls.calc = PipeCalculator(cls.df)

    def _spool(self, parts_df, branch_df):
        return self.calc.build_spool(
            parts_df.to_dict("records"), 80, "PN 16", dir_start="O",
            branches=branch_df.to_dict("records"), count_ends=False)

    def _runde(self, parts_df, branch_df):
        """Einmal durch die Datei und zurueck."""
        text = json.dumps({"pipecraft": 1,
                           "bauteile": app._df_rein(parts_df),
                           "abzweige": app._df_rein(branch_df)},
                          ensure_ascii=False)
        wieder = json.loads(text)
        return (app._df_zurueck(wieder["bauteile"], app._spool_leer),
                app._df_zurueck(wieder["abzweige"], app._branch_leer))

    def test_geladene_route_rechnet_genauso(self):
        parts, zweige = app._spool_demo(), app._branch_demo()
        p2, z2 = self._runde(parts, zweige)
        a, b = self._spool(parts, zweige), self._spool(p2, z2)
        self.assertEqual(a["warnings"], [])
        self.assertEqual(b["warnings"], a["warnings"])
        self.assertAlmostEqual(b["total_axis"], a["total_axis"], places=6)
        self.assertEqual(b["naehte"], a["naehte"])
        self.assertEqual(b["flanschverbindungen"], a["flanschverbindungen"])
        self.assertEqual(b["cut_rows"], a["cut_rows"])
        self.assertEqual(b["mto"], a["mto"])

    def test_spalten_bleiben_in_ordnung(self):
        """Reihenfolge und Satz der Spalten muessen stimmen - die Tabellen in
        der App haengen daran."""
        parts, zweige = app._spool_demo(), app._branch_demo()
        p2, z2 = self._runde(parts, zweige)
        self.assertEqual(list(p2.columns), list(app._spool_leer().columns))
        self.assertEqual(list(z2.columns), list(app._branch_leer().columns))

    def test_leere_route_geht_auch_durch(self):
        p2, z2 = self._runde(app._spool_leer(), app._branch_leer())
        self.assertEqual(list(p2.columns), list(app._spool_leer().columns))
        self.assertEqual(len(p2), 0)
        self.assertEqual(len(z2), 0)

    def test_fehlende_spalte_wird_ergaenzt(self):
        """Eine Datei aus einer aelteren Fassung kennt vielleicht eine Spalte
        noch nicht - die App darf daran nicht scheitern."""
        rows = app._df_rein(app._spool_demo())
        for z in rows:
            z.pop("Massart", None)
        d = app._df_zurueck(rows, app._spool_leer)
        self.assertEqual(list(d.columns), list(app._spool_leer().columns))
        self.assertTrue(d["Massart"].isna().all())


class TestAdresszeile(unittest.TestCase):
    """Autospeichern in die Adresszeile - der Rettungsanker, wenn die Seite weg
    war. Streamlit haelt alles nur in der laufenden Sitzung; auf dem iPhone
    reicht ein Wechsel in eine andere App und die Route ist fort."""

    def _stand(self):
        return {"pipecraft": 1,
                "bauteile": app._df_rein(app._spool_demo()),
                "abzweige": app._df_rein(app._branch_demo()),
                "start": {"dn": 80, "richtung": "O", "stange": 6000.0,
                          "enden": True},
                "projekt": {"werkstoff": "P235GH", "leitung": "80-PL-1001",
                            "x": 0.0, "y": 0.0, "z": 0.0}}

    def test_packen_und_entpacken_ist_verlustfrei(self):
        stand = self._stand()
        self.assertEqual(app._stand_entpacken(app._stand_packen(stand)), stand)

    def test_passt_in_eine_adresszeile(self):
        """Gemessen, nicht geschaetzt: die Zeilen wiederholen sich stark,
        deshalb packt es gut. Bleibt es unter ein paar tausend Zeichen, macht
        kein Browser Aerger."""
        kurz = app._stand_packen(self._stand())
        gross = dict(self._stand())
        gross["bauteile"] = gross["bauteile"] * 6      # ~78 Zeilen
        lang = app._stand_packen(gross)
        self.assertLess(len(kurz), 1200, "schon die kleine Route ist zu lang")
        self.assertLess(len(lang), 3000,
                        "eine grosse Route sprengt die Adresszeile: %d Zeichen"
                        % len(lang))

    def test_kaputte_adresse_wirft_sauber(self):
        """Eine verstuemmelte Adresse darf nicht die App zerlegen - der Aufrufer
        faengt den Fehler und ignoriert den Stand."""
        for muell in ("", "kein-base64!!", "YWJj"):
            with self.assertRaises(Exception):
                app._stand_entpacken(muell)


if __name__ == "__main__":
    unittest.main()
