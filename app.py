import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import datetime
import calendar
import json
import os
import random
import base64

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Zwijnenberg Home Assist", 
    page_icon="🐷", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BROWSER HISTORY & BACK-BUTTON FIX ---
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
except FileNotFoundError:
    st.error("🚨 Kan de API-sleutel niet vinden. Zorg voor een `.streamlit/secrets.toml` bestand.")
    st.stop()

def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

# --- ALGEMENE STYLING ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    
    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1) rotate(0deg); }
        20% { transform: translateY(-3px) scale(1.02) rotate(-1deg); }
        40% { transform: translateY(2px) scale(0.98) rotate(1deg); }
        60% { transform: translateY(-2px) scale(1.01) rotate(-1deg); }
        80% { transform: translateY(1px) scale(0.99) rotate(1deg); }
        100% { transform: translateY(0px) scale(1) rotate(0deg); }
    }
    .Boris-img-talking { animation: avatar-talking 0.3s infinite ease-in-out; }
    </style>
""", unsafe_allow_html=True)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "boodschappen_historie" not in data:
                    data["boodschappen_historie"] = {}
                return data
        except json.JSONDecodeError:
            pass
            
    standaard_data = {
        "agenda": [
            {"datum": "2026-04-22", "beschrijving": "💍 Trouwdag Chiel & Angelica"},
            {"datum": "2026-06-11", "beschrijving": "🎂 Verjaardag Duen (1 jr)"},
            {"datum": "2026-10-24", "beschrijving": "🎂 Verjaardag Tygo (3 jr)"}
        ],
        "boodschappen": [],
        "boodschappen_historie": {}
    }
    sla_data_op(standaard_data)
    return standaard_data

def sla_data_op(data):
    with open(DATA_BESTAND, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "gezin_data" not in st.session_state: st.session_state["gezin_data"] = laad_data()

vandaag = datetime.date.today()
if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append({"datum": datum, "beschrijving": beschrijving})
    sla_data_op(st.session_state["gezin_data"])

def voeg_boodschap_toe(item):
    if "boodschappen" not in st.session_state["gezin_data"]: 
        st.session_state["gezin_data"]["boodschappen"] = []
    if "boodschappen_historie" not in st.session_state["gezin_data"]: 
        st.session_state["gezin_data"]["boodschappen_historie"] = {}
        
    if item not in st.session_state["gezin_data"]["boodschappen"]:
        st.session_state["gezin_data"]["boodschappen"].append(item)
        
    historie = st.session_state["gezin_data"]["boodschappen_historie"]
    historie[item] = historie.get(item, 0) + 1
    
    sla_data_op(st.session_state["gezin_data"])

def verwijder_boodschappen_op_index(indices_om_te_verwijderen):
    huidige = st.session_state["gezin_data"].get("boodschappen", [])
    nieuwe_lijst = [item for i, item in enumerate(huidige) if i not in indices_om_te_verwijderen]
    st.session_state["gezin_data"]["boodschappen"] = nieuwe_lijst
    sla_data_op(st.session_state["gezin_data"])

GEZIN_CONTEXT = (
    "Je bent Boris, de slimme en vriendelijke virtuele huiszwijn-assistent van het gezin Zwijnenberg: "
    "Chiel, Angelica, Tygo (3 jaar) en Duen (1 jaar). Jullie wonen in Luttenberg. "
    "Je helpt met planning en voedselverspilling voorkomen. Je spreekt vrolijk, kort, en eindigt vaak met 'Oink!'."
)

def genereer_tts_script(tekst, knop_tekst="🎙️", img_id="Boris-main-img"):
    schone_tekst = tekst.replace("'", "").replace('"', '').replace('\n', ' ')
    return f"""
    <script>
    function spreekTekst(tekst) {{
        let img = window.parent.document.getElementById('{img_id}');
        window.speechSynthesis.cancel();
        let speech = new SpeechSynthesisUtterance(tekst);
        speech.lang = 'nl-NL'; speech.pitch = 1.1; speech.rate = 1.05;
        let voices = window.speechSynthesis.getVoices();
        let maleVoice = voices.find(v => v.lang.includes('nl') && (v.name.toLowerCase().includes('xander') || v.name.toLowerCase().includes('male')));
        if (maleVoice) {{ speech.voice = maleVoice; }} else if (voices.length > 0) {{ speech.voice = voices.find(v => v.lang.includes('nl')); }}
        speech.onstart = function() {{ if(img) img.classList.add('Boris-img-talking'); }};
        speech.onend = function() {{ if(img) img.classList.remove('Boris-img-talking'); }};
        window.speechSynthesis.speak(speech);
    }}
    </script>
    <div style="text-align: center; margin-top: 5px;">
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: bold; color: #4CAF50; width: 100%; padding: 8px;">
            {knop_tekst}
        </button>
    </div>
    """


# ==========================================
# HOOFDSCHERM
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            min-height: 100px;
            white-space: pre-wrap !important;
            border-radius: 16px;
            border: 1px solid #333;
            background-color: #1a1a1a;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: all 0.2s ease-in-out;
            font-size: 1.1rem;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            line-height: 1.4;
        }
        
        .stButton > button:hover, .stButton > button:active {
            border-color: #4CAF50;
            color: #4CAF50;
            background-color: #222222;
            transform: scale(0.98);
        }
        </style>
    """, unsafe_allow_html=True)

    col_titel, col_datum = st.columns([3, 1])
    with col_titel:
        st.markdown("### 🏠 Zwijnenberg")
    with col_datum:
        st.markdown(f"<p style='text-align: right; font-size: 13px; color: #aaa; margin-top: 10px;'>{vandaag.strftime('%d-%m-%Y')}</p>", unsafe_allow_html=True)
    
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a["datum"] >= vandaag_str])

    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?q=80&w=200&auto=format&fit=crop"

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; background-color: #1a1a1a; padding: 15px; border-radius: 16px; border: 1px solid #333; margin-bottom: 10px;">
                <img src="{IMAGE_SRC}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border: 2px solid #4CAF50;">
                <div style="flex-grow: 1;">
        """, unsafe_allow_html=True)
        if st.button("💬 **Chat met Boris**", key="btn_chat", use_container_width=True):
            ga_naar("Chat")
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    with r1c2:
        if st.button(f"🛒 **Boodschappenlijst**\n\n{aantal_boodschappen} items op lijst", key="btn_boodschappen", use_container_width=True):
            ga_naar("Boodschappenlijst")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if st.button(f"📅 **Agenda**\n\n{aantal_afspraken_komend} afspraken gepland", key="btn_agenda", use_container_width=True):
            ga_naar("Agenda")
    with r2c2:
        if st.button("🍳 **Koken & Recepten**\n\nVoorraad check", key="btn_recepten", use_container_width=True):
            ga_naar("Recepten")

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        if st.button("🧾 **Kassabon Scanner**\n\nBewaar & analyseer", key="btn_bonnen", use_container_width=True):
            ga_naar("Kassabon Scanner")
    with r3c2:
        if st.button("🧸 **Kids Verhaaltje**\n\nVoor Tygo & Duen", key="btn_kids", use_container_width=True):
            with st.spinner("Boris verzint iets..."):
                prompt = f"{GEZIN_CONTEXT} Vertel een heel kort, grappig verhaaltje (max 4 zines). Richt je tot peuter Tygo en baby Duen."
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                st.session_state['laatste_verhaaltje'] = response.text
                ga_naar("Kids")


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
    .cal-day span.date { font-weight: bold; font-size: 0.9rem; color: #fff; }
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
    
    st.markdown("### Aankomende planning:")
    gesorteerd = sorted(st.session_state["gezin_data"].get("agenda", []), key=lambda x: str(x.get("datum", "")))
    for item in gesorteerd:
        if item.get("datum", "") >= f"{jaar}-{maand:02d}-01":
            st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")

# ==========================================
# SUBPAGINA: BOODSCHAPPENLIJST (KASSA TEGEL STIJL & PRIJS BIJ KLIK)
# ==========================================
elif st.session_state["huidige_pagina"] == "Boodschappenlijst":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if "actieve_categorie" not in st.session_state:
        st.session_state["actieve_categorie"] = None

    if "geselecteerd_product" not in st.session_state:
        st.session_state["geselecteerd_product"] = None

    # Schone productnamen zonder specificaties (zoals gewicht/aantal), prijzen per supermarkt zitten apart
    supermarkt_assortiment = {
        "Groente & Fruit": [
            ("🍎", "Appels Elstar", {"AH": "€2,29", "Jumbo": "€2,19"}),
            ("🍎", "Appels Gala", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🍌", "Bananen", {"AH": "€1,79", "Jumbo": "€1,69"}),
            ("🍐", "Peren Conference", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🍊", "Sinaasappels", {"AH": "€2,19", "Jumbo": "€2,09"}),
            ("🍓", "Aardbeien", {"AH": "€3,49", "Jumbo": "€3,29"}),
            ("🍇", "Witte Druiven", {"AH": "€2,99", "Jumbo": "€2,89"}),
            ("🥑", "Avocado", {"AH": "€1,59", "Jumbo": "€1,49"}),
            ("🍅", "Cherry Tomaten", {"AH": "€1,69", "Jumbo": "€1,59"}),
            ("🥒", "Komkommer", {"AH": "€0,99", "Jumbo": "€0,95"}),
            ("🥕", "Bospeen", {"AH": "€1,29", "Jumbo": "€1,19"}),
            ("🥦", "Broccoli", {"AH": "€1,49", "Jumbo": "€1,39"}),
            ("🧅", "Witte Uien", {"AH": "€1,39", "Jumbo": "€1,29"}),
            ("🧄", "Knoflook", {"AH": "€0,75", "Jumbo": "€0,69"}),
            ("🫑", "Paprika Mix", {"AH": "€1,89", "Jumbo": "€1,79"})
        ],
        "Zuivel & Eieren": [
            ("🥛", "Halfvolle Melk", {"AH": "€1,15", "Jumbo": "€1,12"}),
            ("🥛", "Volle Melk", {"AH": "€1,19", "Jumbo": "€1,15"}),
            ("🧈", "Roomboter", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🧀", "Jonge Kaas", {"AH": "€7,99", "Jumbo": "€7,79"}),
            ("🧀", "Belegen Kaas", {"AH": "€8,49", "Jumbo": "€8,29"}),
            ("🥚", "Scharreleieren", {"AH": "€2,89", "Jumbo": "€2,79"}),
            ("🥣", "Griekse Yoghurt", {"AH": "€2,19", "Jumbo": "€2,09"}),
            ("🥣", "Magere Kwark", {"AH": "€1,89", "Jumbo": "€1,79"}),
            ("🍮", "Vanillevla", {"AH": "€1,39", "Jumbo": "€1,29"}),
            ("🧀", "Mozzarella", {"AH": "€0,89", "Jumbo": "€0,85"})
        ],
        "Brood & Beleg": [
            ("🍞", "Witbrood", {"AH": "€1,59", "Jumbo": "€1,49"}),
            ("🍞", "Volkoren Brood", {"AH": "€1,69", "Jumbo": "€1,59"}),
            ("🍞", "Tijgerbruin Brood", {"AH": "€1,89", "Jumbo": "€1,79"}),
            ("🥖", "Afbak Pistolets", {"AH": "€0,99", "Jumbo": "€0,89"}),
            ("🥐", "Croissants", {"AH": "€1,49", "Jumbo": "€1,39"}),
            ("🍫", "Hagelslag Melk", {"AH": "€2,19", "Jumbo": "€2,09"}),
            ("🥜", "Pindakaas", {"AH": "€2,69", "Jumbo": "€2,59"}),
            ("🍯", "Aardbeienjam", {"AH": "€2,19", "Jumbo": "€2,09"})
        ],
        "Vlees & Vis": [
            ("🥩", "Rundergehakt", {"AH": "€4,99", "Jumbo": "€4,89"}),
            ("🍗", "Kipfilet", {"AH": "€5,49", "Jumbo": "€5,29"}),
            ("🍗", "Kippendijen", {"AH": "€5,89", "Jumbo": "€5,69"}),
            ("🍔", "Runderhamburgers", {"AH": "€3,29", "Jumbo": "€3,09"}),
            ("🥓", "Spekblokjes", {"AH": "€1,79", "Jumbo": "€1,69"}),
            ("🐟", "Zalmfilet", {"AH": "€5,99", "Jumbo": "€5,79"}),
            ("🐟", "Tonijn in blik", {"AH": "€3,49", "Jumbo": "€3,29"})
        ],
        "Dranken": [
            ("💧", "Mineraalwater", {"AH": "€0,65", "Jumbo": "€0,60"}),
            ("🥤", "Coca-Cola / Zero", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🧃", "Sinaasappelsap", {"AH": "€2,19", "Jumbo": "€2,09"}),
            ("☕", "Koffiebonen", {"AH": "€13,99", "Jumbo": "€12,99"}),
            ("☕", "Filterkoffie", {"AH": "€4,29", "Jumbo": "€4,09"}),
            ("🍵", "Groene Thee", {"AH": "€1,89", "Jumbo": "€1,79"}),
            ("🍺", "Bier Krat", {"AH": "€15,99", "Jumbo": "€15,49"})
        ],
        "Voorraadkast": [
            ("🍝", "Spaghetti", {"AH": "€1,29", "Jumbo": "€1,19"}),
            ("🍝", "Macaroni / Penne", {"AH": "€1,29", "Jumbo": "€1,19"}),
            ("🍚", "Witte Rijst", {"AH": "€1,79", "Jumbo": "€1,69"}),
            ("🥫", "Pastasaus", {"AH": "€1,89", "Jumbo": "€1,79"}),
            ("🥫", "Groentesoep", {"AH": "€2,19", "Jumbo": "€2,09"}),
            ("🥣", "Bruine Bonen", {"AH": "€1,19", "Jumbo": "€1,09"}),
            ("🌽", "Mais", {"AH": "€1,09", "Jumbo": "€0,99"})
        ],
        "Kruiden & Sauzen": [
            ("🧂", "Zeezout", {"AH": "€0,65", "Jumbo": "€0,60"}),
            ("🧂", "Zwarte Peper", {"AH": "€1,79", "Jumbo": "€1,69"}),
            ("🌿", "Paprikapoeder", {"AH": "€1,29", "Jumbo": "€1,19"}),
            ("🌿", "Bouillonblokjes", "AH": "€1,19", "Jumbo": "€1,09"}),
            ("🥫", "Mayonaise", {"AH": "€2,29", "Jumbo": "€2,19"}),
            ("🍟", "Tomatenketchup", {"AH": "€1,89", "Jumbo": "€1,79"})
        ],
        "Snacks": [
            ("🥔", "Ribbelchips Naturel", {"AH": "€1,69", "Jumbo": "€1,59"}),
            ("🌶️", "Paprika Chips", {"AH": "€1,69", "Jumbo": "€1,59"}),
            ("🍪", "Room Boterkoekjes", {"AH": "€1,89", "Jumbo": "€1,79"}),
            ("🍫", "Chocoladereep Melk", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🥞", "Pannenkoeken", {"AH": "€1,79", "Jumbo": "€1,69"}),
            ("🧇", "Stroopwafels", {"AH": "€1,89", "Jumbo": "€1,79"})
        ],
        "Huishouden & Schoonmaak": [
            ("🧻", "Toiletpapier", {"AH": "€5,49", "Jumbo": "€5,29"}),
            ("🧻", "Keukenpapier", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🧼", "Wasmiddel Vloeibaar", {"AH": "€7,99", "Jumbo": "€7,49"}),
            ("🧽", "Vaatdoekjes", {"AH": "€1,39", "Jumbo": "€1,29"}),
            ("🗑️", "Vuilniszakken", {"AH": "€2,49", "Jumbo": "€2,39"}),
            ("🫧", "Afwasmiddel", "AH: €1,99", "Jumbo": "€1,89"})
        ],
        "Drogisterij & Baby": [
            ("👶", "Pampers Luiers", {"Kruidvat": "€14,99", "AH": "€14,49"}),
            ("🧻", "Billendoekjes", {"Kruidvat": "€12,99", "Lidl": "€9,99"}),
            ("🧴", "Sudocrem Billenzalf", {"Kruidvat": "€4,49", "Etos": "€4,79"}),
            ("🧴", "Zwitsal Badschuim", {"Kruidvat": "€3,29", "AH": "€2,99"}),
            ("🦷", "Tandpasta", {"Kruidvat": "€2,49", "AH": "€2,29"}),
            ("💊", "Paracetamol 500mg", {"Kruidvat": "€1,69", "AH": "€1,49"})
        ],
        "Bakken": [
            ("🧁", "Cupcake / Bakmix", {"AH": "€1,99", "Jumbo": "€1,89"}),
            ("🌾", "Tarwebloem", {"AH": "€1,09", "Jumbo": "€0,99"}),
            ("🧂", "Kristalsuiker", {"AH": "€1,39", "Jumbo": "€1,29"}),
            ("🥣", "Havermout", {"AH": "€1,29", "Jumbo": "€1,19"})
        ]
    }

    # Strakke kassa-tegel styling (compact, vierkant, strakke randen zoals op een winkelkassa)
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            height: 95px !important;
            white-space: pre-wrap !important;
            border-radius: 12px !important;
            border: 1px solid #333333 !important;
            background-color: #1f1f1f !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.1s ease-in-out;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            color: #ffffff !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            line-height: 1.2;
            padding: 5px !important;
        }
        
        .stButton > button:hover, .stButton > button:active {
            border-color: #4CAF50 !important;
            color: #4CAF50 !important;
            background-color: #282828 !important;
            transform: scale(0.97);
        }
        </style>
    """, unsafe_allow_html=True)

    col_lijst, col_tegels = st.columns([1, 1.4])

    with col_lijst:
        st.markdown("### 🛒 Actieve Boodschappenlijst")
        
        with st.form("boodschap_form", clear_on_submit=True):
            nieuw_item = st.text_input("Voeg handmatig een product toe...")
            if st.form_submit_button("Toevoegen") and nieuw_item:
                voeg_boodschap_toe(nieuw_item)
                st.rerun()

        boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
        if boodschappen_lijst:
            st.markdown(f"<p style='color: #aaa; font-size: 0.9rem;'>Totaal {len(boodschappen_lijst)} items op je lijstje</p>", unsafe_allow_html=True)
            indices_om_te_verwijderen = []
            for idx, item in enumerate(boodschappen_lijst):
                if st.checkbox(f"🛍️ {item}", key=f"boodschap_{idx}"): 
                    indices_om_te_verwijderen.append(idx)
            
            if indices_om_te_verwijderen:
                if st.button("🗑️ Verwijder aangevinkte items", type="primary", use_container_width=True):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        else: 
            st.markdown("""
                <div style="background-color: #1a1a1a; border: 2px dashed #444; border-radius: 16px; padding: 25px; text-align: center; color: #888; margin-top: 15px;">
                    <h4>Je lijstje is leeg! 📭</h4>
                    <p style="font-size: 0.9rem; margin-bottom: 0;">Tik rechts op een categorie om direct jullie favoriete producten toe te voegen.</p>
                </div>
            """, unsafe_allow_html=True)

    with col_tegels:
        actieve_cat = st.session_state["actieve_categorie"]
        geselecteerd_prod = st.session_state["geselecteerd_product"]
        
        # Als er een specifiek product is aangeklikt om prijzen per winkel te bekijken:
        if geselecteerd_prod is not None:
            prod_naam, prijzen_dict = geselecteerd_prod
            
            col_terug_prod, col_titel_prod = st.columns([1, 3])
            with col_terug_prod:
                if st.button("⬅️ Terug", key="terug_naar_producten"):
                    st.session_state["geselecteerd_product"] = None
                    st.rerun()
            with col_titel_prod:
                st.markdown(f"#### 🏷️ Prijzen: {prod_naam}")
                
            st.markdown("<p style='color: #aaa; font-size: 0.9rem;'>Vergelijk de prijzen of voeg direct toe aan je lijstje:</p>", unsafe_allow_html=True)
            
            # Toon knoppen per winkel met prijs, en een knop om direct toe te voegen
            cols_prijs = st.columns(len(prijzen_dict))
            for i, (winkel, prijs) in enumerate(prijzen_dict.items()):
                with cols_prijs[i % len(cols_prijs)]:
                    if st.button(f"🏪 **{winkel}**\n\n{prijs}", key=f"winkel_prijs_{i}", use_container_width=True):
                        voeg_boodschap_toe(prod_naam)
                        st.success(f"'{prod_naam}' toegevoegd!")
                        st.session_state["geselecteerd_product"] = None
                        st.rerun()
            
            if st.button("➕ Voeg toe zonder winkelkeuze", use_container_width=True):
                voeg_boodschap_toe(prod_naam)
                st.success(f"'{prod_naam}' toegevoegd!")
                st.session_state["geselecteerd_product"] = None
                st.rerun()

        elif actieve_cat is None:
            st.markdown("### 🗂️ Supermarkt Categorieën")
            
            hoofd_cats = [
                ("🌟", "Eerder Gekozen"),
                ("🍎", "Groente & Fruit"), 
                ("🥛", "Zuivel & Eieren"), 
                ("🍞", "Brood & Beleg"),
                ("🥩", "Vlees & Vis"), 
                ("🥤", "Dranken"), 
                ("🍝", "Voorraadkast"),
                ("🧂", "Kruiden & Sauzen"), 
                ("🥔", "Snacks"), 
                ("🧻", "Huishouden & Schoonmaak"),
                ("👶", "Drogisterij & Baby"), 
                ("🧁", "Bakken")
            ]
            
            cols = st.columns(3)
            for i, (icoon, naam) in enumerate(hoofd_cats):
                col_target = cols[i % 3]
                with col_target:
                    if st.button(f"{icoon}\n\n{naam}", key=f"hoofd_cat_{i}", use_container_width=True):
                        st.session_state["actieve_categorie"] = naam
                        st.rerun()
        else:
            col_terug, col_titel_cat = st.columns([1, 3])
            with col_terug:
                if st.button("⬅️ Terug", key="terug_naar_cats"):
                    st.session_state["actieve_categorie"] = None
                    st.rerun()
            with col_titel_cat:
                st.markdown(f"#### {actieve_cat}")
            
            if actieve_cat == "Eerder Gekozen":
                historie = st.session_state["gezin_data"].get("boodschappen_historie", {})
                gesorteerde_historie = sorted(historie.items(), key=lambda x: x[1], reverse=True)
                
                if not gesorteerde_historie:
                    st.info("Nog geen eerdere items opgeslagen! Voeg wat toe via categorieën of handmatig.")
                else:
                    cols = st.columns(3)
                    for i, (item_naam, count) in enumerate(gesorteerde_historie):
                        col_target = cols[i % 3]
                        with col_target:
                            if st.button(f"⭐\n\n{item_naam}", key=f"hist_btn_{i}", use_container_width=True):
                                voeg_boodschap_toe(item_naam)
                                st.success(f"'{item_naam}' toegevoegd!")
                                st.rerun()
            else:
                items = supermarkt_assortiment.get(actieve_cat, [])
                
                cols = st.columns(3)
                for i, (icoon, subitem, prijzen_dict) in enumerate(items):
                    col_target = cols[i % 3]
                    with col_target:
                        display_icoon = icoon if len(icoon) <= 2 else "🛒"
                        # Kassa tegel toont alleen icoon en productnaam, met een klein subtiel ondertekstje voor actie
                        if st.button(f"{display_icoon}\n\n{subitem}", key=f"sub_btn_{actieve_cat}_{i}", use_container_width=True):
                            # Sla product op en open prijsweergave bij aanklikken van tegel
                            st.session_state["geselecteerd_product"] = (subitem, prijzen_dict)
                            st.rerun()

elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if "chat_messages" not in st.session_state: st.session_state["chat_messages"] = []
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"): st.write(msg["content"])

    user_prompt = st.chat_input("Typ je bericht hier...")
    if user_prompt:
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"): st.write(user_prompt)
            
        with st.chat_message("assistant", avatar="🐗"):
            with st.spinner("Boris denkt na..."):
                instructie = """Geef een JSON: {"actie": "boodschap_toevoegen"|"agenda_toevoegen"|"geen", "boodschap": "item"|"", "agenda_datum": "YYYY-MM-DD"|"", "agenda_beschrijving": "omschrijving"|"", "antwoord": "tekst"}"""
                try:
                    res = client.models.generate_content(model='gemini-3.5-flash', contents=f"{GEZIN_CONTEXT} Gebruiker zegt: '{user_prompt}'\n{instructie}", config={'response_mime_type': 'application/json'})
                    data = json.loads(res.text)
                    actie_melding = ""
                    if data.get("actie") == "boodschap_toevoegen" and data.get("boodschap"): voeg_boodschap_toe(data["boodschap"]); actie_melding = f"\n\n*(✅ '{data['boodschap']}' toegevoegd!)*"
                    elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"): d = data.get("agenda_datum") or vandaag.strftime("%Y-%m-%d"); voeg_agenda_toe(d, data["agenda_beschrijving"]); actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' is ingepland!)*"
                    eind_antwoord = data.get("antwoord", "Oink! Geregeld!") + actie_melding
                except: eind_antwoord = "Oink! Ik begreep het even niet goed."
                
                st.write(eind_antwoord)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.rerun()

elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    camera_file = st.camera_input("📸 Maak direct een foto van je voorraad")
    uploaded_file = st.file_uploader("Of kies een foto uit je galerij", type=["jpg", "png"])
    
    gekozen_foto = camera_file if camera_file is not None else uploaded_file

    if st.button("Genereer Recepten", type="primary") and gekozen_foto:
        with st.spinner("Boris snuffelt..."):
            prompt = f"{GEZIN_CONTEXT}\nKijk naar de foto. Verzin 2 recepten die bederf tegengaan, geschikt voor kinderen (3 en 1). Eindig met JSON: {{\"boodschappen\": [\"item\"]}}."
            res = client.models.generate_content(model='gemini-3.5-flash', contents=[prompt, Image.open(gekozen_foto)])
            st.session_state["laatste_recept"] = res.text
            
    if "laatste_recept" in st.session_state:
        t = st.session_state["laatste_recept"]
        try:
            j = "{" + t.split("{")[-1].split("}")[0] + "}"
            d = json.loads(j)
            t = t.replace(j, "").replace("```json", "").replace("```", "")
            st.markdown(t)
            if d.get("boodschappen"):
                st.info(f"🛒 **Ontbreekt:** {', '.join(d['boodschappen'])}")
                if st.button("Voeg toe aan lijst!"):
                    for i in d["boodschappen"]: voeg_boodschap_toe(i)
                    del st.session_state["laatste_recept"]; st.rerun()
        except: st.markdown(t)

elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    camera_bon = st.camera_input("📸 Maak direct een foto van je bon")
    uploaded_bon = st.file_uploader("Of upload je bon", type=["jpg", "png"])
    gekozen_bon = camera_bon if camera_bon is not None else uploaded_bon

    if st.button("Scan", type="primary") and gekozen_bon:
        with st.spinner("Scannen..."):
            res = client.models.generate_content(model='gemini-3.5-flash', contents=[f"{GEZIN_CONTEXT} Vat deze bon samen en markeer het totaalbedrag.", Image.open(gekozen_bon)])
            st.write(res.text)

elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug naar Home"): ga_naar("Home")
    
    if 'laatste_verhaaltje' in st.session_state:
        base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
        IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?q=80&w=200&auto=format&fit=crop"
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{IMAGE_SRC}" id="Boris-kids-img" class="Boris-img-mini" alt="Boris" style="width: 150px; height: 150px; border-radius:50%; object-fit:cover; border: 3px solid #4CAF50;">
            </div>
        """, unsafe_allow_html=True)
        st.success(st.session_state['laatste_verhaaltje'])
        st.components.v1.html(genereer_tts_script(st.session_state['laatste_verhaaltje'], "🔊 Lees voor", "Boris-kids-img"), height=55)
