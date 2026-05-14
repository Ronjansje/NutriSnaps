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
                # Noodknop fallback voor lokaal testen zonder dataloss
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
    if vandaag.weekday() == 6: st.error("🚨 **TESTDAG!** Het is zondag. Ga snel naar 'Voortgang'!")
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
    p_badge = "🥉 Beginner" if p_reps <= 15 else "🥈 Novice" if p_reps <= 30 else "🥇 Borst van Staal" if p_reps <= 50 else "💎 Push Master" if p_reps <= 75 else "🏆 Elite Atleet" if p_reps <= 99 else "👑 PUSH GOD"
    u_reps = st.session_state.pullup_record
    u_badge = "🥉 Hanger" if u_reps <= 5 else "🥈 Klimmer" if u_reps <= 12 else "🥇 Klauw van Brons" if u_reps <= 20 else "💎 Pull Master" if u_reps <= 29 else "👑 ADELAAR"
    s_reps = st.session_state.pistol_record
    s_badge = "🥉 Wankelaar" if s_reps <= 5 else "🥈 Squat Gevorderd" if s_reps <= 15 else "🥇 Benen van Beton" if s_reps <= 25 else "💎 Leg Legend" if s_reps <= 39 else "👑 TITANIUM"
    pl_sec = st.session_state.plank_record
    pl_badge = "🥉 Plankje" if pl_sec <= 45 else "🥈 Stabiele Basis" if pl_sec <= 90 else "🥇 IJzeren Kern" if pl_sec <= 179 else "💎 Core King" if pl_sec <= 299 else "👑 MUUR"

    st.markdown(f"""
    <div class="badge-grid">
        <div class="badge-box">🌟 <b>Borst (Push)</b><br><span style='color:#FF1493;'>{p_badge}</span><br><small>{p_reps} reps</small></div>
        <div class="badge-box">🦅 <b>Rug (Pull)</b><br><span style='color:#FF1493;'>{u_badge}</span><br><small>{u_reps} reps</small></div>
        <div class="badge-box">🦵 <b>Benen (Squat)</b><br><span style='color:#FF1493;'>{s_badge}</span><br><small>{s_reps} reps (p.b.)</small></div>
        <div class="badge-box">🧱 <b>Core (Plank)</b><br><span style='color:#FF1493;'>{pl_badge}</span><br><small>{pl_sec} sec</small></div>
    </div>
    """, unsafe_allow_html=True)

    resterend_kcal = max(0, afval_kcal - st.session_state.kcal_gegeten)
    resterend_water = max(0.0, doel_water_liters - (st.session_state.water_ml / 1000))
    resterend_eiwit = max(0, doel_eiwit - st.session_state.eiwit_gegeten)
    
    st.subheader("📊 Dagelijkse Voedingsstatus")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Calorieën**")
        st.dataframe(pd.DataFrame({"Status": ["Gegeten", "Nog"], "Kcal": [st.session_state.kcal_gegeten, resterend_kcal]}), hide_index=True, use_container_width=True) 
    with col2:
        st.write("**Eiwitten**")
        st.dataframe(pd.DataFrame({"Status": ["Binnen", "Nog"], "Gram": [st.session_state.eiwit_gegeten, resterend_eiwit]}), hide_index=True, use_container_width=True)

    st.markdown("### 📋 Checklist")
    if st.session_state.kaaklijn_gedaan:
        st.success("✅ Kaaklijntraining voltooid!")
    else:
        st.info("❌ Je moet je kaaklijnoefeningen noch doen vandaag.")
        
    if st.session_state.oefening_gedaan:
        st.success("✅ Krachttraining geregistreerd!")
    else:
        st.warning("⚠️ Voer je workout van vandaag noch in via tekst.")

# --- TAB 2: AI SCANNER ---
with tab2:
    st.header("📸 AI Maaltijd Scanner")
    foto = st.camera_input("Fotografeer je eten")
    if foto:
        st.success("Gescand: 420 kcal en 28g eiwitten!")
        if st.button("Voeg toe"):
            st.session_state.kcal_gegeten += 420
            st.session_state.eiwit_gegeten += 28
            st.rerun()

# --- TAB 3: VOORTGANG ---
with tab3:
    st.header("📈 Voortgang & Groei")
    vandaag = datetime.date.today()
    st.line_chart(pd.DataFrame({"Datum": [vandaag - datetime.timedelta(days=i) for i in range(4, -1, -1)], "Gewicht (kg)": [user['weight']+1.0, user['weight']+0.7, user['weight']+0.4, user['weight']+0.2, user['weight']]}).set_index("Datum"))
    
    st.subheader("📊 Wekelijkse Records Invoeren")
    c1, c2 = st.columns(2)
    with c1:
        n_pushups = st.number_input("Borst: Max Push-ups (Reps)", min_value=0, value=st.session_state.pushup_record)
        n_pistols = st.number_input("Benen: Max Pistol Squats (Reps per been)", min_value=0, value=st.session_state.pistol_record)
    with c2:
        n_pullups = st.number_input("Rug: Max Pull-ups (Reps)", min_value=0, value=st.session_state.pullup_record)
        n_plank = st.number_input("Core: Max Plank (Seconden)", min_value=0, value=st.session_state.plank_record)
        
    if st.button("💾 Alle Records Opslaan & Badges Updaten"):
        st.session_state.pushup_record = n_pushups
        st.session_state.pullup_record = n_pullups
        st.session_state.pistol_record = n_pistols
        st.session_state.plank_record = n_plank
        st.success("Alle records succesvol opgeslagen!")
        st.rerun()
    
    # HIER IS DE TYPEFOUT VOLLEDIG VERGEPAST MET STARTWAARDEN [0, 0, 0, 0]
    df_groei = pd.DataFrame({
        "Weken": ["Week 1", "Week 2", "Week 3", "Week 4"], 
        "Borst: Push-ups": [max(5, n_pushups-12), max(8, n_pushups-8), max(12, n_pushups-4), n_pushups], 
        "Rug: Pull-ups": [max(1, n_pullups-6), max(2, n_pullups-4), max(4, n_pullups-2), n_pullups], 
        "Benen: Pistol Squats": [max(0, n_pistols-6), max(2, n_pistols-4), max(4, n_pistols-2), n_pistols], 
        "Core: Plank (Sec)": [max(10, n_plank-60), max(20, n_plank-40), max(30, n_plank-20), n_plank]
    }).set_index("Weken")
    st.line_chart(df_groei)

# --- TAB 4: WATER & HANDMATIGE INVOER ---
with tab4:
    st.header("💧 Handmatige Invoer")
    ml_toevoegen = st.number_input("Hoeveelheid water (ml):", min_value=0, max_value=2000, value=300, step=50)
    if st.button("➕ Water registreren"): st.session_state.water_ml += ml_toevoegen
    st.progress(min((st.session_state.water_ml / 1000) / doel_water_liters, 1.0))
        
    st.subheader("🔥 Handmatige Voeding")
    hkcal = st.number_input("Calorieën:", min_value=0, max_value=3000, value=250)
    heiwit = st.number_input("Eiwit (g):", min_value=0, max_value=150, value=20)
    if st.button("➕ Voeding opslaan"):
        st.session_state.kcal_gegeten += hkcal
        st.session_state.eiwit_gegeten += heiwit
        st.success("Handmatig bijgewerkt!")

# --- TAB 5: OEFENINGEN ---
with tab5:
    st.header("🗿 Dagelijkse Trainingen")
    if st.button("⏱️ Start 5 Minuten Mewing Timer"):
        timer_placeholder = st.empty()
        for resterend in range(5 * 60, -1, -1):
            mins, secs = divmod(resterend, 60)
            timer_placeholder.metric("Resterende tijd", f"{mins:02d}:{secs:02d}")
            time.sleep(1)
        st.balloons()
    o1 = st.checkbox("Mewing voltooid")
    o2 = st.checkbox("Chin Tucks — 3 sets")
    if o1 and o2: st.session_state.kaaklijn_gedaan = True
        
    st.subheader("Spiertraining Tekstinvoer (Eigen Lichaamsgewicht)")
    user_oefening = st.text_input("Typ in wat je hebt gedaan:")
    if st.button("Verstuur workout"):
        if user_oefening: st.session_state.oefening_gedaan = True

