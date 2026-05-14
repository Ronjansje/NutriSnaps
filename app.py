import streamlit as st
import pandas as pd
import datetime
import hashlib
import time

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
    </style>
""", unsafe_allow_html=True)

# --- 2. LOKALE DATABASE IN HET GEHEUGEN ---
if "user_db" not in st.session_state:
    st.session_state.user_db = {} 

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 3. TRACKING INITIALISATIE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""
if "water_ml" not in st.session_state:
    st.session_state.water_ml = 0
if "kcal_gegeten" not in st.session_state:
    st.session_state.kcal_gegeten = 0
if "eiwit_gegeten" not in st.session_state:
    st.session_state.eiwit_gegeten = 0
if "kaaklijn_gedaan" not in st.session_state:
    st.session_state.kaaklijn_gedaan = False
if "oefening_gedaan" not in st.session_state:
    st.session_state.oefening_gedaan = False

# --- 4. INLOG / REGISTRATIE SCHERM ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI")
    st.caption("Veilig inloggen op jouw toestel")
        
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
        
        if st.button("Registreren"):
            if "@" in email_input and password_input and name:
                if email_input not in st.session_state.user_db:
                    st.session_state.user_db[email_input] = {
                        "password": make_hashes(password_input), "name": name, "age": age,
                        "height": height, "weight": weight, "target_weight": target_weight,
                        "days_train": days_train, "duration_train": duration_train
                    }
                    st.success("Account succesvol aangemaakt! Je kunt nu inloggen.")
                else:
                    st.error("Dit e-mailadres is al geregistreerd.")
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

# Zijmenu instellen
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

# Dashboard tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Hoofdscherm", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen"])

# --- TAB 1: HOOFDSCHERM (DASHBOARD) ---
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    st.caption("Jouw overzicht van vandaag:")

    # 1. DYNAMISCHE MELDING VOOR DE WEKELIJKSE GRAFIEK-TEST
    vandaag = datetime.date.today()
    dag_van_de_week = vandaag.weekday() # 0 = Maandag, 6 = Zondag
    
    st.markdown("### 🔔 Grafiek Update Melding")
    if dag_van_de_week == 6: # Het is Zondag
        st.error("🚨 **TESTDAG!** Het is zondag. Ga naar de tab 'Voortgang' om je wekelijkse herhalingen te testen en te kijken of je bent gegroeid!")
    else:
        dagen_tot_zondag = 6 - dag_van_de_week
        st.info(f"📅 Nog **{dagen_tot_zondag} dagen** tot je wekelijkse calisthenics-test (elke zondag) om je spiergroei-grafiek bij te werken.")

    # Status berekeningen
    resterend_kcal = max(0, afval_kcal - st.session_state.kcal_gegeten)
    resterend_water = max(0.0, doel_water_liters - (st.session_state.water_ml / 1000))
    resterend_eiwit = max(0, doel_eiwit - st.session_state.eiwit_gegeten)
    
    st.subheader("📊 Dagelijkse Voedingsstatus")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Calorieën Status**")
        df_kcal = pd.DataFrame({"Status": ["Gegeten", "Nog"], "Kcal": [st.session_state.kcal_gegeten, resterend_kcal]})
        st.dataframe(df_kcal, hide_index=True, use_container_width=True) 
    with col2:
        st.write("**Eiwitten Status**")
        df_eiwit = pd.DataFrame({"Status": ["Binnen", "Nog"], "Gram": [st.session_state.eiwit_gegeten, resterend_eiwit]})
        st.dataframe(df_eiwit, hide_index=True, use_container_width=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1: st.metric(label="Nog te eten calorieën", value=f"{resterend_kcal} kcal", delta=f"Doel: {afval_kcal}")
    with col_m2: st.metric(label="Nog te drinken water", value=f"{resterend_water:.1f} L", delta=f"Doel: {doel_water_liters}L")

    st.markdown("### 📋 Checklist")
    if st.session_state.kaaklijn_gedaan:
        st.success("✅ Kaaklijntraining voltooid!")
    else:
        st.info("❌ Je moet je kaaklijnoefeningen nog doen vandaag.")
        
    if st.session_state.oefening_gedaan:
        st.success("✅ Krachttraining geregistreerd!")
    else:
        st.warning("⚠️ Voer je workout van vandaag nog in via tekst.")

# --- TAB 2: AI SCANNER ---
with tab2:
    st.header("📸 AI Maaltijd Scanner")
    foto = st.camera_input("Fotografeer je eten")
    if not foto:
        foto = st.file_uploader("Of kies een foto uit je galerij", type=["jpg", "jpeg", "png"])
        
    if foto:
        st.success("Foto succesvol geladen! AI start met analyseren...")
        kcal_gescand = 420
        eiwit_gescand = 28
        st.metric(label="Gescande Calorieën", value=f"{kcal_gescand} kcal")
        st.metric(label="Gescande Eiwitten", value=f"{eiwit_gescand} g")
        
        if st.button("Voeg deze AI waarden toe aan je dag"):
            st.session_state.kcal_gegeten += kcal_gescand
            st.session_state.eiwit_gegeten += eiwit_gescand
            st.success("Succesvol toegevoegd aan je totalen!")

# --- TAB 3: VOORTGANG ---
with tab3:
    st.header("📈 Voortgang & Groei")
    vandaag = datetime.date.today()
    st.line_chart(pd.DataFrame({"Datum": [vandaag - datetime.timedelta(days=i) for i in range(4, -1, -1)], "Gewicht (kg)": [user['weight']+1.0, user['weight']+0.7, user['weight']+0.4, user['weight']+0.2, user['weight']]}).set_index("Datum"))
    
    st.subheader("📊 Wekelijkse Lichaamsgewicht Groei")
    st.caption("Vul hier op zondag je nieuwe maximale herhalingen of seconden in.")
    
    df_groei = pd.DataFrame({
        "Weken": ["Week 1", "Week 2", "Week 3", "Week 4"], 
        "Borst: Push-ups": [20, 22, 25, 27], 
        "Rug: Pull-ups": [5, 6, 6, 8], 
        "Benen: Pistol Squats": [8, 10, 11, 12], 
        "Core: Plank (Sec)": [60, 65, 75, 80]
    }).set_index("Weken")
    st.line_chart(df_groei)

# --- TAB 4: WATER & HANDMATIGE VOEDING LOG ---
with tab4:
    st.header("💧 Handmatige Invoer")
    ml_toevoegen = st.number_input("Hoeveelheid water (ml):", min_value=0, max_value=2000, value=300, step=50)
    if st.button("➕ Water registreren"):
        st.session_state.water_ml += ml_toevoegen
        st.toast(f"{ml_toevoegen}ml toegevoegd!")
        
    st.write(f"Totaal gedronken: {st.session_state.water_ml / 1000} / {doel_water_liters} Liter")
    st.progress(min((st.session_state.water_ml / 1000) / doel_water_liters, 1.0))
        
    st.subheader("🔥 Handmatige Voeding")
    hkcal = st.number_input("Calorieën:", min_value=0, max_value=3000, value=250)
    heiwit = st.number_input("Eiwit (g):", min_value=0, max_value=150, value=20)
    if st.button("➕ Voeding opslaan"):
        st.session_state.kcal_gegeten += hkcal
        st.session_state.eiwit_gegeten += heiwit
        st.success("Handmatig bijgewerkt!")

# --- TAB 5: OEFENINGEN & LIVE KAAKLIJN TIMER ---
with tab5:
    st.header("🗿 Dagelijkse Trainingen")
    
    st.subheader("Dagelijkse Kaaklijntraining")
    st.write("Druk op de knop om te starten met Mewen (5 minuten timer):")
    
    if st.button("⏱️ Start 5 Minuten Mewing Timer"):
        timer_placeholder = st.empty()
        totale_tijd = 5 * 60
        for resterend in range(totale_tijd, -1, -1):
            mins, secs = divmod(resterend, 60)
            timer_placeholder.metric("Resterende tijd", f"{mins:02d}:{secs:02d}")
            time.sleep(1)
        st.balloons()
        st.success("Geweldig! Je hebt 5 minuten geknipt en getraind!")
        
    o1 = st.checkbox("Mewing voltooid")
    o2 = st.checkbox("Chin Tucks (Kin intrekken) — 3 sets")
    if o1 and o2:
        st.session_state.kaaklijn_gedaan = True
        
    st.subheader("Spiertraining Tekstinvoer (Eigen Lichaamsgewicht)")
    user_oefening = st.text_input("Typ in wat je hebt gedaan (bijv. pushups, pullups, planken):", "")
    if st.button("Verstuur workout"):
        if user_oefening:
            st.session_state.oefening_gedaan = True
            st.success("Workout verwerkt!")
            tekst = user_oefening.lower()
            if any(x in tekst for x in ["pushup", "opdrukken"]): st.info("💪 Getraind: Borst & Triceps (85%)")
            if any(x in tekst for x in ["squat", "pistol"]): st.info("🍗 Getraind: Benen & Billen (90%)")
            if any(x in tekst for x in ["pullup", "optrekken"]): st.info("🦅 Getraind: Rug & Biceps (80%)")
            if any(x in tekst for x in ["plank", "buik"]): st.info("🧱 Getraind: Buikspieren / Core (85%)")
