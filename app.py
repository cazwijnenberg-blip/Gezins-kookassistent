import streamlit as st
from google import genai
import datetime
import calendar
import json
import os
import re

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Zwijnenberg Home Assist", 
    page_icon="🐷", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BROWSER HISTORY & ROUTING ---
query_pagina = st.query_params.get("pagina", "Home")
if "huidige_pagina" not in st.session_state or st.session_state["huidige_pagina"] != query_pagina:
    st.session_state["huidige_pagina"] = query_pagina

def ga_naar(pagina):
    st.query_params["pagina"] = pagina
    st.session_state["huidige_pagina"] = pagina
    st.rerun()

# --- VEILIGHEIDSCHECK API KEY ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("🚨 Kan de API-sleutel niet vinden. Zorg voor een `.streamlit/secrets.toml` bestand met `GEMINI_API_KEY`.")
    st.stop()

def parse_json_veilig(tekst):
    try:
        m = re.search(r'\{.*\}', tekst, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(tekst)
    except Exception:
        return None

# --- STYLING (NU EXTRA HARDE OVERRIDE VOOR DE 4-KOLOMS GRID) ---
st.markdown("""
    <style>
    /* Verberg sidebar toggle */
    [data-testid="collapsedControl"] { display: none; }

    /* Forceer layout om niet te wrappen en kolommen exact 25% te maken */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 2px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="column"] {
        flex: 0 0 25% !important;
        width: 25% !important;
        max-width: 25% !important;
        min-width: 25% !important;
        padding: 1px !important;
    }

    /* Zorg dat de knoppen binnen die kolommen passen */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        padding: 2px !important;
        font-size: 0.6rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        background-color: #EBF5EE !important;
        border: 1px solid #C4E0CC !important;
    }
    
    /* Zorg dat de main container niet gaat scrollen */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Zorg dat alle keys bestaan
                keys = ["boodschappen_historie", "agenda", "boodschappen", "weekmenu", "dagschema", "gezondheid", "huishoud"]
                for k in keys:
                    if k not in data: data[k] = [] if k in ["agenda", "boodschappen", "gezondheid", "huishoud", "dagschema"] else {}
                return data
        except: pass
    
    return {
        "agenda": [{"datum": "2026-04-22", "beschrijving": "💍 Trouwdag"}],
        "boodschappen": [],
        "boodschappen_historie": {},
        "weekmenu": {},
        "dagschema": [{"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False}],
        "gezondheid": [],
        "huishoud": [{"taak": "🗑️ Container", "dag": "Maandag", "status": False}]
    }

def sla_data_op(data):
    with open(DATA_BESTAND, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "gezin_data" not in st.session_state: 
    st.session_state["gezin_data"] = laad_data()

vandaag = datetime.date.today()

# --- DASHBOARD LOGICA ---
if st.session_state["huidige_pagina"] == "Home":
    st.markdown("### 🏠 Zwijnenberg")
    
    dashboard_knoppen = [
        ("💬", "Chat", "Chat"),
        ("📅", "Agenda", "Agenda"),
        ("🛒", "Lijst", "Boodschappenlijst"),
        ("🍽️", "Menu", "Weekmenu"),
        ("🎯", "Schema", "Dagschema"),
        ("🧹", "Klusjes", "Huishoud"),
        ("💊", "Zorg", "Gezondheid"),
        ("🎵", "Disco", "Kids")
    ]

    # Renderen in 4 kolommen per rij
    for i in range(0, len(dashboard_knoppen), 4):
        rij = dashboard_knoppen[i:i+4]
        cols = st.columns(4)
        for j, (icoon, tekst, pagina) in enumerate(rij):
            with cols[j]:
                if st.button(f"{icoon}\n{tekst}", key=f"btn_{pagina}", use_container_width=True):
                    ga_naar(pagina)

# --- ANDERE PAGINA'S (Hetzelfde als jouw code) ---
elif st.session_state["huidige_pagina"] != "Home":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if st.session_state["huidige_pagina"] == "Chat":
        st.markdown("### 💬 Chat met Boris")
        # Chat logica...
    elif st.session_state["huidige_pagina"] == "Agenda":
        st.markdown("### 📅 Agenda")
        # Agenda logica...
    # ... (vul hier de rest van je logica aan, de CSS fix zit in de styling bovenaan)
    
    st.info(f"Je bent op pagina: {st.session_state['huidige_pagina']}")
