import streamlit as str_module
import streamlit as st
from google import genai
import datetime
import calendar
import json
import os
import re

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Zwijnenberg Home Assist", 
    page_icon="🐷", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BROWSER HISTORY & ROUTING ---
query_pagina = st.query_params.get("pagina", "Home")
if "huidige_pagina" not in st.session_state or st.session_state["huidige_pagina"] != query_pagina:
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
    st.error("🚨 Kan de API-sleutel niet vinden. Zorg voor een `.streamlit/secrets.toml` bestand met `GEMINI_API_KEY`.")
    st.stop()

def parse_json_veilig(tekst):
    try:
        m = re.search(r'\{.*\}', tekst, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(tekst)
    except Exception:
        return None

# --- STYLING (ALGEMEEN & MOBAIR VRIENDELIJK) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }

    body, html, .main, .block-container {
        max-width: 100vw !important;
        width: 100% !important;
        padding-left: 8px !important;
        padding-right: 8px !important;
        padding-top: 10px !important;
        padding-bottom: 20px !important;
        overflow-x: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA BEHEER ---
DATA_BESTAND = "gezin_data.json"

def laad_data():
    if os.path.exists(DATA_BESTAND):
        try:
            with open(DATA_BESTAND, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "boodschappen_historie" not in data: data["boodschappen_historie"] = {}
                if "agenda" not in data: data["agenda"] = []
                if "boodschappen" not in data: data["boodschappen"] = []
                if "weekmenu" not in data: data["weekmenu"] = {}
                if "dagschema" not in data: 
                    data["dagschema"] = [
                        {"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False},
                        {"taak": "👕 Aankleden", "tijd": "Ochtend", "klaar": False},
                        {"taak": "🥣 Ontbijten", "tijd": "Ochtend", "klaar": False},
                        {"taak": "🛏️ Pyjama aan", "tijd": "Avond", "klaar": False},
                        {"taak": "📚 Verhaaltje lezen", "tijd": "Avond", "klaar": False}
                    ]
                if "gezondheid" not in data: data["gezondheid"] = []
                if "huishoud" not in data: 
                    data["huishoud"] = [
                        {"taak": "🗑️ Grijze container aan straat", "dag": "Maandag", "status": False},
                        {"taak": "♻️ Gft-bak buiten zetten", "dag": "Donderdag", "status": False},
                        {"taak": "🧽 Vaatwasser filter schoonmaken", "dag": "Zaterdag", "status": False},
                        {"taak": "🛏️ Bedden verschonen", "dag": "Zondag", "status": False}
                    ]
                return data
        except Exception:
            pass
            
    standaard_data = {
        "agenda": [
            {"datum": "2026-04-22", "beschrijving": "💍 Trouwdag Chiel & Angelica"},
            {"datum": "2026-06-11", "beschrijving": "🎂 Verjaardag Duén (1 jr)"},
            {"datum": "2026-10-24", "beschrijving": "🎂 Verjaardag Tygo (3 jr)"}
        ],
        "boodschappen": [],
        "boodschappen_historie": {},
        "weekmenu": {},
        "dagschema": [
            {"taak": "🦷 Tanden poetsen", "tijd": "Ochtend", "klaar": False},
            {"taak": "👕 Aankleden", "tijd": "Ochtend", "klaar": False},
            {"taak": "🥣 Ontbijten", "tijd": "Ochtend", "klaar": False},
            {"taak": "🛏️ Pyjama aan", "tijd": "Avond", "klaar": False},
            {"taak": "📚 Verhaaltje lezen", "tijd": "Avond", "klaar": False}
        ],
        "gezondheid": [],
        "huishoud": [
            {"taak": "🗑️ Grijze container aan straat", "dag": "Maandag", "status": False},
            {"taak": "♻️ Gft-bak buiten zetten", "dag": "Donderdag", "status": False},
            {"taak": "🧽 Vaatwasser filter schoonmaken", "dag": "Zaterdag", "status": False},
            {"taak": "🛏️ Bedden verschonen", "dag": "Zondag", "status": False}
        ]
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
if "kalender_jaar" not in st.session_state: st.session_state["kalender_jaar"] = vandaag.year
if "kalender_maand" not in st.session_state: st.session_state["kalender_maand"] = vandaag.month

def voeg_agenda_toe(datum, beschrijving):
    st.session_state["gezin_data"]["agenda"].append({"datum": str(datum), "beschrijving": beschrijving})
    sla_data_op(st.session_state["gezin_data"])

def verwijder_agenda_item(index):
    if 0 <= index < len(st.session_state["gezin_data"]["agenda"]):
        st.session_state["gezin_data"]["agenda"].pop(index)
        sla_data_op(st.session_state["gezin_data"])

def voeg_boodschap_toe(item):
    item_schoon = item.strip().capitalize()
    if not item_schoon: return
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
    if not tekst: return
    try:
        prompt = f"Splits de volgende tekst op in losse boodschappen. Geef enkel een JSON lijst van strings terug, bijv: [\"Melk\", \"Brood\"]. Tekst: '{tekst}'"
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt, 
            config={'response_mime_type': 'application/json'}
        )
        items = json.loads(res.text)
        if isinstance(items, list):
            for item in items:
                voeg_boodschap_toe(str(item))
            return
    except Exception:
        pass
    
    delen = re.split(r',|\sen\s|\splus\s|\sen ook\s', tekst, flags=re.IGNORECASE)
    for d in delen:
        voeg_boodschap_toe(d)

def verwijder_boodschappen_op_index(indices_om_te_verwijderen):
    huidige = st.session_state["gezin_data"].get("boodschappen", [])
    nieuwe_lijst = [item for i, item in enumerate(huidige) if i not in indices_om_te_verwijderen]
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
# HOOFDSCHERM (ANDROID APP LAUNCHER GRID)
# ==========================================
if st.session_state["huidige_pagina"] == "Home":
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    aantal_boodschappen = len(st.session_state["gezin_data"]["boodschappen"])
    aantal_afspraken_komend = len([a for a in st.session_state["gezin_data"]["agenda"] if a.get("datum", "") >= vandaag_str])

    col_titel, col_datum = st.columns([3, 1])
    with col_titel:
        st.markdown("### 🏠 Zwijnenberg")
    with col_datum:
        st.markdown(f"<p style='text-align: right; font-size: 11px; color: #aaa; margin-top: 5px;'>{vandaag.strftime('%d-%m-%Y')}</p>", unsafe_allow_html=True)
    
    dashboard_knoppen = [
        ("💬", "Chat", "Chat"),
        ("📅", f"Agenda ({aantal_afspraken_komend})", "Agenda"),
        ("🛒", f"Lijst ({aantal_boodschappen})", "Boodschappenlijst"),
        ("🍽️", "Menu", "Weekmenu"),
        ("🎯", "Schema", "Dagschema"),
        ("🧹", "Klusjes", "Huishoud"),
        ("💊", "Zorg", "Gezondheid"),
        ("🎵", "Disco", "Kids")
    ]

    # Echte Android app-grid styling en opbouw via HTML/CSS (geen breekbare st.columns)
    app_grid_html = """
    <style>
    .android-app-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-top: 10px;
        width: 100%;
    }
    .app-tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: #EBF5EE;
        border: 1px solid #C4E0CC;
        border-radius: 12px;
        padding: 10px 4px;
        text-decoration: none !important;
        transition: transform 0.1s ease, background-color 0.1s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        height: 72px;
    }
    .app-tile:active, .app-tile:hover {
        transform: scale(0.95);
        background-color: #D6EFE0;
        border-color: #2E7D32;
    }
    .app-icon {
        font-size: 1.4rem;
        line-height: 1.1;
        margin-bottom: 2px;
    }
    .app-label {
        font-size: 0.6rem;
        color: #1B4D2E;
        text-align: center;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 100%;
    }
    </style>
    <div class="android-app-grid">
    """
    
    for icoon, tekst, pagina in dashboard_knoppen:
        app_grid_html += f"""
        <a href="?pagina={pagina}" class="app-tile">
            <span class="app-icon">{icoon}</span>
            <span class="app-label">{tekst}</span>
        </a>
        """
        
    app_grid_html += "</div>"
    st.markdown(app_grid_html, unsafe_allow_html=True)

# ==========================================
# SUBPAGINA: CHAT (MET BORIS)
# ==========================================
elif st.session_state["huidige_pagina"] == "Chat":
    if st.button("🔙 Terug"): ga_naar("Home")
    st.markdown("### 💬 Chat met Boris")
    
    if "chat_historie" not in st.session_state:
        st.session_state["chat_historie"] = [
            {"rol": "assistant", "tekst": "Oink! Hoi! Ik ben Boris, jullie huiszwijn. Waar kan ik jullie vandaag mee helpen?"}
        ]
        
    for bericht in st.session_state["chat_historie"]:
        with st.chat_message(bericht["rol"]):
            st.write(bericht["tekst"])
            
    gebruiker_input = st.chat_input("Typ je bericht aan Boris...")
    if gebruiker_input:
        st.session_state["chat_historie"].append({"rol": "user", "tekst": gebruiker_input})
        with st.chat_message("user"):
            st.write(gebruiker_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Boris denkt na... oink..."):
                try:
                    context_data = f"{GEZIN_CONTEXT}\nActuele gezin data:\nAgenda: {st.session_state['gezin_data'].get('agenda', [])}\nBoodschappen: {st.session_state['gezin_data'].get('boodschappen', [])}"
                    chat_gesprek = [context_data]
                    for b in st.session_state["chat_historie"]:
                        chat_gesprek.append(f"{b['rol']}: {b['tekst']}")
                    
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=chat_gesprek
                    )
                    antwoord = res.text
                    st.write(antwoord)
                    st.session_state["chat_historie"].append({"rol": "assistant", "tekst": antwoord})
                except Exception as e:
                    fout_melding = f"Oink... er ging iets mis: {e}"
                    st.write(fout_melding)
                    st.session_state["chat_historie"].append({"rol": "assistant", "tekst": fout_melding})

# ==========================================
# SUBPAGINA: AGENDA
# ==========================================
elif st.session_state["huidige_pagina"] == "Agenda":
    if st.button("🔙 Terug"): ga_naar("Home")
    
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
            else: st.session_state["kalender_maand"] -= 1
            st.rerun()
    with col_next:
        if st.button("Volgende ➡️"):
            if st.session_state["kalender_maand"] == 12:
                st.session_state["kalender_maand"] = 1
                st.session_state["kalender_jaar"] += 1
            else: st.session_state["kalender_maand"] += 1
            st.rerun()

    jaar = st.session_state["kalender_jaar"]
    maand = st.session_state["kalender_maand"]
    with col_title:
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{calendar.month_name[maand]} {jaar}</h3>", unsafe_allow_html=True)

    agenda_dict = {}
    for item in st.session_state["gezin_data"].get("agenda", []):
        d_str = str(item.get("datum", ""))
        if d_str not in agenda_dict: agenda_dict[d_str] = []
        agenda_dict[d_str].append(item.get("beschrijving", ""))

    cal = calendar.monthcalendar(jaar, maand)
    vandaag_str = vandaag.strftime("%Y-%m-%d")
    
    html_cal = """
    <style>
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; padding-bottom: 10px; }
    .cal-header { text-align: center; font-weight: bold; font-size: 0.7rem; padding: 2px 0; color: #aaa; }
    .cal-day { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; padding: 2px; text-align: center; min-height: 32px; display: flex; flex-direction: column; justify-content: start; align-items: center;}
    .cal-day span.date { font-weight: bold; font-size: 0.75rem; color: #ffffff !important; }
    .cal-day.vandaag { border: 2px solid #ff9800; background-color: #2c221e; }
    .cal-day.afspraak { background-color: #1c2732; border-color: #2196F3; }
    .cal-leeg { background-color: transparent; }
    .cal-badge { font-size: 0.55rem; color: #90caf9; font-weight: bold; margin-top: 1px; }
    </style>
    <div class="cal-wrapper">
    """
    for dag in ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]:
        html_cal += f"<div class='cal-header'>{dag}</div>"
        
    for week in cal:
        for dag in week:
            if dag == 0: html_cal += "<div class='cal-leeg'></div>"
            else:
                datum_str = f"{jaar}-{maand:02d}-{dag:02d}"
                cls = "cal-day"
                if datum_str == vandaag_str: cls += " vandaag"
                if datum_str in agenda_dict: cls += " afspraak"
                badge = f"<div class='cal-badge'>📌 {len(agenda_dict[datum_str])}</div>" if datum_str in agenda_dict else ""
                html_cal += f"<div class='{cls}'><span class='date'>{dag}</span>{badge}</div>"
                
    html_cal += "</div>"
    st.markdown(html_cal, unsafe_allow_html=True)
    
    st.markdown("### 📋 Alle geplande afspraken:")
    agenda_lijst = st.session_state["gezin_data"].get("agenda", [])
    if agenda_lijst:
        for idx, item in enumerate(agenda_lijst):
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"🗓️ **{item.get('datum')}**: {item.get('beschrijving')}")
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
    if st.button("🔙 Terug"): ga_naar("Home")
    
    if "actieve_hoofd_cat" not in st.session_state: st.session_state["actieve_hoofd_cat"] = None
    if "actieve_sub_cat" not in st.session_state: st.session_state["actieve_sub_cat"] = None

    supermarkt_database = {
        "AGF": {
            "Vers fruit": [("🍎", "Appels"), ("🍌", "Bananen"), ("🍓", "Bessen"), ("🍊", "Citrus")],
            "Groenten": [("🥬", "Sla"), ("🍅", "Tomaten"), ("🧅", "Uien"), ("🥕", "Wortels")],
            "Aardappel": [("🥔", "Aardappel"), ("🥔", "Krieltjes")],
            "Salades": [("🥗", "Salade"), ("🥕", "Snacks")]
        },
        "Zuivel": {
            "Melk": [("🥛", "Melk"), ("🥛", "Karnemelk"), ("🥛", "Haver")],
            "Yoghurt": [("🥣", "Yoghurt"), ("🥣", "Kwark")],
            "Kaas": [("🧀", "Jong kaas"), ("🧀", "Oud kaas"), ("🧀", "Smeerkaas")],
            "Eieren/Boter": [("🥚", "Eieren"), ("🧈", "Boter")]
        },
        "Vlees/Vis": {
            "Vlees": [("🍗", "Kip"), ("🥩", "Gehakt"), ("🥩", "Bief")],
            "Vis": [("🐟", "Zalm"), ("🐟", "Kabeljauw"), ("🦐", "Garnaal")],
            "Vega": [("🌱", "Vega"), ("🌱", "Tofu"), ("🧆", "Falafel")]
        },
        "Brood/Ontbijt": {
            "Brood": [("🍞", "Brood"), ("🥖", "Stokbrood"), ("🥐", "Croissant")],
            "Granen": [("🥣", "Muesli"), ("🥣", "Havermout")],
            "Beleg": [("🍓", "Jam"), ("🥜", "Pindakaas"), ("🍫", "Hagel"), ("🍯", "Honing")]
        },
        "Dranken": {
            "Fris/Sap": [("🥤", "Cola"), ("🥤", "Sinas"), ("💧", "Water"), ("🧃", "Sap")],
            "Koffie/Thee": [("☕", "Koffie"), ("🍵", "Thee")],
            "Alcohol": [("🍺", "Bier"), ("🍷", "Wijn")]
        },
        "Houdbaar": {
            "Pasta/Rijst": [("🍝", "Pasta"), ("🍚", "Rijst"), ("🍜", "Mie")],
            "Conserven": [("🥫", "Soep"), ("🥫", "Groente"), ("🐟", "Tonijn")],
            "Sauzen": [("🧂", "Mayo"), ("🍅", "Ketchup"), ("🫒", "Olie")]
        },
        "Snacks": {
            "Zout": [("🥔", "Chips"), ("🍿", "Popcorn"), ("🥨", "Noten")],
            "Zoet": [("🍬", "Snoep"), ("🍫", "Choco"), ("🍪", "Koek")]
        },
        "Diepvries": {
            "Diepvries": [("🍕", "Pizza"), ("🍦", "IJs"), ("🍟", "Friet"), ("🥦", "Groente")]
        },
        "Non-Food": {
            "Verzorging": [("🧴", "Shampoo"), ("🪥", "Tandpasta"), ("🧼", "Zeep")],
            "Schoonmaak": [("🧼", "Vaatwas"), ("🫧", "Wasmiddel"), ("🧻", "Wc-papier"), ("🗑️", "Zakken")]
        }
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
            sub_lijst = list(sub_dict.items())
            cols_per_rij = 4
            for i in range(0, len(sub_lijst), cols_per_rij):
                rij = sub_lijst[i:i+cols_per_rij]
                cols = st.columns(cols_per_rij)
                for j, (s_naam, items_lijst) in enumerate(rij):
                    with cols[j]:
                        ic = items_lijst[0][0] if items_lijst else "🛒"
                        if st.button(f"{ic}\n{s_naam}", key=f"subcat_btn_{i+j}", use_container_width=True):
                            st.session_state["actieve_sub_cat"] = s_naam
                            st.rerun()
        else:
            if st.button("⬅️ Terug naar subcats", key="terug_naar_subs_overzicht"):
                st.session_state["actieve_sub_cat"] = None
                st.rerun()
                
            st.markdown(f"**🏷️ {sub_cat}**")
            producten = sub_dict.get(sub_cat, [])
            
            cols_per_rij = 4
            for i in range(0, len(producten), cols_per_rij):
                rij = producten[i:i+cols_per_rij]
                cols = st.columns(cols_per_rij)
                for j, (icoon, prod_naam) in enumerate(rij):
                    with cols[j]:
                        if st.button(f"{icoon}\n{prod_naam}", key=f"prod_btn_{i+j}", use_container_width=True):
                            voeg_boodschap_toe(prod_naam)
                            st.toast(f"✅ '{prod_naam}' toegevoegd!")
                            st.rerun()

    else:
        hoofd_icoontjes = [
            ("🥦", "AGF"),
            ("🥛", "Zuivel"),
            ("🥩", "Vlees/Vis"),
            ("🥐", "Brood/Ontbijt"),
            ("🥤", "Dranken"),
            ("🥫", "Houdbaar"),
            ("🍫", "Snacks"),
            ("🍕", "Diepvries"),
            ("🧻", "Non-Food")
        ]
        
        cols_per_rij = 4
        for i in range(0, len(hoofd_icoontjes), cols_per_rij):
            rij = hoofd_icoontjes[i:i+cols_per_rij]
            cols = st.columns(cols_per_rij)
            for j, (icoon, cat_naam) in enumerate(rij):
                with cols[j]:
                    if st.button(f"{icoon}\n{cat_naam}", key=f"hoofd_cat_{i+j}", use_container_width=True):
                        st.session_state["actieve_hoofd_cat"] = cat_naam
                        st.session_state["actieve_sub_cat"] = None
                        st.rerun()

    st.markdown("---")

    with st.form("boodschap_form", clear_on_submit=True):
        col_in, col_btn = st.columns([3, 1])
        with col_in:
            nieuw_item = st.text_input("Snel toevoegen:", placeholder="Typ bijv. melk...")
        with col_btn:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("➕")
            if submit and nieuw_item:
                verwerk_meerdere_boodschappen(nieuw_item)
                st.rerun()

    st.markdown("---")
    st.markdown("#### 🛒 Actieve Lijst")
    boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
    if boodschappen_lijst:
        indices_om_te_verwijderen = []
        for idx, item in enumerate(boodschappen_lijst):
            if st.checkbox(f"🛍️ {item}", key=f"boodschap_{idx}"): 
                indices_om_te_verwijderen.append(idx)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if indices_om_te_verwijderen:
                if st.button("🗑️ Wis selectie", use_container_width=True):
                    verwijder_boodschappen_op_index(indices_om_te_verwijderen)
                    st.rerun()
        with col_v2:
            if st.button("❌ Wis alles", use_container_width=True):
                leeg_boodschappenlijst()
                st.rerun()
    else: 
        st.info("Lijstje is leeg!")

# ==========================================
# SUBPAGINA: WEEKMENU
# ==========================================
elif st.session_state["huidige_pagina"] == "Weekmenu":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🍽️ Slim Weekmenu & Boodschappen")
    st.write("Genereer een kindvriendelijk weekmenu en zet ingrediënten direct op de lijst.")
    
    if st.button("✨ Genereer nieuw weekmenu", type="primary"):
        with st.spinner("Boris stelt het menu samen..."):
            prompt = (
                f"{GEZIN_CONTEXT} Genereer een gevarieerd weekmenu voor 5 dagen (Maandag t/m Vrijdag) "
                "specifiek gericht op kindvriendelijke maaltijden (geschikt voor Tygo van 3 en Duén van 1). "
                "Geef de output terug als een JSON object met als sleutels 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', "
                "waarbij elke dag een object is met 'gerecht' (string) en 'ingredienten' (lijst van strings)."
            )
            try:
                res = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=prompt, 
                    config={'response_mime_type': 'application/json'}
                )
                menu_data = parse_json_veilig(res.text)
                if menu_data:
                    st.session_state["gezin_data"]["weekmenu"] = menu_data
                    sla_data_op(st.session_state["gezin_data"])
                    st.success("Oink! Nieuw weekmenu gegenereerd!")
                else:
                    st.error("Kon het menu niet verwerken.")
            except Exception as e:
                st.error(f"Fout: {e}")

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
        if st.button("🛒 Voeg toe aan Boodschappenlijst", type="secondary"):
            totaal_toegevoegd = 0
            for dag, info in huidig_menu.items():
                if isinstance(info, dict):
                    for ing in info.get("ingredienten", []):
                        voeg_boodschap_toe(ing)
                        totaal_toegevoegd += 1
            st.success(f"Oink! {totaal_toegevoegd} ingrediënten toegevoegd!")
    else:
        st.info("Nog geen weekmenu gegenereerd.")

# ==========================================
# SUBPAGINA: DAGSCHEMA
# ==========================================
elif st.session_state["huidige_pagina"] == "Dagschema":
    if st.button("🔙 Terug"): ga_naar("Home")
    
    st.markdown("### 🎯 Visueel Dagschema Tygo")
    st.write("Vink de routines af.")
    
    dagschema = st.session_state["gezin_data"].get("dagschema", [])
    for idx, item in enumerate(dagschema):
        status = st.checkbox(f"{item.get('taak')}", value=item.get("klaar", False), key=f"schema_{idx}")
        if status != item.get("klaar", False):
            dagschema[idx]["klaar"] = status
            sla_data_op(st.session_state["gezin_data"])

# ==========================================
# SUBPAGINA: HUISHOUD & KLUSJES
# ==========================================
elif st.session_state["huidige_pagina"] == "Huishoud":
    if st.button("🔙 Terug"): ga_naar("Home")
    st.markdown("### 🧹 Huishoudelijke Taken")
    
    huishoud_lijst = st.session_state["gezin_data"].get("huishoud", [])
    for idx, item in enumerate(huishoud_lijst):
        status = st.checkbox(f"{item.get('taak')} (*{item.get('dag')}*)", value=item.get("status", False), key=f"huis_{idx}")
        if status != item.get("status", False):
            huishoud_lijst[idx]["status"] = status
            sla_data_op(st.session_state["gezin_data"])

# ==========================================
# SUBPAGINA: GEZONDHEID & ZORG
# ==========================================
elif st.session_state["huidige_pagina"] == "Gezondheid":
    if st.button("🔙 Terug"): ga_naar("Home")
    st.markdown("### 💊 Gezondheid & Zorg (Tygo & Duén)")
    
    with st.form("gezondheid_form", clear_on_submit=True):
        notitie = st.text_input("Medische notitie / Afspraak (bijv. Tandarts, vaccinatie)")
        datum_zorg = st.date_input("Datum", vandaag)
        if st.form_submit_button("Opslaan") and notitie:
            if "gezondheid" not in st.session_state["gezin_data"]:
                st.session_state["gezin_data"]["gezondheid"] = []
            st.session_state["gezin_data"]["gezondheid"].append({"datum": str(datum_zorg), "notitie": notitie})
            sla_data_op(st.session_state["gezin_data"])
            st.success("Oink! Opgeslagen!")
            st.rerun()
            
    st.markdown("---")
    gezondheid_lijst = st.session_state["gezin_data"].get("gezondheid", [])
    if gezondheid_lijst:
        for idx, item in enumerate(gezondheid_lijst):
            st.markdown(f"🩺 **{item.get('datum')}**: {item.get('notitie')}")
    else:
        st.info("Geen medische notities aanwezig.")

# ==========================================
# SUBPAGINA: KIDS / DISCO
# ==========================================
elif st.session_state["huidige_pagina"] == "Kids":
    if st.button("🔙 Terug"): ga_naar("Home")
    st.markdown("### 🎵 Kids & Disco")
    st.info("Tijd voor feest! Zet hier straks favoriete kinderliedjes aan.")

# ==========================================
# OVERIGE PAGINA'S (FALLBACK)
# ==========================================
else:
    if st.button("🔙 Terug"): ga_naar("Home")
    st.markdown(f"### 🚧 {st.session_state['huidige_pagina']}")
    st.info("Deze pagina wordt geladen.")
