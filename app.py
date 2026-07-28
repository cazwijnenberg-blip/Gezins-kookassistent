import streamlit as st
from google import genai
from PIL import Image
import datetime
import calendar
import json
import os

# --- PAGINA CONFIGURATIE ---
st.set_page_config(page_title="Zwijnenberg home assist", page_icon="🐗", layout="wide")

# --- MOBIELE VORMGEVING & CSS OPTIMALISATIE ---
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumns {
            flex-direction: column !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 15px;
        }
    }
    input, select, textarea {
        font-size: 16px !important;
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISEER CLIENTS ---
# Let op: Vul hier jouw echte Gemini API-sleutel in!
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- LOKAAL JSON BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        with open(DATA_BESTAND, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
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

def laad_agenda_van_sheet():
    data = laad_data()
    return data.get("agenda", [])

def laad_boodschappen_van_sheet():
    data = laad_data()
    return data.get("boodschappen", [])

def voeg_agenda_toe_aan_sheet(datum, beschrijving):
    data = laad_data()
    data["agenda"].append({"datum": datum, "beschrijving": beschrijving})
    sla_data_op(data)

def voeg_boodschap_toe_aan_sheet(item):
    data = laad_data()
    if "boodschappen" not in data:
        data["boodschappen"] = []
    data["boodschappen"].append(item)
    sla_data_op(data)

def verwijder_boodschappen_uit_sheet(te_verwijderen_lijst):
    data = laad_data()
    huidige = data.get("boodschappen", [])
    data["boodschappen"] = [item for item in huidige if item not in te_verwijderen_lijst]
    sla_data_op(data)

# --- ACHTERGROND GEZINS- & ALGEMENE INFO VOOR DE AI ---
GEZIN_CONTEXT = (
    "Je bent Boris, de virtuele huiszwijn-assistent van het gezin Zwijnenberg: "
    "Chiel (geboren 13 juni 1989, 37 jaar) en Angelica (geboren 15 januari 1989, 37 jaar, getrouwd 22-04-2024), "
    "Tygo (geboren 24 oktober 2022, 3 jaar) en Duen (geboren 11 juni 2025, 1 jaar). "
    "Je spreekt altijd een beetje vrolijk, behulpzaam en in karakter als een slim huiszwijn (gebruik af en toe een subtiele knipoog zoals 'Oink!'). "
    "Je bent niet alleen expert op het gebied van het huishouden, recepten en de gezinsplanning, maar je hebt ook "
    "brede algemene kennis. Je kunt dus ook feitelijke vragen beantwoorden over het weer, reistijden, aardrijkskunde, etc."
)

# --- ZIJKANT / NAVIGATIE ---
st.sidebar.title("🍳 Menu")
pagina = st.sidebar.radio(
    "Ga naar:", 
    [
        "🏠 Home",
        "🍳 Recepten Generator", 
        "🧾 Kassabon Scanner", 
        "📅 Maandagenda & Planning", 
        "🛒 Boodschappenlijstje"
    ]
)

# --- PAGINA 0: HOME / LANDINGSPAGINA ---
if pagina == "🏠 Home":
    st.title("🏡 Zwijnenberg Home Hub & Boris")
    st.write("Welkom thuis! Maak kennis met **Boris**, jullie persoonlijke virtuele assistent.")

    st.markdown("""
        <style>
        @keyframes speak {
            0% { transform: scale(1); }
            50% { transform: scale(1.1) translateY(-3px); }
            100% { transform: scale(1); }
        }
        .zwijn-container {
            text-align: center;
            background: linear-gradient(135deg, #fff0f3 0%, #ffccd5 100%);
            padding: 20px;
            border-radius: 15px;
            border: 2px solid #ff4b4b;
            margin-bottom: 20px;
        }
        .snuit-pratend {
            display: inline-block;
            animation: speak 0.6s infinite ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)

    is_reagerend = "laatste_antwoord" in st.session_state and st.session_state.laatste_antwoord != ""
    avatar_class = "snuit-pratend" if is_reagerend else ""
    
    st.markdown(f"""
        <div class="zwijn-container">
            <div class="{avatar_class}" style="font-size: 60px;">🐗</div>
            <h3 style="margin: 5px 0 0 0; color: #333;">Boris de Zwijnenberg Assistent</h3>
            <p style="font-style: italic; color: #666; font-size: 14px;">"Oink! Vraag me alles over jullie gezin, recepten, het weer etc!"</p>
        </div>
    """, unsafe_allow_html=True)

    tab_tekst, tab_spraak = st.tabs(["⌨️ Typ je vraag", "🎤 Spreek met Boris"])
    gebruiker_vraag = ""

    with tab_tekst:
        getypte_vraag = st.text_input("💬 Waar kan ik mee helpen?", placeholder="Bijv. 'Wat voor weer wordt het morgen?' of 'Zet melk op de lijst'")
        if getypte_vraag:
            gebruiker_vraag = getypte_vraag

    with tab_spraak:
        st.write("Klik op de opnameknop en spreek je vraag in:")
        audio_file = st.audio_input("Spreek je bericht in voor Boris")
        if audio_file is not None:
            with st.spinner("Boris luistert naar je audio..."):
                audio_bytes = audio_file.read()
                contents = [
                    GEZIN_CONTEXT,
                    {"mime_type": "audio/wav", "data": audio_bytes},
                    "Luister naar deze audio-inspraak van de gebruiker, begrijp de vraag en geef antwoord in de rol van Boris."
                ]
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=contents
                )
                gebruiker_vraag = "(Spraakbericht verwerkt)"
                st.session_state.laatste_antwoord = response.text

    if tab_tekst and st.button("Vraag Boris", type="primary"):
        if gebruiker_vraag:
            with st.spinner("Boris denkt na... 🐗"):
                contents = [GEZIN_CONTEXT, f"De gebruiker vraagt: '{gebruiker_vraag}'. Geef antwoord in de rol van Boris."]
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=contents
                )
                st.session_state.laatste_antwoord = response.text
        else:
            st.warning("Typ eerst even een berichtje.")

    if "laatste_antwoord" in st.session_state and st.session_state.laatste_antwoord:
        st.success(st.session_state.laatste_antwoord)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Binnenkort")
        vandaag = datetime.date.today()
        agenda_data = laad_agenda_van_sheet()
        komende_items = []
        for item in agenda_data:
            try:
                d_obj = datetime.datetime.strptime(str(item["datum"]), "%Y-%m-%d").date()
                if d_obj >= vandaag:
                    komende_items.append({"datum": d_obj, "beschrijving": item["beschrijving"]})
            except:
                pass
        
        gesorteerd = sorted(komende_items, key=lambda x: x["datum"])[:3]
        if gesorteerd:
            for item in gesorteerd:
                st.markdown(f"🗓️ **{item['datum'].strftime('%d-%m-%Y')}**: {item['beschrijving']}")
        else:
            st.write("Geen directe afspraken in de planning.")

    with col2:
        st.subheader("🛒 Boodschappen")
        boodschappen_lijst = laad_boodschappen_van_sheet()
        if boodschappen_lijst:
            st.write(f"Er staan momenteel **{len(boodschappen_lijst)} items** op de lijst.")
        else:
            st.write("De boodschappenlijst is helemaal leeg! 👍")

# --- PAGINA 1: RECEPTEN GENERATOR ---
elif pagina == "🍳 Recepten Generator":
    st.title("🍳 Recepten Generator")
    st.write("Upload een foto van de koelkast. Boris maakt direct een maaltijdplan voor het gezin!")

    uploaded_file = st.file_uploader("Upload foto", type=["jpg", "jpeg", "png"])

    if st.button("Genereer Maaltijdplan", type="primary"):
        if uploaded_file is not None:
            with st.spinner("Boris bekijkt de foto..."):
                contents = [GEZIN_CONTEXT]
                image = Image.open(uploaded_file)
                contents.append(image)
                st.image(image, caption="Geüploade foto", width=400)
                    
                prompt = (
                    "Analyseer deze koelkastfoto in de rol van Boris. Geef op basis hiervan:\n"
                    "1. **Receptopties**: Kindvriendelijke gerechten.\n"
                    "2. **Mini-planning**: Welk recept voor welke dag."
                )
                contents.append(prompt)

                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=contents
                )
                
                st.subheader("Jouw Gezinsrecepten & Planning:")
                st.write(response.text)
        else:
            st.warning("Upload eerst een foto!")

# --- PAGINA 2: KASSABON SCANNER ---
elif pagina == "🧾 Kassabon Scanner":
    st.title("🧾 Kassabon Scanner")
    st.write("Upload een foto van een bon. Boris leest de producten uit voor je boodschappenlijstje!")

    bon_file = st.file_uploader("Upload foto van de bon", type=["jpg", "jpeg", "png"])

    if st.button("Scan Bon", type="primary"):
        if bon_file is not None:
            with st.spinner("De bon wordt gelezen..."):
                contents = [GEZIN_CONTEXT]
                image = Image.open(bon_file)
                contents.append(image)
                st.image(image, caption="Geüploade bon", width=400)
                    
                prompt = (
                    "Lees deze kassabon uit. Geef een duidelijke opsommingslijst van de gekochte producten "
                    "zodat deze direct op de boodschappenlijst gezet kunnen worden."
                )
                contents.append(prompt)

                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=contents
                )
                
                st.subheader("Gevonden producten:")
                st.write(response.text)
        else:
            st.warning("Upload eerst een foto van de kassabon!")

# --- PAGINA 3: MAANDAGENDA & PLANNING ---
elif pagina == "📅 Maandagenda & Planning":
    st.title("📅 Gezins Maandagenda")

    with st.expander("➕ Voeg iets toe", expanded=False):
        with st.form("agenda_form", clear_on_submit=True):
            nieuwe_datum = st.date_input("Datum", datetime.date.today())
            nieuwe_beschrijving = st.text_input("Omschrijving")
            submit_knop = st.form_submit_button("Toevoegen aan agenda")
            
            if submit_knop and nieuwe_beschrijving:
                voeg_agenda_toe_aan_sheet(nieuwe_datum.strftime("%Y-%m-%d"), nieuwe_beschrijving)
                st.success("Toegevoegd!")
                st.rerun()

    st.markdown("---")

    vandaag = datetime.date.today()
    jaar, maand = vandaag.year, vandaag.month
    maand_naam = vandaag.strftime("%B %Y")

    st.subheader(f"📆 Kalenderoverzicht ({maand_naam})")

    agenda_data = laad_agenda_van_sheet()
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
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{dag_naam}</p>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, dag in enumerate(week):
            if dag == 0:
                cols[i].markdown("<div style='padding: 10px; text-align: center; color: #ccc;'>-</div>", unsafe_allow_html=True)
            else:
                huidige_datum_obj = datetime.date(jaar, maand, dag)
                datum_sleutel = huidige_datum_obj.strftime("%Y-%m-%d")
                
                is_vandaag = (huidige_datum_obj == vandaag)
                heeft_afspraak = datum_sleutel in agenda_dict

                bg_color = "#f0f2f6"
                border_style = "1px solid #ddd"
                if is_vandaag: border_style = "2px solid #ff4b4b"
                if heeft_afspraak: bg_color = "#e6f3ff"

                inhoud_tekst = f"<b>{dag}</b>"
                if heeft_afspraak:
                    inhoud_tekst += "<br><span style='font-size: 10px; color: #0066cc;'>📌</span>"

                cols[i].markdown(
                    f"""<div style="background-color: {bg_color}; border: {border_style}; border-radius: 6px; padding: 6px; text-align: center; min-height: 45px; margin-bottom: 3px;">
                        {inhoud_tekst}
                    </div>""", 
                    unsafe_allow_html=True
                )
                
    st.markdown("### Alle geplande items:")
    for item in sorted(agenda_data, key=lambda x: str(x.get("datum", ""))):
        st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")

# --- PAGINA 4: BOODSCHAPPENLIJSTJE ---
elif pagina == "🛒 Boodschappenlijstje":
    st.title("🛒 Boodschappenlijstje")
    
    nieuw_item = st.text_input("Voeg iets toe:")
    if st.button("Toevoegen") and nieuw_item:
        voeg_boodschap_toe_aan_sheet(nieuw_item)
        st.success(f"'{nieuw_item}' toegevoegd!")
        st.rerun()

    boodschappen_lijst = laad_boodschappen_van_sheet()
    if boodschappen_lijst:
        st.markdown("### Huidige lijst:")
        te_verwijderen = []
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(item, key=f"boodschap_{idx}"):
                te_verwijderen.append(item)
        
        if te_verwijderen:
            if st.button("Verwijder aangevinkte items"):
                verwijder_boodschappen_uit_sheet(te_verwijderen)
                st.success("Lijst bijgewerkt!")
                st.rerun()
    else:
        st.info("De lijst is leeg.")
