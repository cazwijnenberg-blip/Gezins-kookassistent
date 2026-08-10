# --- STYLING (EXTREEM COMPACT VOOR MOBIEL) ---
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }

    /* Scherm vullen zonder horizontale scrollbar */
    .main, .block-container {
        max-width: 100% !important;
        padding: 0.4rem 0.4rem !important;
        overflow-x: hidden !important;
    }
    
    /* Dwing de kolommen af om altijd exact 50/50 te verdelen op mobiel */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
        margin-bottom: 6px !important;
    }
    
    div[data-testid="column"], div[data-testid="stColumn"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 50% !important;
        max-width: 50% !important;
    }

    /* Knoppen Stijl: Zeer compacte tegels */
    .stButton > button {
        width: 100% !important;
        height: 60px !important;
        min-height: 60px !important;
        max-height: 60px !important;
        border-radius: 12px !important;
        background: linear-gradient(145deg, #f0f7f2, #e1efe4) !important;
        color: #1B4D2E !important;
        border: 1px solid #d0e5d4 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        white-space: pre-wrap !important;
        padding: 2px 4px !important;
        line-height: 1.1 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }

    .stButton > button p {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 0.75rem !important;
    }

    .stButton > button:hover, .stButton > button:active {
        transform: scale(0.97) !important;
        background: linear-gradient(145deg, #e1efe4, #d0e5d4) !important;
        border-color: #2E7D32 !important;
        color: #0E331A !important;
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
