"""Kein Eingabefeld darf sich seinen Namen mit einem anderen teilen.

Streamlit fuehrt alle Eingaben unter ihrem Schluessel in **einem** Speicher.
Zwei Felder mit demselben Schluessel sind fuer die App dasselbe Feld - was man
im einen eintippt, steht danach im anderen. Genau das war zwischen "X/Y/Z
Startpunkt" der Rohrfolge-Skizze und "Lauf/Seite/Hoehe" im Passstueck-Rechner
passiert: falsche Startkoordinaten in der Nahtliste, ohne dass es jemand
eingegeben haette.

Der Test findet so etwas beim naechsten Mal sofort.
"""
import io
import re
import unittest
from collections import Counter
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "streamlit_app.py"

# Schluessel, die absichtlich mehrfach vorkommen duerfen - mit Begruendung.
ERLAUBT = {
    # Der Bestaetigen-Dialog und das Formular darunter gehoeren zusammen;
    # hier steht (noch) nichts drin.
}


class TestWidgetSchluessel(unittest.TestCase):

    def test_kein_schluessel_doppelt(self):
        quelle = io.open(APP, encoding="utf-8").read()
        # f-Strings wie key=f"sp_ed_{nonce}" sind absichtlich variabel
        schluessel = [k for k in re.findall(r'key="([a-zA-Z0-9_]+)"', quelle)]
        doppelt = {k: n for k, n in Counter(schluessel).items()
                   if n > 1 and k not in ERLAUBT}
        self.assertEqual(
            doppelt, {},
            "diese Eingabefelder teilen sich einen Namen und ueberschreiben "
            "sich dadurch gegenseitig: %s" % sorted(doppelt))


if __name__ == "__main__":
    unittest.main()
