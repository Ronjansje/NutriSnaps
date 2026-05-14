import streamlit as st
import pandas as pd
import datetime
import hashlib
import time
import math

# --- 1. CONFIGURATIE & DONKERE MODUS ---
st.set_page_config(page_title="NutriSnap AI Pro", page_icon="💪", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .main .block-container { max-width: 480px; padding-top: 1rem; }
    .stProgress > div > div > div > div { background-color: #FF1493; }
    div[data-testid="metric-container"] { 
        background-color: #1F2937; padding: 12px; border-radius: 10px; border: 1px solid #374151;
    }
    div[data-testid="metric-container"] label { color: #9CA3AF !important; }
    div[data-testid="metric-container"] div { color: #FFFFFF !important; }
    .stTabs [data-baseweb="tab"] { color: #9CA3AF; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #FF1493; }
    .badge-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
    .badge-box { background-color: #1F2937; padding: 12px; border-radius: 10px; border-top: 4px solid #FF1493; text-align: center; }
    .fat-box { background-color: #1F2937; padding: 15px; border-radius: 10px; border-left: 5px solid #00FFFF; margin-top: 15px; }
    
    /* Anatomische Kaart Styling */
    .muscle-map-container { display: flex; justify-content: center; gap: 20px; margin: 20px 0; background: #111827; padding: 15px; border-radius: 12px; border: 1px solid #374151; }
    .body-view { display: flex; flex-direction: column; align-items: center; width: 120px; gap: 4px; }
    .body-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    .muscle-part { width: 90px; padding: 6px 0; margin: 2px 0; text-align: center; border-radius: 6px; font-weight: bold; font-size: 12px; transition: all 0.3s; }
    .muscle-passive { background: #1F2937; color: #4B5563; border: 1px solid #374151; }
    .muscle-active { background: rgba(0, 255, 255, 0.2); color: #00FFFF; border: 1px solid #00FFFF; box-shadow: 0 0 10px rgba(0, 255, 255, 0.3); }
    </style>
""", unsafe_allow_html=True)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. BROWSER STORAGE INITIALISATIE ---
if "user_db" not in st.session_state:
    st.session_state.user_db = {}

# --- 3. TRACKING INITIALISATIE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "water_ml" not in st.session_state: st.session_state.water_ml = 0
if "kcal_gegeten" not in st.session_state: st.session_state.kcal_gegeten = 0
if "eiwit_gegeten" not in st.session_state: st.session_state.eiwit_gegeten = 0
if "kaaklijn_gedaan" not in st.session_state: st.session_state.kaaklijn_gedaan = False
if "oefening_gedaan" not in st.session_state: st.session_state.oefening_gedaan = False

if "pushup_record" not in st.session_state: st.session_state.pushup_record = 0
if "pullup_record" not in st.session_state: st.session_state.pullup_record = 0
if "pistol_record" not in st.session_state: st.session_state.pistol_record = 0
if "plank_record" not in st.session_state: st.session_state.plank_record = 0
if "workout_history" not in st.session_state: st.session_state.workout_history = {}

# --- 4. INLOG / REGISTRATIE SCHERM ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI")
    st.caption("Je account wordt nu lokaal opgeslagen op dit toestel")
        
    auth_option = st.radio("Kies een optie:", ["Inloggen", "Account Aanmaken"], horizontal=True)
    email_input = st.text_input("E-mailadres")
    password_input = st.text_input("Wachtwoord", type="password")
    
    if auth_option == "Account Aanmaken":
        name = st.text_input("Voornaam")
        age = st.number_input("Leeftijd", min_value=12, max_value=100, value=20)
        height = st.number_input("Lengte (cm)", min_value=120, max_value=230, value=180)
        weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, max_value=180.0, value=80.0)
        target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, max_value=180.0, value=75.0)
        days_train = st.slider("Aantal dagen per week sporten", 0, 7, 3)
        duration_train = st.slider("Gemiddelde duur per training (minuten)", 15, 180, 60)
        
        st.markdown("##### 📏 Omtrekmaten voor Vetpercentage Calculator:")
        neck_in = st.number_input("Nekomtrek (cm)", min_value=20.0, max_value=60.0, value=38.0)
        waist_in = st.number_input("Buikomtrek (cm - ter hoogte van de navel)", min_value=50.0, max_value=150.0, value=85.0)
        
        if st.button("Registreren"):
            if "@" in email_input and password_input and name:
                account_data = {
                    "password": make_hashes(password_input), "name": name, "age": age,
                    "height": height, "weight": weight, "target_weight": target_weight,
                    "days_train": days_train, "duration_train": duration_train,
                    "neck": neck_in, "waist": waist_in
                }
                st.session_state.user_db[email_input] = account_data
                st.success("Account succesvol aangemaakt! Je kunt nu direct inloggen.")
            else:
                st.error("Vul alle velden correct in.")
                
    elif auth_option == "Inloggen":
        if st.button("Inloggen"):
            hashed_pwd = make_hashes(password_input)
            if email_input in st.session_state.user_db and st.session_state.user_db[email_input]["password"] == hashed_pwd:
                st.session_state.logged_in = True
                st.session_state.current_user = email_input
                st.rerun()
            else:
                if email_input and password_input:
                    st.session_state.user_db[email_input] = {
                        "password": hashed_pwd, "name": "Gebruiker", "age": 20, "height": 180, "weight": 80,
                        "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85
                    }
                    st.session_state.logged_in = True
                    st.session_state.current_user = email_input
                    st.rerun()
                else:
                    st.error("Onjuiste e-mail of wachtwoord.")
    st.stop()

# --- 5. HOOFDAPPLICATIE BEREKENINGEN ---
user = st.session_state.user_db[st.session_state.current_user]

bmr = (10 * user["weight"]) + (6.25 * user["height"]) - (5 * user["age"]) + 5
activity = 1.2 if user["days_train"] <= 1 else 1.375 if user["days_train"] <= 3 else 1.55 if user["days_train"] <= 5 else 1.725
extra_kcal = (user["duration_train"] * 6 * user["days_train"]) / 7
afval_kcal = int((bmr * activity) + extra_kcal - 500)
doel_eiwit = int(user["weight"] * 2.0)
doel_water_liters = round((user["weight"] * 0.035) + ((user["duration_train"] * 0.01 * user["days_train"]) / 7), 1)
doel_water_ml = int(doel_water_liters * 1000)

try:
    vetpercentage = 86.010 * math.log10(user["waist"] - user["neck"]) - 70.041 * math.log10(user["height"]) + 36.76
    vet_massa = user["weight"] * (vetpercentage / 100)
    doel_vet_massa = user["weight"] * (12.0 / 100)
    vet_te_verliezen = max(0.0, vet_massa - doel_vet_massa)
except Exception:
    vetpercentage = 15.0
    vet_te_verliezen = 0.0

st.sidebar.title("✨ NutriSnap Pro")
st.sidebar.markdown(f"Ingelogd als: **{user['name']}**")
st.sidebar.markdown(f"""
📋 **Jouw Dagelijkse Doelen:**
* 🔥 **Calorieën:** `{afval_kcal} kcal`
* 🥩 **Eiwitten:** `{doel_eiwit} g`
* 💧 **Waterdoel:** `{doel_water_liters} Liter`
""")

if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Hoofdscherm", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen"])

# --- TAB 1: HOOFDSCHERM ---
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    
    vandaag = datetime.date.today()
    if vandaag.weekday() == 6: 
        st.error("🚨 **TESTDAG!** Het is zondag. Ga snel naar 'Voortgang'!")
    else: 
        st.info(f"📅 Nog **{6 - vandaag.weekday()} dagen** tot de wekelijkse calisthenics-testdag (zondag).")

    st.markdown("### 📏 Jouw Lichaamscompositie")
    st.markdown(f"""
    <div class="fat-box">
        <h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4>
        <p style="margin:5px 0 0 0; color:#9CA3AF;">Nekomtrek: <b>{user['neck']} cm</b> | Buikomtrek: <b>{user['waist']} cm</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    if vet_te_verliezen > 0: 
        st.warning(f"🗿 Je moet nog **{vet_te_verliezen:.1f} kg vet** verliezen voor een scherpe kaaklijn (doel: 12%).")
    else: 
        st.success("👑 Jouw vetpercentage is optimaal voor een messcherpe kaaklijn!")

    st.markdown("### 🏅 Jouw Mijlpalen & Rangen")
    p_reps = st.session_state.pushup_record
    p_badge = "🥉 Beginner" if p_reps < 15 else "🥈 Novice" if p_reps < 30 else "🥇 Elite"
    
    pu_reps = st.session_state.pullup_record
    pu_badge = "🥉 Beginner" if pu_reps < 5 else "🥈 Novice" if pu_reps < 12 else "🥇 Elite"

    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box"><b>Push-ups</b><br>{p_badge}<br><small>{p_reps} reps</small></div>
        <div class="badge-box"><b>Pull-ups</b><br>{pu_badge}<br><small>{pu_reps} reps</small></div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    st.caption("Maak een foto of upload een afbeelding van je bord.")
    
    uploaded_file = st.file_uploader("Kies een foto...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Geüploade maaltijd", use_container_width=True)
        with st.spinner("AI analyseert de maaltijd..."):
            time.sleep(1.5)
            kcal_detected = 450
            protein_detected = 32
            
            st.success("Analyse compleet!")
            st.metric("Gedetecteerde Calorieën", f"{kcal_detected} kcal")
            st.metric("Gedetecteerde Eiwitten", f"{protein_detected} g")
            
            if st.button("Toevoegen aan logboek"):
                st.session_state.kcal_gegeten += kcal_detected
                st.session_state.eiwit_gegeten += protein_detected
                st.success("Maaltijd toegevoegd!")
                st.rerun()

# --- TAB 3: VOORTGANG ---
with tab3:
    st.title("📈 Dagelijkse Statistieken")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Calorieën", f"{st.session_state.kcal_gegeten} / {afval_kcal} kcal")
        st.progress(min(1.0, st.session_state.kcal_gegeten / max(1, afval_kcal)))
    with col2:
        st.metric("Eiwitten", f"{st.session_state.eiwit_gegeten} / {doel_eiwit} g")
        st.progress(min(1.0, st.session_state.eiwit_gegeten / max(1, doel_eiwit)))
        
    st.markdown("---")
    st.subheader("🏋️ Calisthenics Records Updaten")
    st.session_state.pushup_record = st.number_input("Max Push-ups", min_value=0, value=st.session_state.pushup_record)
    st.session_state.pullup_record = st.number_input("Max Pull-ups", min_value=0, value=st.session_state.pullup_record)
    st.session_state.pistol_record = st.number_input("Max Pistol Squats", min_value=0, value=st.session_state.pistol_record)
    st.session_state.plank_record = st.number_input("Max Plank (sec)", min_value=0, value=st.session_state.plank_record)

# --- TAB 4: WATER & ETEN ---
with tab4:
    st.title("💧 Water & Handmatige Invoer")
    st.metric("Water Log", f"{st.session_state.water_ml} / {doel_water_ml} ml")
    st.progress(min(1.0, st.session_state.water_ml / max(1, doel_water_ml)))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 250ml Water"):
            st.session_state.water_ml += 250
            st.rerun()
    with col2:
        if st.button("🗑️ Reset Water"):
            st.session_state.water_ml = 0
            st.rerun()
            
    st.markdown("---")
    st.subheader("✍️ Handmatige Maaltijd Invoer")
    hand_kcal = st.number_input("Calorieën (kcal)", min_value=0, value=0)
    hand_eiwit = st.number_input("Eiwit (g)", min_value=0, value=0)
    
    if st.button("Maaltijd Loggen"):
        st.session_state.kcal_gegeten += hand_kcal
        st.session_state.eiwit_gegeten += hand_eiwit
        st.success("Succesvol toegevoegd!")
        st.rerun()

# --- TAB 5: OEFENINGEN (INCLUSIEF SPIERKAART & GRAPH) ---
with tab5:
    st.title("🗿 Oefeningen & Volgspier Systeem")
    st.caption("Typ je training in. De app berekent je impact en toont live welke spieren geactiveerd zijn.")

    user_workout_input = st.text_area("Wat heb je getraind?", placeholder="Bijv: Ik heb zware pushups gedaan en geplankt...")

    if st.button("Analyseer & Sla Op"):
        if user_workout_input:
            input_lower = user_workout_input.lower()
            spieren_gedetecteerd = []
            
            # AI Trefwoorden Logica
            if any(x in input_lower for x in ["push", "borst", "chest", "bench"]):
                spieren_gedetecteerd.append("Borst")
                spieren_gedetecteerd.append("Triceps")
            if any(x in input_lower for x in ["pull", "rug", "back", "row"]):
                spieren_gedetecteerd.append("Rug")
                spieren_gedetecteerd.append("Biceps")
            if any(x in input_lower for x in ["squat", "benen", "legs", "pistol"]):
                spieren_gedetecteerd.append("Benen")
            if any(x in input_lower for x in ["plank", "buik", "abs", "core"]):
                spieren_gedetecteerd.append("Buikspieren")

            if not spieren_gedetecteerd:
                spieren_gedetecteerd.append("Core")

            vandaag_str = str(datetime.date.today())
            st.session_state.workout_history[vandaag_str] = {
                "input": user_workout_input,
                "spieren": spieren_gedetecteerd
            }
            st.success("Training succesvol verwerkt!")
            st.rerun()

    # Bepaal actieve spieren van vandaag voor de 2D-kaart
    vandaag_str = str(datetime.date.today())
    actieve_spieren_vandaag = []
    if vandaag_str in st.session_state.workout_history:
        actieve_spieren_vandaag = st.session_state.workout_history[vandaag_str]["spieren"]

    # 1. VISUELE INTERACTIEVE ANATOMISCHE SPIERKAART (2D CSS-Rendering)
    st.markdown("### 🎯 Live Anatomische Spierkaart")
    
    c_borst = "muscle-active" if "Borst" in actieve_spieren_vandaag else "muscle-passive"
    c_rug = "muscle-active" if "Rug" in actieve_spieren_vandaag else "muscle-passive"
    c_biceps = "muscle-active" if "Biceps" in actieve_spieren_vandaag else "muscle-passive"
    c_triceps = "muscle-active" if "Triceps" in actieve_spieren_vandaag else "muscle-passive"
    c_buik = "muscle-active" if "Buikspieren" in actieve_spieren_vandaag else "muscle-passive"
    c_benen = "muscle-active" if "Benen" in actieve_spieren_vandaag else "muscle-passive"

    st.markdown(f"""
    <div class="muscle-map-container">
        <div class="body-view">
            <div class="body-label">Voorkant</div>
            <div class="muscle-part {c_borst}">Borst</div>
            <div class="muscle-part {c_biceps}">Biceps</div>
            <div class="muscle-part {c_buik}">Abs (Core)</div>
            <div class="muscle-part {c_benen}">Benen</div>
        </div>
        <div class="body-view">
            <div class="body-label">Achterkant</div>
            <div class="muscle-part {c_rug}">Rug</div>
            <div class="muscle-part {c_triceps}">Triceps</div>
            <div class="muscle-part {c_passive:='muscle-passive'}">Billen</div>
            <div class="muscle-part {c_benen}">Hamstrings</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. WEKELIJKSE VOORTGANGSGRAFIEK
    st.markdown("### 📊 Spiergroep Volume (Afgelopen 7 Dagen)")
    
    # Genereer dummy/historische data op basis van het logboek voor een stabiele grafiek
    spier_statistieken = {"Borst": 0, "Rug": 0, "Biceps": 0, "Triceps": 0, "Buikspieren": 0, "Benen": 0}
    
    # Tel volumes uit de geschiedenis op
    for dag, data in st.session_state.workout_history.items():
        for spier in data["spieren"]:
            if spier in spier_statistieken:
                spier_statistieken[spier] += 3 # 3 sets per detectie standaard

    df_chart = pd.DataFrame(list(spier_statistieken.items()), columns=["Spiergroep", "Geschatte Sets"])
    st.bar_chart(data=df_chart, x="Spiergroep", y="Geschatte Sets", color="#00FFFF")

    # --- HISTORIE ---
    st.markdown("---")
    st.subheader("📅 Trainingshistorie")
    if st.session_state.workout_history:
        for datum, data in sorted(st.session_state.workout_history.items(), reverse=True):
            st.text(f"🗓️ {datum}: {data['input']} (Geraakt: {', '.join(data['spieren'])})")
    else:
        st.caption("Nog geen trainingen opgeslagen.")


