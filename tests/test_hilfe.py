"""Jedes Werkzeug hat seine Erklaerung - und jede Erklaerung ein Werkzeug.

`render_tool_help` ist frueher bei einem unbekannten Schluessel still
ausgestiegen. Deshalb ist lange nicht aufgefallen, dass drei Werkzeuge
(Trigonometrie, Kreisteiler, Fallnaht) gar keinen Text hatten: der Aufruf
stand da, es erschien nur nichts. Dieser Test faengt genau das ab.
"""
import io
import re
import unittest
from pathlib import Path

from modules.help_texts import HELP

APP = Path(__file__).resolve().parent.parent / "streamlit_app.py"


def _gerufene_schluessel():
    quelle = io.open(APP, encoding="utf-8").read()
    # Ziffern muessen mit rein - sonst rutschen "geo_2d" und "geo_3d" durch.
    return set(re.findall(r'render_tool_help\("([a-z0-9_]+)"', quelle))


class TestHilfe(unittest.TestCase):

    def test_jedes_werkzeug_hat_eine_erklaerung(self):
        fehlt = sorted(_gerufene_schluessel() - set(HELP))
        self.assertEqual(fehlt, [],
                         "diese Werkzeuge rufen eine Hilfe auf, die es nicht "
                         "gibt: %s" % fehlt)

    def test_keine_erklaerung_liegt_brach(self):
        ungenutzt = sorted(set(HELP) - _gerufene_schluessel())
        self.assertEqual(ungenutzt, [],
                         "diese Erklaerungen ruft niemand auf: %s" % ungenutzt)

    def test_erklaerungen_sind_vollstaendig(self):
        """Titel und "what" sind Pflicht - ohne sie ist der Eintrag nutzlos."""
        for key, h in HELP.items():
            self.assertTrue(h.get("title"), "%s: Titel fehlt" % key)
            self.assertGreater(len(h.get("what", "")), 40,
                               "%s: Erklaerung zu duenn" % key)


if __name__ == "__main__":
    unittest.main()
