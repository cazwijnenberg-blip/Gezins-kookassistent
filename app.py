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

# --- VEILIGHEIDSCHECK API KEY ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except FileNotFoundError:
    st.error("🚨 Kan de Gemini API-sleutel niet vinden. Zorg dat je een `.streamlit/secrets.toml` bestand hebt met `GEMINI_API_KEY = 'jouw_sleutel'`.")
    st.stop()

def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

# --- STYLING & ANIMATIE (GEOPTIMALISEERD VOOR MOBIEL) ---
st.markdown("""
    <style>
    /* Verberg de zijbalk toggle knop volledig */
    [data-testid="collapsedControl"] { display: none; }
    
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    
    /* Zorg voor een strak 3x2 of 3x3 grid op mobiel */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 2% !important;
        }
        /* Kolommen in het dashboard forceren naar 3 naast elkaar */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 31% !important; 
            flex: 1 1 31% !important;
        }
        /* Container padding kleiner maken op mobiel */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 8px !important;
        }
        /* Tekst in tegels verkleinen voor mobiel */
        .card-title { font-size: 1rem !important; margin-bottom: 2px !important; }
        .card-metric { font-size: 1.4rem !important; margin: 5px 0 !important; }
        .stButton button { padding: 4px !important; font-size: 0.75rem !important; min-height: 35px; }
        .card-desc { font-size: 0.7rem !important; line-height: 1.2; }
    }

    /* Animatie Boris */
    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1) rotate(0deg); }
        20% { transform: translateY(-3px) scale(1.02) rotate(-1deg); }
        40% { transform: translateY(2px) scale(0.98) rotate(1deg); }
        60% { transform: translateY(-2px) scale(1.01) rotate(-1deg); }
        80% { transform: translateY(1px) scale(0.99) rotate(1deg); }
        100% { transform: translateY(0px) scale(1) rotate(0deg); }
    }
    .Boris-img-mini {
        width: 100%; max-width: 80px; aspect-ratio: 1/1; border-radius: 50%; object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 0 auto; display: block;
    }
    .Boris-img-talking { animation: avatar-talking 0.3s infinite ease-in-out; }
    
    /* Desktop Tekst Styling */
    .card-title { color: #1565c0; margin-top: 0; font-size: 1.2rem; text-align: center; }
    .card-metric { font-size: 2rem; font-weight: bold; color: #e65100; line-height: 1; margin: 10px 0; text-align: center; }
    .card-desc { text-align: center; color: #555; }
    </style>
""", unsafe_allow_html=True)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
            
    standaard_data = {
        "agenda": [
            {"datum": "2026-04-22", "beschrijving": "💍 Trouwdag Chiel & Angelica"},
            {"datum": "2026-06-11", "beschrijving": "🎂 Verjaardag Duen (1 jr)"},
            {"datum": "2026-10-24", "beschrijving": "🎂 Verjaardag Tygo (3 jr)"}
        ],
        "boodschappen": []
    }
    sla_data_op(standaard_data)
    return standaard_data

def sla_data_op(data):
    with open(DATA_BESTAND, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "gezin_data" not in st.session_state: st.session_state["gezin_data"] = laad_data()
if "huidige_pagina" not in st.session_state: st.session_state["huidige_pagina"] = "Home"

vandaag = datetime.date.today()
if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

def ga_naar(pagina):
    st.session_state["huidige_pagina"] = pagina

def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append({"datum": datum, "beschrijving": beschrijving})
    sla_data_op(st.session_state["gezin_data"])

def voeg_boodschap_toe(item):
    if "boodschappen" not in st.session_state["gezin_data"]:
        st.session_state["gezin_data"]["boodschappen"] = []
    if item not in st.session_state["gezin_data"]["boodschappen"]:
        st.session_state["gezin_data"]["boodschappen"].append(item)
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
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #ffe0b2; border: 1px solid #ffb74d; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: bold; color: #e65100; width: 100%; padding: 4px;">
            {knop_tekst}
        </button>
    </div>
    """

# ==========================================
# HOOFDSCHERM (COMPACT DASHBOARD)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    st.markdown(f"### 🏡 Zwijnenberg Dashboard <span style='font-size: 14px; color: #666;'>| {vandaag.strftime('%d-%m-%Y')}</span>", unsafe_allow_html=True)
    
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a["datum"] >= vandaag_str])

    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg"

    if "huidige_begroeting" not in st.session_state:
        st.session_state["huidige_begroeting"] = random.choice(["Oink! Klaar voor een nieuwe dag?", "Welkom thuis!", "Hoe kan ik helpen, oink?"])

    # Eén blok van 6 kolommen. Door onze CSS wikkelt dit perfect af op mobiel naar een 3x2 grid!
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        with st.container(border=True):
            st.markdown(f"""
                <div style="text-align: center;">
                    <img src="{IMAGE_SRC}" id="Boris-tegel-img" class="Boris-img-mini" alt="Boris">
                </div>
            """, unsafe_allow_html=True)
            st.components.v1.html(genereer_tts_script(st.session_state['huidige_begroeting'], "🔊 Hallo", "Boris-tegel-img"), height=35)
            if st.button("💬 Chat", key="btn_chat"):
                ga_naar("Chat")
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🛒 Boodschap</h3>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-metric">{aantal_boodschappen}</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">items open</p>', unsafe_allow_html=True)
            if st.button("Bekijk", key="btn_boodschappen"):
                ga_naar("Boodschappenlijst")
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">📅 Agenda</h3>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-metric">{aantal_afspraken_komend}</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">aankomend</p>', unsafe_allow_html=True)
            if st.button("Bekijk", key="btn_agenda"):
                ga_naar("Agenda")
                st.rerun()

    with c4:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🍳 Recepten</h3>', unsafe_allow_html=True)
            st.markdown('<p class="card-metric">🥗</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">Geen verspilling</p>', unsafe_allow_html=True)
            if st.button("Wat eten we?", key="btn_recepten"):
                ga_naar("Recepten")
                st.rerun()

    with c5:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🧾 Bonnen</h3>', unsafe_allow_html=True)
            st.markdown('<p class="card-metric">📸</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">Scan je bon</p>', unsafe_allow_html=True)
            if st.button("Scan", key="btn_bonnen"):
                ga_naar("Kassabon Scanner")
                st.rerun()

    with c6:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🧸 Kids</h3>', unsafe_allow_html=True)
            st.markdown('<p class="card-metric">🐷</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">Verhaaltje</p>', unsafe_allow_html=True)
            if st.button("Lees voor", key="btn_kids"):
                with st.spinner("Boris verzint iets..."):
                    prompt = f"{GEZIN_CONTEXT} Vertel een heel kort, grappig verhaaltje (max 4 zinnen). Richt je tot peuter Tygo en baby Duen."
                    response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                    st.session_state['laatste_verhaaltje'] = response.text
                    ga_naar("Kids")
                    st.rerun()

# ==========================================
# SUBPAGINA: AGENDA (NATIVE HTML KALENDER)
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("📅 Gezinsagenda")
    
    # Formulier bovenaan en plat, niet in een blok, zodat het niet verspringt
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
            else:
                st.session_state["kalender_maand"] -= 1
            st.rerun()
    with col_next:
        if st.button("Volgende ➡️"):
            if st.session_state["kalender_maand"] == 12:
                st.session_state["kalender_maand"] = 1
                st.session_state["kalender_jaar"] += 1
            else:
                st.session_state["kalender_maand"] += 1
            st.rerun()

    jaar = st.session_state["kalender_jaar"]
    maand = st.session_state["kalender_maand"]
    with col_title:
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{calendar.month_name[maand]} {jaar}</h3>", unsafe_allow_html=True)

    # Agenda data formatteren
    agenda_dict = {}
    for item in st.session_state["gezin_data"].get("agenda", []):
        d_str = str(item.get("datum", ""))
        if d_str not in agenda_dict: agenda_dict[d_str] = []
        agenda_dict[d_str].append(item.get("beschrijving", ""))

    # --- PURE HTML KALENDER (Werkt 100% op elk scherm) ---
    cal = calendar.monthcalendar(jaar, maand)
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    
    html_cal = """
    <style>
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; padding-bottom: 20px; }
    .cal-header { text-align: center; font-weight: bold; font-size: 0.85rem; padding: 5px 0; color: #555; }
    .cal-day { background-color: #f0f2f6; border: 1px solid #ddd; border-radius: 6px; padding: 5px; text-align: center; min-height: 45px; display: flex; flex-direction: column; justify-content: start; align-items: center;}
    .cal-day span.date { font-weight: bold; font-size: 0.9rem; }
    .cal-day.vandaag { border: 2px solid #e65100; background-color: #fff3e0; }
    .cal-day.afspraak { background-color: #e3f2fd; border-color: #90caf9; }
    .cal-leeg { background-color: transparent; }
    .cal-badge { font-size: 0.7rem; color: #1565c0; font-weight: bold; margin-top: 2px; }
    </style>
    <div class="cal-wrapper">
    """
    for dag in ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]:
        html_cal += f"<div class='cal-header'>{dag}</div>"
        
    for week in cal:
        for dag in week:
            if dag == 0:
                html_cal += "<div class='cal-leeg'></div>"
            else:
                datum_str = f"{jaar}-{maand:02d}-{dag:02d}"
                cls = "cal-day"
                if datum_str == vandaag_str: cls += " vandaag"
                if datum_str in agenda_dict: cls += " afspraak"
                
                badge = f"<div class='cal-badge'>📌 {len(agenda_dict[datum_str])}</div>" if datum_str in agenda_dict else ""
                html_cal += f"<div class='{cls}'><span class='date'>{dag}</span>{badge}</div>"
                
    html_cal += "</div>"
    st.markdown(html_cal, unsafe_allow_html=True)
    
    # Lijst weergave voor de komende afspraken
    st.markdown("### Aankomende planning:")
    gesorteerd = sorted(st.session_state["gezin_data"].get("agenda", []), key=lambda x: str(x.get("datum", "")))
    for item in gesorteerd:
        if item.get("datum", "") >= f"{jaar}-{maand:02d}-01":
            st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")

# ==========================================
# OVERIGE SUBPAGINA'S (Boodschappen, Chat, Recepten etc.)
# ==========================================
elif st.session_state["huidige_pagina"] == "Boodschappenlijst":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🛒 Boodschappenlijst")
    
    with st.form("boodschap_form", clear_on_submit=True):
        nieuw_item = st.text_input("Wat moet er gehaald worden?")
        if st.form_submit_button("Toevoegen") and nieuw_item:
            voeg_boodschap_toe(nieuw_item)
            st.success(f"'{nieuw_item}' staat erop!")
            st.rerun()

    boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen_lijst:
        st.markdown("### Jouw lijst:")
        indices_om_te_verwijderen = []
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(item, key=f"boodschap_{idx}"):
                indices_om_te_verwijderen.append(idx)
        
        if indices_om_te_verwijderen and st.button("Verwijder geselecteerde items", type="primary"):
            verwijder_boodschappen_op_index(indices_om_te_verwijderen)
            st.rerun()
    else:
        st.info("De lijst is helemaal leeg. Knap gedaan!")

elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("💬 Chat met Boris")
    
    if "chat_messages" not in st.session_state: st.session_state["chat_messages"] = []
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"):
            st.write(msg["content"])

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
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🍳 Slimme Recepten")
    
    uploaded_file = st.file_uploader("Upload foto van je voorraad", type=["jpg", "png"])
    if st.button("Genereer Recepten", type="primary") and uploaded_file:
        with st.spinner("Boris snuffelt..."):
            prompt = f"{GEZIN_CONTEXT}\nKijk naar de foto. Verzin 2 recepten die bederf tegengaan, geschikt voor kinderen (3 en 1). Eindig met JSON: {{\"boodschappen\": [\"item\"]}}."
            res = client.models.generate_content(model='gemini-3.5-flash', contents=[prompt, Image.open(uploaded_file)])
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
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🧾 Scanner")
    bon = st.file_uploader("Upload je bon", type=["jpg", "png"])
    if st.button("Scan", type="primary") and bon:
        with st.spinner("Scannen..."):
            res = client.models.generate_content(model='gemini-3.5-flash', contents=[f"{GEZIN_CONTEXT} Vat deze bon samen en markeer het totaalbedrag.", Image.open(bon)])
            st.write(res.text)

elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🧸 Verhaaltje")
    if 'laatste_verhaaltje' in st.session_state:
        st.success(st.session_state['laatste_verhaaltje'])
        st.components.v1.html(genereer_tts_script(st.session_state['laatste_verhaaltje'], "🔊 Lees voor"), height=55)
