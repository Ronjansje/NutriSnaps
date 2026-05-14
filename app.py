import streamlit as st
import pandas as pd
import datetime
import hashlib
import time
import math
import json

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

if "oefening_log" not in st.session_state: st.session_state.oefening_log = []

# Records (huidige stand voor hoofdscherm)
if "pushup_record" not in st.session_state: st.session_state.pushup_record = 12
if "pullup_record" not in st.session_state: st.session_state.pullup_record = 4
if "pistol_record" not in st.session_state: st.session_state.pistol_record = 2
if "plank_record" not in st.session_state: st.session_state.plank_record = 45

# Historie logboek voor progressie diagrammen (startdata ingevuld als voorbeeld)
if "pr_history" not in st.session_state:
    st.session_state.pr_history = [
        {"Datum": "2026-04-26", "Pushups": 10, "Pullups": 3, "Pistol Squats": 1, "Plank (sec)": 30},
        {"Datum": "2026-05-03", "Pushups": 12, "Pullups": 4, "Pistol Squats": 2, "Plank (sec)": 45}
    ]

OEFENINGEN_INFO = {
    "Pushups": "Borst, Triceps, Schouders, Core",
    "Diamond Pushups": "Triceps, Borst, Schouders",
    "Pullups": "Rug, Biceps, Core",
    "Chin-ups": "Biceps, Rug, Core",
    "Pistol Squats": "Benen, Billen, Hamstrings",
    "Plank": "Core, Schouders, Onderrug",
    "Hollow Body Hold": "Core, Buikspieren"
}

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

# --- 5. HOOFDAPPLICATIE ---
user = st.session_state.user_db[st.session_state.current_user]

bmr = (10 * user["weight"]) + (6.25 * user["height"]) - (5 * user["age"]) + 5
activity = 1.2 if user["days_train"] <= 1 else 1.375 if user["days_train"] <= 3 else 1.55 if user["days_train"] <= 5 else 1.725
extra_kcal = (user["duration_train"] * 6 * user["days_train"]) / 7
afval_kcal = int((bmr * activity) + extra_kcal - 500)
doel_eiwit = int(user["weight"] * 2.0)
doel_water_liters = round((user["weight"] * 0.035) + ((user["duration_train"] * 0.01 * user["days_train"]) / 7), 1)

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
        st.error("🚨 **TESTDAG!** Het is zondag. Ga snel naar 'Voortgang' om je PR's te verbreken!")
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

    st.markdown("### 🏅 Actuele Rangen & PR's")
    p_reps = st.session_state.pushup_record
    p_badge = "🥉 Beginner" if p_reps <= 15 else "🥈 Novice" if p_reps <= 30 else "🥇 Advanced"
    
    pu_reps = st.session_state.pullup_record
    pu_badge = "🥉 Beginner" if pu_reps <= 5 else "🥈 Novice" if pu_reps <= 12 else "🥇 Advanced"
    
    pi_reps = st.session_state.pistol_record
    pi_badge = "🥉 Beginner" if pi_reps <= 3 else "🥈 Novice" if pi_reps <= 8 else "🥇 Advanced"
    
    pl_secs = st.session_state.plank_record
    pl_badge = "🥉 Beginner" if pl_secs <= 60 else "🥈 Novice" if pl_secs <= 120 else "🥇 Advanced"

    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box"><b>Opdrukken</b><br><small>{p_badge} ({p_reps} reps)</small></div>
        <div class="badge-box"><b>Optrekken</b><br><small>{pu_badge} ({pu_reps} reps)</small></div>
        <div class="badge-box"><b>Pistol Squats</b><br><small>{pi_badge} ({pi_reps} reps)</small></div>
        <div class="badge-box"><b>Plank</b><br><small>{pl_badge} ({pl_secs}s)</small></div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    scan_method = st.radio("Kies invoermethode:", ["Camera", "Bestand Uploaden"], horizontal=True)
    img_file = st.camera_input("Maak een foto") if scan_method == "Camera" else st.file_uploader("Kies afbeelding...", type=["jpg", "jpeg", "png"])
        
    if img_file is not None:
        st.image(img_file, use_container_width=True)
        if st.button("Analyseer Maaltijd met AI"):
            with st.spinner("AI analyseert..."):
                time.sleep(2)
                st.success("Analyse compleet!")
                mock_kcal, mock_protein = 450, 32
                st.metric("Geschatte Calorieën", f"{mock_kcal} kcal")
                st.metric("Geschatte Eiwitten", f"{mock_protein} g")
                if st.button("Voeg toe aan log van vandaag"):
                    st.session_state.kcal_gegeten += mock_kcal
                    st.session_state.eiwit_gegeten += mock_protein
                    st.rerun()

# --- TAB 3: VOORTGANG (SAMENGEVOEGD DIAGRAM) ---
with tab3:
    st.title("📈 Jouw Progressie Tijdlijn")
    st.caption("Bekijk hier hoe al je PR's zich week na week ontwikkelen.")
    
    # Maak één DataFrame van de opgeslagen PR-historie
    df_history = pd.DataFrame(st.session_state.pr_history)
    
    # NIEUW: Twee diagrammen samengevoegd in één overzichtelijk combinatiediagram
    st.markdown("#### 📊 Gecombineerde Calisthenics Groei")
    st.line_chart(
        data=df_history, 
        x="Datum", 
        y=["Pushups", "Pullups", "Pistol Squats", "Plank (sec)"], 
        color=["#FF1493", "#00FFFF", "#FFD700", "#00FF00"]
    )
    
    st.markdown("---")
    st.markdown("### 🚨 Zondagse PR Test Registreren")
    st.caption("Voer hier je nieuwe maximale scores in om je grafieklijnen omhoog te stuwen.")
    
    with st.form("records_form"):
        test_date = st.date_input("Datum van test", datetime.date.today())
        new_pushup = st.number_input("Max Pushups", min_value=0, value=st.session_state.pushup_record)
        new_pullup = st.number_input("Max Pullups", min_value=0, value=st.session_state.pullup_record)
        new_pistol = st.number_input("Max Pistol Squats", min_value=0, value=st.session_state.pistol_record)
        new_plank = st.number_input("Max Plankduur (sec)", min_value=0, value=st.session_state.plank_record)
        
        if st.form_submit_button("🔥 Nieuwe PR's Opslaan & Loggen"):
            str_date = test_date.strftime("%Y-%m-%d")
            
            st.session_state.pushup_record = new_pushup
            st.session_state.pullup_record = new_pullup
            st.session_state.pistol_record = new_pistol
            st.session_state.plank_record = new_plank
            
            nieuwe_meting = {
                "Datum": str_date,
                "Pushups": new_pushup,
                "Pullups": new_pullup,
                "Pistol Squats": new_pistol,
                "Plank (sec)": new_plank
            }
            
            st.session_state.pr_history = [h for h in st.session_state.pr_history if h["Datum"] != str_date]
            st.session_state.pr_history.append(nieuwe_meting)
            st.session_state.pr_history = sorted(st.session_state.pr_history, key=lambda x: x["Datum"])
            
            st.success("Geweldig gewerkt! Je gecombineerde tijdlijn is bijgewerkt.")
            time.sleep(1)
            st.rerun()

    if st.button("🔄 Reset Tijdlijn"):
        st.session_state.pr_history = [{"Datum": datetime.date.today().strftime("%Y-%m-%d"), "Pushups": new_pushup, "Pullups": new_pullup, "Pistol Squats": new_pistol, "Plank (sec)": new_plank}]
        st.rerun()

# --- TAB 4: WATER & ETEN ---
with tab4:
    st.title("💧 Water & 🥩 Voeding Tracker")
    col1, col2 = st.columns(2)
    with col1:
        water_liters_nu = st.session_state.water_ml / 1000
        st.metric("Water Inname", f"{water_liters_nu:.1f} / {doel_water_liters} L")
        st.progress(min(1.0, water_liters_nu / max(0.1, doel_water_liters)))
    with col2:
        st.metric("Eiwit Inname", f"{st.session_state.eiwit_gegeten} / {doel_eiwit} g")
        st.progress(min(1.0, st.session_state.eiwit_gegeten / max(1, doel_eiwit)))
    st.metric("Calorieën Verbruikt", f"{st.session_state.kcal_gegeten} / {afval_kcal} kcal")
    st.progress(min(1.0, st.session_state.kcal_gegeten / max(1, afval_kcal)))
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("➕ 250ml Water"): st.session_state.water_ml += 250; st.rerun()
    with c2:
        if st.button("➕ 500ml Water"): st.session_state.water_ml += 500; st.rerun()
    with c3:
        if st.button("🔄 Reset Logs"):
            st.session_state.water_ml, st.session_state.kcal_gegeten, st.session_state.eiwit_gegeten = 0, 0, 0
            st.rerun()

# --- TAB 5: OEFENINGEN ---
with tab5:
    st.title("🗿 Dagelijkse Routines & Tracker")
    
    st.markdown("### Bone / Kaaklijn & Houding")
    st.checkbox("Mewing / Kaaklijnoefeningen gedaan (5 min)", key="kaaklijn_gedaan")
    st.checkbox("Nek- en rughouding stretches gedaan", key="oefening_gedaan")
    
    st.markdown("---")
    st.markdown("### 🏋️‍♂️ Dagelijkse Oefening Registreren")
    
    gekozen_oefening = st.selectbox("Welke oefening heb je gedaan?", list(OEFENINGEN_INFO.keys()))
    sets = st.number_input("Aantal sets", min_value=1, max_value=10, value=3)
    reps = st.number_input("Herhalingen per set (of seconden)", min_value=1, max_value=300, value=10)
    
    if st.button("💪 Log Oefening"):
        spieren = OEFENINGEN_INFO[gekozen_oefening]
        tijdstip = datetime.datetime.now().strftime("%H:%M")
        
        nieuw_log = {
            "Tijd": tijdstip,
            "Oefening": gekozen_oefening,
            "Volume": f"{sets}x{reps}",
            "Getrainde Spieren": spieren
        }
        st.session_state.oefening_log.insert(0, nieuw_log)
        
        st.success(f"**{gekozen_oefening} succesvol gelogd!**")
        st.info(f"🧬 **Getrainde spiergroepen:** {spieren}")
        time.sleep(1)
        st.rerun()

    st.markdown("### 📖 Oefeningen Logboek (Vandaag)")
    if st.session_state.oefening_log:
        df_log = pd.DataFrame(st.session_state.oefening_log)
        st.dataframe(df_log, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Logboek Leegmaken"):
            st.session_state.oefening_log = []
            st.rerun()
    else:
        st.caption("Je hebt vandaag nog geen spieroefeningen gelogd.")
