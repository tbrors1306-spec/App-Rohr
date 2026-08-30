import streamlit as st


def init_app_state():
    """Session-Defaults setzen (nur was die App heute noch braucht)."""
    defaults = {
        "active_tab": "🪚 Smarte Säge",
        "fitting_list": [],     # aktuell gewählte Bauteile (Smarte Säge)
        "saved_cuts": [],       # gespeicherte Schnitte (Smarte Säge)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
