import base64
import calendar
import datetime
import json
import os
import random
import re
from google import genai
from PIL import Image
import streamlit as st

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Zwijnenberg Home Assist",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- BROWSER HISTORY & ROUTING ---
query_pagina = st.query_params.get("pagina", "Home")

if (
    "huidige_pagina" not in st.session_state
    or st.session_state["huidige_pagina"] != query_pagina
):
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
    st.error(
        "🚨 Kan de API-sleutel niet vinden. Zorg voor een `.streamlit/secrets.toml` bestand met `GEMINI_API_KEY`."
    )
    st.stop()


def parse_json_veilig(tekst):
    try:
        m = re.search(r"\{.*\}", tekst, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(tekst)
    except Exception:
        return None


# --- STYLING (MOBIEL GEOPTIMALISEERD: NATIVE APP-LOOK) ---
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }

    /* Voorkom horizontaal scrollen op mobiel */
    .main, .block-container {
        max-width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-top: 1rem !important;
        overflow-x: hidden !important;
    }
    
    /* Layout voor knoppen-grid */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
        margin-bottom: 6px !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 0px !important;
    }

    /* Tegelknoppen Stijl: Vormgeving als moderne iOS/Android App Icons */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border-radius: 20px !important;
        background: linear-gradient(145deg, #f0f7f2, #e1efe4) !important;
        color: #1B4D2E !important;
        border: 1px solid #d0e5d4 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        white-space: pre-wrap !important;
        padding: 6px !important;
        line-height: 1.2 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Pictogrammen (eerste regel van de knop) vergroten */
    .stButton > button p {
        margin: 0 !important;
    }
    .stButton > button p::first-line {
        font-size: 1.7rem !important;
        line-height: 1.3 !important;
    }

    .stButton > button:hover, .stButton > button:active {
        transform: scale(0.96) !important;
        background: linear-gradient(145deg, #e1efe4, #d0e5d4) !important;
        border-color: #2E7D32 !important;
        color: #0E331A !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }

    /* Animaties voor mascotte Boris */
    @keyframes avatar-talking {
        0% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-4px) scale(1.02); }
        100% { transform: translateY(0px) scale(1); }
    }
    .Boris-img-talking { animation: avatar-talking 0.3s infinite ease-in-out; }
    
    @keyframes avatar-dancing {
        0% { transform: rotate(0deg) translateY(0px); }
        25% { transform: rotate(-8deg) translateY(-6px); }
        50% { transform: rotate(0deg) translateY(0px); }
        75% { transform: rotate(8deg) translateY(-6px); }
        100% { transform: rotate(0deg) translateY(0px); }
    }
    .Boris-img-dancing { animation: avatar-dancing 0.5s infinite ease-in-out; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"


def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "boodschappen_historie" not in data:
                    data["boodschappen_historie"] = {}
                if "agenda" not in data:
                    data["agenda"] = []
                if "boodschappen" not in data:
                    data["boodschappen"] = []
                if "weekmenu" not in data:
                    data["weekmenu"] = {}
                if "dagschema" not in data:
                    data["dagschema"] = [
                        {
                            "taak": "🦷 Tanden poetsen",
                            "tijd": "Ochtend",
                            "klaar": False,
                        },
                        {
                            "taak": "👕 Aankleden",
                            "tijd": "Ochtend",
                            "klaar": False,
                        },
                        {
                            "taak": "🥣 Ontbijten",
                            "tijd": "Ochtend",
                            "klaar": False,
                        },
                        {
                            "taak": "🛏️ Pyjama aan",
                            "tijd": "Avond",
                            "klaar": False,
                        },
                        {
                            "taak": "📚 Verhaaltje lezen",
                            "tijd": "Avond",
                            "klaar": False,
                        },
                    ]
                if "gezondheid" not in data:
                    data["gezondheid"] = []
                if "huishoud" not in data:
                    data["huishoud"] = [
                        {
                            "taak": "🗑️ Grijze container aan straat",
                            "dag": "Maandag",
                            "status": False,
                        },
                        {
                            "taak": "♻️ Gft-bak buiten zetten",
                            "dag": "Donderdag",
                            "status": False,
                        },
                        {
                            "taak": "🧽 Vaatwasser filter schoonmaken",
                            "dag": "Zaterdag",
                            "status": False,
                        },
                        {
                            "taak": "🛏️ Bedden verschonen",
                            "dag": "Zondag",
                            "status": False,
                        },
                    ]
                return data
        except Exception:
            pass

    standaard_data = {
        "agenda": [
            {
                "datum": "2026-04-22",
                "beschrijving": "💍 Trouwdag Chiel & Angelica",
            },
            {"datum": "2026-06-11", "beschrijving": "🎂 Verjaardag Duén (1 jr)"},
            {"datum": "2026-10-24", "beschrijving": "🎂 Verjaardag Tygo (3 jr)"},
        ],
        "boodschappen": [],
        "boodschappen_historie": {},
        "weekmenu": {},
        "dagschema": [
            {"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False},
            {"taak": "👕 Aankleden", "tijd": "Ochtend", "klaar": False},
            {"taak": "🥣 Ontbijten", "tijd": "Ochtend", "klaar": False},
            {"taak": "🛏️ Pyjama aan", "tijd": "Avond", "klaar": False},
            {"taak": "📚 Verhaaltje lezen", "tijd": "Avond", "klaar": False},
        ],
        "gezondheid": [],
        "huishoud": [
            {
                "taak": "🗑️ Grijze container aan straat",
                "dag": "Maandag",
                "status": False,
            },
            {
                "taak": "♻️ Gft-bak buiten zetten",
                "dag": "Donderdag",
                "status": False,
            },
            {
                "taak": "🧽 Vaatwasser filter schoonmaken",
                "dag": "Zaterdag",
                "status": False,
            },
            {"taak": "🛏️ Bedden verschonen", "dag": "Zondag", "status": False},
        ],
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
if "kalender_jaar" not in st.session_state:
    st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state:
    st.session_state["kalender_maand"] = vandaag.month


def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append(
        {"datum": str(datum), "beschrijving": beschrijving}
    )
    sla_data_op(st.session_state["gezin_data"])


def verwijder_agenda_item(index):
    if 0 <= index < len(st.session_state["gezin_data"]["agenda"]):
        st.session_state["gezin_data"]["agenda"].pop(index)
        sla_data_op(st.session_state["gezin_data"])


def voeg_boodschap_toe(item):
    item_schoon = item.strip().capitalize()
    if not item_schoon:
        return
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
    if not tekst:
        return
    try:
        prompt = f"Splits de volgende tekst op in losse boodschappen. Geef enkel een JSON lijst van strings terug, bijv: [\"Melk\", \"Brood\"]. Tekst: '{tekst}'"
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        items = json.loads(res.text)
        if isinstance(items, list):
            for item in items:
                voeg_boodschap_toe(str(item))
            return
    except Exception:
        pass

    delen = re.split(
        r",|\sen\s|\splus\s|\sen ook\s", tekst, flags=re.IGNORECASE
    )
    for d in delen:
        voeg_boodschap_toe(d)


def verwijder_boodschappen_op_index(indices_om_te_verwijderen):
    huidige = st.session_state["gezin_data"].get("boodschappen", [])
    nieuwe_lijst = [
        item for i, item in enumerate(huidige) if i not in indices_om_te_verwijderen
    ]
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

# ==========================================
# HOOFDSCHERM (DASHBOARD - APP ICONEN GRID)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len(
        [
            a
            for a in st.session_state["gezin_data"]["agenda"]
            if a.get("datum", "") >= vandaag_str
        ]
    )

    col_titel, col_datum = st.columns([3, 1])
    with col_titel:
        st.markdown("### 🐷 Zwijnenberg Assist")
    with col_datum:
        st.markdown(
            f"<p style='text-align: right; font-size: 13px; color: #888; font-weight: bold; margin-top: 8px;'>{vandaag.strftime('%d-%m-%Y')}</p>",
            unsafe_allow_html=True,
        )

    # 2-koloms app-grid met vierkante tegelknoppen
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if st.button("💬\nChat Boris", use_container_width=True, key="btn_chat"):
            ga_naar("Chat")
    with r1c2:
        if st.button(
            f"📅\nAgenda ({aantal_afspraken_komend})",
            use_container_width=True,
            key="btn_agenda",
        ):
            ga_naar("Agenda")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if st.button(
            f"🛒\nLijstje ({aantal_boodschappen})",
            use_container_width=True,
            key="btn_boodschappen",
        ):
            ga_naar("Boodschappenlijst")
    with r2c2:
        if st.button(
            "🍽️\nWeekmenu", use_container_width=True, key="btn_weekmenu"
        ):
            ga_naar("Weekmenu")

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        if st.button(
            "🎯\nDagschema", use_container_width=True, key="btn_dagschema"
        ):
            ga_naar("Dagschema")
    with r3c2:
        if st.button(
            "🌳\nUitjes", use_container_width=True, key="btn_uitjes"
        ):
            ga_naar("Activiteiten")

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        if st.button(
            "💊\nGezondheid", use_container_width=True, key="btn_gezondheid"
        ):
            ga_naar("Gezondheid")
    with r4c2:
        if st.button(
            "🧹\nHuishoud", use_container_width=True, key="btn_huishoud"
        ):
            ga_naar("Huishoud")

    r5c1, r5c2 = st.columns(2)
    with r5c1:
        if st.button(
            "🔍\nRecepten", use_container_width=True, key="btn_recepten"
        ):
            ga_naar("Recepten")
    with r5c2:
        if st.button(
            "🧾\nScanner", use_container_width=True, key="btn_bonnen"
        ):
            ga_naar("Kassabon Scanner")

    r6c1, r6c2 = st.columns(2)
    with r6c1:
        if st.button("🎵\nMini-Disco", use_container_width=True, key="btn_kids"):
            ga_naar("Kids")
    with r6c2:
        pass


# ==========================================
# SUBPAGINA: CHAT MET BORIS
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 💬 Chat met Boris")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Oink! Hallo Zwijnenbergjes! Hoe kan ik jullie vandaag helpen?",
            }
        ]

    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("Vraag iets aan Boris..."):
        st.session_state["chat_messages"].append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Boris denkt na..."):
                try:
                    prompt = f"{GEZIN_CONTEXT}\n\nGebruiker zegt: {user_input}"
                    res = client.models.generate_content(
                        model="gemini-2.5-flash", contents=prompt
                    )
                    antwoord = res.text
                except Exception as e:
                    antwoord = (
                        f"Oink! Er ging iets mis met mijn varkensbrein: {e}"
                    )

                st.write(antwoord)
                st.session_state["chat_messages"].append(
                    {"role": "assistant", "content": antwoord}
                )


# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("#### ➕ Nieuwe afspraak")
    with st.form("agenda_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            nieuwe_datum = st.date_input("Datum", vandaag)
        with col2:
            nieuwe_beschrijving = st.text_input("Omschrijving")

        if st.form_submit_button("Opslaan") and nieuwe_beschrijving:
            voeg_agenda_toe(
                nieuwe_datum.strftime("%Y-%m-%d"), nieuwe_beschrijving
            )
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
        st.markdown(
            f"<h4 style='text-align: center; margin: 0;'>{calendar.month_name[maand]} {jaar}</h4>",
            unsafe_allow_html=True,
        )

    agenda_dict = {}
    for item in st.session_state["gezin_data"].get("agenda", []):
        d_str = str(item.get("datum", ""))
        if d_str not in agenda_dict:
            agenda_dict[d_str] = []
        agenda_dict[d_str].append(item.get("beschrijving", ""))

    cal = calendar.monthcalendar(jaar, maand)
    vandaag_str = vandaag.strftime("%Y-%m-%d")

    html_cal = """
    <style>
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; padding-bottom: 15px; }
    .cal-header { text-align: center; font-weight: bold; font-size: 0.8rem; padding: 4px 0; color: #888; }
    .cal-day { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 4px; text-align: center; min-height: 42px; display: flex; flex-direction: column; justify-content: start; align-items: center;}
    .cal-day span.date { font-weight: bold; font-size: 0.85rem; color: #333 !important; }
    .cal-day.vandaag { border: 2px solid #ff9800; background-color: #fff8e1; }
    .cal-day.afspraak { background-color: #e3f2fd; border-color: #2196F3; }
    .cal-leeg { background-color: transparent; }
    .cal-badge { font-size: 0.65rem; color: #1976d2; font-weight: bold; margin-top: 2px; }
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
                if datum_str == vandaag_str:
                    cls += " vandaag"
                if datum_str in agenda_dict:
                    cls += " afspraak"
                badge = (
                    f"<div class='cal-badge'>📌 {len(agenda_dict[datum_str])}</div>"
                    if datum_str in agenda_dict
                    else ""
                )
                html_cal += f"<div class='{cls}'><span class='date'>{dag}</span>{badge}</div>"

    html_cal += "</div>"
    st.markdown(html_cal, unsafe_allow_html=True)

    st.markdown("### 📋 Afspraken:")
    agenda_lijst = st.session_state["gezin_data"].get("agenda", [])
    if agenda_lijst:
        for idx, item in enumerate(agenda_lijst):
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}"
                )
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

    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    if "actieve_hoofd_cat" not in st.session_state:
        st.session_state["actieve_hoofd_cat"] = None
    if "actieve_sub_cat" not in st.session_state:
        st.session_state["actieve_sub_cat"] = None

    supermarkt_database = {
        "AGF": {
            "Vers fruit": [
                ("🍎", "Appels"),
                ("🍌", "Bananen"),
                ("🍓", "Bessen"),
                ("🍊", "Citrus"),
            ],
            "Groenten": [
                ("🥬", "Sla"),
                ("🍅", "Tomaten"),
                ("🧅", "Uien"),
                ("🥕", "Wortels"),
            ],
            "Aardappel": [("🥔", "Aardappels"), ("🥔", "Krieltjes")],
            "Salades": [("🥗", "Maaltijdsalade"), ("🥕", "Snackgroente")],
        },
        "Zuivel": {
            "Melk": [("🥛", "Melk"), ("🥛", "Karnemelk"), ("🥛", "Havermelk")],
            "Yoghurt": [("🥣", "Yoghurt"), ("🥣", "Kwark")],
            "Kaas": [
                ("🧀", "Jonge kaas"),
                ("🧀", "Oude kaas"),
                ("🧀", "Smeerkaas"),
            ],
            "Eieren/Boter": [
                ("🥚", "Eieren"),
                ("🧈", "Roomboter"),
                ("🧈", "Margarine"),
            ],
        },
        "Vlees/Vis": {
            "Vlees": [("🍗", "Kipfilet"), ("🥩", "Gehakt"), ("🥩", "Biefstuk")],
            "Vis": [("🐟", "Zalm"), ("🐟", "Kabeljauw"), ("🦐", "Garnalen")],
            "Vega": [("🌱", "Vega burgers"), ("🌱", "Tofu"), ("🧆", "Falafel")],
        },
        "Brood/Ontbijt": {
            "Brood": [("🍞", "Brood"), ("🥖", "Stokbrood"), ("🥐", "Croissants")],
            "Granen": [("🥣", "Muesli"), ("🥣", "Havermout"), ("🥣", "Cruesli")],
            "Beleg": [
                ("🍓", "Jam"),
                ("🥜", "Pindakaas"),
                ("🍫", "Hagelslag"),
                ("🍯", "Honing"),
            ],
        },
        "Dranken": {
            "Fris/Sap": [
                ("🥤", "Cola"),
                ("🥤", "Sinas"),
                ("💧", "Water"),
                ("🧃", "Jus d'orange"),
            ],
            "Koffie/Thee": [
                ("☕", "Koffiebonen"),
                ("☕", "Koffie"),
                ("🍵", "Thee"),
            ],
            "Alcohol": [("🍺", "Bier"), ("🍷", "Wijn")],
        },
        "Houdbaar": {
            "Pasta/Rijst": [("🍝", "Pasta"), ("🍚", "Rijst"), ("🍜", "Mie")],
            "Conserven": [
                ("🥫", "Soep"),
                ("🥫", "Groente blik"),
                ("🐟", "Tonijn"),
            ],
            "Sauzen": [("🧂", "Mayo"), ("🍅", "Ketchup"), ("🫒", "Olijfolie")],
        },
        "Snacks": {
            "Zout": [("🥔", "Chips"), ("🍿", "Popcorn"), ("🥨", "Nootjes")],
            "Zoet": [("🍬", "Snoep"), ("🍫", "Chocolade"), ("🍪", "Koekjes")],
        },
        "Diepvries": {
            "Diepvries": [
                ("🍕", "Pizza"),
                ("🍦", "IJs"),
                ("🍟", "Friet"),
                ("🥦", "Diepvriesgroente"),
            ]
        },
        "Non-Food": {
            "Verzorging": [
                ("🧴", "Shampoo"),
                ("🪥", "Tandpasta"),
                ("🧼", "Zeep"),
            ],
            "Schoonmaak": [
                ("🧼", "Vaatwas"),
                ("🫧", "Wasmiddel"),
                ("🧻", "Wc-papier"),
                ("🗑️", "Zakken"),
            ],
        },
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
                    if st.button(
                        f"{ic}\n{s_naam}",
                        key=f"subcat_btn_{i}",
                        use_container_width=True,
                    ):
                        st.session_state["actieve_sub_cat"] = s_naam
                        st.rerun()
        else:
            if st.button(
                "⬅️ Terug naar overzicht", key="terug_naar_subs_overzicht"
            ):
                st.session_state["actieve_sub_cat"] = None
                st.rerun()

            st.markdown(f"**🏷️ {sub_cat}**")
            producten = sub_dict.get(sub_cat, [])

            cols = st.columns(4)
            for i, (icoon, prod_naam) in enumerate(producten):
                col_target = cols[i % 4]
                with col_target:
                    if st.button(
                        f"{icoon}\n{prod_naam}",
                        key=f"prod_btn_{i}",
                        use_container_width=True,
                    ):
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
            "Non-Food": "🧻",
        }

        cols = st.columns(4)
        for i, (cat_naam, icoon) in enumerate(hoofd_icoontjes.items()):
            col_target = cols[i % 4]
            with col_target:
                if st.button(
                    f"{icoon}\n{cat_naam}",
                    key=f"hoofd_cat_{i}",
                    use_container_width=True,
                ):
                    st.session_state["actieve_hoofd_cat"] = cat_naam
                    st.session_state["actieve_sub_cat"] = None
                    st.rerun()

    st.markdown("---")

    with st.form("boodschap_form", clear_on_submit=True):
        col_in, col_btn = st.columns([3, 1])
        with col_in:
            nieuw_item = st.text_input(
                "Snel toevoegen:", placeholder="Typ bijv. melk, brood..."
            )
        with col_btn:
            st.markdown(
                "<div style='margin-top: 28px;'></div>", unsafe_allow_html=True
            )
            submit = st.form_submit_button("➕ Voeg toe")
            if submit and nieuw_item:
                verwerk_meerdere_boodschappen(nieuw_item)
                st.rerun()

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
                if st.button(
                    "🗑️ Wissen (aangevinkt)", use_container_width=True
                ):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        with col_v2:
            if st.button("❌ Alles wissen", use_container_width=True):
                leeg_boodschappenlijst()
                st.rerun()
    else:
        st.info("Lijstje is leeg! Tik op een categorie hierboven.")


# ==========================================
# SUBPAGINA: WEEKMENU
# ==========================================
elif st.session_state["huidige_pagina"] == "Weekmenu":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🍽️ Slim Weekmenu")
    st.write(
        "Genereer een kindvriendelijk weekmenu (voor Tygo van 3 en Duén van 1) en voeg direct ingrediënten toe aan je boodschappenlijst!"
    )

    if st.button("✨ Genereer nieuw weekmenu", type="primary"):
        with st.spinner("Boris stelt een weekmenu samen..."):
            prompt = (
                f"{GEZIN_CONTEXT} Genereer een gevarieerd weekmenu voor 5 dagen (Maandag t/m Vrijdag) "
                "specifiek gericht op kindvriendelijke maaltijden. "
                "Geef de output terug als een JSON object met als sleutels 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', "
                "waarbij elke dag een object is met 'gerecht' (string) en 'ingredienten' (lijst van strings)."
            )
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                menu_data = parse_json_veilig(res.text)
                if menu_data:
                    st.session_state["gezin_data"]["weekmenu"] = menu_data
                    sla_data_op(st.session_state["gezin_data"])
                    st.success("Oink! Nieuw weekmenu gegenereerd!")
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
        if st.button(
            "🛒 Voeg alle ingrediënten toe aan Boodschappenlijst",
            type="secondary",
        ):
            totaal_toegevoegd = 0
            for dag, info in huidig_menu.items():
                if isinstance(info, dict):
                    for ing in info.get("ingredienten", []):
                        voeg_boodschap_toe(ing)
                        totaal_toegevoegd += 1
            st.success(
                f"Oink! {totaal_toegevoegd} ingrediënten toegevoegd aan je boodschappenlijst!"
            )


# ==========================================
# SUBPAGINA: DAGSCHEMA / ROUTINETRACKER
# ==========================================
elif st.session_state["huidige_pagina"] == "Dagschema":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🎯 Dagschema & Routines")
    dagschema = st.session_state["gezin_data"].get("dagschema", [])

    st.markdown("#### 🌅 Ochtend routine")
    for idx, taak in enumerate(dagschema):
        if taak.get("tijd") == "Ochtend":
            checked = st.checkbox(
                taak["taak"], value=taak.get("klaar", False), key=f"dagsch_{idx}"
            )
            dagschema[idx]["klaar"] = checked

    st.markdown("#### 🌙 Avond routine")
    for idx, taak in enumerate(dagschema):
        if taak.get("tijd") == "Avond":
            checked = st.checkbox(
                taak["taak"], value=taak.get("klaar", False), key=f"dagsch_{idx}"
            )
            dagschema[idx]["klaar"] = checked

    sla_data_op(st.session_state["gezin_data"])


# ==========================================
# SUBPAGINA: ACTIVITEITEN (UITJES)
# ==========================================
elif st.session_state["huidige_pagina"] == "Activiteiten":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🌳 Uitjes & Activiteiten")
    st.write(
        "Vind leuke gezinsactiviteiten in en rondom Luttenberg/Raalte/Overijssel geschikt voor Tygo (3) en Duén (1)."
    )

    weer_type = st.selectbox("Wat voor weer is het?", ["Zonnig ☀️", "Regenachtig 🌧️", "Koud / Winter ❄️"])

    if st.button("🔍 Zoek leuke uitjes"):
        with st.spinner("Boris zoekt de leukste plekjes..."):
            prompt = (
                f"{GEZIN_CONTEXT} Bedenk 3 concrete en ontzettend leuke gezinsuitjes nabij Luttenberg / Salland. "
                f"Het weer is: {weer_type}. De kinderen zijn 3 jaar en 1 jaar oud. "
                "Geef per uitje een titel, korte beschrijving en geschiktheidstip."
            )
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.markdown(res.text)
            except Exception as e:
                st.error(f"Fout bij ophalen van uitjes: {e}")


# ==========================================
# SUBPAGINA: GEZONDHEID
# ==========================================
elif st.session_state["huidige_pagina"] == "Gezondheid":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 💊 Gezondheid & Medicatie")
    st.write("Houd medicatie en gezondheidsnotities bij voor het gezin.")

    with st.form("form_gezondheid", clear_on_submit=True):
        wie = st.selectbox("Voor wie?", ["Tygo", "Duén", "Chiel", "Angelica"])
        notitie = st.text_input("Notitie / Medicatie (bijv. 5ml Paracetamol)")
        if st.form_submit_button("Opslaan") and notitie:
            st.session_state["gezin_data"]["gezondheid"].append(
                {
                    "datum": vandaag.strftime("%Y-%m-%d %H:%M"),
                    "wie": wie,
                    "notitie": notitie,
                }
            )
            sla_data_op(st.session_state["gezin_data"])
            st.success("Genoteerd!")
            st.rerun()

    st.markdown("#### History:")
    for item in reversed(
        st.session_state["gezin_data"].get("gezondheid", [])
    ):
        st.write(
            f"⏱️ **{item.get('datum')}** - **{item.get('wie')}**: {item.get('notitie')}"
        )


# ==========================================
# SUBPAGINA: HUISHOUD
# ==========================================
elif st.session_state["huidige_pagina"] == "Huishoud":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🧹 Huishoudelijke Taken")
    huishoud = st.session_state["gezin_data"].get("huishoud", [])

    for idx, taak in enumerate(huishoud):
        checked = st.checkbox(
            f"[{taak.get('dag')}] {taak.get('taak')}",
            value=taak.get("status", False),
            key=f"hh_{idx}",
        )
        huishoud[idx]["status"] = checked

    sla_data_op(st.session_state["gezin_data"])


# ==========================================
# SUBPAGINA: RECEPTEN
# ==========================================
elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🔍 Wat eten we vandaag?")
    ingrediënten_input = st.text_input(
        "Wat heb je nog in de koelkast/kast?",
        placeholder="bijv. eieren, tomaat, pasta",
    )

    if st.button("💡 Bedenk een recept") and ingrediënten_input:
        with st.spinner("Boris zoekt een lekker recept..."):
            prompt = (
                f"{GEZIN_CONTEXT} Bedenk een snel en kindvriendelijk recept voor het gezin met onder andere deze ingrediënten: {ingrediënten_input}. "
                "Geef een titel, ingrediëntenlijstje en eenvoudige stappen."
            )
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.markdown(res.text)
            except Exception as e:
                st.error(f"Fout: {e}")


# ==========================================
# SUBPAGINA: KASSABON SCANNER
# ==========================================
elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🧾 Kassabon Scanner")
    st.write(
        "Maak een foto van een kassabon om de items automatisch aan je boodschappen-historie of lijstje toe te voegen."
    )

    uploaded_file = st.file_uploader(
        "Kies of maak een foto van de kassabon", type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade kassabon", use_container_width=True)

        if st.button("🔎 Scan Kassabon"):
            with st.spinner("Boris leest de bon af..."):
                try:
                    prompt = "Analyseer deze kassabon. Geef een JSON lijst terug met de gekochte producten. Voorbeeld: [\"Melk\", \"Brood\"]"
                    res = client.models.generate_content(
                        model="gemini-2.5-flash", contents=[image, prompt]
                    )
                    items = parse_json_veilig(res.text)
                    if items and isinstance(items, list):
                        for item in items:
                            voeg_boodschap_toe(str(item))
                        st.success(
                            f"Oink! {len(items)} producten herkend en toegevoegd!"
                        )
                    else:
                        st.write(res.text)
                except Exception as e:
                    st.error(f"Fout bij scannen: {e}")


# ==========================================
# SUBPAGINA: KIDS DISCO
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")

    st.markdown("### 🎵 Boris' Mini-Disco")
    st.write("Feestje voor Tygo en Duén! Klik op de knop om Boris te laten dansen!")

    if st.button("🎉 DANSEN BORIS!"):
        st.balloons()
        st.markdown(
            """
            <div style="text-align: center; font-size: 80px;" class="Boris-img-dancing">
                🐷
            </div>
            <h3 style="text-align: center; color: #ff4081;">Oink Oink Disco Time! 🎶🥳</h3>
        """,
            unsafe_allow_html=True,
        )
