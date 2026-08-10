import base64
import calendar
import datetime
import json
import os
import random
import re
from PIL import Image
from google import genai
import streamlit as st

# ==========================================
# 1. PAGINA CONFIGURATIE (Altijd bovenaan)
# ==========================================
st.set_page_config(
    page_title="Zwijnenberg Home Assist",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 2. BROWSER HISTORY & ROUTING
# ==========================================
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


# ==========================================
# 3. VEILIGHEIDSCHECK API KEY
# ==========================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error(
        "🚨 Kan de API-sleutel niet vinden. Zorg voor een `.streamlit/secrets.toml` bestand met `GEMINI_API_KEY`."
    )
    st.stop()


def get_image_base64(image_path):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None


def parse_json_veilig(tekst):
    try:
        m = re.search(r"\{.*\}", tekst, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(tekst)
    except Exception:
        return None


# ==========================================
# 4. SLIMME STYLING (Tegels vs. Kleine Knoppen)
# ==========================================
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 1 !important; }

    /* Ruime bovenmarge tegen het wegvallen onder de statusbalk/notch */
    .main .block-container {
        max-width: 100% !important;
        padding-top: 5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        overflow-x: hidden !important;
    }
    
    /* Gelijkmatige verdeling van kolommen */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
        margin-bottom: 6px !important;
        align-items: stretch !important;
    }
    
    div[data-testid="column"], div[data-testid="stColumn"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 100% !important;
    }

    /* 1. STANDAARD KNOPPEN (Terugknoppen, Acties, Formulieren): COMPACT & KLEIN */
    .stButton > button {
        width: auto !important;
        min-width: 0 !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        border-radius: 8px !important;
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #41444C !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 4px 12px !important;
        margin: 0 0 10px 0 !important;
        line-height: 1.2 !important;
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: nowrap !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        background-color: #31333F !important;
        border-color: #555867 !important;
        color: #ffffff !important;
    }

    /* 2. TEGEL KNOPPEN (Alleen knoppen met een regelafstand/meerdere regels): VASTE GROOTTE */
    .stButton > button:has(br), .stButton > button:has(p + p) {
        width: 100% !important;
        height: 72px !important;
        min-height: 72px !important;
        max-height: 72px !important;
        border-radius: 12px !important;
        background: linear-gradient(145deg, #f0f7f2, #e1efe4) !important;
        color: #1B4D2E !important;
        border: 1px solid #d0e5d4 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        transition: transform 0.1s ease, background-color 0.1s ease !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        white-space: pre-wrap !important;
        padding: 4px 2px !important;
        margin: 0 !important;
        line-height: 1.1 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        word-break: normal !important;
        overflow: hidden !important;
    }

    /* Pictogram vergroten op tegelknoppen */
    .stButton > button:has(br) p::first-line {
        font-size: 1.25rem !important;
        line-height: 1.2 !important;
    }

    .stButton > button:has(br):hover, .stButton > button:has(br):active {
        transform: scale(0.97) !important;
        background: linear-gradient(145deg, #e1efe4, #d0e5d4) !important;
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
""",
    unsafe_allow_html=True,
)

# ==========================================
# 5. DATA BEHEER & HELPER FUNCTIES
# ==========================================
DATA_BESTAND = "gezin_data.json"


def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("boodschappen_historie", {})
                data.setdefault("agenda", [])
                data.setdefault("boodschappen", [])
                data.setdefault("weekmenu", {})
                data.setdefault(
                    "dagschema",
                    [
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
                    ],
                )
                data.setdefault("gezondheid", [])
                data.setdefault(
                    "huishoud",
                    [
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
                    ],
                )
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


def genereer_tts_script(
    tekst, knop_tekst="🎙️ Voorlezen", img_id="Boris-main-img", auto_play=False
):
    schone_tekst = (
        tekst.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    )
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
# HOOFDSCHERM (DASHBOARD)
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
            f"<p style='text-align: right; font-size: 12px; color: #aaa; margin-top: 5px;'>{vandaag.strftime('%d-%m-%Y')}</p>",
            unsafe_allow_html=True,
        )

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if st.button("💬\nChat Boris", key="btn_chat"):
            ga_naar("Chat")
    with r1c2:
        if st.button(
            f"📅\nAgenda ({aantal_afspraken_komend})", key="btn_agenda"
        ):
            ga_naar("Agenda")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if st.button(
            f"🛒\nLijstje ({aantal_boodschappen})", key="btn_boodschappen"
        ):
            ga_naar("Boodschappenlijst")
    with r2c2:
        if st.button("🍽️\nWeekmenu", key="btn_weekmenu"):
            ga_naar("Weekmenu")

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        if st.button("🎯\nDagschema", key="btn_dagschema"):
            ga_naar("Dagschema")
    with r3c2:
        if st.button("🌳\nUitjes", key="btn_uitjes"):
            ga_naar("Activiteiten")

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        if st.button("💊\nGezondheid", key="btn_gezondheid"):
            ga_naar("Gezondheid")
    with r4c2:
        if st.button("🧹\nHuishoud", key="btn_huishoud"):
            ga_naar("Huishoud")

    r5c1, r5c2 = st.columns(2)
    with r5c1:
        if st.button("🔍\nRecepten", key="btn_recepten"):
            ga_naar("Recepten")
    with r5c2:
        if st.button("🧾\nScanner", key="btn_bonnen"):
            ga_naar("Kassabon Scanner")

    r6c1, r6c2 = st.columns(2)
    with r6c1:
        if st.button("🎵\nMini-Disco", key="btn_kids"):
            ga_naar("Kids")

# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("⬅️ Terug naar Home", key="back_agenda"):
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
        if st.button("⬅️ Vorige", key="cal_prev"):
            if st.session_state["kalender_maand"] == 1:
                st.session_state["kalender_maand"] = 12
                st.session_state["kalender_jaar"] -= 1
            else:
                st.session_state["kalender_maand"] -= 1
            st.rerun()
    with col_next:
        if st.button("Volgende ➡️", key="cal_next"):
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
            f"<h3 style='text-align: center; margin-top: 0;'>{calendar.month_name[maand]} {jaar}</h3>",
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

    st.markdown("### 📋 Alle geplande afspraken:")
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

    if st.button("⬅️ Terug naar Home", key="back_boodschappen"):
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
            "Melk": [
                ("🥛", "Melk"),
                ("🥛", "Karnemelk"),
                ("🥛", "Havermelk"),
            ],
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
            "Brood": [
                ("🍞", "Brood"),
                ("🥖", "Stokbrood"),
                ("🥐", "Croissants"),
            ],
            "Granen": [
                ("🥣", "Muesli"),
                ("🥣", "Havermout"),
                ("🥣", "Cruesli"),
            ],
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
            "Sauzen": [
                ("🧂", "Mayo"),
                ("🍅", "Ketchup"),
                ("🫒", "Olijfolie"),
            ],
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

    st.markdown("#### 📁 Categorieën")
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
                    if st.button(f"{ic}\n{s_naam}", key=f"subcat_btn_{i}"):
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
                    if st.button(f"{icoon}\n{prod_naam}", key=f"prod_btn_{i}"):
                        voeg_boodschap_toe(prod_naam)
                        st.toast(f"✅ '{prod_naam}' toegevoegd!")
                        st.rerun()

    else:
        hoofd_icoontjes = {
            "AGF": "🥦",
            "Zuivel": "🥛",
            "Vlees/Vis": "🥩",
            "Brood / Ontbijt": "🥐",
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
                db_sleutel = "Brood/Ontbijt" if cat_naam == "Brood / Ontbijt" else cat_naam
                if st.button(f"{icoon}\n{cat_naam}", key=f"hoofd_cat_{i}"):
                    st.session_state["actieve_hoofd_cat"] = db_sleutel
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

    st.components.v1.html(
        """
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
    """,
        height=65,
    )

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
                if st.button("🗑️ Wissen (aangevinkt)", key="del_selected"):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        with col_v2:
            if st.button("❌ Alles wissen", key="del_all"):
                leeg_boodschappenlijst()
                st.rerun()
    else:
        st.info("Lijstje is leeg! Tik op een categorie hierboven.")

# ==========================================
# SUBPAGINA: WEEKMENU
# ==========================================
elif st.session_state["huidige_pagina"] == "Weekmenu":
    if st.button("⬅️ Terug naar Home", key="back_weekmenu"):
        ga_naar("Home")

    st.markdown("### 🍽️ Slim Weekmenu & Boodschappen")
    st.write(
        "Genereer een kindvriendelijk weekmenu (geschikt voor Tygo 3jr en Duén 1jr) en voeg direct de ingrediënten toe aan je lijstje!"
    )

    if st.button("✨ Genereer nieuw weekmenu", type="primary", key="gen_menu"):
        with st.spinner(
            "Boris stelt een lekker en kindvriendelijk weekmenu samen..."
        ):
            prompt = (
                f"{GEZIN_CONTEXT} Genereer een gevarieerd weekmenu voor 5 dagen (Maandag t/m Vrijdag) "
                "specifiek gericht op kindvriendelijke maaltijden (geschikt voor Tygo van 3 en Duén van 1). "
                "Geef de output terug als een JSON object met als sleutels 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', "
                "waarbij elke dag een object is met 'gerecht' (string) en 'ingredienten' (lijst van strings). "
                'Voorbeeldformaat: {"Maandag": {"gerecht": "Milde macaroni", "ingredienten": ["Macaroni", "Gehakt", "Tomatensaus"]}}'
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
                else:
                    st.error(
                        "Kon het menu niet goed verwerken, probeer het nog eens."
                    )
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
            "🛒 Voeg alle ingrediënten toe aan Boodschappenlijst", key="add_ingr"
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
    else:
        st.info("Nog geen weekmenu gegenereerd. Klik op de knop hierboven!")

# ==========================================
# SUBPAGINA: DAGSCHEMA
# ==========================================
elif st.session_state["huidige_pagina"] == "Dagschema":
    if st.button("⬅️ Terug naar Home", key="back_dagschema"):
        ga_naar("Home")

    st.markdown("### 🎯 Dagschema & Routines")
    st.write(
        "Vink af wat Tygo en Duén vandaag al gedaan hebben. Klik onderaan op reset om opnieuw te beginnen!"
    )

    dagschema_lijst = st.session_state["gezin_data"].get("dagschema", [])
    gewijzigd = False

    for idx, item in enumerate(dagschema_lijst):
        huidige_status = item.get("klaar", False)
        nieuwe_status = st.checkbox(
            f"[{item.get('tijd', 'Dag')}] {item.get('taak')}",
            value=huidige_status,
            key=f"schema_{idx}",
        )
        if nieuwe_status != huidige_status:
            item["klaar"] = nieuwe_status
            gewijzigd = True

    if gewijzigd:
        sla_data_op(st.session_state["gezin_data"])

    st.markdown("---")
    if st.button("🔄 Reset Dagschema voor morgen", key="reset_dagschema"):
        for item in dagschema_lijst:
            item["klaar"] = False
        sla_data_op(st.session_state["gezin_data"])
        st.toast("Oink! Schema weer fris klaargezet!")
        st.rerun()

# ==========================================
# SUBPAGINA: ACTIVITEITEN / UITJES
# ==========================================
elif st.session_state["huidige_pagina"] == "Activiteiten":
    if st.button("⬅️ Terug naar Home", key="back_activiteiten"):
        ga_naar("Home")

    st.markdown("### 🌳 Uitjes & Activiteiten")
    st.write(
        "Zoek leuke activiteiten in en rondom Luttenberg/Raalte voor Tygo (3 jr) en Duén (1 jr)."
    )

    weer_type = st.radio(
        "Wat voor uitje zoek je?",
        ["🌧️ Binnen (Slecht weer)", "☀️ Buiten (Mooi weer)"],
        horizontal=True,
    )

    if st.button("💡 Bedenk een uitje met Boris", key="gen_uitje"):
        with st.spinner("Boris zoekt leuke plekjes..."):
            prompt = f"{GEZIN_CONTEXT} Bedenk 3 concrete, hele leuke uitjes voor een peuter van 3 en baby van 1 rondom Luttenberg/Salland. Type uitje: {weer_type}. Geef praktische details en waarom het leuk is."
            res = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            st.markdown(res.text)

# ==========================================
# SUBPAGINA: GEZONDHEID
# ==========================================
elif st.session_state["huidige_pagina"] == "Gezondheid":
    if st.button("⬅️ Terug naar Home", key="back_gezondheid"):
        ga_naar("Home")

    st.markdown("### 💊 Gezondheid & Logboek")
    st.write(
        "Houd eenvoudig koorts, medicatie of klachten van de kids of uzelf bij."
    )

    with st.form("gezondheid_form", clear_on_submit=True):
        wie = st.selectbox("Voor wie?", ["Tygo", "Duén", "Chiel", "Angelica"])
        notitie = st.text_input(
            "Notitie", placeholder="bijv. 38.5°C koorts, zetpil 240mg gegeven"
        )
        if st.form_submit_button("Opslaan") and notitie:
            entry = f"{vandaag.strftime('%d-%m %H:%M')} [{wie}] {notitie}"
            st.session_state["gezin_data"]["gezondheid"].append(entry)
            sla_data_op(st.session_state["gezin_data"])
            st.success("Oink! Notitie opgeslagen.")
            st.rerun()

    st.markdown("#### 📜 Historie")
    historie = st.session_state["gezin_data"].get("gezondheid", [])
    if historie:
        for h in reversed(historie):
            st.write(f"- {h}")
    else:
        st.info("Nog geen gezondheidsnotities vastgelegd.")

# ==========================================
# SUBPAGINA: HUISHOUD
# ==========================================
elif st.session_state["huidige_pagina"] == "Huishoud":
    if st.button("⬅️ Terug naar Home", key="back_huishoud"):
        ga_naar("Home")

    st.markdown("### 🧹 Huishoudelijke Taken")

    huishoud_lijst = st.session_state["gezin_data"].get("huishoud", [])
    gewijzigd = False

    for idx, h in enumerate(huishoud_lijst):
        huidig = h.get("status", False)
        nieuw = st.checkbox(
            f"[{h.get('dag')}] {h.get('taak')}",
            value=huidig,
            key=f"huishoud_{idx}",
        )
        if nieuw != huidig:
            h["status"] = nieuw
            gewijzigd = True

    if gewijzigd:
        sla_data_op(st.session_state["gezin_data"])

# ==========================================
# SUBPAGINA: RECEPTEN
# ==========================================
elif st.session_state["huidige_pagina"] == "Recepten":
    if st.button("⬅️ Terug naar Home", key="back_recepten"):
        ga_naar("Home")

    st.markdown("### 🔍 Recepten Bedenken")
    ingr_input = st.text_input(
        "Wat heb je nog in de koelkast/kast?",
        placeholder="bijv. gehakt, courgette, tomaten blokjes",
    )

    if st.button("🍳 Zoek recepten", key="zoek_recept"):
        if ingr_input:
            with st.spinner("Boris bladert door het kookboek..."):
                prompt = f"{GEZIN_CONTEXT} Bedenk 2 snelle, kindvriendelijke recepten met o.a.: {ingr_input}. Vermeld bereidingstijd en stappen."
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.markdown(res.text)

# ==========================================
# SUBPAGINA: KASSABON SCANNER
# ==========================================
elif st.session_state["huidige_pagina"] == "Kassabon Scanner":
    if st.button("⬅️ Terug naar Home", key="back_bonnen"):
        ga_naar("Home")

    st.markdown("### 🧾 Kassabon Scanner")
    uploaded_file = st.file_uploader(
        "Upload een foto van je kassabon", type=["jpg", "png", "jpeg"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade Kassabon", use_container_width=True)

        if st.button("🔍 Scan bon met Boris AI", key="scan_btn"):
            with st.spinner("Kassabon wordt geanalyseerd..."):
                try:
                    res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            image,
                            "Geef een JSON lijst van alle gekochte producten op deze kassabon terug. Bijvoorbeeld: [\"Melk\", \"Brood\", \"Kaas\"].",
                        ],
                        config={"response_mime_type": "application/json"},
                    )
                    items = parse_json_veilig(res.text)
                    if isinstance(items, list):
                        for it in items:
                            voeg_boodschap_toe(str(it))
                        st.success(
                            f"Oink! {len(items)} producten van de bon opgeslagen!"
                        )
                    else:
                        st.warning("Kon geen producten herkennen.")
                except Exception as e:
                    st.error(f"Fout bij scannen: {e}")

# ==========================================
# SUBPAGINA: KIDS (MINI-DISCO)
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("⬅️ Terug naar Home", key="back_kids"):
        ga_naar("Home")

    st.markdown("### 🎵 Mini-Disco met Boris")
    st.write("Feestje voor Tygo & Duén!")

    if st.button("🎉 Start de Disco!", key="start_disco"):
        st.balloons()
        st.markdown(
            "<h1 style='text-align: center;'>🐷🎶 Oink Oink Dansfeest! 🎈</h1>",
            unsafe_allow_html=True,
        )

# ==========================================
# SUBPAGINA: CHAT MET BORIS
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("⬅️ Terug naar Home", key="back_chat"):
        ga_naar("Home")

    st.markdown("### 💬 Chat met Boris")

    if user_input := st.chat_input("Stel een vraag aan Boris..."):
        st.write(f"**Jij:** {user_input}")
        with st.spinner("Boris denkt na..."):
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{GEZIN_CONTEXT}\nVraag: {user_input}",
            )
            st.write(f"**Boris:** {res.text}")
            st.components.v1.html(
                genereer_tts_script(res.text, auto_play=True), height=50
            )

else:
    ga_naar("Home")
