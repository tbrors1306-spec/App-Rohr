import streamlit as st
import pandas as pd
import math

# -----------------------------------------------------------------------------
# 1. KONFIGURATION & DESIGN (HARDCORE LIGHT MODE)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rohrbau Profi", page_icon="🛠️", layout="wide")

# Wir erzwingen extremen Light Mode, damit Smartphones nicht "dazwischenfunken"
st.markdown("""
<style>
    /* Basis: Immer Weiß, Schrift Schwarz */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Sidebar Hell */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    
    /* Alle Texte Schwarz erzwingen */
    h1, h2, h3, h4, p, div, span, label, li {
        color: #000000 !important;
    }
    
    /* Eingabefelder sichtbar machen */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stSlider {
        color: #000000 !important;
        background-color: #ffffff !important;
        border-color: #cccccc !important;
    }
    
    /* Dezenter Hinweis oben */
    .small-info {
        font-size: 0.85rem;
        color: #444;
        background-color: #eef;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 15px;
        border: 1px solid #ccd;
    }
    
    /* Ergebnis Boxen (Hellgrau/Blau) */
    .result-box { 
        background-color: #F4F6F7 !important; 
        padding: 10px; 
        border-radius: 6px; 
        border-left: 5px solid #2980B9; 
        color: #000000 !important; 
        margin-bottom: 8px;
        border: 1px solid #ddd;
        font-size: 0.95rem;
    }
    
    /* Schrauben Boxen (Kleiner, für Spalten) */
    .bolt-box {
        background-color: #FDEDEC !important;
        padding: 8px;
        border-radius: 6px;
        border: 1px solid #E6B0AA;
        text-align: center;
        color: #000000 !important;
        font-size: 0.9rem;
    }
    
    /* Highlight Box (Grün) */
    .highlight-box { 
        background-color: #E9F7EF !important; 
        padding: 15px; 
        border-radius: 6px; 
        border-left: 5px solid #27AE60; 
        color: #000000 !important;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 10px;
        border: 1px solid #ccc;
    }
    
    /* Tabellen lesbar machen */
    .stDataFrame, .stTable { 
        color: black !important; 
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATENBANK
# -----------------------------------------------------------------------------
data = {
    'DN':           [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600],
    'D_Aussen':     [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0, 711.0, 813.0, 914.0, 1016.0, 1219.0, 1422.0, 1626.0],
    'Radius_BA3':   [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914, 1067, 1219, 1372, 1524, 1829, 2134, 2438],
    'T_Stueck_H':   [25, 32, 38, 51, 64, 76, 105, 124, 143, 178, 216, 254, 279, 305, 343, 381, 432, 521, 597, 673, 749, 889, 1029, 1168],
    'Red_Laenge_L': [38, 50, 64, 76, 89, 89, 102, 127, 140, 152, 178, 203, 330, 356, 381, 508, 508, 610, 660, 711, 800, 900, 1000, 1100], 
    
    # PN 16
    'Flansch_b_16': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_16':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 355, 410, 470, 525, 585, 650, 770, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_16':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M33", "M33", "M36", "M36", "M39", "M45", "M45", "M52"],
    'L_Fest_16':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 100, 110, 110, 120, 130, 130, 150, 160, 170, 180, 190, 220, 240, 260],
    'L_Los_16':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 115, 125, 130, 140, 150, 150, 170, 180, 190, 210, 220, 250, 280, 300],
    'Lochzahl_16':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 12, 12, 12, 16, 16, 20, 20, 20, 24, 24, 28, 28, 32, 36, 40],

    # PN 10
    'Flansch_b_10': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_10':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 350, 400, 460, 515, 565, 620, 725, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_10':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M20", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M30", "M33", "M36", "M39", "M45"],
    'L_Fest_10':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 90, 90, 90, 100, 110, 110, 120, 130, 140, 150, 160, 190, 210, 230],
    'L_Los_10':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 105, 105, 110, 120, 130, 130, 140, 150, 160, 170, 180, 210, 240, 260],
    'Lochzahl_10':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 12, 12, 16, 16, 20, 20, 20, 20, 24, 28, 28, 32, 36, 40]
}
df = pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 3. SIDEBAR (MENÜ)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Einstellungen")
selected_dn = st.sidebar.selectbox("Nennweite (DN)", df['DN'], index=8) 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0)

row = df[df['DN'] == selected_dn].iloc[0]

st.sidebar.markdown("---")
st.sidebar.write("✏️ **Korrektur:**")
standard_radius = row['Radius_BA3']
custom_radius = st.sidebar.number_input("Bogenradius (R)", value=float(standard_radius), step=1.0)
st.sidebar.caption("Standard = Bauart 3")

# -----------------------------------------------------------------------------
# 4. HAUPTBEREICH
# -----------------------------------------------------------------------------

# Dezenter Hinweis (Grau auf Hellgrau - absolut sicher)
st.markdown("""<div class="small-info">ℹ️ Einstellungen (DN / PN) findest du im Menü oben links (Pfeil >).</div>""", unsafe_allow_html=True)

st.title(f"Rohrbau Profi (DN {selected_dn})")

suffix = "_16" if selected_pn == "PN 16" else "_10"

# --- TAB NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Maße", "🔄 Bogen", "📏 Säge", "🔥 Stutzen"])

# --- TAB 1: DATENBLATT ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Rohr & Formstücke")
        # Text ist jetzt sicher SCHWARZ
        st.markdown(f"<div class='result-box'>Außen-Ø:<br><b>{row['D_Aussen']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>T-Stück (H):<br><b>{row['T_Stueck_H']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Reduzierung (L):<br><b>{row['Red_Laenge_L']} mm</b></div>", unsafe_allow_html=True)
    
    with col2:
        st.caption(f"Flansch ({selected_pn})")
        lk = row[f'LK_k{suffix}']
        anz = row[f'Lochzahl{suffix}']
        gew = row[f'Schraube_M{suffix}']
        blatt = row[f'Flansch_b{suffix}']
        l_fest = row[f'L_Fest{suffix}']
        l_los = row[f'L_Los{suffix}']
        
        st.markdown(f"<div class='result-box'>Lochkreis:<br><b>{lk} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Flanschblatt (b):<br><b>{blatt} mm</b></div>", unsafe_allow_html=True)
        
        # Schrauben Bereich
        st.markdown("---")
        st.markdown(f"**Schrauben: {anz}x {gew}**")
        
        # Hier die zwei halben Spalten für die Längen
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"<div class='bolt-box'>Fest-Fest<br><b>{l_fest} mm</b></div>", unsafe_allow_html=True)
        with sc2:
             st.markdown(f"<div class='bolt-box'>Fest-Los<br><b>{l_los} mm</b></div>", unsafe_allow_html=True)

# --- TAB 2: BOGEN ---
with tab2:
    st.caption("Bogenberechnung")
    angle = st.slider("Winkel (°)", 0, 90, 45, 1)
    
    # Berechnung
    da = row['D_Aussen']
    r_bogen = custom_radius
    
    aussen = round((r_bogen + (da/2)) * angle * (math.pi/180), 1)
    innen = round((r_bogen - (da/2)) * angle * (math.pi/180), 1)
    vorbau = round(r_bogen * math.tan(math.radians(angle/2)), 1)
    
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='result-box'>Außen (Rücken):<br><b>{aussen} mm</b></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='result-box'>Innen (Bauch):<br><b>{innen} mm</b></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='highlight-box'>Vorbau (Zollstock):<br>{vorbau} mm</div>", unsafe_allow_html=True)

# --- TAB 3: PASSSTÜCK & ETAGE ---
with tab3:
    st.caption("Passstück (Gerades Rohr)")
    col_p1, col_p2 = st.columns(2)
    iso_mass = col_p1.number_input("Gesamtmaß (Iso)", value=2000, step=10)
    spalt = col_p2.number_input("Wurzelspalt", value=6)
    
    col_p3, col_p4 = st.columns(2)
    abzug1 = col_p3.number_input("Abzug Links (-)", value=0)
    abzug2 = col_p4.number_input("Abzug Rechts (-)", value=0)
    
    ergebnis = iso_mass - abzug1 - abzug2 - spalt
    st.markdown(f"<div class='highlight-box'>Sägelänge: {ergebnis} mm</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("Etagen Rechner (Inkl. Bogenabzug)")
    col_e1, col_e2 = st.columns(2)
    h = col_e1.number_input("Höhe H (Versatz)", value=300)
    l = col_e2.number_input("Länge L (Gerade)", value=400)
    
    if l > 0:
        winkel_etage = math.degrees(math.atan(h/l))
        diag = math.sqrt(h**2 + l**2)
        abzug_etage = 2 * (custom_radius * math.tan(math.radians(winkel_etage/2)))
        passstueck_etage = diag - abzug_etage - spalt
        
        st.info(f"Winkel: {round(winkel_etage, 1)}° | Diagonale: {round(diag, 1)} mm")
        st.markdown(f"<div class='highlight-box'>Sägelänge (Etage):<br>{round(passstueck_etage, 1)} mm</div>", unsafe_allow_html=True)

# --- TAB 4: STUTZEN ---
with tab4:
    st.caption("Stutzen Schablone (16er Teilung)")
    dn_stutzen = st.selectbox("DN Stutzen", df['DN'], index=6)
    dn_haupt = st.selectbox("DN Hauptrohr", df['DN'], index=9)
    
    if dn_stutzen > dn_haupt:
        st.error("Stutzen muss kleiner/gleich Hauptrohr sein!")
    else:
        r_klein = df[df['DN'] == dn_stutzen].iloc[0]['D_Aussen'] / 2
        R_gross = df[df['DN'] == dn_haupt].iloc[0]['D_Aussen'] / 2
        
        angles = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]
        res_data = []
        for ang in angles:
            umfang = round((r_klein*2) * math.pi * (ang/360), 1)
            tiefe = round(R_gross - math.sqrt(R_gross**2 - (r_klein * math.sin(math.radians(ang)))**2), 1)
            res_data.append([f"{ang}°", f"{umfang}", f"{tiefe}"])
            
        df_stutzen = pd.DataFrame(res_data, columns=["Winkel", "Umfang", "Tiefe"])
        st.table(df_stutzen)
