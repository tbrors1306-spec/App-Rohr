import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------------------------------------------------------
# KONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rohrbau Profi G-Drive", page_icon="🛠️", layout="wide")

# !!! WICHTIG: HIER DEINE ORDNER-ID EINFÜGEN !!!
# (Findest du im Browser-Link deines Drive-Ordners nach "folders/")
FOLDER_ID = "1DWGDDlpS6qUar365ZgNgKi7-Eys9pzGn"

# Google Sheets Verbindung
@st.cache_resource
def get_gspread_client():
    if "gcp_service_account" in st.secrets:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    return None

client = get_gspread_client()

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stTextInput label, .stRadio label { font-weight: bold; }
    .result-box { background-color: #F4F6F7; padding: 10px; border-radius: 4px; border-left: 5px solid #2980B9; margin-bottom: 5px; border: 1px solid #ccc; font-size: 0.95rem; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 5px solid #27AE60; text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 15px; border: 1px solid #ccc; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .flansch-box { background-color: #FDEDEC; padding: 8px; border-radius: 4px; border-left: 5px solid #C0392B; font-size: 0.9rem; margin-bottom: 10px; border: 1px solid #ccc; }
    .info-box-blue { background-color: #D6EAF8; padding: 10px; border-radius: 4px; border-left: 5px solid #3498DB; font-size: 0.9rem; margin-top: 10px; color: #154360 !important; }
    .stDataFrame { border: 1px solid #000; }
</style>
""", unsafe_allow_html=True)

# ... (Hier bitte die ZEICHNEN-FUNKTIONEN und DATENBANK aus dem alten Code lassen!) ...
# Ich kürze das hier ab, damit es übersichtlich bleibt. 
# Bitte füge hier deine Funktionen zeichne_iso_2d, zeichne_iso_raum und die data/df Variablen ein.
# --- PLATZHALTER FÜR DEINEN ALTEN CODE START ---
def zeichne_iso_2d(h, l, winkel, passstueck):
    fig, ax = plt.subplots(figsize=(3.5, 2))
    ax.text(0.5, 0.5, "ISO Zeichnung", ha='center')
    ax.axis('off')
    return fig
# ... usw ...
data = { 'DN': [25, 32, 40, 50, 65, 80, 100, 125, 150, 200], 'D_Aussen': [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1] } # Gekürzt
df = pd.DataFrame(data)
row = df.iloc[0] # Dummy
standard_radius = 0 # Dummy
flansch_len = 0 # Dummy
selected_dn = 100 # Dummy
# --- PLATZHALTER ENDE ---


# -----------------------------------------------------------------------------
# HAUPTBEREICH
# -----------------------------------------------------------------------------
st.title("Rohrbau Profi (Drive Creator)")

tab1, tab6 = st.tabs(["Werkzeuge", "📝 Rohrbuch (Cloud)"])

with tab1:
    st.info("Hier sind deine Rechner (Säge, ISO, etc.) - Code hier wie gehabt.")

# --- TAB 6: ROHRBUCH (MIT CREATE FUNKTION) ---
with tab6:
    st.subheader("Digitales Rohrbuch")
    
    if client is None:
        st.error("Keine Verbindung. Secrets prüfen!")
    else:
        # 1. DATEI AUSWÄHLEN ODER ERSTELLEN
        st.write("📂 **Datei-Verwaltung**")
        
        # Modus wählen
        aktion = st.radio("Was möchtest du tun?", ["Vorhandene Liste öffnen", "Neue Liste erstellen"], horizontal=True)
        
        aktuelle_tabelle = None
        
        if aktion == "Neue Liste erstellen":
            new_name = st.text_input("Name der neuen Liste (z.B. Baustelle_Berlin_Halle3)")
            if st.button("Neue Tabelle erstellen +"):
                if FOLDER_ID == "HIER_DIE_LANGE_ID_EINFÜGEN":
                    st.error("Bitte trage erst die FOLDER_ID im Code ein!")
                elif new_name:
                    try:
                        # Tabelle erstellen
                        neue_tabelle = client.create(new_name, folder_id=FOLDER_ID)
                        # Kopfzeile schreiben
                        neue_tabelle.sheet1.append_row(["Datum", "ISO", "Naht", "Schweißer", "Bauteil", "Charge", "Länge"])
                        st.success(f"Datei '{new_name}' erfolgreich im Ordner erstellt!")
                        st.rerun() # Seite neu laden
                    except Exception as e:
                        st.error(f"Fehler: {e}")
        
        else: # Vorhandene öffnen
            # Dateinamen eingeben (einfachste Variante)
            file_name = st.text_input("Welche Datei öffnen?", value="Rohrbuch_DB")
            try:
                aktuelle_tabelle = client.open(file_name).sheet1
                st.success(f"Verbunden mit: {file_name}")
            except:
                st.warning("Datei nicht gefunden oder kein Zugriff.")

        st.markdown("---")

        # 2. EINTRÄGE MACHEN (Nur wenn Tabelle offen)
        if aktuelle_tabelle:
            with st.form("entry_form", clear_on_submit=True):
                st.caption("Neuen Eintrag hinzufügen:")
                c1, c2, c3 = st.columns(3)
                iso_nr = c1.text_input("ISO-Nummer")
                naht_nr = c2.text_input("Naht-Nr.")
                schweisser = c3.text_input("Schweißer")
                
                c4, c5, c6 = st.columns(3)
                bauteil = c4.text_input("Bauteil")
                charge = c5.text_input("Charge")
                laenge = c6.number_input("Länge", value=0)
                
                if st.form_submit_button("Speichern 💾"):
                    datum = datetime.now().strftime("%d.%m.%Y %H:%M")
                    aktuelle_tabelle.append_row([datum, iso_nr, naht_nr, schweisser, bauteil, charge, laenge])
                    st.toast("Gespeichert!", icon="✅")
                    st.cache_data.clear() # Cache leeren

            # 3. ANZEIGEN
            st.write("📖 **Inhalt:**")
            # Wir laden die Daten neu
            try:
                records = aktuelle_tabelle.get_all_records()
                if records:
                    st.dataframe(pd.DataFrame(records), use_container_width=True)
            except:
                st.info("Tabelle ist leer.")
