import streamlit as st
from google import genai
from PIL import Image
import datetime
import calendar

# Pagina configuratie
st.set_page_config(page_title="Zwijnenberg home assist", page_icon="🏠", layout="wide")

# Initialiseer de client (vervang met je echte API-sleutel)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- ACHTERGROND GEZINS-INFO VOOR DE AI ---
GEZIN_CONTEXT = (
    "Je bent de persoonlijke kook- en gezinsassistent van het gezin Zwijnenberg: "
    "Chiel (geboren 13 juni 1989, 37 jaar) en Angelica (geboren 15 januari 1989, 37 jaar, getrouwd 22-04-2024), "
    "Tygo (geboren 24 oktober 2022, 3 jaar) en Duen (geboren 11 juni 2025, 1 jaar). "
    "Ze eten van alles wat. Houd bij recepten en planning rekening met de leeftijd van de kinderen."
)

# --- SESSION STATE VOOR GEGEVENS ---
if "agenda_items" not in st.session_state:
    st.session_state.agenda_items = [
        {"datum": datetime.date(2026, 4, 22), "beschrijving": "💍 Trouwdag Chiel & Angelica"},
        {"datum": datetime.date(2026, 6, 11), "beschrijving": "🎂 Verjaardag Duen (1 jr)"},
        {"datum": datetime.date(2026, 10, 24), "beschrijving": "🎂 Verjaardag Tygo (3 jr)"}
    ]

if "boodschappen" not in st.session_state:
    st.session_state.boodschappen = []

# --- ZIJKANT / NAVIGATIE ---
st.sidebar.title("🍳 Menu")
# Omdat '🏠 Home' bovenaan staat, is dit automatisch de landingspagina als je de app opent!
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
    st.title("🏡 Zwijnenberg Home Hub")
    st.write("Welkom thuis! Vraag hieronder iets aan de gezinsassistent of bekijk het snelle overzicht.")

    # Vraagbak / Chat input op de homepage
    gebruiker_vraag = st.text_input("💬 Waar kan ik mee helpen?", placeholder="Bijv. 'Zet melk op de lijst' of 'Wat eten we vanavond?'")
    
    if st.button("Vraag Assistent", type="primary"):
        if gebruiker_vraag:
            with st.spinner("De assistent denkt mee..."):
                contents = [GEZIN_CONTEXT, f"De gebruiker zegt/vraagt het volgende in de home hub: '{gebruiker_vraag}'. Geef een slim, direct antwoord of handel dit praktisch af voor het gezin."]
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=contents
                )
                st.info(response.text)
        else:
            st.warning("Typ eerst even een berichtje.")

    st.markdown("---")
    
    # Snelle samenvatting / widgets op het homescreen
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 Binnenkort")
        vandaag = datetime.date.today()
        komende_items = [item for item in st.session_state.agenda_items if item["datum"] >= vandaag]
        gesorteerd = sorted(komende_items, key=lambda x: x["datum"])[:3]
        
        if gesorteerd:
            for item in gesorteerd:
                st.markdown(f"🗓️ **{item['datum'].strftime('%d-%m-%Y')}**: {item['beschrijving']}")
        else:
            st.write("Geen directe afspraken in de planning.")

    with col2:
        st.subheader("🛒 Boodschappen")
        if st.session_state.boodschappen:
            st.write(f"Er staan momenteel **{len(st.session_state.boodschappen)} items** op de lijst.")
        else:
            st.write("De boodschappenlijst is helemaal leeg! 👍")

# --- PAGINA 1: RECEPTEN GENERATOR ---
elif pagina == "🍳 Recepten Generator":
    st.title("🍳 Recepten Generator")
    st.write("Upload een foto van de koelkast. De AI maakt direct een maaltijdplan voor het gezin!")

    uploaded_file = st.file_uploader("Upload foto", type=["jpg", "jpeg", "png"])

    if st.button("Genereer Maaltijdplan", type="primary"):
        if uploaded_file is not None:
            with st.spinner("De assistent bekijkt de foto..."):
                contents = [GEZIN_CONTEXT]
                image = Image.open(uploaded_file)
                contents.append(image)
                st.image(image, caption="Geüploade foto", width=400)
                    
                prompt = (
                    "Analyseer deze koelkastfoto. Geef op basis hiervan:\n"
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
    st.write("Upload een foto van een bon. De AI leest de producten uit voor je boodschappenlijstje!")

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
                st.session_state.agenda_items.append({"datum": nieuwe_datum, "beschrijving": nieuwe_beschrijving})
                st.success(f"Toegevoegd!")

    st.markdown("---")

    vandaag = datetime.date.today()
    jaar = vandaag.year
    maand = vandaag.month
    maand_naam = vandaag.strftime("%B %Y")

    st.subheader(f"📆 Kalenderoverzicht ({maand_naam})")

    agenda_dict = {}
    for item in st.session_state.agenda_items:
        d_str = item["datum"].strftime("%Y-%m-%d")
        if d_str not in agenda_dict:
            agenda_dict[d_str] = []
        agenda_dict[d_str].append(item["beschrijving"])

    cal = calendar.monthcalendar(jaar, maand)
    weekdagen = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]

    cols = st.columns(7)
    for i, dag_naam in enumerate(weekdagen):
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{dag_naam}</p>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, dag in enumerate(week):
            if dag == 0:
                cols[i].markdown("<div style='padding: 15px; text-align: center; color: #ccc;'>-</div>", unsafe_allow_html=True)
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

                inhoud_tekst = f"<b>{dag}</b>"
                if heeft_afspraak:
                    inhoud_tekst += "<br><span style='font-size: 11px; color: #0066cc;'>📌 Afspraak</span>"

                cols[i].markdown(
                    f"""
                    <div style="background-color: {bg_color}; border: {border_style}; border-radius: 8px; padding: 10px; text-align: center; min-height: 65px; margin-bottom: 5px;">
                        {inhoud_tekst}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                if heeft_afspraak:
                    for afspraak in agenda_dict[datum_sleutel]:
                        st.caption(f"📅 **{dag} {maand_naam[:3]}**: {afspraak}")

# --- PAGINA 4: BOODSCHAPPENLIJSTJE ---
elif pagina == "🛒 Boodschappenlijstje":
    st.title("🛒 Boodschappenlijstje")
    
    nieuw_item = st.text_input("Voeg iets toe:")
    if st.button("Toevoegen") and nieuw_item:
        st.session_state.boodschappen.append(nieuw_item)
        st.success(f"'{nieuw_item}' toegevoegd!")

    if st.session_state.boodschappen:
        st.markdown("### Huidige lijst:")
        for item in st.session_state.boodschappen:
            st.checkbox(item)
    else:
        st.info("De lijst is leeg.")

from twilio.rest import Client as TwilioClient

# Haal Twilio gegevens veilig op uit secrets
TWILIO_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

# Sectie in de sidebar of app voor WhatsApp status
st.sidebar.markdown("---")
st.sidebar.subheader("📱 WhatsApp Koppeling")
st.sidebar.info(
  "Stuur een appje naar het Twilio nummer om de Zwijnenberg Home Hub te"
  " bereiken!"
)
from twilio.twiml.messaging_response import MessagingResponse

# Vang inkomende WhatsApp berichten op via Streamlit query parameters
query_params = st.query_params
if "Body" in query_params:
  incoming_msg = query_params["Body"]

  # Laat Gemini het bericht verwerken (gebruik je bestaande Gemini logica)
  # response = client.models.generate_content(...)

  # Stuur antwoord terug naar WhatsApp
  resp = MessagingResponse()
  resp.message("Ontvangen door de Zwijnenberg Home Hub!")
  st.write(str(resp))
