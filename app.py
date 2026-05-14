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

# --- 2. INITIALISATIE STATE ---
vandaag_str = datetime.date.today().strftime("%Y-%m-%d")

if "user_db" not in st.session_state: st.session_state.user_db = {}
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "water_ml" not in st.session_state: st.session_state.water_ml = 0
if "kcal_gegeten" not in st.session_state: st.session_state.kcal_gegeten = 0
if "eiwit_gegeten" not in st.session_state: st.session_state.eiwit_gegeten = 0
if "oefening_log" not in st.session_state: st.session_state.oefening_log = []
if "pushup_record" not in st.session_state: st.session_state.pushup_record = 12
if "pullup_record" not in st.session_state: st.session_state.pullup_record = 4
if "pistol_record" not in st.session_state: st.session_state.pistol_record = 2
if "plank_record" not in st.session_state: st.session_state.plank_record = 45
if "last_log_date" not in st.session_state: st.session_state.last_log_date = vandaag_str
if "pr_history" not in st.session_state:
    st.session_state.pr_history = [
        {"Datum": "2026-04-26", "Pushups": 10, "Pullups": 3, "Pistol Squats": 1, "Plank (sec)": 30},
        {"Datum": "2026-05-03", "Pushups": 12, "Pullups": 4, "Pistol Squats": 2, "Plank (sec)": 45}
    ]

# Vaste suggesties voor oefeningen
OEFENINGEN_INFO = {
    "Pushups": "Borst, Triceps, Schouders, Core",
    "Diamond Pushups": "Triceps, Borst, Schouders",
    "Pullups": "Rug, Biceps, Core",
    "Chin-ups": "Biceps, Rug, Core",
    "Pistol Squats": "Benen, Billen, Hamstrings",
    "Plank": "Core, Schouders, Onderrug"
}

# Vaste info voor kaaklijnoefeningen
KAAK_INFO = {
    "Mewing (Tongpositie)": "Kaaklijnspieren (Masseter), Tongbeenspieren",
    "Jawline Chews / Gum": "Kauwspieren (Masseter, Temporalis)",
    "Neck Curls (Houding)": "Halsspier (Platysma), Nekspieren"
}

def save_to_browser():
    payload = {
        "user_db": st.session_state.user_db, "current_user": st.session_state.current_user,
        "logged_in": st.session_state.logged_in, "water_ml": st.session_state.water_ml,
        "kcal_gegeten": st.session_state.kcal_gegeten, "eiwit_gegeten": st.session_state.eiwit_gegeten,
        "oefening_log": st.session_state.oefening_log, "pushup_record": st.session_state.pushup_record,
        "pullup_record": st.session_state.pullup_record, "pistol_record": st.session_state.pistol_record,
        "plank_record": st.session_state.plank_record, "pr_history": st.session_state.pr_history,
        "last_log_date": st.session_state.last_log_date
    }
    json_str = json.dumps(payload).replace("'", "\\'")
    html(f"<script>localStorage.setItem('nutrisnap_core_data', '{json_str}');</script>", height=0)

# --- 3. BROWSER DATA SYNC ---
query_params = st.query_params
if "browser_data" in query_params and not st.session_state.get("synced", False):
    try:
        raw_data = json.loads(query_params["browser_data"])
        st.session_state.user_db = raw_data.get("user_db", {})
        st.session_state.current_user = raw_data.get("current_user", "")
        st.session_state.logged_in = raw_data.get("logged_in", False)
        st.session_state.water_ml = raw_data.get("water_ml", 0)
        st.session_state.kcal_gegeten = raw_data.get("kcal_gegeten", 0)
        st.session_state.eiwit_gegeten = raw_data.get("eiwit_gegeten", 0)
        st.session_state.oefening_log = raw_data.get("oefening_log", [])
        st.session_state.pushup_record = raw_data.get("pushup_record", 12)
        st.session_state.pullup_record = raw_data.get("pullup_record", 4)
        st.session_state.pistol_record = raw_data.get("pistol_record", 2)
        st.session_state.plank_record = raw_data.get("plank_record", 45)
        st.session_state.pr_history = raw_data.get("pr_history", st.session_state.pr_history)
        st.session_state.last_log_date = raw_data.get("last_log_date", vandaag_str)
        st.session_state.synced = True
        
        if st.session_state.last_log_date != vandaag_str:
            st.session_state.water_ml, st.session_state.kcal_gegeten, st.session_state.eiwit_gegeten = 0, 0, 0
            st.session_state.oefening_log = []
            st.session_state.last_log_date = vandaag_str
            save_to_browser()
        st.rerun()
    except:
        pass

if "browser_data" not in query_params and not st.session_state.get("synced", False):
    html("""<script>const localData = localStorage.getItem("nutrisnap_core_data"); if (localData) { const url = new URL(window.parent.location.href); url.searchParams.set("browser_data", localData); window.parent.location.href = url.toString(); }</script>""", height=0)

# --- 4. INLOG / REGISTRATIE ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI Pro")
    auth_option = st.radio("Kies optie:", ["Inloggen", "Account Aanmaken"], horizontal=True)
    email_input = st.text_input("E-mailadres")
    password_input = st.text_input("Wachtwoord", type="password")
    
    if auth_option == "Account Aanmaken":
        name = st.text_input("Voornaam")
        age = st.number_input("Leeftijd", min_value=12, value=20)
        height = st.number_input("Lengte (cm)", min_value=120, value=180)
        weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, value=80.0)
        target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, value=75.0)
        days_train = st.slider("Dagen per week sporten", 0, 7, 3)
        duration_train = st.slider("Duur per training (min)", 15, 180, 60)
        neck_in = st.number_input("Nekomtrek (cm)", min_value=20.0, value=38.0)
        waist_in = st.number_input("Buikomtrek (cm)", min_value=50.0, value=85.0)
        
        if st.button("Registreren"):
            if "@" in email_input and password_input and name:
                st.session_state.user_db[email_input] = {"password": make_hashes(password_input), "name": name, "age": age, "height": height, "weight": weight, "target_weight": target_weight, "days_train": days_train, "duration_train": duration_train, "neck": neck_in, "waist": waist_in}
                st.session_state.logged_in, st.session_state.current_user, st.session_state.last_log_date = True, email_input, vandaag_str
                save_to_browser()
                st.rerun()
    elif auth_option == "Inloggen":
        if st.button("Inloggen"):
            hashed_pwd = make_hashes(password_input)
            if email_input in st.session_state.user_db and st.session_state.user_db[email_input]["password"] == hashed_pwd:
                st.session_state.logged_in, st.session_state.current_user = True, email_input
                save_to_browser()
                st.rerun()
            elif email_input and password_input:
                st.session_state.user_db[email_input] = {"password": hashed_pwd, "name": "Gebruiker", "age": 20, "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85}
                st.session_state.logged_in, st.session_state.current_user = True, email_input
                save_to_browser()
                st.rerun()
    st.stop()

# --- 5. HOOFDAPPLICATIE BEREKENINGEN ---
user = st.session_state.user_db.get(st.session_state.current_user, {"name": "Gebruiker", "age": 20, "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85})
bmr = (10 * user["weight"]) + (6.25 * user["height"]) - (5 * user["age"]) + 5
activity = 1.2 if user["days_train"] <= 1 else 1.375 if user["days_train"] <= 3 else 1.55 if user["days_train"] <= 5 else 1.725
extra_kcal = (user["duration_train"] * 6 * user["days_train"]) / 7
afval_kcal = int((bmr * activity) + extra_kcal - 500)
doel_eiwit = int(user["weight"] * 2.0)
doel_water_liters = round((user["weight"] * 0.035) + ((user["duration_train"] * 0.01 * user["days_train"]) / 7), 1)

try:
    vetpercentage = 86.010 * math.log10(user["waist"] - user["neck"]) - 70.041 * math.log10(user["height"]) + 36.76
    vet_te_verliezen = max(0.0, (user["weight"] * (vetpercentage / 100)) - (user["weight"] * 0.12))
except:
    vetpercentage, vet_te_verliezen = 15.0, 0.0

st.sidebar.title("✨ NutriSnap Pro")
if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    html("<script>localStorage.removeItem('nutrisnap_core_data'); window.parent.location.search = '';</script>", height=0)
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Hoofdscherm", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen"])

# --- TAB 1: HOOFDSCHERM ---
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    if datetime.date.today().weekday() == 6: st.error("🚨 **TESTDAG!** Voer je nieuwe PR's in!")
    st.markdown(f"""<div class="fat-box"><h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4></div>""", unsafe_allow_html=True)
    if vet_te_verliezen > 0: st.warning(f"🗿 Nog **{vet_te_verliezen:.1f} kg vet** te verliezen voor doel (12%).")

    st.markdown("### 🏅 Actuele PR Rangen")
    st.markdown(f"""<div class="badge-grid">
        <div class="badge-box"><b>Pushups</b><br>{st.session_state.pushup_record} reps</div>
        <div class="badge-box"><b>Pullups</b><br>{st.session_state.pullup_record} reps</div>
        <div class="badge-box"><b>Pistols</b><br>{st.session_state.pistol_record} reps</div>
        <div class="badge-box"><b>Plank</b><br>{st.session_state.plank_record}s</div>
    </div>""", unsafe_allow_html=True)

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Scanner")
    if st.camera_input("Scan maaltijd"):
        if st.button("Analyseer"):
            st.success("450 kcal & 32g Eiwit toegevoegd!")
            st.session_state.kcal_gegeten += 450; st.session_state.eiwit_gegeten += 32; save_to_browser(); st.rerun()

# --- TAB 3: VOORTGANG ---
with tab3:
    st.title("📈 Progressie")
    st.line_chart(data=pd.DataFrame(st.session_state.pr_history), x="Datum", y=["Pushups", "Pullups", "Pistol Squats", "Plank (sec)"])
    with st.form("pr_form"):
        d = st.date_input("Testdatum", datetime.date.today()).strftime("%Y-%m-%d")
        pu = st.number_input("Pushups Max", value=st.session_state.pushup_record)
        pl = st.number_input("Pullups Max", value=st.session_state.pullup_record)
        pi = st.number_input("Pistols Max", value=st.session_state.pistol_record)
        pk = st.number_input("Plank Max (sec)", value=st.session_state.plank_record)
        if st.form_submit_button("PR Opslaan"):
            st.session_state.pushup_record, st.session_state.pullup_record, st.session_state.pistol_record, st.session_state.plank_record = pu, pl, pi, pk
            st.session_state.pr_history = [h for h in st.session_state.pr_history if h["Datum"] != d]
            st.session_state.pr_history.append({"Datum": d, "Pushups": pu, "Pullups": pl, "Pistol Squats": pi, "Plank (sec)": pk})
            save_to_browser(); st.rerun()

# --- TAB 4: WATER & VOEDING ---
with tab4:
    st.title("💧 Water & Voeding")
    st.metric("Water", f"{st.session_state.water_ml / 1000:.1f} / {doel_water_liters} L")
    st.metric("Eiwit", f"{st.session_state.eiwit_gegeten} / {doel_eiwit} g")
    st.metric("Calorieën", f"{st.session_state.kcal_gegeten} / {afval_kcal} kcal")
    if st.button("➕ 250ml"): st.session_state.water_ml += 250; save_to_browser(); st.rerun()

# --- TAB 5: OEFENINGEN (KAAKLIJN & KRACHT OPSCHRIJVEN) ---
with tab5:
    st.title("🗿 Oefeningen & Routines Tracker")
    
    # SECTIE A: KAAKLIJN OEFENINGEN
    st.markdown("### 🦴 Kaaklijn & Gezichtsspieren")
    kaak_oefening = st.selectbox("Kies je kaaklijnoefening:", list(KAAK_INFO.keys()))
    kaak_duur = st.number_input("Duur (minuten)", min_value=1, max_value=60, value=5)
    
    if st.button("🗿 Log Kaaklijn Oefening"):
        spieren = KAAK_INFO[kaak_oefening]
        st.session_state.oefening_log.insert(0, {
            "Tijd": datetime.datetime.now().strftime("%H:%M"),
            "Oefening": kaak_oefening,
            "Volume": f"{kaak_duur} min",
            "Getrainde Spieren": spieren
        })
        st.success(f"Gelogd! Getrainde spieren: {spieren}")
        save_to_browser()
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    
    # SECTIE B: EIGEN KRACHTOEFENINGEN OPSCHRIJVEN
    st.markdown("### 🏋️‍♂️ Krachtoefening Registreren")
    
    suggesties = ["Zelf opschrijven..."] + list(OEFENINGEN_INFO.keys())
    keuze = st.selectbox("Kies een oefening of schrijf zelf:", suggesties)
    
    # Dynamisch invoerveld als men kiest voor zelf opschrijven
    if keuze == "Zelf opschrijven...":
        oefening_naam = st.text_input("Schrijf hier de naam van je oefening:", placeholder="Bijv. Weighted Dips")
        oefening_spieren = st.text_input("Welke spieren train je hiermee?", placeholder="Bijv. Borst, Triceps")
    else:
        oefening_naam = keuze
        oefening_spieren = OEFENINGEN_INFO[keuze]
        st.info(f"🧬 **Automatische spiergroepen:** {oefening_spieren}")

    sets = st.number_input("Sets", min_value=1, value=3)
    reps = st.number_input("Reps / Seconden", min_value=1, value=10)
    
    if st.button("💪 Log Kracht Oefening"):
        if not oefening_naam:
            st.error("Vul eerst de naam van je oefening in.")
        else:
            st.session_state.oefening_log.insert(0, {
                "Tijd": datetime.datetime.now().strftime("%H:%M"),
                "Oefening": oefening_naam,
                "Volume": f"{sets}x{reps}",
                "Getrainde Spieren": oefening_spieren if oefening_spieren else "Algemeen"
            })
            st.success(f"'{oefening_naam}' toegevoegd aan je logboek!")
            save_to_browser()
            time.sleep(1)
            st.rerun()
        
    # LOGBOEK WEERGAVE
    st.markdown("### 📖 Logboek (Vandaag)")
    if st.session_state.oefening_log:
        st.dataframe(pd.DataFrame(st.session_state.oefening_log), use_container_width=True, hide_index=True)
        if st.button("🗑️ Logboek Leegmaken"):
            st.session_state.oefening_log = []
            save_to_browser(); st.rerun()
    else:
        st.caption("Nog geen oefeningen gedaan vandaag.")
