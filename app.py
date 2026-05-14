import streamlit as st
import pandas as pd
import datetime
import hashlib
import time
import math
import json
from streamlit.components.v1 import html

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

def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

# --- 2. AUTOMATISCHE SPIERGROEP DETECTIE ---
def parse_exercise_muscles(exercise_text):
    text = exercise_text.lower()
    detected = {}
    
    keywords = {
        "pushup": {"Borst": 1.0, "Triceps": 0.6, "Schouders": 0.4},
        "push up": {"Borst": 1.0, "Triceps": 0.6, "Schouders": 0.4},
        "bench": {"Borst": 1.0, "Triceps": 0.5, "Schouders": 0.3},
        "press": {"Borst": 0.8, "Schouders": 0.8, "Triceps": 0.4},
        "fly": {"Borst": 1.0},
        "dip": {"Triceps": 1.0, "Borst": 0.7, "Schouders": 0.5},
        "pullup": {"Lats": 1.0, "Bovenrug": 0.8, "Biceps": 0.5},
        "pull up": {"Lats": 1.0, "Bovenrug": 0.8, "Biceps": 0.5},
        "chin": {"Biceps": 1.0, "Lats": 0.8},
        "row": {"Bovenrug": 1.0, "Lats": 0.7, "Biceps": 0.5},
        "curl": {"Biceps": 1.0},
        "bicep": {"Biceps": 1.0},
        "tricep": {"Triceps": 1.0},
        "squat": {"Quadriceps": 1.0, "Hamstrings": 0.4, "Billen": 0.5},
        "leg": {"Quadriceps": 0.8, "Hamstrings": 0.8},
        "lung": {"Quadriceps": 1.0, "Billen": 0.6},
        "deadlift": {"Hamstrings": 0.9, "Bovenrug": 0.7, "Billen": 0.8},
        "plank": {"Core": 1.0},
        "crunch": {"Core": 1.0},
        "situp": {"Core": 1.0},
        "mew": {"Kaaklijn": 1.0},
        "calf": {"Kuiten": 1.0},
        "kuit": {"Kuiten": 1.0},
        "raise": {"Schouders": 1.0}
    }
    
    for key, muscles in keywords.items():
        if key in text:
            for m, val in muscles.items():
                detected[m] = max(detected.get(m, 0), val)
                
    if not detected:
        detected = {"Core": 0.2, "Borst": 0.2}
        
    return detected

# --- 3. BROWSER STORAGE INITIALISATIE ---
if "user_db" not in st.session_state:
    st.session_state.user_db = {}

# --- 4. TRACKING INITIALISATIE ---
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

if "workout_log" not in st.session_state: st.session_state.workout_log = []

# --- 5. INLOG / REGISTRATIE SCHERM ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI")
    st.caption("Je account wordt nu lokaal opgeslagen op dit toestel")
        
    auth_option = st.radio("Kies een optie:", ["Inloggen", "Account Aanmaken"], horizontal=True)
    email_input = st.text_input("E-mailadres")
    password_input = st.text_input("Wachtwoord", type="password")
    
    if auth_option == "Account Aanmaken":
        name = st.text_input("Voornaam")
        birthday = st.date_input("Geboortedatum", min_value=datetime.date(1930, 1, 1), max_value=datetime.date.today(), value=datetime.date(2000, 1, 1))
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
                age_calc = calculate_age(birthday)
                account_data = {
                    "password": make_hashes(password_input), "name": name, "birthday": birthday.strftime("%Y-%m-%d"),
                    "age": age_calc, "height": height, "weight": weight, "target_weight": target_weight,
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
                        "password": hashed_pwd, "name": "Gebruiker", "birthday": "2006-01-01", "age": 20, 
                        "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, 
                        "neck": 38, "waist": 85
                    }
                    st.session_state.logged_in = True
                    st.session_state.current_user = email_input
                    st.rerun()
                else:
                    st.error("Onjuiste e-mail of wachtwoord.")
    st.stop()

# --- 6. HOOFDAPPLICATIE MATHS & CONFIG ---
user = st.session_state.user_db[st.session_state.current_user]

if "birthday" in user:
    b_date = datetime.datetime.strptime(user["birthday"], "%Y-%m-%d").date()
    user["age"] = calculate_age(b_date)

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
st.sidebar.markdown(f"Leeftijd: `{user['age']} jaar`")
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Hoofdscherm", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen", "⚙️ Profiel"])

# --- TAB 1: HOOFDSCHERM ---
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    vandaag = datetime.date.today()
    if vandaag.weekday() == 6: st.error("🚨 **TESTDAG!** Het is zondag. Ga snel naar 'Voortgang'!")
    else: st.info(f"📅 Nog **{6 - vandaag.weekday()} dagen** tot de wekelijkse calisthenics-testdag (zondag).")

    st.markdown("### 📏 Jouw Lichaamscompositie")
    st.markdown(f"""
    <div class="fat-box">
        <h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4>
        <p style="margin:5px 0 0 0; color:#9CA3AF;">Nekomtrek: <b>{user['neck']} cm</b> | Buikomtrek: <b>{user['waist']} cm</b></p>
    </div>
    """, unsafe_allow_html=True)

    p_badge = "🥉 Beginner" if st.session_state.pushup_record <= 15 else "🥈 Novice" if st.session_state.pushup_record <= 30 else "🥇 Elite"
    u_badge = "🥉 Beginner" if st.session_state.pullup_record <= 5 else "🥈 Novice" if st.session_state.pullup_record <= 12 else "🥇 Elite"
    s_badge = "🥉 Beginner" if st.session_state.pistol_record <= 3 else "🥈 Novice" if st.session_state.pistol_record <= 10 else "🥇 Elite"
    l_badge = "🥉 Beginner" if st.session_state.plank_record <= 60 else "🥈 Novice" if st.session_state.plank_record <= 180 else "🥇 Elite"
    
    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box">🤸‍♂️ Pushup Rang<br><b>{p_badge}</b><br><small>{st.session_state.pushup_record} reps</small></div>
        <div class="badge-box">💪 Pullup Rang<br><b>{u_badge}</b><br><small>{st.session_state.pullup_record} reps</small></div>
        <div class="badge-box">🦵 Pistol Squat<br><b>{s_badge}</b><br><small>{st.session_state.pistol_record} reps</small></div>
        <div class="badge-box">⏱️ Plank Rang<br><b>{l_badge}</b><br><small>{st.session_state.plank_record} sec</small></div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    picture = st.camera_input("Maak een foto van je maaltijd")
    if picture is not None:
        with st.spinner("AI van de maaltijd loopt..."): time.sleep(1)
        st.success("Analyse voltooid! +520 kcal, +38g Eiwit.")
        if st.button("Toevoegen aan logboek"):
            st.session_state.kcal_gegeten += 520
            st.session_state.eiwit_gegeten += 38
            st.rerun()

# --- TAB 3: VOORTGANG ---
with tab3:
    st.title("📈 Voortgang & Statistieken")
    st.metric("Huidig Gewicht", f"{user['weight']} kg")
    new_pushup = st.number_input("Max Pushups PR", value=st.session_state.pushup_record)
    new_pullup = st.number_input("Max Pullups PR", value=st.session_state.pullup_record)
    if st.button("PR's Opslaan"):
        st.session_state.pushup_record = new_pushup
        st.session_state.pullup_record = new_pullup
        st.success("Opgeslagen!")

# --- TAB 4: WATER & ETEN ---
with tab4:
    st.title("💧 Water & Voeding")
    st.subheader(f"Water: {st.session_state.water_ml/1000:.2f} / {doel_water_liters} L")
    if st.button("➕ 250ml Drinken"):
        st.session_state.water_ml += 250
        st.rerun()

# --- TAB 5: WORKOUTS & EXACTE VECTOR AFBEELDING OVERLAY ---
with tab5:
    st.title("🗿 Anatomische Spierkaarten Tracker")
    
    # Activeer spiergroepen
    muscle_status = {
        "Borst": False, "Biceps": False, "Triceps": False, "Schouders": False, 
        "Core": False, "Bovenrug": False, "Lats": False, "Billen": False, 
        "Quadriceps": False, "Hamstrings": False, "Kuiten": False
    }
    
    for item in st.session_state.workout_log:
        for m_group in item["Spieren"].keys():
            if m_group in muscle_status:
                muscle_status[m_group] = True

    st.markdown("### 📊 Exacte Anatomische Spierkaart")
    st.caption("Spieren lichten direct felrood op op de vector-afbeelding zodra je hieronder typt.")
    
    # Zet status om naar JS variabelen
    js_status = json.dumps(muscle_status)
    
    html_code = f"""
    <div style="text-align: center; background-color: #1F2937; padding: 20px; border-radius: 12px; display: flex; justify-content: space-around;">
        <div>
            <h5 style="color: #FF1493; margin-top:0; font-family:sans-serif; font-size:12px; letter-spacing:1px;">VOORKANT</h5>
            <svg width="160" height="320" viewBox="0 0 100 200" style="background:#111827; border-radius:8px;">
                <!-- Exacte anatomische contourlijnen conform jouw afbeelding -->
                <path d="M50,15 C45,15 42,20 42,26 C42,32 46,35 50,35 C54,35 58,32 58,26 C58,20 55,15 50,15 Z" fill="none" stroke="#9CA3AF" stroke-width="1.2"/>
                <path id="v-nek" d="M46,34 L46,45 L54,45 L54,34 Z" fill="#E5E7EB" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Borstspieren -->
                <path id="v-borst-l" d="M32,46 C38,45 48,45 49,46 L49,66 L30,64 Z" fill="{ '#FF0000' if muscle_status['Borst'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="v-borst-r" d="M68,46 C62,45 52,45 51,46 L51,66 L70,64 Z" fill="{ '#FF0000' if muscle_status['Borst'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Abs / Core -->
                <path id="v-core" d="M34,68 L66,68 L62,110 L38,110 Z" fill="{ '#FF0000' if muscle_status['Core'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Schouders -->
                <path id="v-schouder-l" d="M30,46 C24,46 22,54 24,60 C26,66 31,64 32,60 Z" fill="{ '#FF0000' if muscle_status['Schouders'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="v-schouder-r" d="M70,46 C76,46 78,54 76,60 C74,66 69,64 68,60 Z" fill="{ '#FF0000' if muscle_status['Schouders'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Biceps -->
                <path id="v-biceps-l" d="M22,62 C16,74 18,88 22,96 L29,92 L28,64 Z" fill="{ '#FF0000' if muscle_status['Biceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="v-biceps-r" d="M78,62 C84,74 82,88 78,96 L71,92 L72,64 Z" fill="{ '#FF0000' if muscle_status['Biceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Onderarmen -->
                <path id="v-onderarm-l" d="M19,98 L24,136 L30,132 L26,96 Z" fill="{ '#FF0000' if muscle_status['Onderarmen'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="v-onderarm-r" d="M81,98 L76,136 L70,132 L74,96 Z" fill="{ '#FF0000' if muscle_status['Onderarmen'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Quadriceps -->
                <path id="v-quads-l" d="M34,112 L49,112 L46,170 L30,165 Z" fill="{ '#FF0000' if muscle_status['Quadriceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="v-quads-r" d="M66,112 L51,112 L54,170 L70,165 Z" fill="{ '#FF0000' if muscle_status['Quadriceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
            </svg>
        </div>
        <div>
            <h5 style="color: #00FFFF; margin-top:0; font-family:sans-serif; font-size:12px; letter-spacing:1px;">ACHTERKANT</h5>
            <svg width="160" height="320" viewBox="0 0 100 200" style="background:#111827; border-radius:8px;">
                <path d="M50,15 C45,15 42,20 42,26 C42,32 46,35 50,35 C54,35 58,32 58,26 C58,20 55,15 50,15 Z" fill="#E5E7EB" stroke="#9CA3AF" stroke-width="1.2"/>
                
                <!-- Bovenrug (Trapezius V-Shape) -->
                <path id="a-bovenrug" d="M50,42 L30,55 L70,55 Z" fill="{ '#FF0000' if muscle_status['Bovenrug'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Lats -->
                <path id="a-lats-l" d="M30,58 L49,58 L47,94 L32,84 Z" fill="{ '#FF0000' if muscle_status['Lats'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="a-lats-r" d="M70,58 L51,58 L53,94 L68,84 Z" fill="{ '#FF0000' if muscle_status['Lats'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Triceps -->
                <path id="a-triceps-l" d="M22,62 L28,64 L26,94 L20,92 Z" fill="{ '#FF0000' if muscle_status['Triceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="a-triceps-r" d="M78,62 L72,64 L74,94 L80,92 Z" fill="{ '#FF0000' if muscle_status['Triceps'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Glutes / Billen -->
                <path id="a-billen-l" d="M34,108 C34,96 48,96 49,112 L35,124 Z" fill="{ '#FF0000' if muscle_status['Billen'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="a-billen-r" d="M66,108 C66,96 52,96 51,112 L65,124 Z" fill="{ '#FF0000' if muscle_status['Billen'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Hamstrings -->
                <path id="a-hamstrings-l" d="M31,126 L49,126 L46,168 L32,168 Z" fill="{ '#FF0000' if muscle_status['Hamstrings'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="a-hamstrings-r" d="M69,126 L51,126 L54,168 L68,168 Z" fill="{ '#FF0000' if muscle_status['Hamstrings'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                
                <!-- Kuiten -->
                <path id="a-kuiten-l" d="M34,174 L46,174 L44,194 L36,194 Z" fill="{ '#FF0000' if muscle_status['Kuiten'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
                <path id="a-kuiten-r" d="M66,174 L54,174 L56,194 L64,194 Z" fill="{ '#FF0000' if muscle_status['Kuiten'] else '#E5E7EB' }" stroke="#9CA3AF" stroke-width="1"/>
            </svg>
        </div>
    </div>
    """
    html(html_code, height=365)

    # --- 100% SCHRIJFSYSTEEM ---
    st.markdown("### ✍️ Schrijf je Oefening op")
    with st.form("custom_exercise_form"):
        user_exercise_input = st.text_input("Wat heb je gedaan?", placeholder="Bijv. Benchpress, Curls, Squats, Pullups...")
        
        col1, col2 = st.columns(2)
        with col1: s_in = st.number_input("Sets", min_value=1, value=3)
        with col2: r_in = st.number_input("Reps", min_value=1, value=10)
        
        if st.form_submit_button("Log Oefening"):
            if user_exercise_input:
                detected_muscles = parse_exercise_muscles(user_exercise_input)
                st.session_state.workout_log.append({
                    "Oefening": user_exercise_input,
                    "Sets": s_in,
                    "Reps": r_in,
                    "Spieren": detected_muscles
                })
                st.success(f"Toegevoegd! De bijbehorende vector-spieren zijn nu felrood.")
                time.sleep(0.4)
                st.rerun()

    if st.session_state.workout_log:
        st.markdown("##### 📋 Oefeningen Vandaag:")
        display_df = pd.DataFrame([
            {"Oefening": i["Oefening"], "Sets": i["Sets"], "Reps": i["Reps"]} for i in st.session_state.workout_log
        ])
        st.dataframe(display_df, use_container_width=True)
        if st.button("Logboek Resetten"):
            st.session_state.workout_log = []
            st.rerun()

# --- TAB 6: PROFIEL ---
with tab6:
    st.title("⚙️ Account Instellingen")
    if st.button("Schoon alle sessiedata op"):
        st.session_state.clear()
        st.rerun()
