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
    layout="wide"
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

# --- STYLING & ANIMATIE ---
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumns:not(.calendar-grid) {
            flex-direction: column !important;
        }
    }
    .stButton button { width: 100%; border-radius: 8px; }
    
    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1) rotate(0deg); }
        20% { transform: translateY(-6px) scale(1.04) rotate(-2deg); }
        40% { transform: translateY(4px) scale(0.97) rotate(2deg); }
        60% { transform: translateY(-5px) scale(1.03) rotate(-1deg); }
        80% { transform: translateY(2px) scale(0.99) rotate(1deg); }
        100% { transform: translateY(0px) scale(1) rotate(0deg); }
    }
    .Boris-avatar-container {
        text-align: center; background-color: #fff3e0; padding: 15px;
        border-radius: 15px; margin-bottom: 20px; border: 2px solid #ffe0b2;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .Boris-img {
        width: 100%; max-width: 480px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.2s ease;
    }
    .Boris-img-talking {
        animation: avatar-talking 0.3s infinite ease-in-out;
    }
    .dashboard-box {
        background-color: #e3f2fd; padding: 15px; border-radius: 10px;
        border-left: 5px solid #2196f3; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

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
    "Jouw doelen: het gezin helpen met dagelijkse planning, proactief meedenken over maaltijden om "
    "voedselverspilling te voorkomen, en de kinderen af en toe vermaken. Je spreekt vrolijk, kort, "
    "behulpzaam en sluit af en toe af met een slimme 'Oink!'."
)

st.sidebar.title("🐷 Boris Menu")
pagina = st.sidebar.radio(
    "Navigatie:", 
    ["🏠 Home & Dashboard", "🍳 Slimme Recepten", "🧾 Kassabon Scanner", "📅 Gezinsagenda", "🛒 Boodschappenlijst"]
)

# --- HELPER FUNCTIE VOOR TEKST NAAR SPRAAK ---
def genereer_tts_script(tekst, knop_tekst="🎙️ Laat Boris spreken"):
    schone_tekst = tekst.replace("'", "").replace('"', '').replace('\n', ' ')
    return f"""
    <script>
    function spreekTekst(tekst) {{
        let img = window.parent.document.getElementById('Boris-main-img');
        window.speechSynthesis.cancel();
        
        let speech = new SpeechSynthesisUtterance(tekst);
        speech.lang = 'nl-NL';
        speech.pitch = 1.1;
        speech.rate = 1.05;
        
        let voices = window.speechSynthesis.getVoices();
        let nlVoices = voices.filter(v => v.lang.includes('nl') || v.lang.includes('NL'));
        let maleVoice = nlVoices.find(v => v.name.toLowerCase().includes('xander') || v.name.toLowerCase().includes('male'));
        
        if (maleVoice) {{ speech.voice = maleVoice; }} 
        else if (nlVoices.length > 0) {{ speech.voice = nlVoices[0]; }}
        
        speech.onstart = function() {{ if(img) img.classList.add('Boris-img-talking'); }};
        speech.onend = function() {{ if(img) img.classList.remove('Boris-img-talking'); }};
        
        window.speechSynthesis.speak(speech);
    }}
    </script>
    <div style="text-align: center; margin-top: 5px;">
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #ffe0b2; border: 1px solid #ffb74d; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 13px; font-weight: bold; color: #e65100;">
            {knop_tekst}
        </button>
    </div>
    """

# --- 🏠 HOME & DASHBOARD ---
if pagina == "🏠 Home & Dashboard":
    
    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg"

    vandaag_str = vandaag.strftime("%Y-%m-%d")
    afspraken_vandaag = [item for item in st.session_state["gezin_data"]["agenda"] if item["datum"] == vandaag_str]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        begroetingen = [
            "Hey familie Zwijnenberg! Oink! Klaar voor een nieuwe dag in Luttenberg?",
            "Oink oink! Welkom thuis Chiel, Angelica, Tygo en Duen! Hoe kan ik helpen?",
            "Goedendag Zwijnenbergjes! Boris heeft de agenda al voor jullie bekeken."
        ]
        if "huidige_begroeting" not in st.session_state:
            st.session_state["huidige_begroeting"] = random.choice(begroetingen)
        
        st.markdown(f"""
            <div class="Boris-avatar-container">
                <img src="{IMAGE_SRC}" id="Boris-main-img" class="Boris-img" alt="Boris">
                <h4 style="margin: 15px 0 0 0; color: #e65100;">"{st.session_state['huidige_begroeting']}"</h4>
            </div>
        """, unsafe_allow_html=True)
        st.components.v1.html(genereer_tts_script(st.session_state['huidige_begroeting'], "Begroet mij!"), height=55)

        if st.button("🐷 Verhaaltje voor Tygo & Duen!", use_container_width=True):
            with st.spinner("Boris verzint een verhaaltje..."):
                prompt = f"{GEZIN_CONTEXT} Vertel een heel kort, grappig en educatief verhaaltje (max 4 zinnen) over wat jij (Boris) vandaag hebt uitgespookt in de tuin in Luttenberg. Richt je speciaal tot peuter Tygo en baby Duen."
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                st.session_state['laatste_verhaaltje'] = response.text
                
        if 'laatste_verhaaltje' in st.session_state:
            st.success(st.session_state['laatste_verhaaltje'])
            st.components.v1.html(genereer_tts_script(st.session_state['laatste_verhaaltje'], "🔊 Lees voor"), height=55)

    with col2:
        st.markdown(f"""
            <div class="dashboard-box">
                <h4 style="margin-top:0; color: #1565c0;">🗓️ Vandaag ({vandaag.strftime('%d-%m-%Y')})</h4>
                <p style="margin-bottom: 5px;"><b>Agenda:</b> {', '.join([a['beschrijving'] for a in afspraken_vandaag]) if afspraken_vandaag else 'Geen afspraken gepland. Tijd voor ontspanning!'}</p>
                <p style="margin-bottom: 0;"><b>Boodschappenlijst:</b> {len(st.session_state['gezin_data']['boodschappen'])} item(s) benodigd.</p>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("💬 Spreek of chat met Boris")
        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

        chat_container = st.container(height=300)
        for msg in st.session_state["chat_messages"]:
            with chat_container.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"):
                st.write(msg["content"])

        audio_value = st.audio_input("Spraakbericht")
        user_prompt = st.chat_input("Of typ je bericht hier...")

        if audio_value or user_prompt:
            if audio_value:
                audio_part = types.Part.from_bytes(data=audio_value.read(), mime_type='audio/wav')
                input_content = [GEZIN_CONTEXT, "Luister naar deze audio van het gezin en reageer.", audio_part]
                display_text = "*(Spraakbericht)* 🎙️"
            else:
                input_content = f"{GEZIN_CONTEXT} De gebruiker zegt: '{user_prompt}'"
                display_text = user_prompt
                
            st.session_state["chat_messages"].append({"role": "user", "content": display_text})
            with chat_container.chat_message("user", avatar="👤"):
                st.write(display_text)
                
            with chat_container.chat_message("assistant", avatar="🐗"):
                with st.spinner("Boris denkt na..."):
                    instructie = """
                    Analyseer het verzoek. Als de gebruiker vraagt om iets te plannen of iets te kopen, extraheer dit.
                    Geef ALTIJD een JSON-reactie in exact dit formaat (geen markdown eromheen):
                    {
                        "actie": "boodschap_toevoegen" | "agenda_toevoegen" | "geen",
                        "boodschap": "naam van item" (indien actie boodschap is, anders ""),
                        "agenda_datum": "YYYY-MM-DD" (indien actie agenda is, anders ""),
                        "agenda_beschrijving": "omschrijving" (indien actie agenda is, anders ""),
                        "antwoord": "Je vrolijke reactie op de gebruiker als Boris."
                    }
                    """
                    try:
                        contents = [*input_content, instructie] if audio_value else input_content + "\n" + instructie
                        response = client.models.generate_content(
                            model='gemini-3.5-flash',
                            contents=contents,
                            config={'response_mime_type': 'application/json'}
                        )
                        
                        data = json.loads(response.text)
                        actie_melding = ""
                        
                        if data.get("actie") == "boodschap_toevoegen" and data.get("boodschap"):
                            voeg_boodschap_toe(data["boodschap"])
                            actie_melding = f"\n\n*(✅ '{data['boodschap']}' staat op het lijstje!)*"
                        
                        elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"):
                            datum_str = data.get("agenda_datum") or vandaag.strftime("%Y-%m-%d")
                            voeg_agenda_toe(datum_str, data["agenda_beschrijving"])
                            actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' is ingepland voor {datum_str}!)*"

                        eind_antwoord = data.get("antwoord", "Oink! Geregeld!") + actie_melding
                    except Exception as e:
                        eind_antwoord = "Oink! Ik begreep het even niet goed. Probeer het nog eens!"

                    st.write(eind_antwoord)
                    st.components.v1.html(genereer_tts_script(eind_antwoord, "🔊"), height=45)
                    st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                    st.rerun()

# --- 🍳 SLIMME RECEPTEN (ANTI-VERSPILLING) ---
elif pagina == "🍳 Slimme Recepten":
    st.title("🍳 Slimme Recepten & Voorraad")
    st.write("Upload een foto van je koelkast of voorraadkast. Boris kijkt wat op moet en bedenkt kindvriendelijke recepten!")
    
    uploaded_file = st.file_uploader("Upload foto (koelkast/pantry)", type=["jpg", "jpeg", "png"])
    
    if st.button("Inventariseer & Genereer Recepten", type="primary"):
        if uploaded_file:
            with st.spinner("Boris snuffelt door de koelkast naar ingrediënten..."):
                prompt = f"""
                {GEZIN_CONTEXT}
                Kijk naar de bijgevoegde foto van de voedselvoorraad.
                1. Identificeer de ingrediënten. Bedenk welke items waarschijnlijk als eerste op moeten om voedselverspilling te voorkomen.
                2. Verzin 2 gezonde, haalbare recepten die gebruik maken van deze ingrediënten. Houd rekening met de leeftijd van de kinderen (3 en 1).
                3. Sluit het bericht af met een JSON block (enkel JSON) van items die nog missen om de recepten te maken. Formaat: {{"boodschappen": ["item 1", "item 2"]}}.
                """
                response = client.models.generate_content(
                    model='gemini-3.5-flash', 
                    contents=[prompt, Image.open(uploaded_file)]
                )
                st.session_state["laatste_recept"] = response.text
        else:
            st.warning("Oink! Vergeet niet eerst een foto te uploaden.")

    if "laatste_recept" in st.session_state:
        st.markdown("---")
        tekst = st.session_state["laatste_recept"]
        boodschappen_gevonden = []
        
        # Simpele JSON extractie uit de tekst
        try:
            if "```json" in tekst:
                json_part = tekst.split("```json")[1].split("```")[0]
            elif "{" in tekst and "}" in tekst:
                json_part = "{" + tekst.split("{")[-1].split("}")[0] + "}"
            else:
                json_part = "{}"
                
            data = json.loads(json_part.strip())
            if "boodschappen" in data:
                boodschappen_gevonden = data["boodschappen"]
            tekst = tekst.replace(json_part, "").replace("```json", "").replace("
