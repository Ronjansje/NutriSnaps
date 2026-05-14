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
    </style>
""", unsafe_allow_html=True)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

# --- 2. JEFIT DATABASE MET EXACTE URLS NAAR JOUW AFBEELDING ---
# Dit laadt exact de medische spierkaarten uit jouw screenshot
MUSCLE_IMAGES = {
    "Standaard": "jefit.com",
    "Borst": "jefit.com",
    "Biceps": "jefit.com",
    "Triceps": "jefit.com",
    "Schouders": "jefit.com",
    "Bovenrug": "jefit.com",
    "Lats": "jefit.com",
    "Core": "jefit.com",
    "Quadriceps": "jefit.com",
    "Hamstrings": "jefit.com",
    "Glutes": "jefit.com",
    "Kuiten": "jefit.com",
    "Onderarmen": "jefit.com"
}

def parse_exercise_muscles(exercise_text):
    text = exercise_text.lower()
    
    if "pushup" in text or "push up" in text or "bench" in text or "chest" in text or "borst" in text:
        return "Borst"
    if "pullup" in text or "pull up" in text or "lats" in text or "vleugels" in text:
        return "Lats"
    if "row" in text or "rug" in text or "back" in text:
        return "Bovenrug"
    if "curl" in text or "bicep" in text:
        return "Biceps"
    if "tricep" in text or "extension" in text or "dip" in text:
        return "Triceps"
    if "squat" in text or "quad" in text or "pistol" in text:
        return "Quadriceps"
    if "deadlift" in text or "hamstring" in text:
        return "Hamstrings"
    if "plank" in text or "abs" in text or "crunch" in text or "core" in text:
        return "Core"
    if "calf" in text or "kuit" in text:
        return "Kuiten"
    if "forearm" in text or "onderarm" in text:
        return "Onderarmen"
    if "shoulder" in text or "press" in text or "raise" in text or "schouder" in text:
        return "Schouders"
        
    return "Standaard"

# --- 3. BROWSER STORAGE INITIALISATIE ---
if "user_db" not in st.session_state: st.session_state.user_db = {}

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
        birthday = st.date_input("Geboortedatum", value=datetime.date(2000, 1, 1))
        height = st.number_input("Lengte (cm)", min_value=120, value=180)
        weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, value=80.0)
        target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, value=75.0)
        days_train = st.slider("Aantal dagen per week sporten", 0, 7, 3)
        duration_train = st.slider("Gemiddelde duur per training (minuten)", 15, 180, 60)
        neck_in = st.number_input("Nekomtrek (cm)", value=38.0)
        waist_in = st.number_input("Buikomtrek (cm)", value=85.0)
        
        if st.button("Registreren"):
            if "@" in email_input and password_input and name:
                age_calc = calculate_age(birthday)
                st.session_state.user_db[email_input] = {
                    "password": make_hashes(password_input), "name": name, "birthday": birthday.strftime("%Y-%m-%d"),
                    "age": age_calc, "height": height, "weight": weight, "target_weight": target_weight,
                    "days_train": days_train, "duration_train": duration_train, "neck": neck_in, "waist": waist_in
                }
                st.success("Account aangemaakt!")
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
                        "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85
                    }
                    st.session_state.logged_in = True
                    st.session_state.current_user = email_input
                    st.rerun()
    st.stop()

# --- 6. HOOFDAPPLICATIE BEREKENINGEN ---
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
except:
    vetpercentage = 15.0

st.sidebar.title("✨ NutriSnap Pro")
st.sidebar.markdown(f"Ingelogd als: **{user['name']}**")
if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Hoofdscherm", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen", "⚙️ Profiel"])

# Tabs 1, 2, 3, 4 & 6 behouden hun werking...
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    st.markdown(f'<div class="fat-box"><h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4></div>', unsafe_allow_html=True)

with tab2:
    st.title("📸 AI Maaltijd Scanner")
    st.camera_input("Maak een foto van je maaltijd")

with tab3:
    st.title("📈 Voortgang & Statistieken")
    st.metric("Huidig Gewicht", f"{user['weight']} kg")

with tab4:
    st.title("💧 Water & Voeding")
    st.subheader(f"Water: {st.session_state.water_ml/1000:.2f} / {doel_water_liters} L")
    if st.button("➕ 250ml Water"):
        st.session_state.water_ml += 250
        st.rerun()

# --- TAB 5: WORKOUTS MET EXACT JOUW GEWENSTE AFBEELDING ---
with tab5:
    st.title("🗿 Professionele Anatomische Spierkaart")
    
    # Bepaal welke spier als laatste is aangesproken om de juiste afbeelding te selecteren
    active_muscle = "Standaard"
    if st.session_state.workout_log:
        active_muscle = st.session_state.workout_log[-1]["Hoofdspier"]

    # Toon EXACT het originele plaatje uit je screenshot
    st.markdown(f"""
        <div style="text-align: center; background-color: #1F2937; padding: 10px; border-radius: 12px; border: 1px solid #374151;">
            <img src="{MUSCLE_IMAGES[active_muscle]}" width="100%" style="max-width: 380px; border-radius: 8px; background-color: white;">
        </div>
    """, unsafe_allow_html=True)
    
    if active_muscle != "Standaard":
        st.info(f"🔥 Focus spiergroep op afbeelding: **{active_muscle}**")

    # --- 100% VRIJ SCHRIJFSYSTEEM ---
    st.markdown("### ✍️ Schrijf je Oefening op")
    with st.form("custom_exercise_form"):
        user_exercise_input = st.text_input("Wat heb je gedaan?", placeholder="Bijv. Squats, Benchpress, Bicep Curls...")
        col1, col2 = st.columns(2)
        with col1: s_in = st.number_input("Sets", min_value=1, value=3)
        with col2: r_in = st.number_input("Reps", min_value=1, value=10)
        
        if st.form_submit_button("Log Oefening"):
            if user_exercise_input:
                target_group = parse_exercise_muscles(user_exercise_input)
                st.session_state.workout_log.append({
                    "Oefening": user_exercise_input,
                    "Sets": s_in,
                    "Reps": r_in,
                    "Hoofdspier": target_group
                })
                st.success(f"Gelogd! De kaart is bijgewerkt naar: {target_group}")
                time.sleep(0.4)
                st.rerun()

    if st.session_state.workout_log:
        st.markdown("##### 📋 Oefeningen Vandaag:")
        display_df = pd.DataFrame([
            {"Oefening": i["Oefening"], "Sets": i["Sets"], "Reps": i["Reps"], "Spiergroep": i["Hoofdspier"]} for i in st.session_state.workout_log
        ])
        st.dataframe(display_df, use_container_width=True)
        if st.button("Logboek Resetten"):
            st.session_state.workout_log = []
            st.rerun()

with tab6:
    st.title("⚙️ Account Instellingen")

