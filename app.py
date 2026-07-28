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
        .stColumns:not(.calendar-grid) {
            flex-direction: column !important;
        }
        div[data-testid="column"]:not(.calendar-col) {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 10px;
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

GEZIN_CONTEXT = (
    "Je bent Boris, de virtuele huiszwijn-assistent van het gezin Zwijnenberg: "
    "Chiel (geboren 13 juni 1989, 37 jaar) en Angelica (geboren 15 januari 1989, 37 jaar, getrouwd 22-04-2024), "
    "Tygo (geboren 24 oktober 2022, 3 jaar) en Duen (geboren 11 juni 2025, 1 jaar). "
    "Je spreekt altijd een beetje vrolijk, behulpzaam en in karakter als een slim huiszwijn (gebruik af en toe een subtiele knipoog zoals 'Oink!')."
)

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

if pagina == "🏠 Home":
    st.title("🏡 Zwijnenberg Home Hub & Boris")
    st.write("Welkom thuis! Maak kennis met **Boris**, jullie persoonlijke virtuele zwijnen-assistent.")
    
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

elif pagina == "🍳 Recepten Generator":
    st.title("🍳 Recepten Generator")
    uploaded_file = st.file_uploader("Upload foto", type=["jpg", "jpeg", "png"])
    if st.button("Genereer Maaltijdplan", type="primary") and uploaded_file:
        with st.spinner("Boris bekijkt de foto..."):
            contents = [GEZIN_CONTEXT, Image.open(uploaded_file), "Analyseer deze koelkastfoto en geef receptopties."]
            response = client.models.generate_content(model='gemini-3.5-flash', contents=contents)
            st.write(response.text)

elif pagina == "🧾 Kassabon Scanner":
    st.title("🧾 Kassabon Scanner")
    bon_file = st.file_uploader("Upload foto van de bon", type=["jpg", "jpeg", "png"])
    if st.button("Scan Bon", type="primary") and bon_file:
        with st.spinner("De bon wordt gelezen..."):
            contents = [GEZIN_CONTEXT, Image.open(bon_file), "Lees deze kassabon uit voor de boodschappenlijst."]
            response = client.models.generate_content(model='gemini-3.5-flash', contents=contents)
            st.write(response.text)

elif pagina == "📅 Maandagenda & Planning":
    st.title("📅 Gezins Maandagenda")

    with st.expander("➕ Voeg iets toe", expanded=False):
        with st.form("agenda_form", clear_on_submit=True):
            nieuwe_datum = st.date_input("Datum", datetime.date.today())
            nieuwe_beschrijving = st.text_input("Omschrijving")
            if st.form_submit_button("Toevoegen aan agenda") and nieuwe_beschrijving:
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

    # Kalender kolommen geforceerd naast elkaar
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
                if is_vandaag: border_style = "2px solid #ff4b4b"
                if heeft_afspraak: bg_color = "#e6f3ff"

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
    for item in sorted(agenda_data, key=lambda x: str(x.get("datum", ""))):
        st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")

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
        
        if te_verwijderen and st.button("Verwijder aangevinkte items"):
            verwijder_boodschappen_uit_sheet(te_verwijderen)
            st.success("Lijst bijgewerkt!")
            st.rerun()
    else:
        st.info("De lijst is leeg.")

