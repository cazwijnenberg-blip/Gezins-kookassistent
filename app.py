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

# --- STYLING (MOBIEL GEOPTIMALISEERD: VIERKANT + ROUNDED CORNERS + GEEN HORIZONTAAL SCROLLEN) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }

    /* Voorkom horizontaal scrollen van de hele pagina op mobiel */
    .main, .block-container {
        max-width: 100% !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        overflow-x: hidden !important;
    }
    
    /* Dwing horizontale blokken af om NIET uit te steken of te scrollen */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 0px !important;
    }

    /* Tegelknoppen Stijl: Exact Vierkant + Ronde Hoeken */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border-radius: 16px !important;
        background-color: #EBF5EE !important;
        color: #1B4D2E !important;
        border: 1px solid #D2E7D6 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        transition: transform 0.12s ease, background-color 0.12s ease !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        white-space: pre-wrap !important;
        padding: 4px !important;
        margin-bottom: 2px !important;
        line-height: 1.15 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Pictogrammen (eerste regel van tegelknoppen) */
    .stButton > button p::first-line {
        font-size: 1.5rem !important;
        line-height: 1.2 !important;
    }

    .stButton > button:hover, .stButton > button:active {
        transform: scale(0.95) !important;
        background-color: #E1F0E6 !important;
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
    <div style="text-align: center; margin-top: 5px;">
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: bold; color: #4CAF50; width: 100%; padding: 8px;">
            {knop_tekst}
        </button>
    </div>
    """


# ==========================================
# HOOFDSCHERM (DASHBOARD - MOBIEL PASSTAAI)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a.get("datum", "") >= vandaag_str])

    col_titel, col_datum = st.columns([3, 1])
    with col_titel:
        st.markdown("### 🏠 Zwijnenberg")
    with col_datum:
        st.markdown(f"<p style='text-align: right; font-size: 12px; color: #aaa; margin-top: 5px;'>{vandaag.strftime('%d-%m-%Y')}</p>", unsafe_allow_html=True)
    
    # 2-koloms indeling voor alle hoofdfuncties
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if st.button("💬\nChat Boris", use_container_width=True, key="btn_chat"): ga_naar("Chat")
    with r1c2:
        if st.button(f"📅\nAgenda ({aantal_afspraken_komend})", use_container_width=True, key="btn_agenda"): ga_naar("Agenda")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if st.button(f"🛒\nLijstje ({aantal_boodschappen})", use_container_width=True, key="btn_boodschappen"): ga_naar("Boodschappenlijst")
    with r2c2:
        if st.button("🍽️\nWeekmenu", use_container_width=True, key="btn_weekmenu"): ga_naar("Weekmenu")

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        if st.button("🎯\nDagschema", use_container_width=True, key="btn_dagschema"): ga_naar("Dagschema")
    with r3c2:
        if st.button("🌳\nUitjes", use_container_width=True, key="btn_uitjes"): ga_naar("Activiteiten")

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        if st.button("💊\nGezondheid", use_container_width=True, key="btn_gezondheid"): ga_naar("Gezondheid")
    with r4c2:
        if st.button("🧹\nHuishoud", use_container_width=True, key="btn_huishoud"): ga_naar("Huishoud")

    r5c1, r5c2 = st.columns(2)
    with r5c1:
        if st.button("🔍\nRecepten", use_container_width=True, key="btn_recepten"): ga_naar("Recepten")
    with r5c2:
        if st.button("🧾\nScanner", use_container_width=True, key="btn_bonnen"): ga_naar("Kassabon Scanner")

    r6c1, r6c2 = st.columns(2)
    with r6c1:
        if st.button("🎵\nMini-Disco", use_container_width=True, key="btn_kids"): ga_naar("Kids")
    with r6c2:
        # Lege opvulling om de rij te balanceren
        pass


# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
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
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; padding-bottom: 20px; }
    .cal-header { text-align: center; font-weight: bold; font-size: 0.85rem; padding: 5px 0; color: #aaa; }
    .cal-day { background-color: #1a1a1a; border: 1px solid #333; border-radius: 6px; padding: 5px; text-align: center; min-height: 45px; display: flex; flex-direction: column; justify-content: start; align-items: center;}
    .cal-day span.date { font-weight: bold; font-size: 0.9rem; color: #ffffff !important; }
    .cal-day.vandaag { border: 2px solid #ff9800; background-color: #2c221e; }
    .cal-day.afspraak { background-color: #1c2732; border-color: #2196F3; }
    .cal-leeg { background-color: transparent; }
    .cal-badge { font-size: 0.7rem; color: #90caf9; font-weight: bold; margin-top: 2px; }
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
# SUBPAGINA: BOODSCHAPPENLIJST
# ==========================================
elif st.session_state["huidige_pagina"] == "Boodschappenlijst":
    if "spraak_input" in st.query_params:
        gesproken_tekst = st.query_params.get("spraak_input")
        if gesproken_tekst:
            verwerk_meerdere_boodschappen(gesproken_tekst)
            st.toast(f"🎙️ Ingesproken: '{gesproken_tekst}' toegevoegd!")
        del st.query_params["spraak_input"]
        st.rerun()

    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if "actieve_hoofd_cat" not in st.session_state: st.session_state["actieve_hoofd_cat"] = None
    if "actieve_sub_cat" not in st.session_state: st.session_state["actieve_sub_cat"] = None

    supermarkt_database = {
        "AGF": {
            "Vers fruit": [("🍎", "Appels"), ("🍌", "Bananen"), ("🍓", "Bessen"), ("🍊", "Citrus")],
            "Groenten": [("🥬", "Sla"), ("🍅", "Tomaten"), ("🧅", "Uien"), ("🥕", "Wortels")],
            "Aardappel": [("🥔", "Aardappels"), ("🥔", "Krieltjes")],
            "Salades": [("🥗", "Maaltijdsalade"), ("🥕", "Snackgroente")]
        },
        "Zuivel": {
            "Melk": [("🥛", "Melk"), ("🥛", "Karnemelk"), ("🥛", "Havermelk")],
            "Yoghurt": [("🥣", "Yoghurt"), ("🥣", "Kwark")],
            "Kaas": [("🧀", "Jonge kaas"), ("🧀", "Oude kaas"), ("🧀", "Smeerkaas")],
            "Eieren/Boter": [("🥚", "Eieren"), ("🧈", "Roomboter"), ("🧈", "Margarine")]
        },
        "Vlees/Vis": {
            "Vlees": [("🍗", "Kipfilet"), ("🥩", "Gehakt"), ("🥩", "Biefstuk")],
            "Vis": [("🐟", "Zalm"), ("🐟", "Kabeljauw"), ("🦐", "Garnalen")],
            "Vega": [("🌱", "Vega burgers"), ("🌱", "Tofu"), ("🧆", "Falafel")]
        },
        "Brood/Ontbijt": {
            "Brood": [("🍞", "Brood"), ("🥖", "Stokbrood"), ("🥐", "Croissants")],
            "Granen": [("🥣", "Muesli"), ("🥣", "Havermout"), ("🥣", "Cruesli")],
            "Beleg": [("🍓", "Jam"), ("🥜", "Pindakaas"), ("🍫", "Hagelslag"), ("🍯", "Honing")]
        },
        "Dranken": {
            "Fris/Sap": [("🥤", "Cola"), ("🥤", "Sinas"), ("💧", "Water"), ("🧃", "Jus d'orange")],
            "Koffie/Thee": [("☕", "Koffiebonen"), ("☕", "Koffie"), ("🍵", "Thee")],
            "Alcohol": [("🍺", "Bier"), ("🍷", "Wijn")]
        },
        "Houdbaar": {
            "Pasta/Rijst": [("🍝", "Pasta"), ("🍚", "Rijst"), ("🍜", "Mie")],
            "Conserven": [("🥫", "Soep"), ("🥫", "Groente blik"), ("🐟", "Tonijn")],
            "Sauzen": [("🧂", "Mayo"), ("🍅", "Ketchup"), ("🫒", "Olijfolie")]
        },
        "Snacks": {
            "Zout": [("🥔", "Chips"), ("🍿", "Popcorn"), ("🥨", "Nootjes")],
            "Zoet": [("🍬", "Snoep"), ("🍫", "Chocolade"), ("🍪", "Koekjes")]
        },
        "Diepvries": {
            "Diepvries": [("🍕", "Pizza"), ("🍦", "IJs"), ("🍟", "Friet"), ("🥦", "Diepvriesgroente")]
        },
        "Non-Food": {
            "Verzorging": [("🧴", "Shampoo"), ("🪥", "Tandpasta"), ("🧼", "Zeep")],
            "Schoonmaak": [("🧼", "Vaatwas"), ("🫧", "Wasmiddel"), ("🧻", "Wc-papier"), ("🗑️", "Zakken")]
        }
    }

    st.markdown("#### 🗂️ Categorieën")
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
            cols = st.columns(4)
            sub_namen = list(sub_dict.keys())
            for i, s_naam in enumerate(sub_namen):
                col_target = cols[i % 4]
                with col_target:
                    ic = sub_dict[s_naam][0][0] if sub_dict[s_naam] else "🛒"
                    if st.button(f"{ic}\n{s_naam}", key=f"subcat_btn_{i}", use_container_width=True):
                        st.session_state["actieve_sub_cat"] = s_naam
                        st.rerun()
        else:
            if st.button("⬅️ Terug naar overzicht", key="terug_naar_subs_overzicht"):
                st.session_state["actieve_sub_cat"] = None
                st.rerun()
                
            st.markdown(f"**🏷️ {sub_cat}**")
            producten = sub_dict.get(sub_cat, [])
            
            cols = st.columns(4)
            for i, (icoon, prod_naam) in enumerate(producten):
                col_target = cols[i % 4]
                with col_target:
                    if st.button(f"{icoon}\n{prod_naam}", key=f"prod_btn_{i}", use_container_width=True):
                        voeg_boodschap_toe(prod_naam)
                        st.toast(f"✅ '{prod_naam}' toegevoegd!")
                        st.rerun()

    else:
        hoofd_icoontjes = {
            "AGF": "🥦",
            "Zuivel": "🥛",
            "Vlees/Vis": "🥩",
            "Brood/Ontbijt": "🥐",
            "Dranken": "🥤",
            "Houdbaar": "🥫",
            "Snacks": "🍫",
            "Diepvries": "🍕",
            "Non-Food": "🧻"
        }
        
        cols = st.columns(4)
        for i, (cat_naam, icoon) in enumerate(hoofd_icoontjes.items()):
            col_target = cols[i % 4]
            with col_target:
                if st.button(f"{icoon}\n{cat_naam}", key=f"hoofd_cat_{i}", use_container_width=True):
                    st.session_state["actieve_hoofd_cat"] = cat_naam
                    st.session_state["actieve_sub_cat"] = None
                    st.rerun()

    st.markdown("---")

    with st.form("boodschap_form", clear_on_submit=True):
        col_in, col_btn = st.columns([3, 1])
        with col_in:
            nieuw_item = st.text_input("Snel toevoegen:", placeholder="Typ bijv. melk, brood...")
        with col_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("➕ Voeg toe")
            if submit and nieuw_item:
                verwerk_meerdere_boodschappen(nieuw_item)
                st.rerun()

    st.components.v1.html("""
        <div style="text-align: center;">
            <button id="micBtn" onclick="startDictation()" style="
                background-color: #1B4D2E;
                color: white;
                border: 1px solid #2E7D32;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            ">
                🎙️ Spreek een hele lijst in
            </button>
            <p id="statusMsg" style="color: #aaa; font-size: 11px; margin-top: 4px; margin-bottom: 0;"></p>
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

                status.innerText = '🎤 Luisteren... noem je boodschappen op!';
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
                alert('Spraakherkenning wordt niet ondersteund.');
            }
        }
        </script>
    """, height=65)

    st.markdown("---")

    st.markdown("#### 🛒 Mijn Lijstje")
    boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen_lijst:
        indices_om_te_verwijderen = []
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(f"🛍️ {item}", key=f"boodschap_{idx}"): 
                indices_om_te_verwijderen.append(idx)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if indices_om_te_verwijderen:
                if st.button("🗑️ Wissen (aangevinkt)", use_container_width=True):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        with col_v2:
            if st.button("❌ Alles wissen", use_container_width=True):
                leeg_boodschappenlijst()
                st.rerun()
    else: 
        st.info("Lijstje is leeg! Tik op een categorie hierboven.")


# ==========================================
# SUBPAGINA: IDÉE 2 - SLIM WEEKMENU & BOODSCHAPPEN
# ==========================================
elif st.session_state["huidige_pagina"] == "Weekmenu":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🍽️ Slim Weekmenu & Boodschappen")
    st.write("Genereer een volledig, kindvriendelijk weekmenu (voor peuter Tygo en baby Duén) en voeg direct alle ingrediënten toe aan de boodschappenlijst!")
    
    if st.button("✨ Genereer nieuw weekmenu", type="primary"):
        with st.spinner("Boris stelt een lekker en kindvriendelijk weekmenu samen..."):
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
                    st.error("Kon het menu niet goed verwerken, probeer het nog eens.")
            except Exception as e:
                st.error(f"Fout bij genereren: {e}")

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
        if st.button("🛒 Voeg alle ingrediënten toe aan Boodschappenlijst", type="secondary"):
            totaal_toegevoegd = 0
            for dag, info in huidig_menu.items():
                if isinstance(info, dict):
                    for ing in info.get("ingredienten", []):
                        voeg_boodschap_toe(ing)
                        totaal_toegevoegd += 1
            st.success(f"Oink! {totaal_toegevoegd} ingrediënten toegevoegd aan je boodschappenlijst!")
    else:
        st.info("Nog geen weekmenu gegenereerd. Klik op de knop hierboven!")


# ==========================================
# SUBPAGINA: IDÉE 3 - VISUEEL DAGSCHEMA / ROUTINETRACKER
# ==========================================
elif st.session_state["huidige_pagina"] == "Dagschema":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🎯 Visueel Dagschema voor Tygo")
    st.write("Vink de ochtend- en avondroutines af! Als alles klaar is, wacht er een feestje van Boris.")
    
    dagschema = st.session_state["gezin_data"].get("dagschema", [])
    
    # Filter op ochtend / avond of toon alles overzichtelijk
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
            <div style="text-align: center; background-color: #EBF5EE; padding: 15px; border-radius: 16px; border: 2px solid #2E7D32; margin-top: 15px;">
                <img src="{IMAGE_SRC}" class="Boris-img-dancing" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 8px;"><br>
                <h3 style="color: #1B4D2E; margin: 0;">Super gedaan Tygo! 🎉</h3>
                <p style="color: #333; margin-top: 5px;">Alle taakjes zijn afgerond! Boris doet een overwinningsdansje voor jou! Oink oink!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### ➕ Extra taak toevoegen")
    with st.form("add_taak_form", clear_on_submit=True):
        nieuwe_taak_naam = st.text_input("Naam taak (bijv. 👟 Schoenen aan)")
        taak_tijd = st.selectbox("Moment", ["Ochtend", "Middag", "Avond"])
        if st.form_submit_button("Taak toevoegen") and nieuwe_taak_naam:
            st.session_state["gezin_data"]["dagschema"].append({"taak": nieuwe_taak_naam, "tijd": taak_tijd, "klaar": False})
            sla_data_op(st.session_state["gezin_data"])
            st.success("Taak toegevoegd!")
            st.rerun()


# ==========================================
# SUBPAGINA: IDÉE 5 - ACTIVITEITEN-GENERATOR
# ==========================================
elif st.session_state["huidige_pagina"] == "Activiteiten":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🌳 Wat gaan we doen? (Activiteiten-Generator)")
    st.write("Zoek je inspiratie voor een leuke middag in de omgeving van Luttenberg / Salland voor een peuter van 3 en baby van 1?")
    
    locatie_keuze = st.selectbox("Waar willen jullie naartoe?", ["Binnen", "Buiten / Natuur", "Maakt niet uit"])
    tijd_keuze = st.selectbox("Hoeveel tijd hebben jullie?", ["Kort (1 uur)", "Halve dag", "Hele dag"])
    
    if st.button("🔍 Bedenk uitjes!", type="primary"):
        with st.spinner("Boris zoekt de leukste uitjes in Salland..."):
            prompt = (
                f"{GEZIN_CONTEXT} Bedenk 3 kindvriendelijke activiteiten in of rondom Luttenberg/Salland "
                f"die perfect passen bij een binnen/buiten voorkeur van '{locatie_keuze}' en tijdsduur '{tijd_keuze}', "
                "specifiek geschikt voor een kind van 3 jaar én een baby van 1 jaar (bijv. speelboerderij, boswandeling met kinderwagen, etc.). "
                "Geef een vrolijke, heldere beschrijving per activiteit."
            )
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            st.session_state["laatste_activiteiten"] = res.text

    if "laatste_activiteiten" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["laatste_activiteiten"])
        st.components.v1.html(
            genereer_tts_script(st.session_state["laatste_activiteiten"], "🔊 Vertel de uitjes", "Boris-main-img"),
            height=50
        )


# ==========================================
# SUBPAGINA: IDÉE 6 - ZIEKTE & MEDICIJNEN LOGBOEK
# ==========================================
elif st.session_state["huidige_pagina"] == "Gezondheid":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 💊 Ziekte & Medicijnen Logboek")
    st.write("Houd in de gaten wanneer wie welke medicatie of zetpil heeft gehad en log de temperatuur.")
    
    with st.form("gezondheid_form", clear_on_submit=True):
        kind = st.selectbox("Wie is er ziek / krijgt medicatie?", ["Tygo", "Duén"])
        medicijn = st.text_input("Medicijn / Omschrijving (bijv. Zetpil 240mg of Pufje)")
        temp = st.text_input("Temperatuur in °C (optioneel, bijv. 38.5)")
        notitie = st.text_area("Extra notities")
        
        if st.form_submit_button("Log registreren"):
            nu_tijd = datetime.datetime.now().strftime("%d-%m-%Y om %H:%M")
            item = {
                "tijd": nu_tijd,
                "kind": kind,
                "medicijn": medicijn,
                "temperatuur": temp,
                "notitie": notitie
            }
            if "gezondheid" not in st.session_state["gezin_data"]:
                st.session_state["gezin_data"]["gezondheid"] = []
            st.session_state["gezin_data"]["gezondheid"].insert(0, item)
            sla_data_op(st.session_state["gezin_data"])
            st.success("Oink! Gegevens opgeslagen in het logboek.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Logboek Historie")
    gezondheid_logs = st.session_state["gezin_data"].get("gezondheid", [])
    if gezondheid_logs:
        for idx, log in enumerate(gezondheid_logs):
            temp_str = f" | 🌡️ {log.get('temperatuur')}°C" if log.get('temperatuur') else ""
            med_str = f" | 💊 {log.get('medicijn')}" if log.get('medicijn') else ""
            not_str = f"<br><small>{log.get('notitie')}</small>" if log.get('notitie') else ""
            st.markdown(f"🕒 **{log.get('tijd')}** — **{log.get('kind')}**{med_str}{temp_str}{not_str}", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("Er zijn nog geen medische logs geregistreerd.")


# ==========================================
# SUBPAGINA: IDÉE 7 - HUISHOUD- & KLUSJESROOSTER
# ==========================================
elif st.session_state["huidige_pagina"] == "Huishoud":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🧹 Huishoud- & Klusjesrooster")
    st.write("Overzicht van terugkerende huishoudelijke taken in huis.")
    
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
    st.markdown("#### ➕ Nieuwe taak toevoegen")
    with st.form("add_huishoud_form", clear_on_submit=True):
        nieuwe_klustaken = st.text_input("Taak omschrijving (bijv. 🪟 Ramen lappen)")
        dag_selectie = st.selectbox("Vaste dag", ["Elke dag", "Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"])
        if st.form_submit_button("Taak toevoegen") and nieuwe_klustaken:
            st.session_state["gezin_data"]["huishoud"].append({"taak": nieuwe_klustaken, "dag": dag_selectie, "status": False})
            sla_data_op(st.session_state["gezin_data"])
            st.success("Klusje toegevoegd!")
            st.rerun()


# ==========================================
# SUBPAGINA: CHAT MET BORIS
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if "chat_messages" not in st.session_state: 
        st.session_state["chat_messages"] = []
        
    for idx, msg in enumerate(st.session_state["chat_messages"]):
        with st.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"): 
            st.write(msg["content"])
            if msg["role"] == "assistant":
                st.components.v1.html(genereer_tts_script(msg["content"], "🔊 Beluister", f"chat_tts_{idx}"), height=45)

    user_prompt = st.chat_input("Typ je bericht aan Boris...")
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
                        actie_melding = f"\n\n*(✅ '{data['boodschap']}' toegevoegd aan de boodschappen!)*"
                    elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"): 
                        d = data.get("agenda_datum") or vandaag.strftime("%Y-%m-%d")
                        voeg_agenda_toe(d, data["agenda_beschrijving"])
                        actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' gepland op {d}!)*"
                    
                    eind_antwoord = data.get("antwoord", res.text) + actie_melding
                except Exception:
                    eind_antwoord = "Oink! Er ging even iets mis, maar ik ben er weer!"
                
                st.write(eind_antwoord)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.rerun()


# ==========================================
# SUBPAGINA: RECEPTEN & VOORRAAD
# ==========================================
elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🍳 Recepten & Voorraad Check")
    st.write("Maak een foto van de koelkast of voorraadkast. Boris verzint kindvriendelijke recepten!")
    
    camera_file = st.camera_input("📸 Maak direct een foto")
    uploaded_file = st.file_uploader("Of kies een foto uit je galerij", type=["jpg", "png", "jpeg"])
    gekozen_foto = camera_file if camera_file is not None else uploaded_file
    
    if st.button("👨‍🍳 Genereer Recepten", type="primary") and gekozen_foto:
        with st.spinner("Boris snuffelt tussen de ingrediënten..."):
            prompt = f"{GEZIN_CONTEXT}\nKijk naar de foto. Verzin 2 snelle, kindvriendelijke recepten (voor peuter Tygo en baby Duén). Eindig je tekst exact met deze JSON indeling op een nieuwe regel: {{\"boodschappen\": [\"ontbrekend item 1\", \"ontbrekend item 2\"]}}."
            res = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt, Image.open(gekozen_foto)])
            st.session_state["laatste_recept"] = res.text
            
    if "laatste_recept" in st.session_state:
        tekst = st.session_state["laatste_recept"]
        data = parse_json_veilig(tekst)
        
        leesbare_tekst = re.sub(r'\{.*\}', '', tekst, flags=re.DOTALL).strip()
        st.markdown(leesbare_tekst)
        
        if data and data.get("boodschappen"):
            ontbrekende_items = data["boodschappen"]
            st.info(f"🛒 **Ontbrekende ingrediënten:** {', '.join(ontbrekende_items)}")
            if st.button("➕ Voeg ontbrekende ingrediënten toe aan Boodschappenlijst"):
                for item in ontbrekende_items: 
                    voeg_boodschap_toe(item)
                st.success("Ingrediënten toegevoegd aan je boodschappenlijst!")


# ==========================================
# SUBPAGINA: KASSABON SCANNER
# ==========================================
elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🧾 Kassabon Scanner")
    camera_bon = st.camera_input("📸 Maak direct een foto van je bon")
    uploaded_bon = st.file_uploader("Of upload je bon", type=["jpg", "png", "jpeg"])
    gekozen_bon = camera_bon if camera_bon is not None else uploaded_bon
    
    if st.button("Scan Kassabon", type="primary") and gekozen_bon:
        with st.spinner("Kassabon analyseren..."):
            res = client.models.generate_content(model='gemini-2.5-flash', contents=[f"{GEZIN_CONTEXT} Vat deze bon overzichtelijk samen. Noem de winkel, het totaalbedrag en de opvallendste producten.", Image.open(gekozen_bon)])
            st.markdown(res.text)


# ==========================================
# SUBPAGINA: BORIS' MINI-DISCO
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    st.markdown("### 🎵 Boris' Beweeg & Dansfeestje!")
    
    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?q=80&w=200&auto=format&fit=crop"
    
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 15px;">
            <img src="{IMAGE_SRC}" id="Boris-dance-img" class="Boris-img-dancing" style="width: 120px; height: 120px; border-radius: 50%; border: 3px solid #ff9800; object-fit: cover;">
        </div>
    """, unsafe_allow_html=True)
    
    if "huidige_dans_opdracht" not in st.session_state:
        st.session_state["huidige_dans_opdracht"] = "Doe een gekke dans als een zwijntje! Oink oink!"

    col_dans1, col_dans2 = st.columns(2)
    with col_dans1:
        if st.button("🎲 Nieuwe Dansopdracht!", use_container_width=True):
            opdrachten = [
                "Spring 5 keer zo hoog als een kangoeroe!",
                "Draai drie rondjes en doe een varkenssnuitje na!",
                "Dans als een robot die heel hard moet lachen!",
                "Kruip als een tijger over de vloer en maak een gek geluid!",
                "Zwaai met je armen alsof je een hele snelle molen bent!"
            ]
            st.session_state["huidige_dans_opdracht"] = random.choice(opdrachten)
            st.rerun()

    with col_dans2:
        if st.button("✨ Vraag Boris een opdracht", use_container_width=True):
            with st.spinner("Boris bedenkt een gekke actie..."):
                try:
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"{GEZIN_CONTEXT} Bedenk één hele korte, super vrolijke dans- of beweegopdracht voor Tygo (3 jaar) en baby Duén. Maximaal 1 of 2 zinnen."
                    )
                    st.session_state["huidige_dans_opdracht"] = res.text.strip()
                except Exception:
                    st.session_state["huidige_dans_opdracht"] = "Klap in je handjes en stamp op de grond! Oink!"
            st.rerun()

    st.info(f"💃 **Boris zegt:** {st.session_state['huidige_dans_opdracht']}")
    
    st.components.v1.html(
        genereer_tts_script(st.session_state["huidige_dans_opdracht"], "🔊 Spreek opdracht uit!", "Boris-dance-img"),
        height=50
    )
