# --- 🏠 HOME ---
if pagina == "🏠 Home":
    
    # 1. DIRECTE DIRECTE LINK NAAR NGW-GEHOST AFBEELDINGSBESTAND
    # Mocht de online link ooit offline gaan, pakt hij de lokale boris.png
    ONLINE_BORIS_URL = "https://i.ibb.co/6R2S8h2/boris-pig.jpg"  # Direct werkende afbeeldingslink
    
    if os.path.exists("boris.png"):
        IMAGE_SRC = f"data:image/png;base64,{get_image_base64('boris.png')}"
    else:
        IMAGE_SRC = ONLINE_BORIS_URL

    # Begroetingen
    begroetingen = [
        "Hey familie Zwijnenberg! Oink! Waar kan ik jullie vandaag mee helpen?",
        "Oink oink! Welkom thuis Chiel, Angelica, Tygo en Duen! Wat gaan we doen vandaag?",
        "Goedendag Zwijnenbergjes! Boris staat voor jullie klaar. Wat staat er op het programma?",
        "Oink! Hallo allemaal! Hebben we nog boodschappen of afspraken voor de lijst?",
        "Hey Zwijnenberg! Fijn dat jullie er zijn. Waar kan ik mijn snuit vandaag in steken?"
    ]
    
    if "huidige_begroeting" not in st.session_state:
        st.session_state["huidige_begroeting"] = random.choice(begroetingen)

    gekozen_tekst = st.session_state["huidige_begroeting"]
    schone_begroeting = gekozen_tekst.replace("'", "").replace('"', '').replace('\n', ' ')

    # Boris Afbeelding & Visualisatie direct bovenaan (ZONDER de titel)
    st.markdown(f"""
        <div class="boris-avatar-container" style="margin-top: 10px;">
            <img src="{IMAGE_SRC}" id="boris-main-img" class="boris-img boris-img-talking" alt="Boris het Gezinszwijn" style="width: 100%; max-width: 500px; border-radius: 15px;">
            <h3 style="margin: 15px 0 0 0; color: #e65100;">"{gekozen_tekst}"</h3>
            <p style="color: #666; margin-top: 5px; font-size: 14px;">- Boris, jullie virtuele huiszwijn</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Auto-play Audio Script
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
    
    # 2. CHAT MET BORIS
    st.subheader("💬 Vraag het aan Boris")
    
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    for idx, msg in enumerate(st.session_state["chat_messages"]):
        avatar = "🐗" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
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

    if user_prompt := st.chat_input("Zeg bijvoorbeeld: 'Zet melk op de lijst' of 'Zet morgen zwemmen in de agenda'..."):
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"):
            st.write(user_prompt)
        
        with st.chat_message("assistant", avatar="🐗"):
            with st.spinner("Boris knikt en antwoordt... 🐗💭"):
                
                prompt = f"""
                {GEZIN_CONTEXT}
                Vandaag is {datetime.date.today().strftime('%Y-%m-%d')}.
                
                Bericht van gebruiker: "{user_prompt}"
                
                Geef een JSON-reactie in exact dit formaat:
                {{
                    "actie": "boodschap_toevoegen" of "agenda_toevoegen" of "geen",
                    "boodschap": "naam van item of leeg",
                    "agenda_datum": "YYYY-MM-DD",
                    "agenda_beschrijving": "omschrijving of leeg",
                    "antwoord": "Korte vrolijke reactie van Boris aan de familie"
                }}
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config={'response_mime_type': 'application/json'}
                    )
                    
                    data = json.loads(response.text)
                    
                    actie_melding = ""
                    if data.get("actie") == "boodschap_toevoegen" and data.get("boodschap"):
                        voeg_boodschap_toe(data["boodschap"])
                        actie_melding = f"\n\n*(✅ '{data['boodschap']}' toegevoegd aan het boodschappenlijstje!)*"
                    
                    elif data.get("actie") == "agenda_toevoegen" and data.get("agenda_beschrijving"):
                        datum_str = data.get("agenda_datum") or datetime.date.today().strftime("%Y-%m-%d")
                        voeg_agenda_toe(datum_str, data["agenda_beschrijving"])
                        actie_melding = f"\n\n*(🗓️ '{data['agenda_beschrijving']}' op {datum_str} in de agenda gezet!)*"

                    eind_antwoord = data.get("antwoord", "Oink! Ik heb het voor je geregeld!") + actie_melding
                    
                except Exception:
                    eind_antwoord = "Oink! Ik luister naar je!"

                st.write(eind_antwoord)
                st.session_state["chat_messages"].append({"role": "assistant", "content": eind_antwoord})
                st.session_state["huidige_begroeting"] = random.choice(begroetingen)
                st.rerun()

    st.markdown("---")

    # Overzicht binnenkort & Boodschappen
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Binnenkort")
        agenda_data = st.session_state["gezin_data"].get("agenda", [])
        komende_items = []
        for item in agenda_data:
            try:
                d_obj = datetime.datetime.strptime(str(item["datum"]), "%Y-%m-%d").date()
                if d_obj >= vandaag:
                    komende_items.append({"datum": d_obj, "beschrijving": item["beschrijving"]})
            except ValueError:
                pass
        
        gesorteerd = sorted(komende_items, key=lambda x: x["datum"])[:3]
        if gesorteerd:
            for item in gesorteerd:
                st.markdown(f"🗓️ **{item['datum'].strftime('%d-%m-%Y')}**: {item['beschrijving']}")
        else:
            st.write("Geen directe afspraken in de planning.")

    with col2:
        st.subheader("🛒 Boodschappen")
        boodschappen_lijst = st.session_state["gezin_data"].get("boodschappen", [])
        if boodschappen_lijst:
            st.write(f"Er staan momenteel **{len(boodschappen_lijst)} items** op de lijst.")
        else:
            st.write("De boodschappenlijst is helemaal leeg! 👍")
