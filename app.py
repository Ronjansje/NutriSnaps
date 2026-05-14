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

# --- 4. INLOG / REGISTRATIE SCHERM ---
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

# --- 5. HOOFDAPPLICATIE ---
user = st.session_state.user_db[st.session_state.current_user]

if "birthday" in user:
    b_date = datetime.datetime.strptime(user["birthday"], "%Y-%m-%d").date()
    user["age"] = calculate_age(b_date)

# Gezondheidsberekeningen
bmr = (10 * user["weight"]) + (6.25 * user["height"]) - (5 * user["age"]) + 5
activity = 1.2 if user["days_train"] <= 1 else 1.375 if user["days_train"] <= 3 else 1.55 if user["days_train"] <= 5 else 1.725
extra_kcal = (user["duration_train"] * 6 * user["days_train"]) / 7
afval_kcal = int((bmr * activity) + extra_kcal - 500)
doel_eiwit = int(user["weight"] * 2.0)
doel_water_liters = round((user["weight"] * 0.035) + ((user["duration_train"] * 0.01 * user["days_train"]) / 7), 1)

# Vetpercentage
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
    p_badge = "🥉 Beginner" if p_reps <= 15 else "🥈 Novice" if p_reps <= 30 else "🥇 Elite"
    
    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box">🥇 Pushup Rang<br><b>{p_badge}</b><br><small>{p_reps} herhalingen</small></div>
        <div class="badge-box">💧 Hydratie Status<br><b>{"Perfect" if st.session_state.water_ml >= (doel_water_liters * 1000) else "Drink meer!"}</b></div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    st.caption("Maak een foto of upload een afbeelding van je maaltijd voor directe macro-analyse.")
    
    upload_file = st.file_uploader("Kies een afbeelding...", type=["jpg", "jpeg", "png"])
    if upload_file is not None:
        st.image(upload_file, caption="Geüploade maaltijd", use_container_width=True)
        with st.spinner("AI analyseert de maaltijd..."):
            time.sleep(2)
        st.success("Analyse voltooid!")
        
        sim_kcal = 450
        sim_protein = 35
        
        st.metric("Gescande Calorieën", f"{sim_kcal} kcal")
        st.metric("Gescande Eiwitten", f"{sim_protein} g")
        
        if st.button("Voeg toe aan logboek"):
            st.session_state.kcal_gegeten += sim_kcal
            st.session_state.eiwit_gegeten += sim_protein
            st.success("Toegevoegd aan je dagelijkse totalen!")

# --- TAB 3: VOORTGANG ---
with tab3:
    st.title("📈 Voortgang & Statistieken")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Huidig Gewicht", f"{user['weight']} kg")
    with col2:
        st.metric("Doel Gewicht", f"{user['target_weight']} kg")
        
    st.markdown("### Wekelijkse Calisthenics Testgegevens")
    new_pushup = st.number_input("Max Pushups", min_value=0, value=st.session_state.pushup_record)
    new_pullup = st.number_input("Max Pullups", min_value=0, value=st.session_state.pullup_record)
    
    if st.button("Records Bijwerken"):
        st.session_state.pushup_record = new_pushup
        st.session_state.pullup_record = new_pullup
        st.success("Records succesvol opgeslagen!")

# --- TAB 4: WATER & ETEN ---
with tab4:
    st.title("💧 Water & Voeding Tracker")
    
    st.subheader(f"Waterinname: {st.session_state.water_ml / 1000:.2f} / {doel_water_liters} L")
    st.progress(min(1.0, st.session_state.water_ml / (doel_water_liters * 1000)))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 250ml Water"):
            st.session_state.water_ml += 250
            st.rerun()
    with col2:
        if st.button("🗑️ Reset Water"):
            st.session_state.water_ml = 0
            st.rerun()
            
    st.subheader("Voeding Handmatig Toevoegen")
    add_kcal = st.number_input("Calorieën (kcal)", min_value=0, value=0)
    add_protein = st.number_input("Eiwit (g)", min_value=0, value=0)
    
    if st.button("Maaltijd Loggen"):
        st.session_state.kcal_gegeten += add_kcal
        st.session_state.eiwit_gegeten += add_protein
        st.success("Maaltijd succesvol opgeslagen!")
        
    st.markdown("### Dagelijkse Status")
    st.write(f"🔥 Calorieën: {st.session_state.kcal_gegeten} / {afval_kcal} kcal")
    st.write(f"🥩 Eiwitten: {st.session_state.eiwit_gegeten} / {doel_eiwit} g")

# --- TAB 5: OEFENINGEN ---
with tab5:
    st.title("🗿 Oefeningen & Kaaklijntraining")
    
    st.checkbox("Kaaklijntraining voltooid (Mewing / Kauwgom)", value=st.session_state.kaaklijn_gedaan, key="kaaklijn_chk")
    st.checkbox("Dagelijkse workout routine voltooid", value=st.session_state.oefening_gedaan, key="workout_chk")
    
    st.session_state.kaaklijn_gedaan = st.session_state.kaaklijn_chk
    st.session_state.oefening_gedaan = st.session_state.workout_chk

# --- TAB 6: PROFIEL AANPASSEN ---
with tab6:
    st.title("⚙️ Account & Profiel Aanpassen")
    st.caption("Wijzig hier je persoonlijke instellingen. Je doelen worden direct opnieuw berekend.")
    
    current_birthday = datetime.datetime.strptime(user.get("birthday", "2000-01-01"), "%Y-%m-%d").date()
    
    with st.form("profile_form"):
        new_name = st.text_input("Voornaam", value=user["name"])
        new_birthday = st.date_input("Geboortedatum", min_value=datetime.date(1930, 1, 1), max_value=datetime.date.today(), value=current_birthday)
        new_height = st.number_input("Lengte (cm)", min_value=120, max_value=230, value=int(user["height"]))
        new_weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, max_value=180.0, value=float(user["weight"]))
        new_target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, max_value=180.0, value=float(user["target_weight"]))
        
        st.markdown("##### 🏋️‍♂️ Trainingsinstellingen")
        new_days = st.slider("Aantal dagen per week sporten", 0, 7, int(user["days_train"]))
        new_duration = st.slider("Gemiddelde duur per training (minuten)", 15, 180, int(user["duration_train"]))
        
        st.markdown("##### 📏 Omtrekmaten")
        new_neck = st.number_input("Nekomtrek (cm)", min_value=20.0, max_value=60.0, value=float(user["neck"]))
        new_waist = st.number_input("Buikomtrek (cm)", min_value=50.0, max_value=150.0, value=float(user["waist"]))
        
        submit_profile = st.form_submit_button("Wijzigingen Opslaan")
        
        if submit_profile:
            if new_name:
                age_calc = calculate_age(new_birthday)
                st.session_state.user_db[st.session_state.current_user].update({
                    "name": new_name,
                    "birthday": new_birthday.strftime("%Y-%m-%d"),
                    "age": age_calc,
                    "height": new_height,
                    "weight": new_weight,
                    "target_weight": new_target_weight,
                    "days_train": new_days,
                    "duration_train": new_duration,
                    "neck": new_neck,
                    "waist": new_waist
                })
                st.success("Profiel succesvol bijgewerkt!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Naam mag niet leeg zijn.")
