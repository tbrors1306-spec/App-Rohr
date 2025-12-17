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
st.set_page_config(page_title="Rohrbau Profi 6.2", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stRadio label, .stTextInput label { font-weight: bold; }
    
    .result-box { background-color: #F4F6F7; padding: 12px; border-radius: 4px; border-left: 6px solid #2980B9; color: black !important; margin-bottom: 8px; border: 1px solid #ddd; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 6px solid #27AE60; color: black !important; text-align: center; font-size: 1.3rem; font-weight: bold; margin-top: 10px; border: 1px solid #ddd; }
    .info-blue { background-color: #D6EAF8; padding: 10px; border-radius: 5px; border: 1px solid #AED6F1; color: #21618C; font-size: 0.9rem; margin-top: 10px; }
    
    .red-box { background-color: #FADBD8; padding: 12px; border-radius: 4px; border-left: 6px solid #C0392B; color: #922B21 !important; font-weight: bold; margin-top: 10px; border: 1px solid #E6B0AA; }
    
    /* Summary Styles */
    .kpi-card { background-color: #FCF3CF; padding: 15px; border-radius: 8px; border: 1px solid #F1C40F; text-align: center; margin-bottom: 10px;}
    .material-list { background-color: #EAFAF1; padding: 15px; border-radius: 5px; border: 1px solid #2ECC71; }
</style>
""", unsafe_allow_html=True)

# Session State
if 'rohrbuch_data' not in st.session_state:
    st.session_state.rohrbuch_data = []
if 'bogen_winkel' not in st.session_state:
    st.session_state.bogen_winkel = 90
if 'kalk_liste' not in st.session_state:
    st.session_state.kalk_liste = [] 

# -----------------------------------------------------------------------------
# 2. HILFSFUNKTIONEN
# -----------------------------------------------------------------------------
schrauben_db = {
    "M12": [18, 60], "M16": [24, 130], "M20": [30, 250], "M24": [36, 420],
    "M27": [41, 600], "M30": [46, 830], "M33": [50, 1100], "M36": [55, 1400],
    "M39": [60, 1800], "M45": [70, 2700], "M52": [80, 4200]
}
wandstaerken_std = {
    25: 3.2, 32: 3.6, 40: 3.6, 50: 3.9, 65: 5.2, 80: 5.5, 
    100: 6.0, 125: 6.6, 150: 7.1, 200: 8.2, 250: 9.3, 300: 9.5,
    350: 9.5, 400: 9.5, 450: 9.5, 500: 9.5
}

def get_schrauben_info(gewinde): return schrauben_db.get(gewinde, ["?", "?"])
def get_wandstaerke(dn): return wandstaerken_std.get(dn, 6.0)

def zeichne_passstueck(iso_mass, abzug1, abzug2, saegelaenge):
    fig, ax = plt.subplots(figsize=(6, 2.5))
    rohr_farbe, abzug_farbe, fertig_farbe, linie_farbe = '#ECF0F1', '#E74C3C', '#2ECC71', '#2C3E50'
    y_mitte, rohr_hoehe = 50, 40
    ax.add_patch(patches.Rectangle((0, y_mitte - rohr_hoehe/2), iso_mass, rohr_hoehe, facecolor=rohr_farbe, edgecolor=linie_farbe, hatch='///', alpha=0.3))
    if abzug1 > 0:
        ax.add_patch(patches.Rectangle((0, y_mitte - rohr_hoehe/2), abzug1, rohr_hoehe, facecolor=abzug_farbe, alpha=0.6))
        ax.text(abzug1/2, y_mitte, f"-{abzug1}", ha='center', va='center', color='white', fontweight='bold')
    if abzug2 > 0:
        start_abzug2 = iso_mass - abzug2
        ax.add_patch(patches.Rectangle((start_abzug2, y_mitte - rohr_hoehe/2), abzug2, rohr_hoehe, facecolor=abzug_farbe, alpha=0.6))
        ax.text(start_abzug2 + abzug2/2, y_mitte, f"-{abzug2}", ha='center', va='center', color='white', fontweight='bold')
    start_saege = abzug1
    ax.add_patch(patches.Rectangle((start_saege, y_mitte - rohr_hoehe/2), saegelaenge, rohr_hoehe, facecolor=fertig_farbe, edgecolor=linie_farbe, linewidth=2))
    ax.text(start_saege + saegelaenge/2, y_mitte, f"{saegelaenge} mm", ha='center', va='center', color='black', fontweight='bold')
    ax.set_xlim(-50, iso_mass + 50); ax.set_ylim(0, 100); ax.axis('off')
    return fig

def zeichne_iso_2d(h, l, winkel, passstueck):
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.plot([0, l], [0, h], color='#2C3E50', linewidth=3, zorder=2)
    ax.plot([l, l], [0, h], color='#E74C3C', linestyle='--', linewidth=1, zorder=1)
    ax.plot([0, l], [0, 0], color='#E74C3C', linestyle='--', linewidth=1, zorder=1)
    ax.scatter([0, l], [0, h], color='white', edgecolor='#2C3E50', s=60, zorder=3, linewidth=2)
    ax.text(l + 10, h/2, f"H={h}", color='#E74C3C', fontweight='bold', fontsize=8)
    ax.text(l/2, -30, f"L={l}", color='#E74C3C', fontweight='bold', ha='center', fontsize=8)
    ax.text(l/2, h/2 + 20, f"Säge: {round(passstueck, 1)}", color='#27AE60', fontweight='bold', ha='right', fontsize=9)
    ax.set_aspect('equal'); ax.axis('off')
    return fig

def zeichne_iso_raum(s, h, l, diag_raum, passstueck):
    fig, ax = plt.subplots(figsize=(2.8, 2.2))
    angle = math.radians(30); cx, cy = math.cos(angle), math.sin(angle)
    scale = 100 / max(s, h, l, 1)
    S, H, L = s*scale, h*scale, l*scale
    p_l = (L * cx, L * cy); p_ls = (p_l[0] + S * cx, p_l[1] - S * cy); p_end = (p_ls[0], p_ls[1] + H)
    ax.plot([0, p_l[0]], [0, p_l[1]], '--', color='grey', lw=0.5)
    ax.plot([p_l[0], p_ls[0]], [p_l[1], p_ls[1]], '--', color='grey', lw=0.5)
    ax.plot([p_ls[0], p_end[0]], [p_ls[1], p_end[1]], '--', color='grey', lw=0.5)
    ax.plot([0, p_end[0]], [0, p_end[1]], color='#2C3E50', lw=2.5)
    ax.scatter([0, p_end[0]], [0, p_end[1]], color='white', edgecolor='#2C3E50', s=40, zorder=5)
    ax.text(p_end[0]/2, p_end[1]/2 + 10, f"Säge: {round(passstueck)}", color='#27AE60', fontweight='bold', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    ax.set_aspect('equal'); ax.axis('off')
    return fig

def zeichne_stutzen_abwicklung(df_coords):
    fig, ax = plt.subplots(figsize=(4.0, 2.0))
    ax.plot(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#2980B9', linewidth=2)
    ax.fill_between(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#D6EAF8', alpha=0.5)
    ax.set_xlabel("Winkel (°)", fontsize=8); ax.set_ylabel("Tiefe (mm)", fontsize=8)
    ax.set_title("Schnittkurve", fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5); ax.set_xticks([0, 90, 180, 270, 360])
    plt.tight_layout()
    return fig

# -----------------------------------------------------------------------------
# 3. DATENBANK
# -----------------------------------------------------------------------------
data = {
    'DN':           [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600],
    'D_Aussen':     [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0, 711.0, 813.0, 914.0, 1016.0, 1219.0, 1422.0, 1626.0],
    'Radius_BA3':   [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914, 1067, 1219, 1372, 1524, 1829, 2134, 2438],
    'T_Stueck_H':   [25, 32, 38, 51, 64, 76, 105, 124, 143, 178, 216, 254, 279, 305, 343, 381, 432, 521, 597, 673, 749, 889, 1029, 1168],
    'Red_Laenge_L': [38, 50, 64, 76, 89, 89, 102, 127, 140, 152, 178, 203, 330, 356, 381, 508, 508, 610, 660, 711, 800, 900, 1000, 1100], 
    'Flansch_b_16': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_16':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 355, 410, 470, 525, 585, 650, 770, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_16':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M33", "M33", "M36", "M36", "M39", "M45", "M45", "M52"],
    'L_Fest_16':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 100, 110, 110, 120, 130, 130, 150, 160, 170, 180, 190, 220, 240, 260],
    'L_Los_16':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 115, 125, 130, 140, 150, 150, 170, 180, 190, 210, 220, 250, 280, 300],
    'Lochzahl_16':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 12, 12, 12, 16, 16, 20, 20, 20, 24, 24, 28, 28, 32, 36, 40],
    'Flansch_b_10': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_10':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 350, 400, 460, 515, 565, 620, 725, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_10':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M20", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M30", "M33", "M36", "M39", "M45"],
    'L_Fest_10':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 90, 90, 90, 100, 110, 110, 120, 130, 140, 150, 160, 190, 210, 230],
    'L_Los_10':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 105, 105, 110, 120, 130, 130, 140, 150, 160, 170, 180, 210, 240, 260],
    'Lochzahl_10':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 12, 12, 16, 16, 20, 20, 20, 20, 24, 28, 28, 32, 36, 40]
}
df = pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 4. APP LOGIK
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Einstellungen")
selected_dn = st.sidebar.selectbox("Nennweite (DN)", df['DN'], index=8) 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0)

# Auto-Sync für Kalkulations-Tabs
current_dn_index = df['DN'].tolist().index(selected_dn)
row = df[df['DN'] == selected_dn].iloc[0]
standard_radius = float(row['Radius_BA3']) 

st.title(f"Rohrbau Profi (DN {selected_dn})")
suffix = "_16" if selected_pn == "PN 16" else "_10"

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["📋 Maße", "🔧 Montage", "🔄 Bogen", "📏 Säge", "🔥 Stutzen", "📐 Etagen", "📝 Rohrbuch", "💰 Kalkulation", "📊 Projekt-Summe"])

# --- TAB 1: MAßE ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Rohr & Formstücke**")
        st.markdown(f"<div class='result-box'>Außen-Ø: <b>{row['D_Aussen']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Radius (3D): <b>{standard_radius} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>T-Stück (H): <b>{row['T_Stueck_H']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Reduzierung (L): <b>{row['Red_Laenge_L']} mm</b></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"**Flansch ({selected_pn})**")
        st.markdown(f"<div class='result-box'>Flansch (Blatt): <b>{row[f'Flansch_b{suffix}']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Lochkreis: <b>{row[f'LK_k{suffix}']} mm</b></div>", unsafe_allow_html=True)

# --- TAB 2: MONTAGE ---
with tab2:
    st.header("Schlüsselweiten & Drehmomente")
    schraube = row[f'Schraube_M{suffix}']
    anzahl = row[f'Lochzahl{suffix}']
    sw, nm = get_schrauben_info(schraube)
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Schraubengröße", schraube)
    col_m1.caption(f"Anzahl: {anzahl} Stück")
    col_m2.metric("Schlüsselweite (SW)", f"{sw} mm")
    col_m3.metric("Drehmoment (ca.)", f"{nm} Nm")
    
    st.markdown("---")
    st.header("Schraubenlängen")
    l_fest = row[f'L_Fest{suffix}']
    l_los = row[f'L_Los{suffix}']
    
    c_len1, c_len2 = st.columns(2)
    with c_len1:
        st.markdown(f"<div class='result-box'>Länge (Fest-Fest): <b>{l_fest} mm</b></div>", unsafe_allow_html=True)
    with c_len2:
        st.markdown(f"<div class='result-box' style='border-left: 6px solid #8E44AD;'>Länge (Fest-Los): <b>{l_los} mm</b></div>", unsafe_allow_html=True)
    
    st.markdown("""<div class="red-box"><b>⚠️ WICHTIG:</b> Die angegebenen Drehmomente gelten für Schrauben, die <b>mit Molykote eingeschmiert</b> sind (Reibungszahl µ ≈ 0,10). Bei Öl oder Trockenmontage stimmen die Werte nicht!</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="red-box"><b>⚠️ ACHTUNG GGG:</b> Bei Verbindungen mit Gusseisen-Flanschen (GGG) sind die Flanschblätter oft dicker als bei Stahl. Bitte Klemmlänge prüfen! (Meist +10mm Bolzenlänge nötig).</div>""", unsafe_allow_html=True)

# --- TAB 3: BOGEN ---
with tab3:
    st.caption("Bogen Zuschnitt")
    angle = st.slider("Winkel (°)", 0, 90, 45, 1, key="bogen_winkel")
    da = row['D_Aussen']
    aussen = round((standard_radius + (da/2)) * angle * (math.pi/180), 1)
    innen = round((standard_radius - (da/2)) * angle * (math.pi/180), 1)
    vorbau = round(standard_radius * math.tan(math.radians(angle/2)), 1)
    c1, c2 = st.columns(2)
    c1.metric("Außen (Rücken)", f"{aussen} mm")
    c2.metric("Innen (Bauch)", f"{innen} mm")
    st.markdown(f"<div class='highlight-box'>Vorbau (Zollstock): {vorbau} mm</div>", unsafe_allow_html=True)

# --- TAB 4: SÄGE ---
with tab4:
    st.caption("Einfaches Passstück")
    iso_mass = st.number_input("Gesamtmaß (Iso)", value=1000, step=10)
    spalt = st.number_input("Wurzelspalt (Gesamt)", value=6)
    abzuege = st.number_input("Abzüge (z.B. 52+30)", value=0.0, step=1.0)
    
    winkel_aus_tab2 = st.session_state.get("bogen_winkel", 45)
    vorbau_tab2 = int(round(standard_radius * math.tan(math.radians(winkel_aus_tab2/2)), 0))

    st.markdown(f"""
    <div class="info-blue">
    <b>Infos für Abzüge (DN {selected_dn}):</b><br>
    • Flansch Bauhöhe: <b>{row[f'Flansch_b{suffix}']} mm</b><br>
    • Bogen 90° (Vorbau): <b>{standard_radius} mm</b><br>
    • Bogen {winkel_aus_tab2}° (aus Tab Bogen): <b>{vorbau_tab2} mm</b>
    </div>
    """, unsafe_allow_html=True)
    
    saege_erg = iso_mass - spalt - abzuege
    st.markdown(f"<div class='highlight-box'>Sägelänge: {saege_erg} mm</div>", unsafe_allow_html=True)

# --- TAB 5: STUTZEN ---
with tab5:
    
    st.caption("Stutzen Schablone (Zentrisch)")
    c_st1, c_st2 = st.columns(2)
    dn_stutzen = c_st1.selectbox("DN Stutzen (Abzweig)", df['DN'], index=6)
    dn_haupt = c_st2.selectbox("DN Hauptrohr (Run)", df['DN'], index=9)
    
    if dn_stutzen > dn_haupt:
        st.error("⚠️ Fehler: Der Stutzen darf nicht größer als das Hauptrohr sein!")
    else:
        r_k = df[df['DN'] == dn_stutzen].iloc[0]['D_Aussen'] / 2
        r_g = df[df['DN'] == dn_haupt].iloc[0]['D_Aussen'] / 2
        
        plot_data = []
        for a in range(0, 361, 5): 
            u = (r_k*2) * math.pi * (a/360)
            t = r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2)
            plot_data.append([a, u, t])
            
        table_data = []
        schritte = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]
        for a in schritte:
            u = int(round((r_k*2) * math.pi * (a/360), 0))
            t = int(round(r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2), 0))
            table_data.append([f"{a}°", u, t])

        df_plot = pd.DataFrame(plot_data, columns=["Winkel_Raw", "Umfang", "Tiefe (mm)"])
        c_res1, c_res2 = st.columns([1, 2])
        with c_res1:
            st.table(pd.DataFrame(table_data, columns=["Winkel", "Umfang (mm)", "Tiefe (mm)"]))
        with c_res2:
            st.pyplot(zeichne_stutzen_abwicklung(df_plot))

# --- TAB 6: ETAGEN ---
with tab6:
    calc_type = st.radio("Berechnungsart wählen:", 
                         ["2D Einfache Etage", 
                          "3D Raum-Etage (Kastenmaß)", 
                          "3D Raum-Etage (Fix-Winkel)"])
    st.markdown("---")
    spalt_etage = st.number_input("Wurzelspalt (Gesamt)", value=6, key="spalt_et")

    # MODUS 1: 2D
    if calc_type == "2D Einfache Etage":
        col_e1, col_e2 = st.columns(2)
        h = col_e1.number_input("Höhe H (Versatz)", value=300)
        l = st.number_input("Länge L (Gerade)", value=400)
        winkel = math.degrees(math.atan(h/l)) if l > 0 else 90
        diag = math.sqrt(h**2 + l**2)
        abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
        pass_etage = diag - abzug - spalt_etage
        st.info(f"Winkel: {round(winkel, 1)}° | Diagonale: {round(diag, 1)} mm")
        try: st.pyplot(zeichne_iso_2d(h, l, winkel, pass_etage))
        except: pass
        st.markdown(f"<div class='highlight-box'>Sägelänge: {round(pass_etage, 1)} mm</div>", unsafe_allow_html=True)

    # MODUS 2: 3D Kastenmaß (Rolling Offset)
    elif calc_type == "3D Raum-Etage (Kastenmaß)":
        st.caption("Berechnet den Winkel aus den Maßen (H, B, L)")
        c1, c2, c3 = st.columns(3)
        b = c1.number_input("Breite (Seite/Roll)", value=200)
        h = c2.number_input("Höhe (Auf/Set)", value=300)
        l = c3.number_input("Länge (Vor/Run)", value=400)
        
        diag_raum = math.sqrt(h**2 + l**2 + b**2) # Travel
        l_proj = math.sqrt(l**2 + b**2)
        
        spread = math.sqrt(b**2 + h**2)
        winkel = math.degrees(math.atan(spread / l)) if l > 0 else 90
        
        abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
        pass_etage = diag_raum - abzug - spalt_etage
        
        st.write(f"Spreizung (Spread): **{round(spread, 1)} mm**")
        st.info(f"Benötigter Bogen: {round(winkel, 1)}° | Raum-Diagonale: {round(diag_raum, 1)} mm")
        try: st.pyplot(zeichne_iso_raum(b, h, l, diag_raum, pass_etage))
        except: pass
        st.markdown(f"<div class='highlight-box'>Sägelänge: {round(pass_etage, 1)} mm</div>", unsafe_allow_html=True)

    # MODUS 3: 3D Fix-Winkel (Länge suchen)
    elif calc_type == "3D Raum-Etage (Fix-Winkel)":
        st.caption("Berechnet die Länge (Run) bei festem Bogen (z.B. 45°)")
        c1, c2 = st.columns(2)
        b = c1.number_input("Breite (Seite/Roll)", value=200)
        h = c2.number_input("Höhe (Auf/Set)", value=300)
        fix_winkel = st.selectbox("Vorhandener Bogen (°)", [15, 30, 45, 60, 90], index=2)
        
        spread = math.sqrt(b**2 + h**2)
        
        if fix_winkel > 0 and fix_winkel < 90:
            l_notwendig = spread / math.tan(math.radians(fix_winkel))
            diag_raum = math.sqrt(b**2 + h**2 + l_notwendig**2)
            abzug = 2 * (standard_radius * math.tan(math.radians(fix_winkel/2)))
            pass_etage = diag_raum - abzug - spalt_etage
            
            st.write(f"Spreizung (Spread): **{round(spread, 1)} mm**")
            st.write(f"Du musst **{round(l_notwendig, 1)} mm** in der Länge (Run) verziehen.")
            st.info(f"Raum-Diagonale: {round(diag_raum, 1)} mm")
            
            try: st.pyplot(zeichne_iso_raum(b, h, l_notwendig, diag_raum, pass_etage))
            except: pass
            st.markdown(f"<div class='highlight-box'>Sägelänge: {round(pass_etage, 1)} mm</div>", unsafe_allow_html=True)
        else:
            st.error("Winkel muss zwischen 0 und 90 Grad liegen.")

# --- TAB 7: ROHRBUCH ---
with tab7:
    st.header("📝 Digitales Rohrbuch")
    with st.form("rohrbuch_form", clear_on_submit=True):
        col_r1, col_r2, col_r3 = st.columns(3)
        iso_nr = col_r1.text_input("ISO / Leitungs-Nr.", placeholder="z.B. L-1001")
        naht_nr = col_r2.text_input("Naht-Nr.", placeholder="z.B. N-01")
        datum = col_r3.date_input("Datum", datetime.today())
        
        col_r4, col_r5, col_r6 = st.columns(3)
        rb_dn = col_r4.selectbox("Dimension (DN)", df['DN'], index=8)
        rb_bauteil = col_r5.selectbox("Bauteil", ["Rohr", "Bogen", "Flansch (V)", "Flansch (Blind)", "Muffe", "Nippel", "T-Stück", "Reduzierung"])
        rb_laenge = col_r5.number_input("Länge (mm)", value=0)
        
        with col_r6:
            charge = st.text_input("Charge / APZ-Nr.")
            schweisser = st.text_input("Schweißer-Kürzel")
        
        if st.form_submit_button("Eintrag hinzufügen"):
            st.session_state.rohrbuch_data.append({
                "ISO": iso_nr, "Naht": naht_nr, "Datum": datum.strftime("%d.%m.%Y"),
                "Dimension": f"DN {rb_dn}", "Bauteil": rb_bauteil, "Länge": rb_laenge,
                "Charge": charge, "Schweißer": schweisser
            })
            st.success("Gespeichert!")

    if len(st.session_state.rohrbuch_data) > 0:
        df_rb = pd.DataFrame(st.session_state.rohrbuch_data)
        st.dataframe(df_rb, use_container_width=True)
        
        c_down, c_del1, c_del2 = st.columns([2,1,1])
        with c_down:
            buffer = BytesIO()
            try:
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_rb.to_excel(writer, index=False)
                st.download_button("📥 Excel Download", buffer.getvalue(), f"Rohrbuch_{datetime.now().date()}.xlsx")
            except:
                st.error("Excel-Export Fehler (openpyxl fehlt).")
        with c_del1:
            if st.button("↩️ Letzten Eintrag löschen"):
                st.session_state.rohrbuch_data.pop()
                st.rerun()
        with c_del2:
            if st.button("🗑️ Alles löschen"):
                st.session_state.rohrbuch_data = []
                st.rerun()
    else:
        st.caption("Noch keine Einträge vorhanden.")

# --- TAB 8: KALKULATION ---
with tab8:
    st.header("💰 Kosten & Zeit Kalkulation")
    
    kalk_mode = st.radio("Was möchtest du berechnen?", 
                         ["🔥 Schweißnaht & Vorbereitung", 
                          "✂️ Schnittkosten & Verschleiß",
                          "🛡️ Nachumhüllung (WKS / Binden)"], 
                         horizontal=True)
    st.markdown("---")

    # -------------------------------------------------------------------------
    # MODUS 1: SCHWEISSNAHT
    # -------------------------------------------------------------------------
    if kalk_mode == "🔥 Schweißnaht & Vorbereitung":
        c1, c2, c3 = st.columns(3)
        kd_dn = c1.selectbox("Dimension (DN)", df['DN'], index=current_dn_index, key="kalk_dn")
        std_ws = get_wandstaerke(kd_dn)
        kd_ws = c2.number_input("Stahl-Wandstärke (mm)", value=std_ws, step=0.1, format="%.1f")
        kd_verf = c3.selectbox("Verfahren", ["WIG", "E-Hand (CEL 70)", "WIG (Wurzel) + E-Hand", "MAG (Fülldraht)"])
        
        st.markdown("#### 🚧 Erschwernisse")
        col_z1, col_z2 = st.columns(2)
        has_zma = col_z1.checkbox("Innen: Beton/ZMA?", help="Zeit für Einschneiden/Ausbrechen")
        has_iso = col_z2.checkbox("Außen: Umhüllung?", help="Zeit für Wegbrennen/Schälen")

        da = df[df['DN'] == kd_dn].iloc[0]['D_Aussen']
        umfang = da * math.pi
        
        # Schweißzeit
        querschnitt_mm2 = (kd_ws ** 2) * 0.8 + (kd_ws * 1.5) 
        vol_cm3 = (umfang * querschnitt_mm2) / 1000
        gewicht_kg = (vol_cm3 * 7.85) / 1000
        
        gas_l_min = 0 
        if "WIG" == kd_verf:
            leistung = 0.5; faktor_nebenzeit = 0.15; gas_l_min = 10
        elif "WIG (Wurzel)" in kd_verf: 
            leistung = 0.6; faktor_nebenzeit = 0.2; gas_l_min = 10 
        elif "MAG" in kd_verf: 
            leistung = 2.8; faktor_nebenzeit = 0.25; gas_l_min = 15
        elif "E-Hand" in kd_verf:
            leistung = 1.2; faktor_nebenzeit = 0.4 

        arc_time_min = (gewicht_kg / leistung) * 60
        
        # Nebenarbeiten
        zoll = kd_dn / 25
        zeit_vorrichten = zoll * 3.0 
        zeit_neben = arc_time_min * faktor_nebenzeit
        
        zeit_zma = (kd_dn / 100) * 2.5 if has_zma else 0
        zeit_iso = (kd_dn / 100) * 3.5 if has_iso else 0
        
        total_arbeit_min = arc_time_min + zeit_vorrichten + zeit_neben + zeit_zma + zeit_iso
        gas_total = arc_time_min * gas_l_min

        st.subheader(f"Kalkulation pro Naht (DN {kd_dn})")
        
        # --- ERGEBNISSE OBEN ---
        c_time1, c_time2 = st.columns(2)
        c_time1.metric("Gesamtzeit (1 Naht)", f"{int(total_arbeit_min)} min", f"ca. {round(total_arbeit_min/60, 2)} Std.")
        
        anzahl = c_time2.number_input("Anzahl Nähte", value=1, step=1)
        
        # LOGIK FÜR BUTTON: SPEICHERN MIT LABEL
        mat_1_label = "Zusatzwerkstoff (kg)"
        mat_1_val = gewicht_kg * anzahl
        mat_2_label = "Gas (Liter)"
        mat_2_val = gas_total * anzahl
        
        if "CEL 70" in kd_verf:
            # CEL Spezial (Stückzahl speichern)
            # Gewichtung neu: Wurzel 20%, Füll 50%, Deck 30%
            # Hinweis: Wir speichern hier nur Wurzel und Füll/Deck summiert als Labeltext, da die Struktur nur 2 Mat-Spalten hat
            # Workaround: Mat_1 = Wurzel Stk, Mat_2 = Füll+Deck Stk
            w_root = gewicht_kg * 0.20
            w_rest = gewicht_kg * 0.80
            stueck_root = math.ceil(w_root / 0.018)
            # Für die Summe nehmen wir einen Durchschnitt der Füll/Deck Elektrode an (ca 4.5mm)
            stueck_rest = math.ceil(w_rest / 0.035) 
            
            mat_1_label = "CEL 3.2 (Stk)"
            mat_1_val = stueck_root * anzahl
            mat_2_label = "CEL Füll/Deck (Stk)"
            mat_2_val = stueck_rest * anzahl

        if st.button("➕ Zu Projekt-Summe hinzufügen", key="btn_weld"):
            st.session_state.kalk_liste.append({
                "Typ": "Schweißen",
                "Info": f"DN {kd_dn} ({kd_verf})",
                "Menge": anzahl,
                "Zeit_Min": total_arbeit_min * anzahl,
                "Mat_1_Label": mat_1_label, "Mat_1_Val": mat_1_val,
                "Mat_2_Label": mat_2_label, "Mat_2_Val": mat_2_val
            })
            st.success(f"{anzahl}x DN {kd_dn} hinzugefügt!")
            
        st.markdown("---")
        
        # --- DETAILS MITTE ---
        c_det1, c_det2 = st.columns(2)
        with c_det1:
            st.markdown("**Zeit-Aufschlüsselung:**")
            st.write(f"• Vorrichten/Heften: **{int(zeit_vorrichten)} min**")
            st.write(f"• Reines Schweißen: **{int(arc_time_min)} min**")
            st.write(f"• Putzen/Wechseln: **{int(zeit_neben)} min**")
        with c_det2:
            st.markdown("**Erschwernisse:**")
            st.write(f"• ZMA entfernen: **{int(zeit_zma)} min**")
            st.write(f"• Umhüllung entf.: **{int(zeit_iso)} min**")
            
        st.markdown("---")
        
        # --- MATERIAL UNTEN ---
        st.markdown("##### Materialbedarf pro Naht")
        
        if "CEL 70" in kd_verf:
            c_sel_el1, c_sel_el2 = st.columns(2)
            d_fill = c_sel_el1.radio("Ø Fülllage", ["4.0 mm", "5.0 mm"], horizontal=True)
            d_cap = c_sel_el2.radio("Ø Decklage", ["4.0 mm", "5.0 mm"], horizontal=True)
            
            w_root = gewicht_kg * 0.20
            w_fill = gewicht_kg * 0.50
            w_cap = gewicht_kg * 0.30
            
            stueck_root = math.ceil(w_root / 0.018) 
            
            w_per_stick_fill = 0.045 if d_fill == "5.0 mm" else 0.028
            stueck_fill = math.ceil(w_fill / w_per_stick_fill)
            
            w_per_stick_cap = 0.045 if d_cap == "5.0 mm" else 0.028
            stueck_cap = math.ceil(w_cap / w_per_stick_cap)
            
            c_mat1, c_mat2, c_mat3 = st.columns(3)
            c_mat1.metric("Wurzel (CEL 3.2)", f"ca. {stueck_root} Stk.")
            c_mat2.metric(f"Füll (CEL {d_fill})", f"ca. {stueck_fill} Stk.")
            c_mat3.metric(f"Deck (CEL {d_cap})", f"ca. {stueck_cap} Stk.")
            st.caption(f"Gesamtgewicht Eisen: {round(gewicht_kg, 2)} kg")
            
        else:
            c_mat1, c_mat2 = st.columns(2)
            c_mat1.metric("Zusatzmaterial (Draht/Stab)", f"{round(gewicht_kg, 2)} kg")
            if gas_l_min > 0:
                c_mat2.metric(f"Schweißgas ({gas_l_min} l/min)", f"ca. {int(gas_total)} Liter")
            else:
                c_mat2.metric("Schweißgas", "-")


    # -------------------------------------------------------------------------
    # MODUS 2: SCHNITTKOSTEN
    # -------------------------------------------------------------------------
    elif kalk_mode == "✂️ Schnittkosten & Verschleiß":
        st.caption("Berechnet Trennscheiben (Stahl) und Diamantscheiben (ZMA) getrennt.")
        
        col_cut1, col_cut2, col_cut3 = st.columns(3)
        cut_dn = col_cut1.selectbox("Dimension (DN)", df['DN'], index=current_dn_index, key="cut_dn")
        cut_anzahl = col_cut2.number_input("Anzahl Schnitte", value=10, step=1)
        cut_zma = col_cut3.checkbox("Rohr hat Beton (ZMA)?", value=True)
        
        row_c = df[df['DN'] == cut_dn].iloc[0]
        da = row_c['D_Aussen']
        ws_std = get_wandstaerke(cut_dn)
        di = da - (2 * ws_std)
        
        flaeche_aussen = (math.pi * (da/2)**2)
        flaeche_innen = (math.pi * (di/2)**2)
        schnittflaeche_stahl_cm2 = ((flaeche_aussen - flaeche_innen) * cut_anzahl) / 100
        
        n_scheiben_125_stahl = math.ceil(schnittflaeche_stahl_cm2 / 200)
        n_scheiben_180_stahl = math.ceil(schnittflaeche_stahl_cm2 / 350)
        n_scheiben_diamant = 0
        if cut_zma:
            umfang_m = (da * math.pi) / 1000
            total_schnittweg_m = umfang_m * cut_anzahl
            n_scheiben_diamant = math.ceil(total_schnittweg_m / 60)
        
        if st.button("➕ Zu Projekt-Summe hinzufügen", key="btn_cut"):
            st.session_state.kalk_liste.append({
                "Typ": "Schneiden",
                "Info": f"DN {cut_dn} ({'ZMA' if cut_zma else 'Stahl'})",
                "Menge": cut_anzahl,
                "Zeit_Min": 0, 
                "Mat_1_Label": "Stahl-Scheiben (Stk)", "Mat_1_Val": n_scheiben_125_stahl + n_scheiben_180_stahl,
                "Mat_2_Label": "Diamant-Scheiben (Stk)", "Mat_2_Val": n_scheiben_diamant
            })
            st.success(f"{cut_anzahl} Schnitte hinzugefügt!")

        st.markdown("### Materialbedarf Schätzung")
        c_res1, c_res2, c_res3 = st.columns(3)
        with c_res1: st.metric("Stahl-Scheiben 125mm", f"{n_scheiben_125_stahl} Stk.")
        with c_res2: st.metric("Stahl-Scheiben 180mm", f"{n_scheiben_180_stahl} Stk.")
        with c_res3: 
            if cut_zma: st.metric("Diamant-Scheiben", f"{n_scheiben_diamant} Stk.")
            else: st.metric("Diamant-Scheiben", "-")

    # -------------------------------------------------------------------------
    # MODUS 3: NACHUMHÜLLUNG
    # -------------------------------------------------------------------------
    elif kalk_mode == "🛡️ Nachumhüllung (WKS / Binden)":
        
        iso_typ = st.radio("System wählen:", ["Schrumpf-Manschette (WKS)", "Kebu Zweibandsystem (C 50-C)", "Kebu Einbandsystem (B80-C)"], horizontal=True)
        
        c_iso1, c_iso2, c_iso3 = st.columns(3)
        iso_dn = c_iso1.selectbox("Dimension (DN)", df['DN'], index=current_dn_index, key="iso_dn")
        iso_anzahl = c_iso2.number_input("Anzahl Nähte", value=1, step=1)
        
        row_w = df[df['DN'] == iso_dn].iloc[0]
        da = row_w['D_Aussen']
        umfang_mm = da * math.pi
        
        if iso_typ == "Schrumpf-Manschette (WKS)":
            st.caption("Standard WKS Feldnaht")
            wks_test = c_iso3.checkbox("Inkl. Porenprüfung (Iso-Test)?")
            laenge_manschette_mm = umfang_mm + 150 
            
            zeit_vorbereitung = 8 + (iso_dn * 0.04)
            zeit_schrumpfen = 8 + (iso_dn * 0.03)
            zeit_test = 5 if wks_test else 0
            total_zeit_min = (zeit_vorbereitung + zeit_schrumpfen + zeit_test) * iso_anzahl
            gas_kg = (0.15 + (iso_dn * 0.001)) * iso_anzahl
            
            if st.button("➕ Zu Projekt-Summe hinzufügen", key="btn_wks"):
                st.session_state.kalk_liste.append({
                    "Typ": "WKS",
                    "Info": f"DN {iso_dn} Schrumpfen",
                    "Menge": iso_anzahl,
                    "Zeit_Min": total_zeit_min,
                    "Mat_1_Label": "Manschetten (Stk)", "Mat_1_Val": iso_anzahl,
                    "Mat_2_Label": "Propangas (kg)", "Mat_2_Val": gas_kg
                })
                st.success("WKS hinzugefügt!")
            
            st.markdown("### Bedarf WKS")
            c_res1, c_res2, c_res3 = st.columns(3)
            c_res1.metric("Arbeitszeit Gesamt", f"{int(total_zeit_min)} min")
            c_res2.metric("Propangas", f"{round(gas_kg, 1)} kg")
            c_res3.metric("Zuschnitt pro Naht", f"{int(laenge_manschette_mm)} mm")
            
        else:
            is_zweiband = "Zweibandsystem" in iso_typ
            sys_name = "Kebu C 50-C" if is_zweiband else "Kebu B80-C"
            st.caption(f"System: {sys_name} (4-lagig)")
            
            c_kebu1, c_kebu2 = st.columns(2)
            band_breite = c_kebu1.selectbox("Bandbreite", [50, 100], index=1 if iso_dn > 100 else 0)
            std_len_inner = 10 if is_zweiband else 15
            std_len_outer = 25 if is_zweiband else 15
            
            with c_kebu2:
                if is_zweiband:
                    len_inner = st.number_input("Rollenlänge Innen (1,2 H)", value=std_len_inner)
                    len_outer = st.number_input("Rollenlänge Außen (PE 0,50)", value=std_len_outer)
                else:
                    len_inner = st.number_input("Rollenlänge (B80-C)", value=std_len_inner)
                    len_outer = len_inner 
            
            kebu_test = st.checkbox("Inkl. Porenprüfung (Iso-Test)?")
            
            zone_breite_m = 0.5 
            rohr_flaeche_naht_m2 = (umfang_mm / 1000) * zone_breite_m
            voranstrich_liter = rohr_flaeche_naht_m2 * 0.20 * iso_anzahl 
            zeit_wickeln = 5 + (iso_dn * 0.07) 
            zeit_test = 5 if kebu_test else 0
            total_zeit_min = (20 + zeit_wickeln + zeit_test) * iso_anzahl 
            
            if is_zweiband:
                flaeche_inner = rohr_flaeche_naht_m2 * 2.2
                lm_inner = flaeche_inner / (band_breite / 1000)
                rollen_inner = math.ceil((lm_inner * iso_anzahl) / len_inner) 
                flaeche_outer = rohr_flaeche_naht_m2 * 2.2
                lm_outer = flaeche_outer / (band_breite / 1000)
                rollen_outer = math.ceil((lm_outer * iso_anzahl) / len_outer)
                
                mat_1_label = f"Kebulen 1.2 H ({len_inner}m)"
                mat_1_val = rollen_inner
                mat_2_label = f"Kebulen PE 0.50 ({len_outer}m)"
                mat_2_val = rollen_outer
            else:
                benoetigte_bandflaeche_m2 = rohr_flaeche_naht_m2 * 4.4 
                laufmeter_band = benoetigte_bandflaeche_m2 / (band_breite / 1000)
                anzahl_rollen = math.ceil((laufmeter_band * iso_anzahl) / len_inner)
                mat_1_label = f"B80-C ({len_inner}m)"
                mat_1_val = anzahl_rollen
                mat_2_label = "Voranstrich K III (l)"
                mat_2_val = voranstrich_liter

            if st.button("➕ Zu Projekt-Summe hinzufügen", key="btn_kebu"):
                st.session_state.kalk_liste.append({
                    "Typ": sys_name,
                    "Info": f"DN {iso_dn} Wickeln",
                    "Menge": iso_anzahl,
                    "Zeit_Min": total_zeit_min,
                    "Mat_1_Label": mat_1_label, "Mat_1_Val": mat_1_val,
                    "Mat_2_Label": mat_2_label, "Mat_2_Val": mat_2_val
                })
                st.success("Kebu hinzugefügt!")

            st.markdown(f"### Materialbedarf {sys_name}")
            c1, c2 = st.columns(2)
            c1.metric(mat_1_label, f"{mat_1_val} Rollen")
            c2.metric(mat_2_label, f"{round(mat_2_val, 1)} Stk/Liter")
            st.info(f"Zeit (inkl. Trocknen & Test): **{int(total_zeit_min)} min**")

# --- TAB 9: PROJEKT SUMME (NEU) ---
with tab9:
    st.header("📊 Projekt-Zusammenfassung")
    
    if len(st.session_state.kalk_liste) > 0:
        
        # DataFrame für Anzeige aufbereiten
        display_data = []
        for item in st.session_state.kalk_liste:
            # Kombiniere Mat 1 und Mat 2 für lesbare Tabelle
            mat_info = ""
            if item.get("Mat_1_Val", 0) > 0:
                mat_info += f"{round(item['Mat_1_Val'], 1)} {item.get('Mat_1_Label', '')} "
            if item.get("Mat_2_Val", 0) > 0:
                if mat_info: mat_info += " | "
                mat_info += f"{round(item['Mat_2_Val'], 1)} {item.get('Mat_2_Label', '')}"
            
            display_data.append({
                "Typ": item["Typ"],
                "Details": item["Info"],
                "Menge": item["Menge"],
                "Zeit (h)": round(item["Zeit_Min"] / 60, 1),
                "Material-Details": mat_info
            })
            
        df_display = pd.DataFrame(display_data)
        
        # Gesamtzeit
        total_min = sum(item["Zeit_Min"] for item in st.session_state.kalk_liste)
        total_h = round(total_min / 60, 1)
        
        # KPI Cards
        k1, k2 = st.columns(2)
        k1.metric("Gesamt-Arbeitszeit", f"{total_h} Std.")
        k2.metric("Positionen", len(st.session_state.kalk_liste))
        
        st.dataframe(df_display, use_container_width=True)
        
        # --- INTELLIGENTE MATERIAL-ZUSAMMENFASSUNG (SHOPPING LIST) ---
        st.markdown("#### 🛒 Material-Bestellliste (Summiert)")
        
        # Dictionary zum Sammeln gleicher Materialien
        material_sums = {} 
        
        for item in st.session_state.kalk_liste:
            # Check Mat 1
            if item.get("Mat_1_Val", 0) > 0:
                lbl = item.get("Mat_1_Label", "Sonstiges")
                val = item.get("Mat_1_Val", 0)
                material_sums[lbl] = material_sums.get(lbl, 0) + val
            # Check Mat 2
            if item.get("Mat_2_Val", 0) > 0:
                lbl = item.get("Mat_2_Label", "Sonstiges")
                val = item.get("Mat_2_Val", 0)
                material_sums[lbl] = material_sums.get(lbl, 0) + val
        
        # Anzeige als saubere Liste
        if material_sums:
            cols = st.columns(3)
            idx = 0
            for label, value in material_sums.items():
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="material-list">
                    <b>{label}</b><br>
                    <span style="font-size: 1.5em; font-weight: bold;">{round(value, 1)}</span>
                    </div>
                    """, unsafe_allow_html=True)
                idx += 1
        
        st.markdown("---")
        
        # Buttons
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("🗑️ Projekt-Liste leeren"):
            st.session_state.kalk_liste = []
            st.rerun()
            
        buffer = BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_display.to_excel(writer, sheet_name="Positionen", index=False)
                # Material Sheet
                df_mat = pd.DataFrame(list(material_sums.items()), columns=["Material", "Menge"])
                df_mat.to_excel(writer, sheet_name="Material_Summe", index=False)
            c_btn2.download_button("📥 Download Excel", buffer.getvalue(), f"Kalkulation_{datetime.now().date()}.xlsx")
        except:
            st.error("Excel Fehler")
            
    else:
        st.info("Noch keine Positionen. Nutze den '➕' Button in Tab 8.")
