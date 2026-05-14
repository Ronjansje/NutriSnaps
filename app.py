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
    .status-box { background-color: #1F2937; padding: 15px; border-radius: 10px; border-left: 5px solid #FF1493; margin-top: 15px; margin-bottom: 15px; }
    .routine-box { background-color: #1F2937; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #FF1493; }
    .streak-box { background-color: #1F2937; padding: 15px; border-radius: 10px; border: 2px dashed #FF1493; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Automatische spierherkenning op basis van trefwoorden
def voorspel_spieren(oefening_naam):
    naam = oefening_naam.lower()
    gevonden_spieren = []
    
    if "dip" in naam: gevonden_spieren.extend(["Triceps", "Onderkant Borst", "Voorkant Schouders"])
    if "push" in naam or "druk" in naam or "press" in naam: gevonden_spieren.extend(["Borstspieren", "Triceps", "Schouders"])
    if "pull" in naam or "row" in naam or "trek" in naam: gevonden_spieren.extend(["Brede Rugspier (Lats)", "Biceps", "Bovenrug"])
    if "chin" in naam: gevonden_spieren.extend(["Biceps", "Brede Rugspier"])
    if "curl" in naam: gevonden_spieren.extend(["Biceps (Armen)"])
    if "squat" in naam or "benen" in naam or "leg" in naam or "lunge" in naam: gevonden_spieren.extend(["Quadriceps (Bovenbenen)", "Gluteus (Billen)", "Hamstrings"])
    if "raise" in naam or "fly" in naam: gevonden_spieren.extend(["Schouders (Deltoideus)"])
    if "plank" in naam or "crunch" in naam or "sit" in naam or "abs" in naam or "hold" in naam: gevonden_spieren.extend(["Rechte Buikspieren", "Core Stabiliteit"])
    if "calf" in naam or "kuit" in naam: gevonden_spieren.extend(["Kuiten"])
    if "deadlift" in naam: gevonden_spieren.extend(["Onderrug", "Hamstrings", "Billen", "Gripkracht"])
    
    if not gevonden_spieren:
        return "Algemene spiergroepen (Geen specifieke match gevonden)"
    
    return ", ".join(list(set(gevonden_spieren)))

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
if "kaaklijn_vinkjes" not in st.session_state: st.session_state.kaaklijn_vinkjes = {}
if "kaaklijn_streak" not in st.session_state: st.session_state.kaaklijn_streak = 0
if "last_streak_date" not in st.session_state: st.session_state.last_streak_date = ""

# Gewichtsgeschiedenis initialisatie
if "weight_history" not in st.session_state:
    st.session_state.weight_history = [
        {"Datum": "2026-04-19", "Gewicht (kg)": 82.0},
        {"Datum": "2026-04-26", "Gewicht (kg)": 81.2},
        {"Datum": "2026-05-03", "Gewicht (kg)": 80.5}
    ]

if "pr_history" not in st.session_state:
    st.session_state.pr_history = [
        {"Datum": "2026-04-26", "Pushups": 10, "Pullups": 3, "Pistol Squats": 1, "Plank (sec)": 30},
        {"Datum": "2026-05-03", "Pushups": 12, "Pullups": 4, "Pistol Squats": 2, "Plank (sec)": 45}
    ]

OEFENINGEN_INFO = {
    "Pushups": "Borstspieren (Pectoralis), Triceps, Voorkant Schouders (Deltoideus), Core",
    "Diamond Pushups": "Triceps (Binnenkop), Grote Borstspier, Voorkant Schouders",
    "Pullups": "Brede Rugspier (Latissimus Dorsi), Biceps, Onderarmen, Bovenrug",
    "Chin-ups": "Biceps Brachii, Brede Rugspier, Grote Ronde Rugspier, Core",
    "Pistol Squats": "Quadriceps (Bovenbenen), Gluteus Maximus (Billen), Hamstrings, Kuiten",
    "Plank": "Rechte Buikspieren (Abs), Schuine Buikspieren, Onderrug, Schouders"
}

DAGELIJKSE_KAAKLIJN_ROUTINE = {
    "Mewing (Tongpositie)": {
        "doel": "Tong plat tegen het gehemelte houden, ademen door de neus.",
        "duur": "Hele dag (focus op 10 min)",
        "spieren": "Tongbeenspieren (Digastricus), Kaaklijnspieren (Masseter), Kaak-tongspier"
    },
    "Jawline Chews / Mastiek Gom": {
        "doel": "Kauw krachtig op harde gom of kaaklijntrainers.",
        "duur": "5 tot 10 minuten",
        "spieren": "Kauwspier (Masseter), Slaapspier (Temporalis)"
    },
    "Chin Tucks (Dubbele kin oefening)": {
        "doel": "Trek je hoofd recht naar achteren alsof je een dubbele kin maakt.",
        "duur": "3 sets van 15 herhalingen",
        "spieren": "Diepe nekinbuigers, Houdingsspieren van de nek"
    },
    "Neck Curls (Platysma Activatie)": {
        "doel": "Lig op je rug, til je hoofd op en breng je kin naar je borst.",
        "duur": "3 sets van 20 herhalingen",
        "spieren": "Halsspier (Platysma), Sternocleidomastoideus (Nekspier)"
    }
}

def save_to_browser():
    payload = {
        "user_db": st.session_state.user_db, "current_user": st.session_state.current_user,
        "logged_in": st.session_state.logged_in, "water_ml": st.session_state.water_ml,
        "kcal_gegeten": st.session_state.kcal_gegeten, "eiwit_gegeten": st.session_state.eiwit_gegeten,
        "oefening_log": st.session_state.oefening_log, "pushup_record": st.session_state.pushup_record,
        "pullup_record": st.session_state.pullup_record, "pistol_record": st.session_state.pistol_record,
        "plank_record": st.session_state.plank_record, "pr_history": st.session_state.pr_history,
        "last_log_date": st.session_state.last_log_date, "kaaklijn_vinkjes": st.session_state.kaaklijn_vinkjes,
        "kaaklijn_streak": st.session_state.kaaklijn_streak, "last_streak_date": st.session_state.last_streak_date,
        "weight_history": st.session_state.weight_history
    }
    json_str = json.dumps(payload).replace("'", "\\'")
    html(f"<script>localStorage.setItem('nutrisnap_core_data', '{json_str}');</script>", height=0)

# --- 3. BROWSER DATA SYNC & RESET CONTROL ---
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
        st.session_state.kaaklijn_vinkjes = raw_data.get("kaaklijn_vinkjes", {})
        st.session_state.kaaklijn_streak = raw_data.get("kaaklijn_streak", 0)
        st.session_state.last_streak_date = raw_data.get("last_streak_date", "")
        st.session_state.weight_history = raw_data.get("weight_history", st.session_state.weight_history)
        st.session_state.synced = True
        
        if st.session_state.last_log_date != vandaag_str:
            if st.session_state.last_streak_date:
                laatste_streak_dag = datetime.datetime.strptime(st.session_state.last_streak_date, "%Y-%m-%d").date()
                if (datetime.date.today() - laatste_streak_dag).days > 1:
                    st.session_state.kaaklijn_streak = 0
            
            st.session_state.water_ml = 0
            st.session_state.kcal_gegeten = 0
            st.session_state.eiwit_gegeten = 0
            st.session_state.oefening_log = []
            st.session_state.kaaklijn_vinkjes = {}
            st.session_state.last_log_date = vandaag_str
            save_to_browser()
        st.rerun()
    except:
        pass

if "browser_data" not in query_params and not st.session_state.get("synced", False):
    html("""<script>const localData = localStorage.getItem("nutrisnap_core_data"); if (localData) { const url = new URL(window.parent.location.href); url.searchParams.set("browser_data", localData); window.parent.location.href = url.toString(); }</script>""", height=0)

# --- 4. INLOG / REGISTRATIE SCHERM ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI Pro")
    auth_option = st.radio("Kies optie:", ["Inloggen", "Account Aanmaken"], horizontal=True)
    email_input = st.text_input("E-mailadres")
    password_input = st.text_input("Wachtwoord", type="password")
    
    if auth_option == "Account Aanmaken":
        name = st.text_input("Voornaam")
        birthday = st.date_input("Geboortedatum", datetime.date(2005, 1, 1))
        height = st.number_input("Lengte (cm)", min_value=120, value=180)
        weight = st.number_input("Huidig Gewicht (kg)", min_value=40.0, value=80.0)
        target_weight = st.number_input("Doel Gewicht (kg)", min_value=40.0, value=75.0)
        days_train = st.slider("Dagen per week sporten", 0, 7, 3)
        duration_train = st.slider("Duur per training (min)", 15, 180, 60)
        neck_in = st.number_input("Nekomtrek (cm)", min_value=20.0, value=38.0)
        waist_in = st.number_input("Buikomtrek (cm)", min_value=50.0, value=85.0)
        
        if st.button("Registreren"):
            if "@" in email_input and password_input and name:
                age_calc = datetime.date.today().year - birthday.year - ((datetime.date.today().month, datetime.date.today().day) < (birthday.month, birthday.day))
                st.session_state.user_db[email_input] = {
                    "password": make_hashes(password_input), "name": name, "birthday": birthday.strftime("%Y-%m-%d"), "age": age_calc,
                    "height": height, "weight": weight, "target_weight": target_weight, "days_train": days_train, "duration_train": duration_train, "neck": neck_in, "waist": waist_in
                }
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
                st.session_state.user_db[email_input] = {"password": hashed_pwd, "name": "Gebruiker", "birthday": "2006-01-01", "age": 20, "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85}
                st.session_state.logged_in, st.session_state.current_user = True, email_input
                save_to_browser()
                st.rerun()
    st.stop()

# --- 5. HOOFDAPPLICATIE BEREKENINGEN ---
user = st.session_state.user_db.get(st.session_state.current_user, {"name": "Gebruiker", "birthday": "2006-01-01", "age": 20, "height": 180, "weight": 80, "target_weight": 75, "days_train": 3, "duration_train": 60, "neck": 38, "waist": 85})
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

vinkjes_teller = sum(1 for v in st.session_state.kaaklijn_vinkjes.values() if v)
totaal_routines = len(DAGELIJKSE_KAAKLIJN_ROUTINE)

st.sidebar.title("✨ NutriSnap Pro")
if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    html("<script>localStorage.removeItem('nutrisnap_core_data'); window.parent.location.search = '';</script>", height=0)
    st.rerun()

# Toegevoegd: "👤 Account" Tabblad aan de navigatiebalk
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Dashboard", "📸 AI Scanner", "📈 Voortgang", "💧 Water & Eten", "🗿 Oefeningen", "👤 Account"])

# --- TAB 1: HOOFDSCHERM (DASHBOARD) ---
with tab1:
    st.title(f"Hoi {user['name']}! 👋")
    if datetime.date.today().weekday() == 6: st.error("🚨 **WEEG- EN TESTDAG!** Voer je nieuwe gewicht en PR's in!")
    
    st.markdown("### 📋 Status Kaaklijn Routine")
    if vinkjes_teller == totaal_routines:
        st.markdown("""<div class="status-box" style="border-left-color: #00FF00;"><b style="color: #00FF00;">✅ Kaaklijn Routine Compleet!</b></div>""", unsafe_allow_html=True)
    elif vinkjes_teller > 0:
        st.markdown(f"""<div class="status-box" style="border-left-color: #FFD700;"><b style="color: #FFD700;">⏳ Gestart ({vinkjes_teller}/{totaal_routines} gedaan)</b></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="status-box" style="border-left-color: #FF1493;"><b style="color: #FF1493;">❌ Routine nog niet gedaan (0/4)</b></div>""", unsafe_allow_html=True)

    st.markdown("### 📏 Lichaamscompositie")
    st.markdown(f"""<div class="fat-box"><h4 style="margin:0; color:#00FFFF;">🧬 Vetpercentage: {vetpercentage:.1f}%</h4></div>""", unsafe_allow_html=True)
    if vet_te_verliezen > 0: st.warning(f"🗿 Nog **{vet_te_verliezen:.1f} kg vet** te verliezen voor doel (12%).")

# --- TAB 2: AI SCANNER ---
with tab2:
    st.title("📸 AI Scanner")
    if st.camera_input("Scan maaltijd"):
        if st.button("Analyseer"):
            st.success("450 kcal & 32g Eiwit toegevoegd!")
            st.session_state.kcal_gegeten += 450; st.session_state.eiwit_gegeten += 32; save_to_browser(); st.rerun()

# --- TAB 3: VOORTGANG (INCLUSIEF SAMENGEVOEGDE EN GEWICHTS GRAFIEK) ---
with tab3:
    st.title("📈 Voortgang & Statistieken")
    
    st.markdown("### 📉 Gewichtsverloop (Zondagse Weging)")
    df_weight = pd.DataFrame(st.session_state.weight_history)
    st.line_chart(data=df_weight, x="Datum", y="Gewicht (kg)", color="#00FFFF")
    
    with st.form("weight_form"):
        w_date = st.date_input("Weegdatum", datetime.date.today()).strftime("%Y-%m-%d")
        w_val = st.number_input("Nieuw gewicht (kg)", min_value=30.0, max_value=200.0, value=float(user["weight"]))
        if st.form_submit_button("⚖️ Gewicht Opslaan"):
            st.session_state.weight_history = [h for h in st.session_state.weight_history if h["Datum"] != w_date]
            st.session_state.weight_history.append({"Datum": w_date, "Gewicht (kg)": w_val})
            st.session_state.weight_history = sorted(st.session_state.weight_history, key=lambda x: x["Datum"])
            st.session_state.user_db[st.session_state.current_user]["weight"] = w_val
            save_to_browser(); st.rerun()

    st.markdown("### 📊 Kracht Progressie")
    st.line_chart(data=pd.DataFrame(st.session_state.pr_history), x="Datum", y=["Pushups", "Pullups", "Pistol Squats", "Plank (sec)"])
    with st.form("pr_form"):
        d = st.date_input("Testdatum", datetime.date.today()).strftime("%Y-%m-%d")
        pu = st.number_input("Pushups Max", value=st.session_state.pushup_record)
        pl = st.number_input("Pullups Max", value=st.session_state.pullup_record)
        pi = st.number_input("Pistols Max", value=st.session_state.pistol_record)
        pk = st.number_input("Plank Max (sec)", value=st.session_state.plank_record)
        if st.form_submit_button("PR's Opslaan"):
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

# --- TAB 5: OEFENINGEN ---
with tab5:
    st.title("🗿 Oefeningen & Routines")
    st.markdown(f"""<div class="streak-box"><h2 style="margin:0; color:#FF1493;">🔥 Kaaklijn Streak: {st.session_state.kaaklijn_streak} Dagen</h2></div>""", unsafe_allow_html=True)
    
    st.markdown("### 🦴 Dagelijks Kaaklijn Schema")
    for titel, data in DAGELIJKSE_KAAKLIJN_ROUTINE.items():
        st.markdown(f"""<div class="routine-box"><b style="color: #FF1493;">{titel}</b><br><small>{data['doel']}</small></div>""", unsafe_allow_html=True)
        is_checked = st.session_state.kaaklijn_vinkjes.get(titel, False)
        vinkje = st.checkbox("Gerealiseerd", value=is_checked, key=f"chk_{titel}")
        
        if vinkje and not is_checked:
            st.session_state.kaaklijn_vinkjes[titel] = True
            st.session_state.oefening_log.insert(0, {"Tijd": datetime.datetime.now().strftime("%H:%M"), "Oefening": titel, "Volume": "1 Sessie", "Getrainde Spieren": data["spieren"]})
            st.success(f"Geregistreerd!")
            st.info(f"🧬 **Getrainde Gezichtsspieren:** {data['spieren']}")
            nieuwe_telling = vinkjes_teller + 1
            if nieuwe_telling == len(DAGELIJKSE_KAAKLIJN_ROUTINE) and st.session_state.last_streak_date != vandaag_str:
                st.session_state.kaaklijn_streak += 1
                st.session_state.last_streak_date = vandaag_str
                st.balloons()
            save_to_browser(); time.sleep(2); st.rerun()
            
        elif not vinkje and is_checked:
            st.session_state.kaaklijn_vinkjes[titel] = False
            st.session_state.oefening_log = [l for l in st.session_state.oefening_log if l["Oefening"] != titel]
            if st.session_state.last_streak_date == vandaag_str:
                st.session_state.kaaklijn_streak = max(0, st.session_state.kaaklijn_streak - 1)
                st.session_state.last_streak_date = ""
            save_to_browser(); st.rerun()

    st.markdown("---")
    st.markdown("### 🏋️‍♂️ Krachtoefening Registreren")
    suggesties = ["Zelf opschrijven..."] + list(OEFENINGEN_INFO.keys())
    keuze = st.selectbox("Kies een oefening of typ volledig zelf:", suggesties)
    
    if keuze == "Zelf opschrijven...":
        oefening_naam = st.text_input("Naam van de oefening:", placeholder="Bijv. Incline Bench Press")
        oefening_spieren = ""
    else:
        oefening_naam = keuze
        oefening_spieren = OEFENINGEN_INFO[keuze]
        st.info(f"🧬 **Gekoppelde spieren:** {oefening_spieren}")

    sets = st.number_input("Sets", min_value=1, value=3)
    reps = st.number_input("Reps", min_value=1, value=10)
    
    if st.button("💪 Log Deze Oefening"):
        if not oefening_naam:
            st.error("Vul een naam in.")
        else:
            eind_spieren = voorspel_spieren(oefening_naam) if keuze == "Zelf opschrijven..." else oefening_spieren
            st.session_state.oefening_log.insert(0, {"Tijd": datetime.datetime.now().strftime("%H:%M"), "Oefening": oefening_naam, "Volume": f"{sets}x{reps}", "Getrainde Spieren": eind_spieren})
            st.success("Succesvol geregistreerd!")
            st.info(f"🧬 **Automatische Spierdetectie:** {eind_spieren}")
            save_to_browser(); time.sleep(2.5); st.rerun()

# --- TAB 6: ACCOUNT PERSONALISATIE (HERSTELD & VERBETERD) ---
with tab6:
    st.title("👤 Mijn Account & Instellingen")
    st.caption("Pas hier je persoonlijke profielgegevens aan. De macro-doelen veranderen automatisch mee.")
    
    with st.form("account_settings_form"):
        new_name = st.text_input("Voornaam of Displaynaam", value=user["name"])
        
        # Geboortedatum parsering om fouten te voorkomen
        
