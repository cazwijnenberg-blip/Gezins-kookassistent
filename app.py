import streamlit as st
from google import genai
from PIL import Image
import datetime
import calendar
import json
import os
import base64
import re
import random

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

def get_image_base64(image_path):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception:
            return None
    return None

def parse_json_veilig(tekst):
    try:
        m = re.search(r'\{.*\}', tekst, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(tekst)
    except Exception:
        return None

# --- STYLING (GEFORCEERD 4-KOLOMMS APP-GRID) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }

    * {
        box-sizing: border-box !important;
    }

    .main, .block-container {
        max-width: 100vw !important;
        width: 100% !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
        padding-top: 0.4rem !important;
        overflow-x: hidden !important;
    }
    
    /* Forceer rijen en kolommen om ALTIJD 4 naast elkaar te blijven (geen automatische mobiele stapeling) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 25% !important;
        min-width: 0px !important;
        max-width: 25% !important;
    }

    /* Strakke App-Tegels (Vierkant Raster) */
    .stButton > button {
        width: 100% !important;
        height: 56px !important;
        border-radius: 10px !important;
        background-color: #EBF5EE !important;
        color: #1B4D2E !important;
        border: 1px solid #C4E0CC !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: transform 0.1s ease, background-color 0.1s ease !important;
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        padding: 2px !important;
        margin-bottom: 4px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 2px !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }

    .stButton > button p, .stButton > button div {
        font-size: 0.68rem !important;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    .stButton > button:hover, .stButton > button:active {
        transform: scale(0.97) !important;
        background-color: #D6EFE0 !important;
        border-color: #2E7D32 !important;
        color: #0E331A !important;
    }

    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1) rotate(0deg); }
        20% { transform: translateY(-3px) scale(1.02) rotate(-1deg); }
        40% { transform: translateY(2px) scale(0.98) rotate(1deg); }
        60% { transform: translateY(-2px) scale(1.01) rotate(-1deg); }
        80% { transform: translateY(1px) scale(0.99) rotate(1deg); }
        100% { transform: translateY(0px) scale(1) rotate(0deg); }
    }
    .Boris-img-talking { animation: avatar-talking 0.3s infinite ease-in-out; }
    
    @keyframes avatar-dancing {
        0% { transform: rotate(0deg) translateY(0px); }
        25% { transform: rotate(-10deg) translateY(-8px); }
        50% { transform: rotate(0deg) translateY(0px); }
        75% { transform: rotate(10deg) translateY(-8px); }
        100% { transform: rotate(0deg) translateY(0px); }
    }
    .Boris-img-dancing { animation: avatar-dancing 0.6s infinite ease-in-out; }
    </style>
""", unsafe_allow_html=True)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "boodschappen_historie" not in data: data["boodschappen_historie"] = {}
                if "agenda" not in data: data["agenda"] = []
                if "boodschappen" not in data: data["boodschappen"] = []
                if "weekmenu" not in data: data["weekmenu"] = {}
                if "dagschema" not in data: 
                    data["dagschema"] = [
                        {"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False},
                        {"taak": "👕 Aankleden", "tijd": "Ochtend", "klaar": False},
                        {"taak": "🥣 Ontbijten", "tijd": "Ochtend", "klaar": False},
                        {"taak": "🛏️ Pyjama aan", "tijd": "Avond", "klaar": False},
                        {"taak": "📚 Verhaaltje lezen", "tijd": "Avond", "klaar": False}
                    ]
                if "gezondheid" not in data: data["gezondheid"] = []
                if "huishoud" not in data: 
                    data["huishoud"] = [
                        {"taak": "🗑️ Grijze container aan straat", "dag": "Maandag", "status": False},
                        {"taak": "♻️ Gft-bak buiten zetten", "dag": "Donderdag", "status": False},
                        {"taak": "🧽 Vaatwasser filter schoonmaken", "dag": "Zaterdag", "status": False},
                        {"taak": "🛏️ Bedden verschonen", "dag": "Zondag", "status": False}
                    ]
                return data
        except Exception:
            pass
            
    standaard_data = {
        "agenda": [
            {"datum": "2026-04-22", "beschrijving": "💍 Trouwdag Chiel & Angelica"},
            {"datum": "2026-06-11", "beschrijving": "🎂 Verjaardag Duén (1 jr)"},
            {"datum": "2026-10-24", "beschrijving": "🎂 Verjaardag Tygo (3 jr)"}
        ],
        "boodschappen": [],
        "boodschappen_historie": {},
        "weekmenu": {},
        "dagschema": [
            {"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False},
            {"taak": "👕 Aankleden", "tijd": "Ochtend", "klaar": False},
            {"taak": "🥣 Ontbijten", "tijd": "Ochtend", "klaar": False},
            {"taak": "🛏️ Pyjama aan", "tijd": "Avond", "klaar": False},
            {"taak": "📚 Verhaaltje lezen", "tijd": "Avond", "klaar": False}
        ],
        "gezondheid": [],
        "huishoud": [
            {"taak": "🗑️ Grijze container aan straat", "dag": "Maandag", "status": False},
            {"taak": "♻️ Gft-bak buiten zetten", "dag": "Donderdag", "status": False},
            {"taak": "🧽 Vaatwasser filter schoonmaken", "dag": "Zaterdag", "status": False},
            {"taak": "🛏️ Bedden verschonen", "dag": "Zondag", "status": False}
        ]
    }
    sla_data_op(standaard_data)
    return standaard_data

def sla_data_op(data):
    try:
        with open(DATA_BESTAND, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fout bij opslaan: {e}")

if "gezin_data" not in st.session_state: 
    st.session_state["gezin_data"] = laad_data()

vandaag = datetime.date.today()
if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append({"datum": str(datum), "beschrijving": beschrijving})
    sla_data_op(st.session_state["gezin_data"])

def verwijder_agenda_item(index):
    if 0 <= index < len(st.session_state["gezin_data"]["agenda"]):
        st.session_state["gezin_data"]["agenda"].pop(index)
        sla_data_op(st.session_state["gezin_data"])

def voeg_boodschap_toe(item):
    item_schoon = item.strip().capitalize()
    if not item_schoon: return
    if "boodschappen" not in st.session_state["gezin_data"]: 
        st.session_state["gezin_data"]["boodschappen"] = []
    if "boodschappen_historie" not in st.session_state["gezin_data"]: 
        st.session_state["gezin_data"]["boodschappen_historie"] = {}
        
    if item_schoon not in st.session_state["gezin_data"]["boodschappen"]:
        st.session_state["gezin_data"]["boodschappen"].append(item_schoon)
        
    historie = st.session_state["gezin_data"]["boodschappen_historie"]
    historie[item_schoon] = historie.get(item_schoon, 0) + 1
    sla_data_op(st.session_state["gezin_data"])

def verwerk_meerdere_boodschappen(tekst):
    if not tekst: return
    try:
        prompt = f"Splits de volgende tekst op in losse boodschappen. Geef enkel een JSON lijst van strings terug, bijv: [\"Melk\", \"Brood\"]. Tekst: '{tekst}'"
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt, 
            config={'response_mime_type': 'application/json'}
        )
        items = json.loads(res.text)
        if isinstance(items, list):
            for item in items:
                voeg_boodschap_toe(str(item))
            return
    except Exception:
        pass
    
    delen = re.split(r',|\sen\s|\splus\s|\sen ook\s', tekst, flags=re.IGNORECASE)
    for d in delen:
        voeg_boodschap_toe(d)

def verwijder_boodschappen_op_index(indices_om_te_verwijderen):
    huidige = st.session_state["gezin_data"].get("boodschappen", [])
    nieuwe_lijst = [item for i, item in enumerate(huidige) if i not in indices_om_te_verwijderen]
    st.session_state["gezin_data"]["boodschappen"] = nieuwe_lijst
    sla_data_op(st.session_state["gezin_data"])

def leeg_boodschappenlijst():
    st.session_state["gezin_data"]["boodschappen"] = []
    sla_data_op(st.session_state["gezin_data"])

GEZIN_CONTEXT = (
    "Je bent Boris, de slimme en vriendelijke virtuele huiszwijn-assistent van het gezin Zwijnenberg: "
    "Chiel, Angelica, Tygo (3 jaar) en Duén (1 jaar). Jullie wonen in Luttenberg. "
    "Je helpt met planning en voedselverspilling voorkomen. Je spreekt vrolijk, kort, en eindigt vaak met 'Oink!'."
)

def genereer_tts_script(tekst, knop_tekst="🎙️ Voorlezen", img_id="Boris-main-img", auto_play=False):
    schone_tekst = tekst.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
    auto_code = "spreekTekst('" + schone_tekst + "');" if auto_play else ""
    return f"""
    <script>
    function spreekTekst(tekst) {{
        let img = window.parent.document.getElementById('{img_id}');
        window.speechSynthesis.cancel();
        let speech = new SpeechSynthesisUtterance(tekst);
        speech.lang = 'nl-NL'; 
        speech.pitch = 1.6;
        speech.rate = 1.05;
        let voices = window.speechSynthesis.getVoices();
        let nlVoice = voices.find(v => v.lang.includes('nl'));
        if (nlVoice) {{ speech.voice = nlVoice; }}
        speech.onstart = function() {{ if(img) img.classList.add('Boris-img-talking'); }};
        speech.onend = function() {{ if(img) img.classList.remove('Boris-img-talking'); }};
        window.speechSynthesis.speak(speech);
    }}
    {auto_code}
    </script>
    <div style="text-align: center; margin-top: 3px;">
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: bold; color: #4CAF50; width: 100%; padding: 4px;">
            {knop_tekst}
        </button>
    </div>
    """


# ==========================================
# HOOFDSCHERM (DASHBOARD - 4x4 RASTER APPS)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a.get("datum", "") >= vandaag_str])

    col_titel, col_datum = st.columns([3, 1])
    with col_titel:
        st.markdown("### 🏠 Zwijnenberg")
    with col_datum:
        st.markdown(f"<p style='text-align: right; font-size: 11px; color: #aaa; margin-top: 5px;'>{vandaag.strftime('%d-%m-%Y')}</p>", unsafe_allow_html=True)
    
    dashboard_knoppen = [
        ("💬", "Chat", "Chat"),
        ("📅", f"Agenda ({aantal_afspraken_komend})", "Agenda"),
        ("🛒", f"Lijst ({aantal_boodschappen})", "Boodschappenlijst"),
        ("🍽️", "Menu", "Weekmenu"),
        ("🎯", "Schema", "Dagschema"),
        ("🌳", "Uitjes", "Activiteiten"),
        ("💊", "Zorg", "Gezondheid"),
        ("🧹", "Klusjes", "Huishoud"),
        ("🔍", "Recept", "Recepten"),
        ("🧾", "Bon", "Kassabon Scanner"),
        ("🎵", "Disco", "Kids")
    ]

    cols_per_rij = 4
    for i in range(0, len(dashboard_knoppen), cols_per_rij):
        rij_items = dashboard_knoppen[i:i+cols_per_rij]
        cols = st.columns(cols_per_rij)
        for j, (icoon, tekst, pagina) in enumerate(rij_items):
            with cols[j]:
                if st.button(f"{icoon}\n{tekst}", use_container_width=True, key=f"dash_btn_{pagina}"):
                    ga_naar(pagina)


# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("#### ➕ Nieuwe afspraak")
    with st.form("agenda_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 2])
        with col1: nieuwe_datum = st.date_input("Datum", vandaag)
        with col2: nieuwe_beschrijving = st.text_input("Omschrijving")
        
        if st.form_submit_button("Opslaan") and nieuwe_beschrijving:
            voeg_agenda_toe(nieuwe_datum.strftime("%Y-%m-%d"), nieuwe_beschrijving)
            st.success("Oink! Staat genoteerd!")
            st.rerun()

    st.markdown("---")
    
    col_prev, col_title, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Vorige"):
            if st.session_state["kalender_maand"] == 1:
                st.session_state["kalender_maand"] = 12
                st.session_state["kalender_jaar"] -= 1
            else: st.session_state["kalender_maand"] -= 1
            st.rerun()
    with col_next:
        if st.button("Volgende ➡️"):
            if st.session_state["kalender_maand"] == 12:
                st.session_state["kalender_maand"] = 1
                st.session_state["kalender_jaar"] += 1
            else: st.session_state["kalender_maand"] += 1
            st.rerun()

    jaar = st.session_state["kalender_jaar"]
    maand = st.session_state["kalender_maand"]
    with col_title:
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{calendar.month_name[maand]} {jaar}</h3>", unsafe_allow_html=True)

    agenda_dict = {}
    for item in st.session_state["gezin_data"].get("agenda", []):
        d_str = str(item.get("datum", ""))
        if d_str not in agenda_dict: agenda_dict[d_str] = []
        agenda_dict[d_str].append(item.get("beschrijving", ""))

    cal = calendar.monthcalendar(jaar, maand)
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    
    html_cal = """
    <style>
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; padding-bottom: 10px; }
    .cal-header { text-align: center; font-weight: bold; font-size: 0.7rem; padding: 2px 0; color: #aaa; }
    .cal-day { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; padding: 2px; text-align: center; min-height: 32px; display: flex; flex-direction: column; justify-content: start; align-items: center;}
    .cal-day span.date { font-weight: bold; font-size: 0.75rem; color: #ffffff !important; }
    .cal-day.vandaag { border: 2px solid #ff9800; background-color: #2c221e; }
    .cal-day.afspraak { background-color: #1c2732; border-color: #2196F3; }
    .cal-leeg { background-color: transparent; }
    .cal-badge { font-size: 0.55rem; color: #90caf9; font-weight: bold; margin-top: 1px; }
    </style>
    <div class="cal-wrapper">
    """
    for dag in ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]:
        html_cal += f"<div class='cal-header'>{dag}</div>"
        
    for week in cal:
        for dag in week:
            if dag == 0: html_cal += "<div class='cal-leeg'></div>"
            else:
                datum_str = f"{jaar}-{maand:02d}-{dag:02d}"
                cls = "cal-day"
                if datum_str == vandaag_str: cls += " vandaag"
                if datum_str in agenda_dict: cls += " afspraak"
                badge = f"<div class='cal-badge'>📌 {len(agenda_dict[datum_str])}</div>" if datum_str in agenda_dict else ""
                html_cal += f"<div class='{cls}'><span class='date'>{dag}</span>{badge}</div>"
                
    html_cal += "</div>"
    st.markdown(html_cal, unsafe_allow_html=True)
    
    st.markdown("### 📋 Alle geplande afspraken:")
    agenda_lijst = st.session_state["gezin_data"].get("agenda", [])
    if agenda_lijst:
        for idx, item in enumerate(agenda_lijst):
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")
            with col_del:
                if st.button("🗑️", key=f"del_agenda_{idx}"):
                    verwijder_agenda_item(idx)
                    st.rerun()
    else:
        st.info("Er staan nog geen afspraken in de agenda.")


# ==========================================
# SUBPAGINA: BOODSCHAPPENLIJST (4x4 APP GRID)
# ==========================================
elif st.session_state["huidige_pagina"] == "Boodschappenlijst":
    if "spraak_input" in st.query_params:
        gesproken_tekst = st.query_params.get("spraak_input")
        if gesproken_tekst:
            verwerk_meerdere_boodschappen(gesproken_tekst)
            st.toast(f"🎙️ Ingesproken: '{gesproken_tekst}' toegevoegd!")
        del st.query_params["spraak_input"]
        st.rerun()

    if st.button("🔙 Terug"): ga_naar("Home")
    
    if "actieve_hoofd_cat" not in st.session_state: st.session_state["actieve_hoofd_cat"] = None
    if "actieve_sub_cat" not in st.session_state: st.session_state["actieve_sub_cat"] = None

    supermarkt_database = {
        "AGF": {
            "Vers fruit": [("🍎", "Appels"), ("🍌", "Bananen"), ("🍓", "Bessen"), ("🍊", "Citrus")],
            "Groenten": [("🥬", "Sla"), ("🍅", "Tomaten"), ("🧅", "Uien"), ("🥕", "Wortels")],
            "Aardappel": [("🥔", "Aardappel"), ("🥔", "Krieltjes")],
            "Salades": [("🥗", "Salade"), ("🥕", "Snacks")]
        },
        "Zuivel": {
            "Melk": [("🥛", "Melk"), ("🥛", "Karnemelk"), ("🥛", "Haver")],
            "Yoghurt": [("🥣", "Yoghurt"), ("🥣", "Kwark")],
            "Kaas": [("🧀", "Jong kaas"), ("🧀", "Oud kaas"), ("🧀", "Smeerkaas")],
            "Eieren/Boter": [("🥚", "Eieren"), ("🧈", "Boter")]
        },
        "Vlees/Vis": {
            "Vlees": [("🍗", "Kip"), ("🥩", "Gehakt"), ("🥩", "Bief")],
            "Vis": [("🐟", "Zalm"), ("🐟", "Kabeljauw"), ("🦐", "Garnaal")],
            "Vega": [("🌱", "Vega"), ("🌱", "Tofu"), ("🧆", "Falafel")]
        },
        "Brood/Ontbijt": {
            "Brood": [("🍞", "Brood"), ("🥖", "Stokbrood"), ("🥐", "Croissant")],
            "Granen": [("🥣", "Muesli"), ("🥣", "Havermout")],
            "Beleg": [("🍓", "Jam"), ("🥜", "Pindakaas"), ("🍫", "Hagel"), ("🍯", "Honing")]
        },
        "Dranken": {
            "Fris/Sap": [("🥤", "Cola"), ("🥤", "Sinas"), ("💧", "Water"), ("🧃", "Sap")],
            "Koffie/Thee": [("☕", "Koffie"), ("🍵", "Thee")],
            "Alcohol": [("🍺", "Bier"), ("🍷", "Wijn")]
        },
        "Houdbaar": {
            "Pasta/Rijst": [("🍝", "Pasta"), ("🍚", "Rijst"), ("🍜", "Mie")],
            "Conserven": [("🥫", "Soep"), ("🥫", "Groente"), ("🐟", "Tonijn")],
            "Sauzen": [("🧂", "Mayo"), ("🍅", "Ketchup"), ("🫒", "Olie")]
        },
        "Snacks": {
            "Zout": [("🥔", "Chips"), ("🍿", "Popcorn"), ("🥨", "Noten")],
            "Zoet": [("🍬", "Snoep"), ("🍫", "Choco"), ("🍪", "Koek")]
        },
        "Diepvries": {
            "Diepvries": [("🍕", "Pizza"), ("🍦", "IJs"), ("🍟", "Friet"), ("🥦", "Groente")]
        },
        "Non-Food": {
            "Verzorging": [("🧴", "Shampoo"), ("🪥", "Tandpasta"), ("🧼", "Zeep")],
            "Schoonmaak": [("🧼", "Vaatwas"), ("🫧", "Wasmiddel"), ("🧻", "Wc-papier"), ("🗑️", "Zakken")]
        }
    }

    st.markdown("#### 🗂️ Kassaregister Categorieën")
    hoofd_cat = st.session_state["actieve_hoofd_cat"]
    sub_cat = st.session_state["actieve_sub_cat"]

    if hoofd_cat is not None:
        col_terug, col_titel_cat = st.columns([1, 3])
        with col_terug:
            if st.button("⬅️ Terug", key="terug_naar_hoofd"):
                st.session_state["actieve_hoofd_cat"] = None
                st.rerun()
        with col_titel_cat:
            st.markdown(f"**📂 {hoofd_cat}**")
        
        sub_dict = supermarkt_database.get(hoofd_cat, {})
        
        if sub_cat is None:
            sub_lijst = list(sub_dict.items())
            cols_per_rij = 4
            for i in range(0, len(sub_lijst), cols_per_rij):
                rij = sub_lijst[i:i+cols_per_rij]
                cols = st.columns(cols_per_rij)
                for j, (s_naam, items_lijst) in enumerate(rij):
                    with cols[j]:
                        ic = items_lijst[0][0] if items_lijst else "🛒"
                        if st.button(f"{ic}\n{s_naam}", key=f"subcat_btn_{i+j}", use_container_width=True):
                            st.session_state["actieve_sub_cat"] = s_naam
                            st.rerun()
        else:
            if st.button("⬅️ Terug naar subcats", key="terug_naar_subs_overzicht"):
                st.session_state["actieve_sub_cat"] = None
                st.rerun()
                
            st.markdown(f"**🏷️ {sub_cat}**")
            producten = sub_dict.get(sub_cat, [])
            
            cols_per_rij = 4
            for i in range(0, len(producten), cols_per_rij):
                rij = producten[i:i+cols_per_rij]
                cols = st.columns(cols_per_rij)
                for j, (icoon, prod_naam) in enumerate(rij):
                    with cols[j]:
                        if st.button(f"{icoon}\n{prod_naam}", key=f"prod_btn_{i+j}", use_container_width=True):
                            voeg_boodschap_toe(prod_naam)
                            st.toast(f"✅ '{prod_naam}' toegevoegd!")
                            st.rerun()

    else:
        hoofd_icoontjes = [
            ("🥦", "AGF"),
            ("🥛", "Zuivel"),
            ("🥩", "Vlees/Vis"),
            ("🥐", "Brood/Ontbijt"),
            ("🥤", "Dranken"),
            ("🥫", "Houdbaar"),
            ("🍫", "Snacks"),
            ("🍕", "Diepvries"),
            ("🧻", "Non-Food")
        ]
        
        cols_per_rij = 4
        for i in range(0, len(hoofd_icoontjes), cols_per_rij):
            rij = hoofd_icoontjes[i:i+cols_per_rij]
            cols = st.columns(cols_per_rij)
            for j, (icoon, cat_naam) in enumerate(rij):
                with cols[j]:
                    if st.button(f"{icoon}\n{cat_naam}", key=f"hoofd_cat_{i+j}", use_container_width=True):
                        st.session_state["actieve_hoofd_cat"] = cat_naam
                        st.session_state["actieve_sub_cat"] = None
                        st.rerun()

    st.markdown("---")

    with st.form("boodschap_form", clear_on_submit=True):
        col_in, col_btn = st.columns([3, 1])
        with col_in:
            nieuw_item = st.text_input("Snel toevoegen:", placeholder="Typ bijv. melk...")
        with col_btn:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("➕")
            if submit and nieuw_item:
                verwerk_meerdere_boodschappen(nieuw_item)
                st.rerun()

    st.components.v1.html("""
        <div style="text-align: center;">
            <button id="micBtn" onclick="startDictation()" style="
                background-color: #1B4D2E;
                color: white;
                border: 1px solid #2E7D32;
                border-radius: 6px;
                padding: 5px;
                font-size: 11px;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
                box-shadow: 0 1px 2px rgba(0,0,0,0.15);
            ">
                🎙️ Spreek hele lijst in
            </button>
            <p id="statusMsg" style="color: #aaa; font-size: 9px; margin-top: 2px; margin-bottom: 0;"></p>
        </div>

        <script>
        function startDictation() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                var recognition = new SpeechRecognition();
                recognition.lang = 'nl-NL';
                recognition.interimResults = false;

                var btn = document.getElementById('micBtn');
                var status = document.getElementById('statusMsg');

                status.innerText = '🎤 Luisteren...';
                btn.style.backgroundColor = '#d32f2f';

                recognition.start();

                recognition.onresult = function(event) {
                    var res = event.results[0][0].transcript;
                    status.innerText = 'Verwerken: "' + res + '"';
                    
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set("spraak_input", res);
                    window.parent.location.href = url.href;
                };

                recognition.onerror = function(event) {
                    status.innerText = 'Fout: ' + event.error;
                    btn.style.backgroundColor = '#1B4D2E';
                };

                recognition.onend = function() {
                    btn.style.backgroundColor = '#1B4D2E';
                };
            } else {
                alert('Spraakherkenning niet ondersteund.');
            }
        }
        </script>
    """, height=45)

    st.markdown("---")

    st.markdown("#### 🛒 Actieve Lijst")
    boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen_lijst:
        indices_om_te_verwijderen = []
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(f"🛍️ {item}", key=f"boodschap_{idx}"): 
                indices_om_te_verwijderen.append(idx)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if indices_om_te_verwijderen:
                if st.button("🗑️ Wis selectie", use_container_width=True):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        with col_v2:
            if st.button("❌ Wis alles", use_container_width=True):
                leeg_boodschappenlijst()
                st.rerun()
    else: 
        st.info("Lijstje is leeg!")


# ==========================================
# SUBPAGINA: WEEKMENU
# ==========================================
elif st.session_state["huidige_pagina"] == "Weekmenu":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🍽️ Slim Weekmenu & Boodschappen")
    st.write("Genereer een kindvriendelijk weekmenu (voor Tygo en Duén) en zet ingrediënten direct op de lijst.")
    
    if st.button("✨ Genereer nieuw weekmenu", type="primary"):
        with st.spinner("Boris stelt het menu samen..."):
            prompt = (
                f"{GEZIN_CONTEXT} Genereer een gevarieerd weekmenu voor 5 dagen (Maandag t/m Vrijdag) "
                "specifiek gericht op kindvriendelijke maaltijden (geschikt voor Tygo van 3 en Duén van 1). "
                "Geef de output terug als een JSON object met als sleutels 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', "
                "waarbij elke dag een object is met 'gerecht' (string) en 'ingredienten' (lijst van strings). "
                "Voorbeeldformaat: {\"Maandag\": {\"gerecht\": \"Milde macaroni\", \"ingredienten\": [\"Macaroni\", \"Gehakt\", \"Tomatensaus\"]}}"
            )
            try:
                res = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=prompt, 
                    config={'response_mime_type': 'application/json'}
                )
                menu_data = parse_json_veilig(res.text)
                if menu_data:
                    st.session_state["gezin_data"]["weekmenu"] = menu_data
                    sla_data_op(st.session_state["gezin_data"])
                    st.success("Oink! Nieuw weekmenu gegenereerd!")
                else:
                    st.error("Kon het menu niet verwerken.")
            except Exception as e:
                st.error(f"Fout: {e}")

    huidig_menu = st.session_state["gezin_data"].get("weekmenu", {})
    if huidig_menu:
        st.markdown("---")
        for dag, info in huidig_menu.items():
            if isinstance(info, dict):
                gerecht = info.get("gerecht", "")
                ingr = info.get("ingredienten", [])
                st.markdown(f"**📅 {dag}:** {gerecht}")
                if ingr:
                    st.caption(f"*Benodigdheden:* {', '.join(ingr)}")
        
        st.markdown("")
        if st.button("🛒 Voeg toe aan Boodschappenlijst", type="secondary"):
            totaal_toegevoegd = 0
            for dag, info in huidig_menu.items():
                if isinstance(info, dict):
                    for ing in info.get("ingredienten", []):
                        voeg_boodschap_toe(ing)
                        totaal_toegevoegd += 1
            st.success(f"Oink! {totaal_toegevoegd} ingrediënten toegevoegd!")
    else:
        st.info("Nog geen weekmenu gegenereerd.")


# ==========================================
# SUBPAGINA: DAGSCHEMA
# ==========================================
elif st.session_state["huidige_pagina"] == "Dagschema":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🎯 Visueel Dagschema Tygo")
    st.write("Vink de routines af voor een beloning van Boris.")
    
    dagschema = st.session_state["gezin_data"].get("dagschema", [])
    alle_klaar = True if dagschema else False
    
    for idx, item in enumerate(dagschema):
        col_chk, col_lbl = st.columns([1, 5])
        with col_chk:
            nieuw_status = st.checkbox("", value=item.get("klaar", False), key=f"dag_taak_{idx}")
            if nieuw_status != item.get("klaar", False):
                st.session_state["gezin_data"]["dagschema"][idx]["klaar"] = nieuw_status
                sla_data_op(st.session_state["gezin_data"])
                st.rerun()
        with col_lbl:
            tijd_label = f" *({item.get('tijd')})*" if item.get('tijd') else ""
            st.markdown(f"**{item.get('taak')}**{tijd_label}")
        if not item.get("klaar", False):
            alle_klaar = False

    if dagschema and alle_klaar:
        st.balloons()
        base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
        IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?q=80&w=200&auto=format&fit=crop"
        st.markdown(f"""
            <div style="text-align: center; background-color: #EBF5EE; padding: 10px; border-radius: 10px; border: 2px solid #2E7D32; margin-top: 8px;">
                <img src="{IMAGE_SRC}" class="Boris-img-dancing" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; margin-bottom: 4px;"><br>
                <h3 style="color: #1B4D2E; margin: 0; font-size: 1rem;">Super gedaan Tygo! 🎉</h3>
                <p style="color: #333; margin-top: 2px; font-size: 0.8rem;">Alles afgerond! Boris danst voor jou!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    with st.form("add_taak_form", clear_on_submit=True):
        nieuwe_taak_naam = st.text_input("Extra taak (bijv. 👟 Schoenen)")
        taak_tijd = st.selectbox("Moment", ["Ochtend", "Middag", "Avond"])
        if st.form_submit_button("Toevoegen") and nieuwe_taak_naam:
            st.session_state["gezin_data"]["dagschema"].append({"taak": nieuwe_taak_naam, "tijd": taak_tijd, "klaar": False})
            sla_data_op(st.session_state["gezin_data"])
            st.rerun()


# ==========================================
# SUBPAGINA: ACTIVITEITEN
# ==========================================
elif st.session_state["huidige_pagina"] == "Activiteiten":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🌳 Activiteiten-Generator")
    st.write("Leuke uitjes in Salland voor een peuter en baby.")
    
    locatie_keuze = st.selectbox("Waar?", ["Binnen", "Buiten / Natuur", "Maakt niet uit"])
    tijd_keuze = st.selectbox("Tijd?", ["Kort (1 uur)", "Halve dag", "Hele dag"])
    
    if st.button("🔍 Zoek uitjes", type="primary"):
        with st.spinner("Boris zoekt..."):
            prompt = (
                f"{GEZIN_CONTEXT} Bedenk 3 kindvriendelijke activiteiten in/rondom Luttenberg/Salland "
                f"voor '{locatie_keuze}' en tijdsduur '{tijd_keuze}', geschikt voor 3 jr en 1 jr."
            )
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            st.session_state["laatste_activiteiten"] = res.text

    if "laatste_activiteiten" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["laatste_activiteiten"])
        st.components.v1.html(
            genereer_tts_script(st.session_state["laatste_activiteiten"], "🔊 Beluister", "Boris-main-img"),
            height=40
        )


# ==========================================
# SUBPAGINA: GEZONDHEID
# ==========================================
elif st.session_state["huidige_pagina"] == "Gezondheid":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 💊 Ziekte & Medicijnen Logboek")
    
    with st.form("gezondheid_form", clear_on_submit=True):
        kind = st.selectbox("Wie?", ["Tygo", "Duén"])
        medicijn = st.text_input("Medicijn / Omschrijving")
        temp = st.text_input("Temp in °C (optioneel)")
        notitie = st.text_area("Notitie")
        
        if st.form_submit_button("Opslaan"):
            nu_tijd = datetime.datetime.now().strftime("%d-%m-%Y om %H:%M")
            item = {"tijd": nu_tijd, "kind": kind, "medicijn": medicijn, "temperatuur": temp, "notitie": notitie}
            if "gezondheid" not in st.session_state["gezin_data"]:
                st.session_state["gezin_data"]["gezondheid"] = []
            st.session_state["gezin_data"]["gezondheid"].insert(0, item)
            sla_data_op(st.session_state["gezin_data"])
            st.success("Opgeslagen!")
            st.rerun()

    st.markdown("---")
    gezondheid_logs = st.session_state["gezin_data"].get("gezondheid", [])
    if gezondheid_logs:
        for log in gezondheid_logs:
            temp_str = f" | 🌡️ {log.get('temperatuur')}°C" if log.get('temperatuur') else ""
            med_str = f" | 💊 {log.get('medicijn')}" if log.get('medicijn') else ""
            st.markdown(f"🕒 **{log.get('tijd')}** — **{log.get('kind')}**{med_str}{temp_str}")
            st.markdown("---")
    else:
        st.info("Geen logs.")


# ==========================================
# SUBPAGINA: HUISHOUD
# ==========================================
elif st.session_state["huidige_pagina"] == "Huishoud":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🧹 Huishoud- & Klusjesrooster")
    
    huishoud_taken = st.session_state["gezin_data"].get("huishoud", [])
    for idx, taken_item in enumerate(huishoud_taken):
        col_c, col_t = st.columns([1, 5])
        with col_c:
            status = st.checkbox("", value=taken_item.get("status", False), key=f"huishoud_chk_{idx}")
            if status != taken_item.get("status", False):
                st.session_state["gezin_data"]["huishoud"][idx]["status"] = status
                sla_data_op(st.session_state["gezin_data"])
                st.rerun()
        with col_t:
            dag_str = f" *({taken_item.get('dag')})*" if taken_item.get('dag') else ""
            st.markdown(f"**{taken_item.get('taak')}**{dag_str}")

    st.markdown("---")
    with st.form("add_huishoud_form", clear_on_submit=True):
        nieuwe_klustaken = st.text_input("Taak omschrijving")
        dag_selectie = st.selectbox("Dag", ["Elke dag", "Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"])
        if st.form_submit_button("Toevoegen") and nieuwe_klustaken:
            st.session_state["gezin_data"]["huishoud"].append({"taak": nieuwe_klustaken, "dag": dag_selectie, "status": False})
            sla_data_op(st.session_state["gezin_data"])
            st.rerun()


# ==========================================
# SUBPAGINA: CHAT MET BORIS
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    if "chat_messages" not in st.session_state: 
        st.session_state["chat_messages"] = []
        
    for idx, msg in enumerate(st.session_state["chat_messages"]):
        with st.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"): 
            st.write(msg["content"])
            if msg["role"] == "assistant":
                st.components.v1.html(genereer_tts_script(msg["content"], "🔊 Beluister", f"chat_tts_{idx}"), height=35)

    user_prompt = st.chat_input("Typ je bericht...")
    if user_prompt:
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"): 
            st.write(user_prompt)
            
        with st.chat_message("assistant", avatar="🐗"):
            with st.spinner("Boris denkt na..."):
                instructie = """Geef een JSON object terug: {"actie": "boodschap_toevoegen"|"agenda_toevoegen"|"geen", "boodschap": "item"|"", "agenda_datum": "YYYY-MM-DD"|"", "agenda_beschrijving": "omschrijving"|"", "antwoord": "tekst"}"""
                try:
                    res = client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=f"{GEZIN_CONTEXT} Gebruiker zegt: '{user_prompt}'\n{instructie}", 
                        config={'response_mime_type': 'application/json'}
                    )
                    data = parse_json_veilig(res.text) or {}
                    actie_melding = ""
                    if data.get("actie") == "boodschap_toevoegen" and data.get("boodschap"): 
                        voeg_boodschap_toe(data["boodschap"])
                        actie_melding = f"\n\n*(✅ '{data['boodschap']}' toegevoegd!)*"
                    elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"): 
                        d = data.get("agenda_datum") or vandaag.strftime("%Y-%m-%d")
                        voeg_agenda_toe(d, data["agenda_beschrijving"])
                        actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' gepland!)*"
                    
                    eind_antwoord = data.get("antwoord", res.text) + actie_melding
                except Exception:
                    eind_antwoord = "Oink! Er ging even iets mis!"
                
                st.write(eind_antwoord)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.rerun()


# ==========================================
# SUBPAGINA: RECEPTEN & VOORRAAD
# ==========================================
elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🍳 Recepten & Voorraad Check")
    camera_file = st.camera_input("📸 Maak foto")
    uploaded_file = st.file_uploader("Of upload", type=["jpg", "png", "jpeg"])
    gekozen_foto = camera_file if camera_file is not None else uploaded_file
    
    if st.button("👨‍🍳 Genereer Recepten", type="primary") and gekozen_foto:
        with st.spinner("Boris snuffelt..."):
            prompt = f"{GEZIN_CONTEXT}\nVerzin 2 kindvriendelijke recepten. Eindig met JSON: {{\"boodschappen\": [\"item 1\"]}}."
            res = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt, Image.open(gekozen_foto)])
            st.session_state["laatste_recept"] = res.text
            
    if "laatste_recept" in st.session_state:
        tekst = st.session_state["laatste_recept"]
        data = parse_json_veilig(tekst)
        leesbare_tekst = re.sub(r'\{.*\}', '', tekst, flags=re.DOTALL).strip()
        st.markdown(leesbare_tekst)
        
        if data and data.get("boodschappen"):
            ontbrekende_items = data["boodschappen"]
            st.info(f"🛒 **Ontbrekend:** {', '.join(ontbrekende_items)}")
            if st.button("➕ Voeg toe aan boodschappenlijst"):
                for item in ontbrekende_items: voeg_boodschap_toe(item)
                st.success("Toegevoegd!")


# ==========================================
# SUBPAGINA: KASSABON SCANNER
# ==========================================
elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🧾 Kassabon Scanner")
    camera_bon = st.camera_input("📸 Foto van bon")
    uploaded_bon = st.file_uploader("Of upload bon", type=["jpg", "png", "jpeg"])
    gekozen_bon = camera_bon if camera_bon is not None else uploaded_bon
    
    if st.button("Scan", type="primary") and gekozen_bon:
        with st.spinner("Analyseren..."):
            res = client.models.generate_content(model='gemini-2.5-flash', contents=[f"{GEZIN_CONTEXT} Vat deze bon samen.", Image.open(gekozen_bon)])
            st.markdown(res.text)


# ==========================================
# SUBPAGINA: BORIS' MINI-DISCO
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🎵 Boris' Mini-Disco!")
    
    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?q=80&w=200&auto=format&fit=crop"
    
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 8px;">
            <img src="{IMAGE_SRC}" id="Boris-dance-img" class="Boris-img-dancing" style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid #ff9800; object-fit: cover;">
        </div>
    """, unsafe_allow_html=True)
    
    if "huidige_dans_opdracht" not in st.session_state:
        st.session_state["huidige_dans_opdracht"] = "Doe een gekke dans als een zwijntje! Oink oink!"

    col_dans1, col_dans2 = st.columns(2)
    with col_dans1:
        if st.button("🎲 Dansopdracht", use_container_width=True):
            opdrachten = [
                "Spring 5 keer als een kangoeroe!",
                "Draai drie rondjes en maak een varkenssnuitje!",
                "Dans als een robot die moet lachen!",
                "Kruip als een tijger over de vloer!",
                "Zwaai met je armen als een windmolen!"
            ]
            st.session_state["huidige_dans_opdracht"] = random.choice(opdrachten)
            st.rerun()

    with col_dans2:
        if st.button("✨ Vraag Boris", use_container_width=True):
            with st.spinner("Boris bedenkt..."):
                try:
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"{GEZIN_CONTEXT} Bedenk één korte, super vrolijke dansopdracht voor Tygo en Duén."
                    )
                    st.session_state["huidige_dans_opdracht"] = res.text.strip()
                except Exception:
                    st.session_state["huidige_dans_opdracht"] = "Klap in je handjes! Oink!"
            st.rerun()

    st.info(f"💃 **Boris:** {st.session_state['huidige_dans_opdracht']}")
    
    st.components.v1.html(
        genereer_tts_script(st.session_state["huidige_dans_opdracht"], "🔊 Spreek uit!", "Boris-dance-img"),
        height=40
    )
