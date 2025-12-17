import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# 1. DESIGN (CLEAN / LIGHT MODE)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rohrbau Profi Kalkulation", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stRadio label { font-weight: bold; }
    
    .small-info { font-size: 0.9rem; color: #555; background-color: #F8F9F9; padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ddd; }
    .result-box { background-color: #F4F6F7; padding: 12px; border-radius: 4px; border-left: 6px solid #2980B9; color: #000000 !important; margin-bottom: 8px; border: 1px solid #ddd; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 6px solid #27AE60; color: #000000 !important; text-align: center; font-size: 1.3rem; font-weight: bold; margin-top: 10px; border: 1px solid #ddd; }
    .calc-box { background-color: #FFF8E1; padding: 10px; border-radius: 4px; border: 1px solid #FFECB3; margin-bottom: 10px; }
    .stDataFrame { border: 1px solid #000; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HILFSFUNKTIONEN
# -----------------------------------------------------------------------------
def zeichne_iso_etage(h, l, winkel, passstueck):
    fig, ax = plt.subplots(figsize=(5, 3))
    iso_angle_rad = math.radians(30)
    vec_y_x, vec_y_y = math.cos(iso_angle_rad), math.sin(iso_angle_rad)
    anschluss_len = 100
    p1 = (0, 0)
    p2 = (p1[0] + anschluss_len * vec_y_x, p1[1] + anschluss_len * vec_y_y)
    p3 = (p2[0] + l * vec_y_x, p2[1] + l * vec_y_y + h)
    p4 = (p3[0] + anschluss_len * vec_y_x, p3[1] + anschluss_len * vec_y_y)
    
    ax.plot([p1[0], p2[0], p3[0], p4[0]], [p1[1], p2[1], p3[1], p4[1]], color='#2C3E50', linewidth=4, zorder=10, solid_capstyle='round')
    ax.scatter([p2[0], p3[0]], [p2[1], p3[1]], color='white', edgecolor='#2C3E50', s=80, zorder=11, linewidth=2)
    p_corner_x, p_corner_y = p3[0], p3[1] - h
    ax.plot([p2[0], p_corner_x], [p2[1], p_corner_y], color='grey', linestyle='--', linewidth=1)
    ax.plot([p_corner_x, p3[0]], [p_corner_y, p3[1]], color='grey', linestyle='--', linewidth=1)
    
    ax.text(p_corner_x + 10, p_corner_y + h/2, f"H={h}", color='#E74C3C', fontweight='bold', ha='left', fontsize=9)
    ax.text((p2[0] + p_corner_x)/2, (p2[1] + p_corner_y)/2 - 20, f"L={l}", color='#E74C3C', fontweight='bold', ha='right', fontsize=9)
    mid_x, mid_y = (p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2
    ax.text(mid_x - 20, mid_y + 20, f"Säge: {round(passstueck,1)}", color='#27AE60', fontweight='bold', ha='right', fontsize=10, bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    arrow_x, arrow_y = max(p4[0], p3[0]) + 20, max(p4[1], p3[1]) + 30
    ax.arrow(arrow_x, arrow_y, 0, 25, head_width=8, head_length=8, fc='black', ec='black')
    ax.text(arrow_x, arrow_y + 35, "N", ha='center', fontweight='bold', fontsize=9)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig

# -----------------------------------------------------------------------------
# DATENBANK
# -----------------------------------------------------------------------------
data = {
    'DN':           [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600],
    'D_Aussen':     [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0, 711.0, 813.0, 914.0, 1016.0, 1219.0, 1422.0, 1626.0],
    'Radius_BA3':   [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914, 1067, 1219, 1372, 1524, 1829, 2134, 2438],
    'T_Stueck_H':   [25, 32, 38, 51, 64, 76, 105, 124, 143, 178, 216, 2
