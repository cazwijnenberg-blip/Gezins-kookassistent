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

# --- 1. PAGINA CONFIGURATIE (Moet bovenaan) ---
st.set_page_config(
    page_title="Zwijnenberg Home Assist",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- 2. ROUTING & STATE ---
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


# --- 3. API KEY CHECK ---
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


# --- 4. STYLING (MOBIEL COMPACT & WEERGAVE-FIX) ---
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }

    .block-container {
        padding: 0.8rem 0.5rem !important;
        max-width: 100% !important;
    }
    
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
    }
    
    div[data-testid="column"], div[data-testid="stColumn"] {
        flex: 1 1 50% !important;
        min-width: 0 !important;
        width: 50% !important;
    }

    .stButton > button {
        width: 100% !important;
        min-height: 65px !important;
        border-radius: 12px !important;
        background: linear-gradient(145deg, #f0f7f2, #e1efe4) !important;
        color: #1B4D2E !important;
        border: 1px solid #d0e5d4 !important;
        font-size: 0.8rem !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 4px !important;
        margin-bottom: 4px !important;
    }

    .stButton > button:hover, .stButton > button:active {
        background: linear-gradient(145deg, #e1efe4, #d0e5d4) !important;
        color: #0E331A !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 5. DATA BEHEER ---
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
huidige_pagina = st.session_state.get("huidige_pagina", "Home")

GEZIN_CONTEXT = (
    "Je bent Boris, de virtuele assistent van gezin Zwijnenberg: "
    "Chiel, Angelica, Tygo (3 jaar) en Duén (1 jaar) uit Luttenberg. "
    "Spreek vrolijk en eindig vaak met 'Oink!'."
)


def voeg_boodschap_toe(item):
    item_schoon = item.strip().capitalize()
    if not item_schoon:
        return
    if item_schoon not in st.session_state["gezin_data"]["boodschappen"]:
        st.session_state["gezin_data"]["boodschappen"].append(item_schoon)
    sla_data_op(st.session_state["gezin_data"])


# ==========================================
# HOOFDSCHERM & SUBPAGINA ROUTING
# ==========================================

if huidige_pagina == "Home":
    st.markdown("### 🐷 Zwijnenberg Assist")

    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken = len(st.session_state["gezin_data"]["agenda"])

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if st.button("💬\nChat Boris", key="btn_chat"):
            ga_naar("Chat")
    with r1c2:
        if st.button(f"📅\nAgenda ({aantal_afspraken})", key="btn_agenda"):
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

elif huidige_pagina == "Chat":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 💬 Chat met Boris")
    if user_input := st.chat_input("Vraag iets aan Boris..."):
        st.write(f"**Jij:** {user_input}")
        with st.spinner("Boris denkt na..."):
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{GEZIN_CONTEXT}\n{user_input}",
            )
            st.write(f"**Boris:** {res.text}")

elif huidige_pagina == "Agenda":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 📅 Agenda")
    for item in st.session_state["gezin_data"].get("agenda", []):
        st.write(f"- **{item.get('datum')}**: {item.get('beschrijving')}")

elif huidige_pagina == "Boodschappenlijst":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🛒 Boodschappenlijst")
    boodschappen = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen:
        for b in boodschappen:
            st.write(f"- {b}")
    else:
        st.info("Je boodschappenlijstje is leeg!")

elif huidige_pagina == "Weekmenu":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🍽️ Weekmenu")
    st.write("Genereer of bekijk het menu voor deze week.")

elif huidige_pagina == "Dagschema":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🎯 Dagschema")
    for t in st.session_state["gezin_data"].get("dagschema", []):
        st.checkbox(t.get("taak"), value=t.get("klaar", False))

elif huidige_pagina == "Activiteiten":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🌳 Uitjes & Activiteiten")
    st.write("Leuke uitjes voor Tygo (3) en Duén (1) rondom Luttenberg.")

elif huidige_pagina == "Gezondheid":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 💊 Gezondheid")
    for g in st.session_state["gezin_data"].get("gezondheid", []):
        st.write(f"- {g}")

elif huidige_pagina == "Huishoud":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🧹 Huishouden")
    for h in st.session_state["gezin_data"].get("huishoud", []):
        st.checkbox(
            f"[{h.get('dag')}] {h.get('taak')}", value=h.get("status", False)
        )

elif huidige_pagina == "Recepten":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🔍 Recepten Zoeken")
    st.write("Bedenk wat je wilt koken op basis van je koelkastinhoud.")

elif huidige_pagina == "Kassabon Scanner":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🧾 Kassabon Scanner")
    st.file_uploader(
        "Upload een foto van een kassabon", type=["jpg", "png", "jpeg"]
    )

elif huidige_pagina == "Kids":
    if st.button("🔙 Terug naar Home"):
        ga_naar("Home")
    st.markdown("### 🎵 Mini-Disco")
    if st.button("🎉 Dansen!"):
        st.balloons()
        st.markdown(
            "<h1 style='text-align: center;'>🐷🎶 Oink Oink!</h1>",
            unsafe_allow_html=True,
        )

else:
    ga_naar("Home")
