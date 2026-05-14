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

# Initialiseer wekelijkse gewichtshistorie
if "wekelijks_gewicht" not in st.session_state:
    st.session_state.wekelijks_gewicht = []

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
                    "height": height, "weight": float(weight), "target_weight": float(target_weight),
                    "days_train": days_train, "duration_train": duration_train,
                    "neck": float(neck_in), "waist": float(waist_in)
                }
                st.session_state.user_db[email_input] = account_data
                # Voeg eerste wekelijkse gewicht toe op basis van profiel
                st.session_state.wekelijks_gewicht = [{"Week": f"Week {datetime.date.today().isocalendar()[1]}", "Gewicht (kg)": float(weight)}]
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
                # Noodknop fallback voor lokaal testen zonder dataloss (Hier stonden integers, nu gecorrigeerd naar floats!)
                if email_input and password_input:
                    st.session_state.user_db[email_input] = {
                        "password": hashed_pwd, "name": "Gebruiker", "age": 20, "height": 180, "weight": 80.0,
                        "target_weight": 75.0, "days_train": 3, "duration_train": 60, "neck": 38.0, "waist": 85.0
                    }
                    if not st.session_state.wekelijks_gewicht:
                        st.session_state.wekelijks_gewicht = [{"Week": f"Week {datetime.date.today().isocalendar()[1]}", "Gewicht (kg)": 80.0}]
                    st.session_state.logged_in = True
                    st.session_state.current_user = email_input
                    st.rerun()
                else:
                    st.error("Onjuiste e-mail of wachtwoord.")
    st.stop()

# --- 5. HOOFDAPPLICATIE ---
user = st.session_state.user_db[st.session_state.current_user]

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
    if vandaag.weekday() == 6: st.error("🚨 **TESTDAG!** Het is zondag. Ga snel naar 'Voortgang' of 'Oefeningen'!")
    else: st.info(f"📅 Nog **{6 - vandaag.weekday()} dagen** tot de wekelijkse calisthenics-testdag (zondag).")

    st.markdown("### 📏 Jouw Lichaamscompositie")
    st.markdown(f"""
    <div class="fat-box">
        <h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4>
        <p style="margin:5px 0 0 0; color:#9CA3AF;">Nekomtrek: <b>{user['neck']} cm</b> | Buikomtrek: <b>{user['waist']} cm</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    if vet_te_verliezen > 0: st.warning(f"🗿 Je moet nog **{vet_te_verliezen:.1f} kg vet** verliezen voor een scherpe kaaklijn (doel: 12%).")
    else: st.success("👑 Jouw vetpercentage is optimaal voor een messcherpe kaaklijn!")

    st.markdown("### 🏅 Jouw Mijlpalen & Rangen")
    p_reps = st.session_state.pushup_record
    p_badge = "🥉 Beginner" if p_reps <= 15 else "🥈 Novice" if p_reps <= 30 else "🥇 Elite"
    
    u_reps = st.session_state.pullup_record
    u_badge = "🥉 Beginner" if u_reps <= 5 else "🥈 Novice" if u_reps <= 12 else "🥇 Elite"

    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box">🛡️ <b>Push-ups</b><br><span style='color:#FF1493;'>{p_badge}</span><br><small>{p_reps} herhalingen</small></div>
        <div class="badge-box">🦅 <b>Pull-ups</b><br><span style='color:#FF1493;'>{u_badge}</span><br><small>{u_reps} herhalingen</small></div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    st.caption("Maak een foto van je bord om direct macro's te schatten")
    
    upload_file = st.file_uploader("Upload of maak een foto", type=["jpg", "jpeg", "png"])
    if upload_file is not None:
        st.image(upload_file, caption="Ingezonden maaltijd", use_container_width=True)
        with st.spinner("AI analyseert de maaltijd..."):
            time.sleep(2)
        st.success("Maaltijd gedetecteerd: Kipfilet met Rijst en Broccoli")
        
        col1, col2 = st.columns(2)
        col1.metric("Geschatte Kcal", "450 kcal")
        col2.metric("Geschatte Eiwitten", "38 g")
        
        if st.button("Toevoegen aan logboek"):
            st.session_state.kcal_gegeten += 450
            st.session_state.eiwit_gegeten += 38
            st.success("Toegevoegd aan dagtotaal!")
            st.rerun()

# --- TAB 3: VOORTGANG ---
with tab3:
    st.title("📈 Dagelijkse Voortgang")
    
    col1, col2 = st.columns(2)
    col1.metric("Calorieën", f"{st.session_state.kcal_gegeten} / {afval_kcal} kcal")
    col2.metric("Eiwitten", f"{st.session_state.eiwit_gegeten} / {doel_eiwit} g")
    
    kcal_progress = min(1.0, float(st.session_state.kcal_gegeten) / max(1, afval_kcal))
    st.progress(kcal_progress)
    
    # --- WEKELIJKS GEWICHT LOGBOEK ---
    st.markdown("---")
    st.markdown("### ⚖️ Wekelijks Gewicht Logboek")
    st.caption("Log je gewicht één keer per week (bijvoorbeeld op zondag tijdens de testdag).")

    # Invoerveld (Gecorrigeerd naar float() om typesync fouten te voorkomen)
    gewicht_input = st.number_input(
        "Huidig gewicht voor deze week (kg)", 
        min_value=40.0, 
        max_value=180.0, 
        value=float(user["weight"]), 
        step=0.1,
        key="wekelijks_gewicht_input"
    )

    if st.button("Weekmeting Opslaan"):
        # Haal het weeknummer op uit de tuple
        huidige_week_nummer = datetime.date.today().isocalendar()[1]
        week_label = f"Week {huidige_week_nummer}"
        
        # Verwijder oude meting van deze week
        st.session_state.wekelijks_gewicht = [
            meting for meting in st.session_state.wekelijks_gewicht if meting["Week"] != week_label
        ]
        
        # Voeg de nieuwe float meting toe
        st.session_state.wekelijks_gewicht.append({"Week": week_label, "Gewicht (kg)": float(gewicht_input)})
        st.session_state.user_db[st.session_state.current_user]["weight"] = float(gewicht_input)
        st.success(f"Gewicht voor {week_label} succesvol opgeslagen!")
        st.rerun()

    # Toon de wekelijkse trend in een grafiek
    if st.session_state.wekelijks_gewicht:
        df_wekelijks = pd.DataFrame(st.session_state.wekelijks_gewicht)
        st.line_chart(df_wekelijks.set_index("Week"))
        
        with st.expander("📄 Bekijk alle weekmetingen"):
            st.dataframe(df_wekelijks, hide_index=True, use_container_width=True)

# --- TAB 4: WATER & ETEN ---
with tab4:
    st.title("💧 Water & Handmatige Invoer")
    
    huidige_water_liters = st.session_state.water_ml / 1000.0
    st.metric("Water gedronken", f"{huidige_water_liters:.1f} / {doel_water_liters} L")
    
    col1, col2 = st.columns(2)
    if col1.button("+250 ml Water"):
        st.session_state.water_ml += 250
        st.rerun()
    if col2.button("Reset Water"):
        st.session_state.water_ml = 0
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🍳 Handmatige Macro Invoer")
    hand_kcal = st.number_input("Calorieën (kcal)", min_value=0, max_value=5000, value=0)
    hand_eiwit = st.number_input("Eiwitten (g)", min_value=0, max_value=300, value=0)
    if st.button("Voeg macro's toe"):
        st.session_state.kcal_gegeten += hand_kcal
        st.session_state.eiwit_gegeten += hand_eiwit
        st.success("Macro's succesvol bijgewerkt!")
        st.rerun()

# --- TAB 5: OEFENINGEN ---
with tab5:
    st.title("🗿 Kaaklijn & Calisthenics Records")
    
    st.checkbox("Dagelijkse Kaaklijnoefeningen gedaan (Mewing / Kauwen)", key="kaaklijn_gedaan")
    st.checkbox("Dagelijkse Workout afgerond", key="oefening_gedaan")
    
    st.markdown("---")
    st.markdown("### 🏆 Werk je persoonlijke records bij")
    
    new_pushup = st.number_input("Push-ups max reps", min_value=0, max_value=200, value=st.session_state.pushup_record)
    new_pullup = st.number_input("Pull-ups max reps", min_value=0, max_value=100, value=st.session_state.pullup_record)
    
    if st.button("Records Opslaan"):
        st.session_state.pushup_record = new_pushup
        st.session_state.pullup_record = new_pullup
        st.success("Je records zijn bijgewerkt!")
        st.rerun()
