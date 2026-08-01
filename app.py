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
# Dit stelt ook de favicon (het app-icoontje op je telefoon) in!
st.set_page_config(
    page_title="Zwijnenberg Home Assist", 
    page_icon="Boris.png", 
    layout="wide"
)

# --- HELPER FUNCTIE VOOR AFBEELDING ---
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

# --- MOBIELE VORMGEVING & MIMIC ANIMATIES ---
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumns:not(.calendar-grid) {
            flex-direction: column !important;
        }
        div[data-testid="column"]:not(.calendar-col) {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 10px;
        }
    }
    input, select, textarea { font-size: 16px !important; }
    .stButton button { width: 100%; }
    
    /* PRATENDE ANIMATIE BORIS */
    @keyframes boris-talking {
        0% { transform: translateY(0px) scale(1); }
        25% { transform: translateY(-4px) scale(1.02) rotate(-1deg); }
        50% { transform: translateY(3px) scale(0.99) rotate(1deg); }
        75% { transform: translateY(-2px) scale(1.01) rotate(-0.5deg); }
        100% { transform: translateY(0px) scale(1); }
    }
    .boris-avatar-container {
        text-align: center; background-color: #fff3e0; padding: 15px;
        border-radius: 15px; margin-bottom: 20px; border: 2px solid #ffe0b2;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .boris-img {
        width: 100%; max-width: 480px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.3s ease;
    }
    .boris-img-talking {
        animation: boris-talking 0.35s infinite ease-in-out;
    }
    .dashboard-box {
        background-color: #e3f2fd; padding: 15px; border-radius: 10px;
        border-left: 5px solid #2196f3; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISEER CLIENTS ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- LOKAAL JSON BEHEER ---
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

if "gezin_data" not in st.session_state:
    st.session_state["gezin_data"] = laad_data()

vandaag = datetime.date.today()

if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append({"datum": datum, "beschrijving": beschrijving})
    sla_data_op(st.session_state["gezin_data"])

def voeg_boodschap_toe(item):
    if "boodschappen" not in st.session_state["gezin_data"]:
        st.session_state["gezin_data"]["boodschappen"] = []
    st.session_state["gezin_data"]["boodschappen"].append(item)
    sla_data_op(st.session_state["gezin_data"])

def verwijder_boodschappen_op_index(indices_om_te_verwijderen):
    huidige = st.session_state["gezin_data"].get("boodschappen", [])
    nieuwe_lijst = [item for i, item in enumerate(huidige) if i not in indices_om_te_verwijderen]
    st.session_state["gezin_data"]["boodschappen"] = nieuwe_lijst
    sla_data_op(st.session_state["gezin_data"])

GEZIN_CONTEXT = (
    "Je bent Boris, de virtuele huiszwijn-assistent van het gezin Zwijnenberg: "
    "Chiel (geboren 13 juni 1989), Angelica (geboren 15 januari 1989, getrouwd 22-04-2024), "
    "Tygo (geboren 24 oktober 2022) en Duen (geboren 11 juni 2025). "
    "Jullie wonen in Raalte. Je spreekt vrolijk, kort, en als een slim huiszwijn ('Oink!')."
)

# --- NAVIGATIE ---
st.sidebar.title("🍳 Menu")
pagina = st.sidebar.radio(
    "Ga naar:", 
    ["🏠 Home", "🍳 Recepten Generator", "🧾 Kassabon Scanner", "📅 Maandagenda", "🛒 Boodschappenlijstje"]
)

# --- 🏠 HOME ---
if pagina == "🏠 Home":
    
    # 1. AFBEELDING INLADEN (Zoekt lokaal naar png of jpg, anders de reservefoto)
    base64_boris = get_image_base64('Boris.png')
    base64_boris_jpg = get_image_base64('Boris.jpg')
    
    if base64_boris:
        IMAGE_SRC = f"data:image/png;base64,{base64_boris}"
    elif base64_Boris_jpg:
        IMAGE_SRC = f"data:image/jpeg;base64,{base64_Boris_jpg}"
    else:
        # Fallback foto van een varkentje als Boris.png / Boris.jpg ontbreekt
        IMAGE_SRC = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg"

    # 2. 'GOEIEMORGEN' DASHBOARD
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    afspraken_vandaag = [item for item in st.session_state["gezin_data"]["agenda"] if item["datum"] == vandaag_str]
    
    st.markdown(f"""
        <div class="dashboard-box">
            <h4 style="margin-top:0; color: #1565c0;">🌤️ Vandaag in Raalte ({vandaag.strftime('%d-%m-%Y')})</h4>
            <p style="margin-bottom: 5px;"><b>Agenda:</b> {', '.join([a['beschrijving'] for a in afspraken_vandaag]) if afspraken_vandaag else 'Geen afspraken gepland vandaag! Tijd om te spelen!'}</p>
        </div>
    """, unsafe_allow_html=True)

    # 3. BEGROETING EN BORIS VISUALISATIE
    begroetingen = [
        "Hey familie Zwijnenberg! Oink! Waar kan ik jullie vandaag mee helpen?",
        "Oink oink! Welkom thuis Chiel, Angelica, Tygo en Duen!",
        "Goedendag Zwijnenbergjes! Boris staat voor jullie klaar."
    ]
    if "huidige_begroeting" not in st.session_state:
        st.session_state["huidige_begroeting"] = random.choice(begroetingen)
    
    gekozen_tekst = st.session_state["huidige_begroeting"]
    schone_begroeting = gekozen_tekst.replace("'", "").replace('"', '').replace('\n', ' ')

    st.markdown(f"""
        <div class="boris-avatar-container">
            <img src="{IMAGE_SRC}" id="boris-main-img" class="boris-img boris-img-talking" alt="Boris">
            <h3 style="margin: 15px 0 0 0; color: #e65100;">"{gekozen_tekst}"</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Auto-play TTS Script (Voor de begroeting)
    auto_greet_script = f"""
    <script>
    function spreekBegroeting() {{
        let img = window.parent.document.getElementById('boris-main-img');
        if(img) img.classList.add('boris-img-talking');
        
        window.speechSynthesis.cancel();
        let speech = new SpeechSynthesisUtterance('{schone_begroeting}');
        speech.lang = 'nl-NL';
        speech.pitch = 1.2;
        speech.rate = 0.95;
        
        speech.onend = function() {{
            if(img) img.classList.remove('boris-img-talking');
        }};
        
        window.speechSynthesis.speak(speech);
    }}
    setTimeout(spreekBegroeting, 500);
    </script>
    
    <div style="text-align: center; margin-bottom: 20px;">
        <button onclick="spreekBegroeting()" style="background-color: #ffe0b2; border: 1px solid #ffb74d; border-radius: 20px; padding: 8px 18px; cursor: pointer; font-size: 14px; font-weight: bold; color: #e65100;">
            🔊 Tik hier als Boris nog niet sprak
        </button>
    </div>
    """
    st.components.v1.html(auto_greet_script, height=50)
    
    # 4. DE KIDS KNOP (Voor Tygo & Duen)
    if st.button("🐷 Vertel een verhaaltje voor Tygo & Duen!", use_container_width=True):
        with st.spinner("Boris verzint een verhaaltje..."):
            prompt = f"{GEZIN_CONTEXT} Vertel een heel kort, grappig en lief verhaaltje (max 4 zinnen) over wat jij (Boris) vandaag hebt uitgespookt. Richt je speciaal tot Tygo (3) en Duen (1)."
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            st.success(response.text)
            
    st.markdown("---")
    
    # 5. SPRAAK & CHAT MET BORIS
    st.subheader("💬 Vraag het aan Boris")
    
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"):
            st.write(msg["content"])
            
            # Spraakknop voor eerdere berichten
            if msg["role"] == "assistant":
                schone_tekst = msg["content"].replace("'", "").replace('"', '').replace('\n', ' ')
                tts_script = f"""
                <button onclick="
                    let img = window.parent.document.getElementById('boris-main-img');
                    if(img) img.classList.add('boris-img-talking');
                    
                    window.speechSynthesis.cancel();
                    let speech = new SpeechSynthesisUtterance('{schone_tekst}');
                    speech.lang = 'nl-NL';
                    speech.pitch = 1.2;
                    
                    speech.onend = function() {{
                        if(img) img.classList.remove('boris-img-talking');
                    }};
                    
                    window.speechSynthesis.speak(speech);
                " style="background-color: #ffe0b2; border: 1px solid #ffb74d; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 13px; font-weight: bold; color: #e65100; margin-top: 5px;">
                    🔊 Laat Boris praten & bewegen!
                </button>
                """
                st.components.v1.html(tts_script, height=45)

    # Spraakinvoer (vereist moderne Streamlit versie)
    audio_value = st.audio_input("🎙️ Spreek tegen Boris (werkt op mobiel!)")
    user_prompt = st.chat_input("Of typ je bericht hier...")

    if audio_value or user_prompt:
        if audio_value:
            audio_part = types.Part.from_bytes(data=audio_value.read(), mime_type='audio/wav')
            input_content = [GEZIN_CONTEXT, "Luister naar de audio en reageer alsof het getypt was.", audio_part]
            display_text = "*(Spraakbericht verzonden)* 🎙️"
        else:
            input_content = f"{GEZIN_CONTEXT} Gebruiker zegt: '{user_prompt}'"
            display_text = user_prompt
            
        st.session_state["chat_messages"].append({"role": "user", "content": display_text})
        with st.chat_message("user", avatar="👤"):
            st.write(display_text)
            
        with st.chat_message("assistant", avatar="🐗"):
            with st.spinner("Boris denkt na... 🐗💭"):
                instructie = """
                Geef een JSON-reactie in exact dit formaat:
                {
                    "actie": "boodschap_toevoegen" of "agenda_toevoegen" of "geen",
                    "boodschap": "naam van item of leeg",
                    "agenda_datum": "YYYY-MM-DD",
                    "agenda_beschrijving": "omschrijving of leeg",
                    "antwoord": "Korte vrolijke reactie"
                }
                """
                
                try:
                    if audio_value:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=[*input_content, instructie],
                            config={'response_mime_type': 'application/json'}
                        )
                    else:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=input_content + "\n" + instructie,
                            config={'response_mime_type': 'application/json'}
                        )
                        
                    data = json.loads(response.text)
                    
                    actie_melding = ""
                    if data.get("actie") == "boodschap_toevoegen" and data.get("boodschap"):
                        voeg_boodschap_toe(data["boodschap"])
                        actie_melding = f"\n\n*(✅ '{data['boodschap']}' toegevoegd!)*"
                    
                    elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"):
                        datum_str = data.get("agenda_datum") or vandaag.strftime("%Y-%m-%d")
                        voeg_agenda_toe(datum_str, data["agenda_beschrijving"])
                        actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' gepland!)*"

                    eind_antwoord = data.get("antwoord", "Oink! Geregeld!") + actie_melding
                except Exception as e:
                    eind_antwoord = "Oink! Ik begreep het even niet goed."

                st.write(eind_antwoord)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.rerun()

# --- 🍳 RECEPTEN GENERATOR ---
elif pagina == "🍳 Recepten Generator":
    st.title("🍳 Recepten Generator")
    uploaded_file = st.file_uploader("Upload foto van de koelkast", type=["jpg", "jpeg", "png"])
    
    if st.button("Genereer Maaltijdplan", type="primary"):
        if uploaded_file:
            with st.spinner("Boris snuffelt door de koelkast..."):
                contents = [
                    GEZIN_CONTEXT, Image.open(uploaded_file), 
                    "Geef 2 receptopties. Eindig je bericht met een JSON-lijst van ingrediënten die waarschijnlijk nog gekocht moeten worden in deze structuur: {'boodschappen': ['item1', 'item2']}"
                ]
                response = client.models.generate_content(model='gemini-1.5-flash', contents=contents)
                
                # Sla het antwoord op in session state
                st.session_state["laatste_recept"] = response.text
        else:
            st.warning("Upload eerst een afbeelding!")

    # SLIMME KOPPELING NAAR BOODSCHAPPENLIJST
    if "laatste_recept" in st.session_state:
        st.markdown("### Jouw Recepten:")
        
        tekst = st.session_state["laatste_recept"]
        boodschappen_gevonden = []
        try:
            if "{" in tekst and "}" in tekst:
                json_str = "{" + tekst.split("{")[-1].split("}")[0] + "}"
                data = json.loads(json_str.replace("'", '"'))
                if "boodschappen" in data:
                    boodschappen_gevonden = data["boodschappen"]
                tekst = tekst.replace(json_str, "")
        except:
            pass

        st.write(tekst)

        if boodschappen_gevonden:
            st.success(f"Gevonden ontbrekende items: {', '.join(boodschappen_gevonden)}")
            if st.button("🛒 Zet deze ingrediënten op de boodschappenlijst!"):
                for item in boodschappen_gevonden:
                    voeg_boodschap_toe(item)
                st.toast("Toegevoegd aan de lijst!", icon="✅")
                del st.session_state["laatste_recept"]
                st.rerun()

# --- 🧾 KASSABON SCANNER ---
elif pagina == "🧾 Kassabon Scanner":
    st.title("🧾 Kassabon Scanner")
    bon_file = st.file_uploader("Upload foto van de bon", type=["jpg", "jpeg", "png"])
    if st.button("Scan Bon", type="primary") and bon_file:
        with st.spinner("Bon wordt gelezen..."):
            response = client.models.generate_content(
                model='gemini-1.5-flash', 
                contents=[GEZIN_CONTEXT, Image.open(bon_file), "Lees de bon en geef het totaalbedrag."]
            )
            st.write(response.text)

# --- 📅 MAANDAGENDA ---
elif pagina == "📅 Maandagenda":
    st.title("📅 Maandagenda & Planning")
    
    with st.expander("➕ Voeg een afspraak toe", expanded=False):
        with st.form("agenda_form", clear_on_submit=True):
            nieuwe_datum = st.date_input("Datum", vandaag)
            nieuwe_beschrijving = st.text_input("Omschrijving")
            if st.form_submit_button("Toevoegen aan agenda") and nieuwe_beschrijving:
                voeg_agenda_toe(nieuwe_datum.strftime("%Y-%m-%d"), nieuwe_beschrijving)
                st.success("Toegevoegd!")
                st.rerun()

    st.markdown("---")

    col_prev, col_title, col_next = st.columns([1, 4, 1])
    
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
    maand_naam = calendar.month_name[maand]

    with col_title:
        st.subheader(f"📆 {maand_naam} {jaar}")

    agenda_data = st.session_state["gezin_data"].get("agenda", [])
    agenda_dict = {}
    for item in agenda_data:
        d_str = str(item.get("datum", ""))
        if d_str not in agenda_dict:
            agenda_dict[d_str] = []
        agenda_dict[d_str].append(item.get("beschrijving", ""))

    cal = calendar.monthcalendar(jaar, maand)
    weekdagen = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]

    cols = st.columns(7)
    for i, dag_naam in enumerate(weekdagen):
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold; font-size: 12px;'>{dag_naam}</p>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, dag in enumerate(week):
            if dag == 0:
                cols[i].markdown("<div style='padding: 5px; text-align: center; color: #ccc;'>-</div>", unsafe_allow_html=True)
            else:
                huidige_datum_obj = datetime.date(jaar, maand, dag)
                datum_sleutel = huidige_datum_obj.strftime("%Y-%m-%d")
                
                is_vandaag = (huidige_datum_obj == vandaag)
                heeft_afspraak = datum_sleutel in agenda_dict

                bg_color = "#f0f2f6"
                border_style = "1px solid #ddd"
                if is_vandaag: 
                    border_style = "2px solid #ff4b4b"
                if heeft_afspraak: 
                    bg_color = "#e6f3ff"

                inhoud_tekst = f"<b style='font-size: 12px;'>{dag}</b>"
                if heeft_afspraak:
                    inhoud_tekst += "<br><span style='font-size: 9px; color: #0066cc;'>📌</span>"

                cols[i].markdown(
                    f"""<div style="background-color: {bg_color}; border: {border_style}; border-radius: 4px; padding: 4px; text-align: center; min-height: 35px; margin-bottom: 2px;">
                        {inhoud_tekst}
                    </div>""", 
                    unsafe_allow_html=True
                )
                
    st.markdown("### Alle geplande items:")
    gesorteerd_agenda = sorted(agenda_data, key=lambda x: str(x.get("datum", "")))
    for item in gesorteerd_agenda:
        st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")

# --- 🛒 BOODSCHAPPENLIJSTJE ---
elif pagina == "🛒 Boodschappenlijstje":
    st.title("🛒 Boodschappenlijstje")
    
    with st.form("boodschap_form", clear_on_submit=True):
        nieuw_item = st.text_input("Voeg iets toe:")
        if st.form_submit_button("Toevoegen") and nieuw_item:
            voeg_boodschap_toe(nieuw_item)
            st.success(f"'{nieuw_item}' toegevoegd!")
            st.rerun()

    boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen_lijst:
        st.markdown("### Huidige lijst:")
        indices_om_te_verwijderen = []
        
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(item, key=f"boodschap_{idx}"):
                indices_om_te_verwijderen.append(idx)
        
        if indices_om_te_verwijderen and st.button("Verwijder aangevinkte items"):
            verwijder_boodschappen_op_index(indices_om_te_verwijderen)
            st.success("Lijst bijgewerkt!")
            st.rerun()
    else:
        st.info("De lijst is leeg.")
