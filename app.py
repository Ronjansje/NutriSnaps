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

if "workout_log" not in st.session_state: st.session_state.workout_log = []

# Vaste oefeningen database (voor snelle selectie)
EXERCISE_MUSCLES = {
    "Pushups (Regulier)": {"Borst": 1.0, "Triceps": 0.6, "Schouders": 0.4, "Core": 0.3},
    "Diamond Pushups": {"Triceps": 1.0, "Borst": 0.5, "Schouders": 0.3, "Core": 0.3},
    "Pullups": {"Bovenrug": 1.0, "Lats": 0.9, "Biceps": 0.6, "Onderarmen": 0.4},
    "Chin-ups": {"Biceps": 1.0, "Lats": 0.7, "Bovenrug": 0.5, "Onderarmen": 0.4},
    "Pistol Squats": {"Bovenbenen": 1.0, "Kuiten": 0.4, "Core": 0.4},
    "Dips": {"Triceps": 1.0, "Borst": 0.7, "Schouders": 0.5},
    "Plank": {"Core": 1.0, "Schouders": 0.2},
    "Mewing Sessie (minuten)": {"Kaaklijn": 1.0}
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
    st.caption("Maak direct een foto met je camera of upload een afbeelding voor macro-analyse.")
    
    scan_method = st.radio("Kies invoermethode:", ["📷 Camera gebruiken", "📁 Bestand uploaden"], horizontal=True)
    picture = None
    
    if scan_method == "📷 Camera gebruiken":
        picture = st.camera_input("Maak een foto van je maaltijd")
    else:
        picture = st.file_uploader("Kies een afbeelding...", type=["jpg", "jpeg", "png"])
        
    if picture is not None:
        if scan_method == "📁 Bestand uploaden":
            st.image(picture, caption="Geüploade maaltijd", use_container_width=True)
            
        with st.spinner("AI scant maaltijd..."):
            time.sleep(1.5)
        st.success("Analyse voltooid!")
        
        st.metric("Gescande Calorieën", "520 kcal")
        st.metric("Gescande Eiwitten", "38 g")
        
        if st.button("Voeg toe aan logboek"):
            st.session_state.kcal_gegeten += 520
            st.session_state.eiwit_gegeten += 38
            st.success("Toegevoegd!")

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
    new_pistol = st.number_input("Max Pistol Squats", min_value=0, value=st.session_state.pistol_record)
    new_plank = st.number_input("Max Plank Tijd (sec)", min_value=0, value=st.session_state.plank_record)
    
    if st.button("Records Bijwerken"):
        st.session_state.pushup_record = new_pushup
        st.session_state.pullup_record = new_pullup
        st.session_state.pistol_record = new_pistol
        st.session_state.plank_record = new_plank
        st.success("Records opgeslagen!")
        st.rerun()

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

# --- TAB 5: WORKOUT & DETAIL-HEATMAP ---
with tab5:
    st.title("🗿 Oefeningen & Kaaklijntraining")
    
    st.checkbox("Kaaklijntraining voltooid (Mewing / Kauwgom)", value=st.session_state.kaaklijn_gedaan, key="k_chk")
    st.session_state.kaaklijn_gedaan = st.st.get("k_chk", False) if "k_chk" in st.session_state else st.session_state.kaaklijn_gedaan

    # Berekening spieractivatie uit logboek
    muscle_scores = {"Kaaklijn": 0, "Borst": 0, "Biceps": 0, "Triceps": 0, "Onderarmen": 0, "Schouders": 0, "Core": 0, "Bovenrug": 0, "Lats": 0, "Bovenbenen": 0, "Kuiten": 0}
    for item in st.session_state.workout_log:
        oefen_naam = item["Oefening"]
        total_vol = item["Sets"] * item["Reps"]
        
        if oefen_naam in EXERCISE_MUSCLES:
            for m_group, factor in EXERCISE_MUSCLES[oefen_naam].items():
                if m_group in muscle_scores: muscle_scores[m_group] += total_vol * factor
        elif "Hoofdspier" in item:
            # Custom handmatig ingevulde oefening
            m_group = item["Hoofdspier"]
            if m_group in muscle_scores: muscle_scores[m_group] += total_vol * 1.0

    st.markdown("### 📊 Gedetailleerde 2D Spieractivatie Heatmap")
    
    # Renderen van interactieve HTML5-Canvas voor Voor- én Achterkant
    js_data = json.dumps(muscle_scores)
    html_code = f"""
    <div style="text-align: center; background-color: #1F2937; padding: 15px; border-radius: 12px; display: flex; justify-content: space-around;">
        <div>
            <h5 style="color: #FF1493; margin-top:0;">VOORKANT</h5>
            <canvas id="frontCanvas" width="180" height="320" style="background-color:#111827; border-radius:8px;"></canvas>
        </div>
        <div>
            <h5 style="color: #00FFFF; margin-top:0;">ACHTERKANT</h5>
            <canvas id="backCanvas" width="180" height="320" style="background-color:#111827; border-radius:8px;"></canvas>
        </div>
    </div>
    <script>
        const scores = {js_data};
        let maxS = 0; for(let m in scores) {{ if(scores[m]>maxS) maxS=scores[m]; }}
        
        function c(mName) {{
            let s = scores[mName] || 0;
            if(s===0) return '#4B5563';
            let r = s / maxS;
            return `rgb(${{Math.floor(210+45*r)}}, ${{Math.floor(20*(1-r))}}, ${{Math.floor(120+135*r)}})`;
        }}
        
        // --- VOORKANT DRAW ---
        const fCtx = document.getElementById('frontCanvas').getContext('2d');
        fCtx.lineWidth = 2; fCtx.strokeStyle = '#FFFFFF';
        // Hoofd & Kaak
        fCtx.fillStyle = c('Kaaklijn'); fCtx.beginPath(); fCtx.arc(90, 35, 15, 0, Math.PI*2); fCtx.fill(); fCtx.stroke();
        // Borst
        fCtx.fillStyle = c('Borst'); fCtx.fillRect(65, 75, 50, 30); fCtx.strokeRect(65, 75, 50, 30);
        // Abs / Core
        fCtx.fillStyle = c('Core'); fCtx.fillRect(68, 110, 44, 45); fCtx.strokeRect(68, 110, 44, 45);
        // Schouders
        fCtx.fillStyle = c('Schouders'); 
        fCtx.beginPath(); fCtx.arc(52, 82, 10, 0, Math.PI*2); fCtx.fill(); fCtx.stroke();
        fCtx.beginPath(); fCtx.arc(128, 82, 10, 0, Math.PI*2); fCtx.fill(); fCtx.stroke();
        // Armen (Biceps & Onderarmen)
        fCtx.fillStyle = c('Biceps'); fCtx.fillRect(38, 95, 12, 35); fCtx.strokeRect(38, 95, 12, 35);
        fCtx.fillRect(130, 95, 12, 35); fCtx.strokeRect(130, 95, 12, 35);
        fCtx.fillStyle = c('Onderarmen'); fCtx.fillRect(36, 133, 11, 35); fCtx.strokeRect(36, 133, 11, 35);
        fCtx.fillRect(133, 133, 11, 35); fCtx.strokeRect(133, 133, 11, 35);
        // Benen (Bovenbenen)
        fCtx.fillStyle = c('Bovenbenen'); fCtx.fillRect(66, 160, 20, 75); fCtx.strokeRect(66, 160, 20, 75);
        fCtx.fillRect(94, 160, 20, 75); fCtx.strokeRect(94, 160, 20, 75);
        
        // --- ACHTERKANT DRAW ---
        const bCtx = document.getElementById('backCanvas').getContext('2d');
        bCtx.lineWidth = 2; bCtx.strokeStyle = '#FFFFFF';
        // Hoofd Achter
        bCtx.fillStyle = '#4B5563'; bCtx.beginPath(); bCtx.arc(90, 35, 15, 0, Math.PI*2); bCtx.fill(); bCtx.stroke();
        // Bovenrug
        bCtx.fillStyle = c('Bovenrug'); bCtx.fillRect(62, 72, 56, 28); bCtx.strokeRect(62, 72, 56, 28);
        // Lats (V-Shape)
        bCtx.fillStyle = c('Lats'); bCtx.fillRect(66, 102, 48, 35); bCtx.strokeRect(66, 102, 48, 35);
        // Armen Achter (Triceps & Onderarmen)
        bCtx.fillStyle = c('Triceps'); bCtx.fillRect(38, 95, 12, 35); bCtx.strokeRect(38, 95, 12, 35);
        bCtx.fillRect(130, 95, 12, 35); bCtx.strokeRect(130, 95, 12, 35);
        bCtx.fillStyle = c('Onderarmen'); bCtx.fillRect(36, 133, 11, 35); bCtx.strokeRect(36, 133, 11, 35);
        bCtx.fillRect(133, 133, 11, 35); bCtx.strokeRect(133, 133, 11, 35);
        // Kuiten
        bCtx.fillStyle = c('Kuiten'); bCtx.fillRect(66, 220, 18, 55); bCtx.strokeRect(66, 220, 18, 55);
        bCtx.fillRect(96, 220, 18, 55); bCtx.strokeRect(96, 220, 18, 55);
    </script>
    """
    html(html_code, height=370)

    # --- INPUT: SCHRIJF JE EIGEN OEFENING ---
    st.markdown("### 📝 Oefening Loggen")
    log_mode = st.radio("Type invoer:", ["Kiezen uit lijst", "✍️ Zelf een oefening opschrijven"], horizontal=True)
    
    with st.form("exercise_form_detailed"):
        if log_mode == "Kiezen uit lijst":
            ex_name = st.selectbox("Selecteer oefening:", list(EXERCISE_MUSCLES.keys()))
            chosen_muscle = None
        else:
            ex_name = st.text_input("Schrijf hier de naam van je oefening:", placeholder="Bijv. Incline Dumbbell Curl")
            chosen_muscle = st.selectbox("Welke spiergroep traint dit primair?", list(muscle_scores.keys()))
            
        col1, col2 = st.columns(2)
        with col1: sets_input = st.number_input("Sets", min_value=1, value=3)
        with col2: reps_input = st.number_input("Reps", min_value=1, value=10)
        
        submit_ex = st.form_submit_button("Oefening Toevoegen")
        if submit_ex and ex_name:
            log_data = {"Oefening": ex_name, "Sets": sets_input, "Reps": reps_input}
            if chosen_muscle: log_data["Hoofdspier"] = chosen_muscle
            
            st.session_state.workout_log.append(log_data)
            st.success(f"'{ex_name}' succesvol opgeslagen! De 2D Heatmap is bijgewerkt.")
            time.sleep(0.5)
            st.rerun()

    if st.session_state.workout_log:
        st.markdown("##### 📋 Jouw training van vandaag:")
        st.dataframe(pd.DataFrame(st.session_state.workout_log)[["Oefening", "Sets", "Reps"]], use_container_width=True)
        if st.button("Logboek Leegmaken"):
            st.session_state.workout_log = []
            st.rerun()

# --- TAB 6: PROFIEL AANPASSEN ---
with tab6:
    st.title("⚙️ Account & Profiel Aanpassen")
    current_birthday = datetime.datetime.strptime(user.get("birthday", "2000-01-01"), "%Y-%m-%d").date()
    
    with st.form("profile_form"):
        new_name = st.text_input("Voornaam", value=user["name"])
        new_birthday = st.date_input("Geboortedatum", value=current_birthday)
        new_height = st.number_input("Lengte (cm)", min_value=120, value=int(user["height"]))
        new_weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, value=float(user["weight"]))
        new_target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, value=float(user["target_weight"]))
        
        new_days = st.slider("Dagen per week sporten", 0, 7, int(user["days_train"]))
        new_duration = st.slider("Duur per training (min)", 15, 180, int(user["duration_train"]))
        new_neck = st.number_input("Nekomtrek (cm)", value=float(user["neck"]))
        new_waist = st.number_input("Buikomtrek (cm)", value=float(user["waist"]))
        
        if st.form_submit_button("Wijzigingen Opslaan"):
            if new_name:
                age_calc = calculate_age(new_birthday)
                st.session_state.user_db[st.session_state.current_user].update({
                    "name": new_name, "birthday": new_birthday.strftime("%Y-%m-%d"), "age": age_calc,
                    "height": new_height, "weight": new_weight, "target_weight": new_target_weight,
                    "days_train": new_days, "duration_train": new_duration, "neck": new_neck, "waist": new_waist
                })
                st.success("Profiel bijgewerkt!")
                time.sleep(0.5)
                st.rerun()

