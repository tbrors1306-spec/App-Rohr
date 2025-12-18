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
st.set_page_config(page_title="Rohrbau Profi 8.0", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stRadio label, .stTextInput label { font-weight: bold; }
    
    .result-box { background-color: #F4F6F7; padding: 12px; border-radius: 4px; border-left: 6px solid #2980B9; color: black !important; margin-bottom: 8px; border: 1px solid #ddd; }
    .red-box { background-color: #FADBD8; padding: 12px; border-radius: 4px; border-left: 6px solid #C0392B; color: #922B21 !important; font-weight: bold; margin-top: 10px; border: 1px solid #E6B0AA; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 6px solid #27AE60; color: black !important; text-align: center; font-size: 1.3rem; font-weight: bold; margin-top: 10px; border: 1px solid #ddd; }
    .info-blue { background-color: #D6EAF8; padding: 10px; border-radius: 5px; border: 1px solid #AED6F1; color: #21618C; font-size: 0.9rem; margin-top: 10px; border-left: 5px solid #2980B9;}
    
    .kpi-card { background-color: #FCF3CF; padding: 15px; border-radius: 8px; border: 1px solid #F1C40F; text-align: center; margin-bottom: 10px;}
    .material-list { background-color: #EAFAF1; padding: 10px; border-radius: 5px; border: 1px solid #2ECC71; font-size: 0.9rem; margin-bottom: 5px; }
    .stDataFrame { border: 1px solid #000; }
</style>
""", unsafe_allow_html=True)

# Session State Initialisierung
if 'rohrbuch_data' not in st.session_state:
    st.session_state.rohrbuch_data = []
if 'kalk_liste' not in st.session_state:
    st.session_state.kalk_liste = [] 
if 'bogen_winkel' not in st.session_state:
    st.session_state.bogen_winkel = 90

# -----------------------------------------------------------------------------
# 2. HILFSFUNKTIONEN & DATEN
# -----------------------------------------------------------------------------
schrauben_db = {
    "M12": [18, 60], "M16": [24, 130], "M20": [30, 250], "M24": [36, 420],
    "M27": [41, 600], "M30": [46, 830], "M33": [50, 1100], "M36": [55, 1400],
    "M39": [60, 1800], "M45": [70, 2700], "M52": [80, 4200]
}
ws_liste = [2.0, 2.3, 2.6, 2.9, 3.2, 3.6, 4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 8.8, 10.0, 11.0, 12.5, 14.2, 16.0]
wandstaerken_std = {
    25: 3.2, 32: 3.6, 40: 3.6, 50: 3.9, 65: 5.2, 80: 5.5, 
    100: 6.0, 125: 6.6, 150: 7.1, 200: 8.2, 250: 9.3, 300: 9.5,
    350: 9.5, 400: 9.5, 450: 9.5, 500: 9.5
}

def get_schrauben_info(gewinde): return schrauben_db.get(gewinde, ["?", "?"])
def get_wandstaerke(dn): return wandstaerken_std.get(dn, 6.0)

# --- ZEICHNEN ---
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
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot([0, l], [0, h], color='#2C3E50', linewidth=3, zorder=2)
    ax.plot([l, l], [0, h], color='#E74C3C', linestyle='--', linewidth=1, zorder=1)
    ax.plot([0, l], [0, 0], color='#E74C3C', linestyle='--', linewidth=1, zorder=1)
    ax.scatter([0, l], [0, h], color='white', edgecolor='#2C3E50', s=60, zorder=3, linewidth=2)
    ax.text(l + 10, h/2, f"H={h}", color='#E74C3C', fontweight='bold', fontsize=9)
    ax.text(l/2, -30, f"L={l}", color='#E74C3C', fontweight='bold', ha='center', fontsize=9)
    ax.text(l/2, h/2 + 20, f"Säge: {round(passstueck, 1)}", color='#27AE60', fontweight='bold', ha='right', fontsize=10)
    ax.set_aspect('equal'); ax.axis('off')
    return fig

def zeichne_iso_raum(s, h, l, diag_raum, passstueck):
    fig, ax = plt.subplots(figsize=(4, 3))
    angle = math.radians(30); cx, cy = math.cos(angle), math.sin(angle)
    scale = 100 / max(s, h, l, 1)
    S, H, L = s*scale, h*scale, l*scale
    p_l = (L * cx, L * cy); p_ls = (p_l[0] + S * cx, p_l[1] - S * cy); p_end = (p_ls[0], p_ls[1] + H)
    ax.plot([0, p_l[0]], [0, p_l[1]], '--', color='grey', lw=0.5)
    ax.plot([p_l[0], p_ls[0]], [p_l[1], p_ls[1]], '--', color='grey', lw=0.5)
    ax.plot([p_ls[0], p_end[0]], [p_ls[1], p_end[1]], '--', color='grey', lw=0.5)
    ax.plot([0, p_end[0]], [0, p_end[1]], color='#2C3E50', lw=2.5)
    ax.scatter([0, p_end[0]], [0, p_end[1]], color='white', edgecolor='#2C3E50', s=40, zorder=5)
    ax.text(p_end[0]/2, p_end[1]/2 + 10, f"Säge: {round(passstueck)}", color='#27AE60', fontweight='bold', ha='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    ax.set_aspect('equal'); ax.axis('off')
    return fig

def zeichne_stutzen_abwicklung(df_coords):
    fig, ax = plt.subplots(figsize=(4.0, 2.0))
    ax.plot(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#2980B9', linewidth=2)
    ax.fill_between(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#D6EAF8', alpha=0.5)
    ax.set_xlabel("Winkel (°)", fontsize=8); ax.set_ylabel("Tiefe (mm)", fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5); ax.set_xticks([0, 90, 180, 270, 360])
    plt.tight_layout()
    return fig

# -----------------------------------------------------------------------------
# 3. DATENBANK (Rohre & Flansche)
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
selected_dn_global = st.sidebar.selectbox("Nennweite (Global)", df['DN'], index=8) 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0)

# PREIS DB
st.sidebar.markdown("---")
with st.sidebar.expander("💶 Preis-Datenbank (Editieren)", expanded=False):
    p_lohn = st.number_input("Stundensatz Lohn (€/h)", value=60.0, step=5.0)
    p_stahl_disc = st.number_input("Stahl-Scheibe (€/Stk)", value=2.50, step=0.5)
    p_dia_disc = st.number_input("Diamant-Scheibe (€/Stk)", value=45.00, step=5.0)
    p_cel = st.number_input("Elektrode CEL 70 (€/Stk)", value=0.40, step=0.05)
    p_draht = st.number_input("MAG/WIG Draht (€/kg)", value=15.00, step=1.0)
    p_gas = st.number_input("Schweißgas (€/Liter)", value=0.05, step=0.01)
    p_wks = st.number_input("WKS Manschette (€/Stk)", value=25.00, step=5.0)
    p_kebu_in = st.number_input("Kebu 1.2 H (€/Rolle)", value=15.00, step=1.0)
    p_kebu_out = st.number_input("Kebu PE 0.50 (€/Rolle)", value=12.00, step=1.0)
    p_primer = st.number_input("Voranstrich K3 (€/Liter)", value=12.00, step=1.0)

row = df[df['DN'] == selected_dn_global].iloc[0]
standard_radius = float(row['Radius_BA3'])
suffix = "_16" if selected_pn == "PN 16" else "_10"

st.title(f"Rohrbau Profi (DN {selected_dn_global})")

# TABS
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
    col_m1.metric("Schraube", f"{anzahl}x {schraube}")
    col_m2.metric("Schlüsselweite", f"{sw} mm")
    col_m3.metric("Drehmoment", f"{nm} Nm")
    
    st.markdown("---")
    st.header("Schraubenlängen")
    l_fest = row[f'L_Fest{suffix}']
    l_los = row[f'L_Los{suffix}']
    
    c_len1, c_len2 = st.columns(2)
    with c_len1:
        st.markdown(f"<div class='result-box'>Länge (Fest-Fest): <b>{l_fest} mm</b></div>", unsafe_allow_html=True)
    with c_len2:
        st.markdown(f"<div class='result-box' style='border-left: 6px solid #8E44AD;'>Länge (Fest-Los): <b>{l_los} mm</b></div>", unsafe_allow_html=True)
    
    st.markdown("""<div class="red-box"><b>⚠️ WICHTIG:</b> Drehmomente gelten für geschmierte Schrauben (Molykote). Bei Grauguss-Flanschen Längen prüfen (+10mm)!</div>""", unsafe_allow_html=True)

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
    <b>Infos für Abzüge (DN {selected_dn_global}):</b><br>
    • Flansch Bauhöhe: <b>{row[f'Flansch_b{suffix}']} mm</b><br>
    • Bogen 90° (Vorbau): <b>{standard_radius} mm</b><br>
    • Bogen {winkel_aus_tab2}° (aus Tab Bogen): <b>{vorbau_tab2} mm</b>
    </div>
    """, unsafe_allow_html=True)
    
    saege_erg = iso_mass - spalt - abzuege
    try: st.pyplot(zeichne_passstueck(iso_mass, abzuege, 0, saege_erg))
    except: pass
    st.markdown(f"<div class='highlight-box'>Sägelänge: {saege_erg} mm</div>", unsafe_allow_html=True)

# --- TAB 5: STUTZEN ---
with tab5:
    st.caption("Stutzen Schablone (Zentrisch)")
    c_st1, c_st2 = st.columns(2)
    dn_stutzen = c_st1.selectbox("DN Stutzen (Abzweig)", df['DN'], index=6)
    dn_haupt = c_st2.selectbox("DN Hauptrohr (Run)", df['DN'], index=9)
    
    if dn_stutzen > dn_haupt:
        st.error("Stutzen muss kleiner sein!")
    else:
        r_k = df[df['DN'] == dn_stutzen].iloc[0]['D_Aussen'] / 2
        r_g = df[df['DN'] == dn_haupt].iloc[0]['D_Aussen'] / 2
        
        plot_data = []
        for a in range(0, 361, 5): 
            t = r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2)
            plot_data.append([a, t])
            
        table_data = []
        for a in [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]:
            u = int(round((r_k*2) * math.pi * (a/360), 0))
            t = int(round(r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2), 0))
            table_data.append([f"{a}°", u, t])

        df_plot = pd.DataFrame(plot_data, columns=["Winkel_Raw", "Tiefe (mm)"])
        c_res1, c_res2 = st.columns([1, 2])
        with c_res1:
            st.table(pd.DataFrame(table_data, columns=["Winkel", "Umfang (mm)", "Tiefe (mm)"]))
        with c_res2:
            st.pyplot(zeichne_stutzen_abwicklung(df_plot))

# --- TAB 6: ETAGEN ---
with tab6:
    calc_type = st.radio("Modus:", ["2D Einfache Etage", "3D Raum-Etage (Kastenmaß)", "3D Raum-Etage (Fix-Winkel)"], horizontal=True)
    st.markdown("---")
    spalt_etage = st.number_input("Wurzelspalt (Gesamt)", value=6, key="spalt_et")

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

    elif calc_type == "3D Raum-Etage (Kastenmaß)":
        c1, c2, c3 = st.columns(3)
        b = c1.number_input("Breite (Seite/Roll)", value=200)
        h = c2.number_input("Höhe (Auf/Set)", value=300)
        l = c3.number_input("Länge (Vor/Run)", value=400)
        diag_raum = math.sqrt(h**2 + l**2 + b**2)
        l_proj = math.sqrt(l**2 + b**2)
        spread = math.sqrt(b**2 + h**2)
        winkel = math.degrees(math.atan(spread / l)) if l > 0 else 90
        abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
        pass_etage = diag_raum - abzug - spalt_etage
        st.write(f"Spreizung (Spread): **{round(spread, 1)} mm**")
        st.info(f"Winkel: {round(winkel, 1)}° | Diagonale: {round(diag_raum, 1)} mm")
        try: st.pyplot(zeichne_iso_raum(b, h, l, diag_raum, pass_etage))
        except: pass
        st.markdown(f"<div class='highlight-box'>Sägelänge: {round(pass_etage, 1)} mm</div>", unsafe_allow_html=True)

    elif calc_type == "3D Raum-Etage (Fix-Winkel)":
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
            st.write(f"Du musst **{round(l_notwendig, 1)} mm** in der Länge verziehen.")
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
        rb_bauteil = col_r5.selectbox("Bauteil", ["Rohr", "Bogen", "Flansch (V)", "Muffe", "Nippel", "T-Stück", "Reduzierung"])
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
        c_down, c_del1 = st.columns([3,1])
        with c_down:
            buffer = BytesIO()
            try:
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_rb.to_excel(writer, index=False)
                st.download_button("📥 Excel Download", buffer.getvalue(), f"Rohrbuch_{datetime.now().date()}.xlsx")
            except: st.error("Excel Fehler (openpyxl fehlt)")
        with c_del1:
            if st.button("🗑️ Liste leeren"):
                st.session_state.rohrbuch_data = []
                st.rerun()
    else:
        st.caption("Noch keine Einträge vorhanden.")

# --- TAB 8: KALKULATION ---
with tab8:
    st.header("💰 Kosten & Zeit Kalkulation")
    kalk_mode = st.radio("Modus:", 
                         ["🔥 Schweißnaht & Vorbereitung", "✂️ Schnittkosten & Verschleiß",
                          "🛡️ Nachumhüllung", "🚗 Fahrzeit & Regie"], horizontal=True)
    st.markdown("---")

    if kalk_mode == "🔥 Schweißnaht & Vorbereitung":
        c1, c2, c3 = st.columns(3)
        kd_dn = c1.selectbox("Dimension", df['DN'], index=8, key="kalk_dn")
        kd_ws = c2.number_input("Wandstärke (mm)", value=get_wandstaerke(kd_dn), step=0.1)
        kd_verf = c3.selectbox("Verfahren", ["WIG", "E-Hand (CEL 70)", "WIG + E-Hand", "MAG"])
        
        da = df[df['DN'] == kd_dn].iloc[0]['D_Aussen']
        vol_cm3 = (da * math.pi * ((kd_ws**2)*0.8 + (kd_ws*1.5))) / 1000
        gewicht_kg = (vol_cm3 * 7.85) / 1000
        
        gas_l = 10 if "WIG" in kd_verf else (15 if "MAG" in kd_verf else 0)
        leistung = 0.5 if "WIG" == kd_verf else (1.2 if "E-Hand" in kd_verf else 2.8)
        
        zeit_schweiss = (gewicht_kg / leistung) * 60
        zeit_vor = (kd_dn / 25) * 3.0
        zeit_total = zeit_schweiss + zeit_vor
        
        anzahl = st.number_input("Anzahl Nähte", 1)
        cost_time = (zeit_total/60 * p_lohn) * anzahl
        cost_mat = (gewicht_kg * anzahl * (p_cel if "CEL" in kd_verf else p_draht)) + (zeit_schweiss*gas_l/60 * anzahl * p_gas)
        
        st.subheader(f"Ergebnis für {anzahl} Nähte:")
        c_k1, c_k2 = st.columns(2)
        c_k1.metric("Zeit (Gesamt)", f"{round(zeit_total*anzahl/60, 1)} h")
        c_k2.metric("Kosten (Total)", f"{round(cost_time + cost_mat, 2)} €")
        
        if st.button("➕ Zu Projekt hinzufügen"):
            st.session_state.kalk_liste.append({
                "Typ": "Schweißen", "Info": f"DN {kd_dn} {kd_verf}", "Menge": anzahl,
                "Zeit_Min": zeit_total*anzahl, "Kosten": cost_time + cost_mat,
                "Mat_Text": f"{round(gewicht_kg*anzahl,1)} kg Zusatz"
            })
            st.success("Hinzugefügt!")

    elif kalk_mode == "✂️ Schnittkosten & Verschleiß":
        c1, c2 = st.columns(2)
        cut_dn = c1.selectbox("DN", df['DN'], index=8, key="cut_dn")
        cut_anz = c2.number_input("Anzahl", 10)
        
        da = df[df['DN'] == cut_dn].iloc[0]['D_Aussen']
        ws = get_wandstaerke(cut_dn)
        flaeche = (math.pi * (da/2)**2) - (math.pi * ((da-2*ws)/2)**2)
        total_fl = flaeche * cut_anz
        
        n_disc = math.ceil(total_fl / 200)
        time_total = (cut_dn/25) * 2.0 * cut_anz
        cost = (time_total/60 * p_lohn) + (n_disc * p_stahl_disc)
        
        st.metric("Kosten", f"{round(cost, 2)} €")
        if st.button("➕ Hinzufügen"):
            st.session_state.kalk_liste.append({
                "Typ": "Schnitt", "Info": f"DN {cut_dn}", "Menge": cut_anz,
                "Zeit_Min": time_total, "Kosten": cost, "Mat_Text": f"{n_disc} Scheiben"
            })
            st.success("OK")

    elif kalk_mode == "🛡️ Nachumhüllung":
        iso_typ = st.radio("System", ["WKS Manschette", "Kebu B80"], horizontal=True)
        c1, c2 = st.columns(2)
        iso_dn = c1.selectbox("DN", df['DN'], index=8, key="iso_dn")
        iso_anz = c2.number_input("Anzahl", 1)
        
        time_total = (20 + (iso_dn * 0.05)) * iso_anz
        cost_mat = (iso_anz * p_wks) if "WKS" in iso_typ else (iso_anz * 0.5 * p_kebu_in) # Vereinfacht
        cost = (time_total/60 * p_lohn) + cost_mat
        
        st.metric("Kosten", f"{round(cost, 2)} €")
        if st.button("➕ Hinzufügen"):
            st.session_state.kalk_liste.append({
                "Typ": "Iso", "Info": f"{iso_typ} DN{iso_dn}", "Menge": iso_anz,
                "Zeit_Min": time_total, "Kosten": cost, "Mat_Text": iso_typ
            })
            st.success("OK")

    elif kalk_mode == "🚗 Fahrzeit & Regie":
        c1, c2 = st.columns(2)
        t_min = c1.number_input("Minuten", 60)
        pers = c2.number_input("Personen", 2)
        cost = (t_min/60 * p_lohn) * pers
        st.metric("Kosten", f"{round(cost, 2)} €")
        if st.button("➕ Hinzufügen"):
            st.session_state.kalk_liste.append({
                "Typ": "Fahrt", "Info": f"{pers} Pers", "Menge": 1,
                "Zeit_Min": t_min*pers, "Kosten": cost, "Mat_Text": "-"
            })
            st.success("OK")

# --- TAB 9: PROJEKT SUMME ---
with tab9:
    st.header("📊 Projekt-Zusammenfassung")
    if len(st.session_state.kalk_liste) > 0:
        df_sum = pd.DataFrame(st.session_state.kalk_liste)
        st.dataframe(df_sum, use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Gesamt-Kosten", f"{round(df_sum['Kosten'].sum(), 2)} €")
        c2.metric("Gesamt-Stunden", f"{round(df_sum['Zeit_Min'].sum()/60, 1)} h")
        
        if st.button("🗑️ Liste leeren"):
            st.session_state.kalk_liste = []
            st.rerun()
    else:
        st.info("Kalkulation leer.")
