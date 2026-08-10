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
    initial_sidebar_state="collapsed" # Verbergt de zijbalk standaard
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
    /* Verberg de zijbalk toggle knop volledig voor een app-gevoel */
    [data-testid="collapsedControl"] { display: none; }
    
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    
    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1) rotate(0deg); }
        20% { transform: translateY(-3px) scale(1.02) rotate(-1deg); }
        40% { transform: translateY(2px) scale(0.98) rotate(1deg); }
        60% { transform: translateY(-2px) scale(1.01) rotate(-1deg); }
        80% { transform: translateY(1px) scale(0.99) rotate(1deg); }
        100% { transform: translateY(0px) scale(1) rotate(0deg); }
    }
    .Boris-img-mini {
        width: 100px; height: 100px; border-radius: 50%; object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 0 auto; display: block;
    }
    .Boris-img-talking {
        animation: avatar-talking 0.3s infinite ease-in-out;
    }
    .card-title {
        color: #1565c0; margin-top: 0; font-size: 1.2rem;
    }
    .card-metric {
        font-size: 2rem; font-weight: bold; color: #e65100; line-height: 1; margin: 10px 0;
    }
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

if "gezin_data" not in st.session_state:
    st.session_state["gezin_data"] = laad_data()

vandaag = datetime.date.today()

if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

# --- NAVIGATIE STATE ---
if "huidige_pagina" not in st.session_state:
    st.session_state["huidige_pagina"] = "Home"

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
    "Jouw doelen: het gezin helpen met dagelijkse planning, proactief meedenken over maaltijden om "
    "voedselverspilling te voorkomen, en de kinderen af en toe vermaken. Je spreekt vrolijk, kort, "
    "behulpzaam en sluit af en toe af met een slimme 'Oink!'."
)

# --- HELPER FUNCTIE VOOR TEKST NAAR SPRAAK ---
def genereer_tts_script(tekst, knop_tekst="🎙️ Spreek", img_id="Boris-main-img"):
    schone_tekst = tekst.replace("'", "").replace('"', '').replace('\n', ' ')
    return f"""
    <script>
    function spreekTekst(tekst) {{
        let img = window.parent.document.getElementById('{img_id}');
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
        <button onclick="spreekTekst('{schone_tekst}')" style="background-color: #ffe0b2; border: 1px solid #ffb74d; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 13px; font-weight: bold; color: #e65100; width: 100%;">
            {knop_tekst}
        </button>
    </div>
    """

# ==========================================
# HOOFDSCHERM (DASHBOARD MET TEGELS)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    st.title("🏡 Zwijnenberg Dashboard")
    st.markdown(f"**Luttenberg | {vandaag.strftime('%d-%m-%Y')}**")
    
    # Bereken handige metrics voor op de tegels
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    afspraken_vandaag = [item for item in st.session_state["gezin_data"]["agenda"] if item["datum"] == vandaag_str]
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a["datum"] >= vandaag_str])

    base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
    IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg"

    begroetingen = [
        "Oink! Klaar voor een nieuwe dag?",
        "Welkom thuis familie Zwijnenberg!",
        "Hoe kan ik helpen, oink?"
    ]
    if "huidige_begroeting" not in st.session_state:
        st.session_state["huidige_begroeting"] = random.choice(begroetingen)

    # --- TEGEL GRID (3x2) ---
    col1, col2, col3 = st.columns(3)
    
    # Tegel 1: BORIS (Profiel & Snelle acties)
    with col1:
        with st.container(border=True):
            st.markdown(f"""
                <div style="text-align: center;">
                    <img src="{IMAGE_SRC}" id="Boris-tegel-img" class="Boris-img-mini" alt="Boris">
                    <p style="margin: 10px 0 5px 0; font-weight: bold; color: #e65100;">"{st.session_state['huidige_begroeting']}"</p>
                </div>
            """, unsafe_allow_html=True)
            st.components.v1.html(genereer_tts_script(st.session_state['huidige_begroeting'], "🔊 Zeg hallo", "Boris-tegel-img"), height=45)
            if st.button("💬 Chat met Boris"):
                ga_naar("Chat")
                st.rerun()

    # Tegel 2: BOODSCHAPPENLIJST
    with col2:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🛒 Boodschappen</h3>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-metric">{aantal_boodschappen}</p><p style="margin-top:-10px;">items op de lijst</p>', unsafe_allow_html=True)
            st.write("") # Spacer
            if st.button("Beheer Lijst", key="btn_boodschappen"):
                ga_naar("Boodschappenlijst")
                st.rerun()

    # Tegel 3: GEZINSAGENDA
    with col3:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">📅 Agenda</h3>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-metric">{aantal_afspraken_komend}</p><p style="margin-top:-10px;">geplande afspraken</p>', unsafe_allow_html=True)
            if afspraken_vandaag:
                st.caption(f"Vandaag: {afspraken_vandaag[0]['beschrijving'][:20]}...")
            else:
                st.caption("Vandaag: Geen afspraken")
            
            if st.button("Bekijk Agenda", key="btn_agenda"):
                ga_naar("Agenda")
                st.rerun()

    # Rij 2
    col4, col5, col6 = st.columns(3)

    # Tegel 4: SLIMME RECEPTEN
    with col4:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🍳 Recepten</h3>', unsafe_allow_html=True)
            st.write("Scan je koelkast en ga voedselverspilling tegen.")
            st.write("")
            if st.button("Wat eten we?", key="btn_recepten"):
                ga_naar("Recepten")
                st.rerun()

    # Tegel 5: KASSABON SCANNER
    with col5:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🧾 Kassabonnen</h3>', unsafe_allow_html=True)
            st.write("Scan bonnen voor een makkelijk financieel overzicht.")
            st.write("")
            if st.button("Scan een bon", key="btn_bonnen"):
                ga_naar("Kassabon Scanner")
                st.rerun()

    # Tegel 6: KIDS ENTERTAINMENT
    with col6:
        with st.container(border=True):
            st.markdown('<h3 class="card-title">🧸 Kids</h3>', unsafe_allow_html=True)
            st.write("Laat Boris een verhaaltje vertellen aan Tygo & Duen.")
            st.write("")
            if st.button("Verhaaltje voorlezen", key="btn_kids"):
                with st.spinner("Verhaaltje verzinnen..."):
                    prompt = f"{GEZIN_CONTEXT} Vertel een heel kort, grappig verhaaltje (max 4 zinnen) over wat jij (Boris) vandaag hebt uitgespookt. Richt je speciaal tot peuter Tygo en baby Duen."
                    response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                    st.session_state['laatste_verhaaltje'] = response.text
                    ga_naar("Kids")
                    st.rerun()


# ==========================================
# SUBPAGINA: CHAT MET BORIS
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("💬 Chat met Boris")
    
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    chat_container = st.container(height=400)
    for msg in st.session_state["chat_messages"]:
        with chat_container.chat_message(msg["role"], avatar="🐗" if msg["role"] == "assistant" else "👤"):
            st.write(msg["content"])

    audio_value = st.audio_input("Spraakbericht (Werkt op mobiel)")
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
                Geef ALTIJD een JSON-reactie in exact dit formaat (geen markdown eromheen):
                {
                    "actie": "boodschap_toevoegen" | "agenda_toevoegen" | "geen",
                    "boodschap": "naam van item" (of ""),
                    "agenda_datum": "YYYY-MM-DD" (of ""),
                    "agenda_beschrijving": "omschrijving" (of ""),
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
                        actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' is ingepland!)*"

                    eind_antwoord = data.get("antwoord", "Oink! Geregeld!") + actie_melding
                except Exception as e:
                    eind_antwoord = "Oink! Ik begreep het even niet goed. Probeer het nog eens!"

                st.write(eind_antwoord)
                st.components.v1.html(genereer_tts_script(eind_antwoord, "🔊 Spreek uit"), height=45)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.rerun()


# ==========================================
# SUBPAGINA: BOODSCHAPPENLIJST
# ==========================================
elif st.session_state["huidige_pagina"] == "Boodschappenlijst":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🛒 Boodschappenlijst")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("boodschap_form", clear_on_submit=True):
            nieuw_item = st.text_input("Wat moet er nog gehaald worden?")
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
            st.toast("Lijst netjes opgeruimd!", icon="🧹")
            st.rerun()
    else:
        st.info("De lijst is helemaal leeg. Knap gedaan!")


# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("📅 Gezinsagenda")
    
    with st.expander("➕ Nieuwe afspraak inplannen", expanded=False):
        with st.form("agenda_form", clear_on_submit=True):
            nieuwe_datum = st.date_input("Kies datum", vandaag)
            nieuwe_beschrijving = st.text_input("Omschrijving van de afspraak")
            if st.form_submit_button("Opslaan in agenda") and nieuwe_beschrijving:
                voeg_agenda_toe(nieuwe_datum.strftime("%Y-%m-%d"), nieuwe_beschrijving)
                st.success("Staat genoteerd! Oink!")
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
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold; font-size: 14px;'>{dag_naam}</p>", unsafe_allow_html=True)

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
                if is_vandaag: border_style = "2px solid #e65100"
                if heeft_afspraak: bg_color = "#e3f2fd"

                inhoud_tekst = f"<b style='font-size: 14px;'>{dag}</b>"
                if heeft_afspraak:
                    inhoud_tekst += "<br><span style='font-size: 11px; color: #1565c0;'>📌 " + str(len(agenda_dict[datum_sleutel])) + "</span>"

                cols[i].markdown(
                    f"""<div style="background-color: {bg_color}; border: {border_style}; border-radius: 6px; padding: 6px; text-align: center; min-height: 50px; margin-bottom: 5px;">
                        {inhoud_tekst}
                    </div>""", 
                    unsafe_allow_html=True
                )
                
    st.markdown("### Komende activiteiten:")
    gesorteerd_agenda = sorted(agenda_data, key=lambda x: str(x.get("datum", "")))
    for item in gesorteerd_agenda:
        if item.get("datum", "") >= f"{jaar}-{maand:02d}-01":
            st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")


# ==========================================
# SUBPAGINA: RECEPTEN
# ==========================================
elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🍳 Slimme Recepten")
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
            tekst = tekst.replace(json_part, "").replace("```json", "").replace("```", "")
        except:
            pass

        st.markdown(tekst)

        if boodschappen_gevonden:
            st.info(f"🛒 **Ontbrekende ingrediënten:** {', '.join(boodschappen_gevonden)}")
            if st.button("Voeg deze direct toe aan de boodschappenlijst!"):
                for item in boodschappen_gevonden:
                    voeg_boodschap_toe(item)
                st.toast("Succesvol toegevoegd!", icon="✅")
                del st.session_state["laatste_recept"]
                st.rerun()


# ==========================================
# SUBPAGINA: KASSABON SCANNER
# ==========================================
elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🧾 Kassabon Scanner")
    st.write("Scan een bon om het totaalbedrag en de categorieën uit te lezen.")
    
    bon_file = st.file_uploader("Upload foto van de bon", type=["jpg", "jpeg", "png"])
    if st.button("Scan Bon", type="primary") and bon_file:
        with st.spinner("Bon wordt geanalyseerd..."):
            prompt = f"{GEZIN_CONTEXT} Lees deze bon. Geef een overzichtelijke samenvatting van de gekochte items, verdeel ze in logische categorieën en benadruk het totaalbedrag in het vet."
            response = client.models.generate_content(
                model='gemini-3.5-flash', 
                contents=[prompt, Image.open(bon_file)]
            )
            st.write(response.text)


# ==========================================
# SUBPAGINA: KIDS VERHAALTJE
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug naar Home"): ga_naar("Home"); st.rerun()
    st.title("🧸 Tijd voor een verhaaltje!")
    
    if 'laatste_verhaaltje' in st.session_state:
        base64_Boris = get_image_base64('Boris.png') or get_image_base64('Boris.jpg')
        IMAGE_SRC = f"data:image/png;base64,{base64_Boris}" if base64_Boris else "[https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Juliana_pig_in_straw.jpg/500px-Juliana_pig_in_straw.jpg)"
        
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{IMAGE_SRC}" id="Boris-kids-img" class="Boris-img-mini" alt="Boris" style="width: 150px; height: 150px;">
            </div>
        """, unsafe_allow_html=True)
        
        st.success(st.session_state['laatste_verhaaltje'])
        st.components.v1.html(genereer_tts_script(st.session_state['laatste_verhaaltje'], "🔊 Lees het verhaaltje voor!", "Boris-kids-img"), height=55)
