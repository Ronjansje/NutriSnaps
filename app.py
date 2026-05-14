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

# --- 2. AUTOMATISCHE SPIERGROEP DETECTIE (NLP LIGHT) ---
def parse_exercise_muscles(exercise_text):
    text = exercise_text.lower()
    detected = {}
    
    # Woordenboek voor trefwoord-koppelingen
    keywords = {
        "pushup": {"Borst": 1.0, "Triceps": 0.6, "Schouders": 0.4, "Core": 0.2},
        "push up": {"Borst": 1.0, "Triceps": 0.6, "Schouders": 0.4, "Core": 0.2},
        "bench": {"Borst": 1.0, "Triceps": 0.5, "Schouders": 0.3},
        "press": {"Borst": 0.8, "Schouders": 0.8, "Triceps": 0.4},
        "fly": {"Borst": 1.0, "Schouders": 0.2},
        "dip": {"Triceps": 1.0, "Borst": 0.7, "Schouders": 0.5},
        "pullup": {"Lats": 1.0, "Bovenrug": 0.8, "Biceps": 0.5, "Onderarmen": 0.3},
        "pull up": {"Lats": 1.0, "Bovenrug": 0.8, "Biceps": 0.5, "Onderarmen": 0.3},
        "chin": {"Biceps": 1.0, "Lats": 0.8, "Bovenrug": 0.4, "Onderarmen": 0.4},
        "row": {"Bovenrug": 1.0, "Lats": 0.7, "Biceps": 0.5, "Onderarmen": 0.3},
        "curl": {"Biceps": 1.0, "Onderarmen": 0.4},
        "bicep": {"Biceps": 1.0},
        "tricep": {"Triceps": 1.0},
        "extension": {"Triceps": 1.0},
        "squat": {"Quadriceps": 1.0, "Hamstrings": 0.4, "Core": 0.3},
        "leg": {"Quadriceps": 0.8, "Hamstrings": 0.8},
        "lung": {"Quadriceps": 1.0, "Hamstrings": 0.5},
        "deadlift": {"Hamstrings": 0.9, "Bovenrug": 0.7, "Core": 0.6},
        "plank": {"Core": 1.0, "Schouders": 0.2},
        "crunch": {"Core": 1.0},
        "situp": {"Core": 1.0},
        "mew": {"Kaaklijn": 1.0},
        "kauw": {"Kaaklijn": 1.0},
        "calf": {"Kuiten": 1.0},
        "kuit": {"Kuiten": 1.0},
        "raise": {"Schouders": 1.0}
    }
    
    # Check welke spieren matchen
    for key, muscles in keywords.items():
        if key in text:
            for m, val in muscles.items():
                detected[m] = max(detected.get(m, 0), val)
                
    # Fallback als er niks wordt herkend (alles een heel klein beetje voor de activiteit)
    if not detected:
        detected = {"Core": 0.2, "Borst": 0.2, "Bovenrug": 0.2}
        
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

# --- TAB 2: AI maaltijd SCANNER ---
with tab2:
    st.title("📸 AI Maaltijd Scanner")
    picture = st.camera_input("Maak een foto van je maaltijd")
    if picture is not None:
        with st.spinner("AI scant maaltijd..."): time.sleep(1)
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

# --- TAB 5: WORKOUTS & HOGE RESOLUTIE HEATMAP ---
with tab5:
    st.title("🗿 Slimme Trainingslog & 2D Anatomie")
    
    kaaklijn_chk = st.checkbox("Kaaklijntraining voltooid (Mewing / Kauwgom)", value=st.session_state.kaaklijn_gedaan, key="k_chk")
    st.session_state.kaaklijn_gedaan = kaaklijn_chk

    # Dynamische spierbelasting berekenen
    muscle_scores = {
        "Kaaklijn": 0, "Borst": 0, "Biceps": 0, "Triceps": 0, "Onderarmen": 0, 
        "Schouders": 0, "Core": 0, "Bovenrug": 0, "Lats": 0, "Quadriceps": 0, "Hamstrings": 0, "Kuiten": 0
    }
    
    for item in st.session_state.workout_log:
        total_vol = item["Sets"] * item["Reps"]
        for m_group, factor in item["Spieren"].items():
            if m_group in muscle_scores:
                muscle_scores[m_group] += total_vol * factor

    st.markdown("### 📊 Ultra-Gedetailleerde 2D Spieractivatie Kaart")
    
    js_data = json.dumps(muscle_scores)
    html_code = f"""
    <div style="text-align: center; background-color: #1F2937; padding: 15px; border-radius: 12px; display: flex; justify-content: space-around;">
        <div>
            <h5 style="color: #FF1493; margin-top:0; font-family:sans-serif;">VOORKANT</h5>
            <canvas id="frontCanvas" width="200" height="340" style="background-color:#111827; border-radius:8px;"></canvas>
        </div>
        <div>
            <h5 style="color: #00FFFF; margin-top:0; font-family:sans-serif;">ACHTERKANT</h5>
            <canvas id="backCanvas" width="200" height="340" style="background-color:#111827; border-radius:8px;"></canvas>
        </div>
    </div>
    <script>
        const scores = {js_data};
        let maxS = 0; for(let m in scores) {{ if(scores[m]>maxS) maxS=scores[m]; }}
        
        function c(mName) {{
            let s = scores[mName] || 0;
            if(s===0) return '#374151';
            let r = s / maxS;
            return `rgb(${{Math.floor(220+35*r)}}, ${{Math.floor(15*(1-r))}}, ${{Math.floor(130+125*r)}})`;
        }}
        
        // --- VOORKANT (Gedetailleerd) ---
        const f = document.getElementById('frontCanvas').getContext('2d');
        f.lineWidth = 1.5; f.strokeStyle = '#FFFFFF';
        
        // Hoofd & Kaak
        f.fillStyle = c('Kaaklijn'); f.beginPath(); f.arc(100, 30, 14, 0, Math.PI*2); f.fill(); f.stroke();
        // Schouders (Delts)
        f.fillStyle = c('Schouders');
        f.beginPath(); f.arc(63, 72, 11, 0, Math.PI*2); f.fill(); f.stroke();
        f.beginPath(); f.arc(137, 72, 11, 0, Math.PI*2); f.fill(); f.stroke();
        // Borst (Pecs opgesplitst links/rechts)
        f.fillStyle = c('Borst');
        f.fillRect(72, 68, 26, 28); f.strokeRect(72, 68, 26, 28);
        f.fillRect(102, 68, 26, 28); f.strokeRect(102, 68, 26, 28);
        // Abs / Core (Gedetailleerde blokken)
        f.fillStyle = c('Core');
        f.fillRect(76, 100, 48, 48); f.strokeRect(76, 100, 48, 48);
        // Armen (Biceps)
        f.fillStyle = c('Biceps');
        f.fillRect(48, 86, 13, 32); f.strokeRect(48, 86, 13, 32);
        f.fillRect(139, 86, 13, 32); f.strokeRect(139, 86, 13, 32);
        // Onderarmen (Forearms)
        f.fillStyle = c('Onderarmen');
        f.fillRect(45, 122, 11, 35); f.strokeRect(45, 122, 11, 35);
        f.fillRect(144, 122, 11, 35); f.strokeRect(144, 122, 11, 35);
        // Benen (Quadriceps)
        f.fillStyle = c('Quadriceps');
        f.fillRect(74, 154, 22, 80); f.strokeRect(74, 154, 22, 80);
        f.fillRect(104, 154, 22, 80); f.strokeRect(104, 154, 22, 80);

        // --- ACHTERKANT (Gedetailleerd) ---
        const b = document.getElementById('backCanvas').getContext('2d');
        b.lineWidth = 1.5; b.strokeStyle = '#FFFFFF';
        
        // Hoofd Achter
        b.fillStyle = '#374151'; b.beginPath(); b.arc(100, 30, 14, 0, Math.PI*2); b.fill(); b.stroke();
        // Bovenrug (Traps / Rhomboids)
        b.fillStyle = c('Bovenrug');
        b.fillRect(70, 65, 60, 25); b.strokeRect(70, 65, 60, 25);
        // Lats (V-vormige rugvleugels)
        b.fillStyle = c('Lats');
        b.fillRect(72, 94, 26, 42); b.strokeRect(72, 94, 26, 42);
        b.fillRect(102, 94, 26, 42); b.strokeRect(102, 94, 26, 42);
        // Armen (Triceps achterkant)
        b.fillStyle = c('Triceps');
        b.fillRect(48, 86, 13, 32); b.strokeRect(48, 86, 13, 32);
        b.fillRect(139, 86, 13, 32); b.strokeRect(139, 86, 13, 32);
        // Onderarmen Achter
        b.fillStyle = c('Onderarmen');
        b.fillRect(45, 122, 11, 35); b.strokeRect(45, 122, 11, 35);
        b.fillRect(144, 122, 11, 35); b.strokeRect(144, 122, 11, 35);
        // Hamstrings
        b.fillStyle = c('Hamstrings');
        b.fillRect(74, 154, 22, 75); b.strokeRect(74, 154, 22, 75);
        b.fillRect(104, 154, 22, 75); b.strokeRect(104, 154, 22, 75);
        // Kuiten (Calves)
        b.fillStyle = c('Kuiten');
        b.fillRect(75, 236, 18, 55); b.strokeRect(75, 236, 18, 55);
        b.fillRect(107, 236, 18, 55); b.strokeRect(107, 236, 18, 55);
    </script>
    """
    html(html_code, height=365)

    # --- 100% HANDMATIG WRITING-SYSTEEM ---
    st.markdown("### ✍️ Wat heb je vandaag gedaan?")
    with st.form("custom_exercise_form"):
        user_exercise_input = st.text_input("Schrijf hier je oefening op:", placeholder="Bijv. Heavy Dumbbell Bicep Curls of Benchpress")
        
        col1, col2 = st.columns(2)
        with col1: s_in = st.number_input("Sets", min_value=1, value=3)
        with col2: r_in = st.number_input("Reps", min_value=1, value=10)
        
        if st.form_submit_button("Oefening Analyseren & Loggen"):
            if user_exercise_input:
                # Analyseer welke spieren getraind worden met de parser
                detected_muscles = parse_exercise_muscles(user_exercise_input)
                
                # Sla op in de logs
                st.session_state.workout_log.append({
                    "Oefening": user_exercise_input,
                    "Sets": s_in,
                    "Reps": r_in,
                    "Spieren": detected_muscles
                })
                st.success(f"Gelogd! Automatisch gedetecteerde spieractivatie: {', '.join(detected_muscles.keys())}")
                time.sleep(0.5)
                st.rerun()

    if st.session_state.workout_log:
        st.markdown("##### 📋 Oefeningen van vandaag:")
        display_df = pd.DataFrame([
            {"Oefening": i["Oefening"], "Sets": i["Sets"], "Reps": i["Reps"], "Doelwitspieren": ", ".join(i["Spieren"].keys())}
            for i in st.session_state.workout_log
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
