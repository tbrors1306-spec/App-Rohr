import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. DESIGN & CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rohrbau Profi", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stRadio label, .stTextInput label { font-weight: bold; }
    .result-box { background-color: #F4F6F7; padding: 12px; border-radius: 4px; border-left: 6px solid #2980B9; color: black !important; margin-bottom: 8px; border: 1px solid #ddd; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 6px solid #27AE60; color: black !important; text-align: center; font-size: 1.3rem; font-weight: bold; margin-top: 10px; border: 1px solid #ddd; }
    .info-blue { background-color: #D6EAF8; padding: 10px; border-radius: 5px; border: 1px solid #AED6F1; color: #21618C; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Session State für Rohrbuch
if 'rohrbuch_data' not in st.session_state:
    st.session_state.rohrbuch_data = []

# -----------------------------------------------------------------------------
# 2. HILFSFUNKTIONEN (ZEICHNEN)
# -----------------------------------------------------------------------------
def zeichne_etage_2d(h, l, winkel, passstueck):
    """Zeichnet die 2D Ansicht aus Bild 7"""
    fig, ax = plt.subplots(figsize=(5, 3))
    
    # Koordinaten berechnen (einfaches Dreieck)
    p_start = (0, 0)
    p_eck = (l, 0)
    p_end = (l, h)
    
    # Linien
    ax.plot([0, l], [0, h], color='#2C3E50', linewidth=4, label='Rohr', zorder=2) # Diagonale
    ax.plot([l, l], [0, h], color='#E74C3C', linestyle='--', linewidth=1, zorder=1) # H
    ax.plot([0, l], [0, 0], color='#E74C3C', linestyle='--', linewidth=1, zorder=1) # L
    
    # Punkte (Bögen)
    ax.scatter([0, l], [0, h], color='white', edgecolor='#2C3E50', s=80, zorder=3, linewidth=2)
    
    # Text
    ax.text(l + 10, h/2, f"H={h}", color='#E74C3C', fontweight='bold')
    ax.text(l/2, -30, f"L={l}", color='#E74C3C', fontweight='bold', ha='center')
    ax.text(l/2, h/2 + 20, f"Säge: {round(passstueck, 1)}", color='#27AE60', fontweight='bold', ha='right', fontsize=12)
    
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

# -----------------------------------------------------------------------------
# 3. DATENBANK
# -----------------------------------------------------------------------------
# (Gekürzte Datenbank für Übersichtlichkeit, Logik bleibt gleich)
data = {
    'DN': [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600],
    'D_Aussen': [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0, 711.0, 813.0, 914.0, 1016.0, 1219.0, 1422.0, 1626.0],
    'Radius_BA3': [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914, 1067, 1219, 1372, 1524, 1829, 2134, 2438],
    'T_Stueck_H': [25, 32, 38, 51, 64, 76, 105, 124, 143, 178, 216, 254, 279, 305, 343, 381, 432, 521, 597, 673, 749, 889, 1029, 1168],
    'Red_Laenge_L': [38, 50, 64, 76, 89, 89, 102, 127, 140, 152, 178, 203, 330, 356, 381, 508, 508, 610, 660, 711, 800, 900, 1000, 1100],
    'Flansch_b_16': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_16': [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 355, 410, 470, 525, 585, 650, 770, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_16': ["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M33", "M33", "M36", "M36", "M39", "M45", "M45", "M52"],
    'L_Fest_16': [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 100, 110, 110, 120, 130, 130, 150, 160, 170, 180, 190, 220, 240, 260],
    'L_Los_16': [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 115, 125, 130, 140, 150, 150, 170, 180, 190, 210, 220, 250, 280, 300],
    'Lochzahl_16': [4, 4, 4, 4, 4, 8, 8, 8, 8, 12, 12, 12, 16, 16, 20, 20, 20, 24, 24, 28, 28, 32, 36, 40],
    'Flansch_b_10': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_10': [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 350, 400, 460, 515, 565, 620, 725, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_10': ["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M20", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M30", "M33", "M36", "M39", "M45"],
    'L_Fest_10': [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 90, 90, 90, 100, 110, 110, 120, 130, 140, 150, 160, 190, 210, 230],
    'L_Los_10': [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 105, 105, 110, 120, 130, 130, 140, 150, 160, 170, 180, 210, 240, 260],
    'Lochzahl_10': [4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 12, 12, 16, 16, 20, 20, 20, 20, 24, 28, 28, 32, 36, 40]
}
df = pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 4. APP LOGIK
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Einstellungen")
selected_dn = st.sidebar.selectbox("Nennweite (DN)", df['DN'], index=8) 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0)

row = df[df['DN'] == selected_dn].iloc[0]
standard_radius = row['Radius_BA3']

st.sidebar.markdown("---")
st.sidebar.write("✏️ **Korrektur:**")
custom_radius = st.sidebar.number_input("Bogenradius (R)", value=float(standard_radius), step=1.0)

st.title(f"Rohrbau Profi (DN {selected_dn})")
suffix = "_16" if selected_pn == "PN 16" else "_10"

# Tabs definieren
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Maße", "🔄 Bogen", "📏 Säge", "🔥 Stutzen", "📐 Etagen Berechnung", "📝 Rohrbuch"])

# --- TAB 1: MAßE ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Rohr & Formstücke**")
        st.markdown(f"<div class='result-box'>Außen-Ø: <b>{row['D_Aussen']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Radius (3D): <b>{custom_radius} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>T-Stück (H): <b>{row['T_Stueck_H']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Reduzierung (L): <b>{row['Red_Laenge_L']} mm</b></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"**Flansch ({selected_pn})**")
        st.markdown(f"<div class='result-box'>V-Flansch (Blatt): <b>{row[f'Flansch_b{suffix}']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Lochkreis: <b>{row[f'LK_k{suffix}']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Schrauben: <b>{row[f'Lochzahl{suffix}']}x {row[f'Schraube_M{suffix}']}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Länge (Fest-Fest): <b>{row[f'L_Fest{suffix}']} mm</b></div>", unsafe_allow_html=True)

# --- TAB 2: BOGEN ---
with tab2:
    st.caption("Bogen Zuschnitt")
    angle = st.slider("Winkel (°)", 0, 90, 45, 1)
    
    da = row['D_Aussen']
    aussen = round((custom_radius + (da/2)) * angle * (math.pi/180), 1)
    innen = round((custom_radius - (da/2)) * angle * (math.pi/180), 1)
    vorbau = round(custom_radius * math.tan(math.radians(angle/2)), 1)
    
    c1, c2 = st.columns(2)
    c1.metric("Außen (Rücken)", f"{aussen} mm")
    c2.metric("Innen (Bauch)", f"{innen} mm")
    st.markdown(f"<div class='highlight-box'>Vorbau (Zollstock): {vorbau} mm</div>", unsafe_allow_html=True)

# --- TAB 3: SÄGE (Mit der blauen Info-Box aus Bild 6) ---
with tab3:
    st.caption("Einfaches Passstück")
    iso_mass = st.number_input("Gesamtmaß (Iso)", value=1000, step=10)
    spalt = st.number_input("Wurzelspalt (Gesamt)", value=6)
    
    abzuege = st.number_input("Abzüge (z.B. 52+30)", value=0.0, step=1.0)
    
    # Die blaue Info-Box wiederhergestellt!
    st.markdown(f"""
    <div class="info-blue">
    <b>Infos für Abzüge (DN {selected_dn}):</b><br>
    • Flansch Bauhöhe: <b>{row[f'Flansch_b{suffix}']} mm</b> (V-Flansch)<br>
    • Bogen 90° (Vorbau): <b>{custom_radius} mm</b><br>
    • T-Stück (Höhe): <b>{row['T_Stueck_H']} mm</b>
    </div>
    """, unsafe_allow_html=True)
    
    saege_erg = iso_mass - spalt - abzuege
    st.markdown(f"<div class='highlight-box'>Sägelänge: {saege_erg} mm</div>", unsafe_allow_html=True)

# --- TAB 4: STUTZEN ---
with tab4:
    st.caption("Stutzen Schablone")
    dn_stutzen = st.selectbox("DN Stutzen", df['DN'], index=6)
    dn_haupt = st.selectbox("DN Hauptrohr", df['DN'], index=9)
    if dn_stutzen > dn_haupt:
        st.error("Stutzen muss kleiner sein!")
    else:
        r_k = df[df['DN'] == dn_stutzen].iloc[0]['D_Aussen'] / 2
        r_g = df[df['DN'] == dn_haupt].iloc[0]['D_Aussen'] / 2
        res = []
        for a in [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]:
            u = round((r_k*2) * math.pi * (a/360), 1)
            t = round(r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2), 1)
            res.append([f"{a}°", u, t])
        st.table(pd.DataFrame(res, columns=["Winkel", "Umfang", "Tiefe"]))

# --- TAB 5: ETAGEN (WIEDER MIT 3D AUSWAHL AUS BILD 7) ---
with tab5:
    st.markdown("### Etagen Berechnung")
    
    # Radio Button für Berechnungsart (wie in Bild 7)
    calc_type = st.radio("Berechnungsart wählen:", ["2D Einfache Etage", "3D Raum-Etage (Kastenmaß)"])
    
    col_e1, col_e2 = st.columns(2)
    spalt_etage = col_e1.number_input("Wurzelspalt (Gesamt)", value=6, key="spalt_et")
    h = col_e2.number_input("Höhe H (Versatz)", value=300)
    l = st.number_input("Länge L (Gerade)", value=400)
    
    # Logik für 3D
    b = 0.0
    if calc_type == "3D Raum-Etage (Kastenmaß)":
        b = st.number_input("Breite B (Seitlicher Versatz)", value=200)
        st.caption("Berechnung erfolgt über Diagonale im Raum")
    
    # Berechnung
    # Wahre Länge der Diagonale (Hypotenuse)
    diag_real = math.sqrt(h**2 + l**2 + b**2)
    
    # Winkel berechnen (projizierte Länge am Boden ist sqrt(l²+b²))
    l_proj = math.sqrt(l**2 + b**2)
    if l_proj > 0:
        winkel_real = math.degrees(math.atan(h / l_proj))
    else:
        winkel_real = 90.0
        
    # Abzug für Bögen (2x Vorbau mit REALEM Winkel)
    abzug_bogen = 2 * (custom_radius * math.tan(math.radians(winkel_real/2)))
    pass_etage = diag_real - abzug_bogen - spalt_etage
    
    st.info(f"Winkel: {round(winkel_real, 1)}° | Mitte-Mitte: {round(diag_real, 1)} mm")
    
    # Zeichnung (Nur bei 2D sinnvoll darstellbar, bei 3D Hinweis)
    if calc_type == "2D Einfache Etage":
        try: st.pyplot(zeichne_etage_2d(h, l, winkel_real, pass_etage))
        except: pass
    else:
        st.caption("3D-Darstellung: Werte beziehen sich auf die Raumdiagonale.")
        
    st.markdown(f"<div class='highlight-box'>Sägelänge: {round(pass_etage, 1)} mm</div>", unsafe_allow_html=True)

# --- TAB 6: ROHRBUCH (WIEDER MIT FELDERN AUS BILD 8) ---
with tab6:
    st.header("📝 Digitales Rohrbuch (Lokal)")
    st.caption("Daten werden beim Neuladen gelöscht.")
    
    with st.form("rohrbuch_form", clear_on_submit=True):
        # Zeile 1
        st.markdown("**Naht-Daten**")
        iso_val = st.text_input("ISO-Nr.", placeholder="ISO-001")
        naht_val = st.text_input("Naht-Nr.", placeholder="N-01")
        schw_val = st.text_input("Schweißer (Kürzel)")
        
        st.markdown("---")
        # Zeile 2 (Wie in Bild 8)
        c_r1, c_r2 = st.columns(2)
        dn_select = c_r1.selectbox("DN", df['DN'], index=8) # Default 150
        bauteil_select = c_r2.selectbox("Bauteil / Spool", ["Rohr", "Bogen 90°", "Bogen 45°", "T-Stück", "Reduzierung", "Flansch", "Muffe", "Nippel"])
        
        c_r3, c_r4 = st.columns(2)
        len_val = c_r3.number_input("Länge (mm)", value=0, step=10) # Das fehlte vorher!
        charge_val = c_r4.text_input("Charge / APZ-Nr.")
        
        if st.form_submit_button("Eintrag hinzufügen"):
            st.session_state.rohrbuch_data.append({
                "ISO": iso_val,
                "Naht": naht_val,
                "Schweißer": schw_val,
                "DN": dn_select,
                "Bauteil": bauteil_select,
                "Länge": len_val,
                "Charge": charge_val,
                "Datum": datetime.now().strftime("%d.%m.%Y")
            })
            st.success("Gespeichert!")

    # Tabelle & Excel Button
    if st.session_state.rohrbuch_data:
        df_rb = pd.DataFrame(st.session_state.rohrbuch_data)
        st.dataframe(df_rb, use_container_width=True)
        
        # Excel Download
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_rb.to_excel(writer, index=False)
        st.download_button("📥 Excel Download", buffer.getvalue(), f"Rohrbuch_{datetime.now().date()}.xlsx")
    else:
        st.info("Noch keine Einträge heute.")
