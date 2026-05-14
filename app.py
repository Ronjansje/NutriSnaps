import streamlit as st
import pandas as pd
import datetime
import hashlib
import time

# --- 1. CONFIGURATION & DARK MODE ---
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

# --- 2. LOCAL DATABASE IN MEMORY ---
if "user_db" not in st.session_state:
    st.session_state.user_db = {} # Saves accounts locally

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 3. SESSION STATE TRACKING INITIALIZATION ---
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

# --- 4. AUTHENTICATION SCREEN ---
if not st.session_state.logged_in:
    st.title("📸 NutriSnap AI")
    st.caption("Securely log in on your device")
        
    auth_option = st.radio("Choose an option:", ["Log In", "Create Account"], horizontal=True)
    email_input = st.text_input("Email Address")
    password_input = st.text_input("Password", type="password")
    
    if auth_option == "Create Account":
        name = st.text_input("First Name")
        age = st.number_input("Age", min_value=12, max_value=100, value=20)
        height = st.number_input("Height (cm)", min_value=120, max_value=230, value=180)
        weight = st.number_input("Current Weight (kg)", min_value=40.0, max_value=180.0, value=80.0)
        target_weight = st.number_input("Target Weight (kg)", min_value=40.0, max_value=180.0, value=75.0)
        days_train = st.slider("Number of days per week to exercise", 0, 7, 3)
        duration_train = st.slider("Average duration per training (minutes)", 15, 180, 60)
        
        if st.button("Register"):
            if "@" in email_input and password_input and name:
                if email_input not in st.session_state.user_db:
                    st.session_state.user_db[email_input] = {
                        "password": make_hashes(password_input), "name": name, "age": age,
                        "height": height, "weight": weight, "target_weight": target_weight,
                        "days_train": days_train, "duration_train": duration_train
                    }
                    st.success("Account successfully created! You can now log in.")
                else:
                    st.error("This email address is already registered.")
            else:
                st.error("Please fill in all fields correctly.")
                
    elif auth_option == "Log In":
        if st.button("Log In"):
            hashed_pwd = make_hashes(password_input)
            if email_input in st.session_state.user_db and st.session_state.user_db[email_input]["password"] == hashed_pwd:
                st.session_state.logged_in = True
                st.session_state.current_user = email_input
                st.rerun()
            else:
                st.error("Incorrect email or password.")
    st.stop()

# --- 5. USER DATA & SETTINGS ---
user = st.session_state.user_db[st.session_state.current_user]

# Dynamic health calculations
bmr = (10 * user["weight"]) + (6.25 * user["height"]) - (5 * user["age"]) + 5
activity = 1.2 if user["days_train"] <= 1 else 1.375 if user["days_train"] <= 3 else 1.55 if user["days_train"] <= 5 else 1.725
extra_kcal = (user["duration_train"] * 6 * user["days_train"]) / 7
afval_kcal = int((bmr * activity) + extra_kcal - 500)
doel_eiwit = int(user["weight"] * 2.0)
doel_water_liters = round((user["weight"] * 0.035) + ((user["duration_train"] * 0.01 * user["days_train"]) / 7), 1)

st.sidebar.title("✨ NutriSnap Pro")
st.sidebar.markdown(f"Logged in as: **{user['name']}**")
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "📸 AI Scanner", "📈 Progress", "💧 Water & Food", "🗿 Exercises"])

# --- TAB 1: HOME SCREEN ---
with tab1:
    st.title(f"Hi {user['name']}! 👋")
    resterend_kcal = max(0, afval_kcal - st.session_state.kcal_gegeten)
    resterend_water = max(0.0, doel_water_liters - (st.session_state.water_ml / 1000))
    resterend_eiwit = max(0, doel_eiwit - st.session_state.eiwit_gegeten)
    
    st.subheader("📊 Daily Nutritional Status")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Calories Status**")
        st.dataframe(pd.DataFrame({"Status": ["Eaten", "Remaining"], "Kcal": [st.session_state.kcal_gegeten, resterend_kcal]}), hide_index=True) 
    with col2:
        st.write("**Protein Status**")
        st.dataframe(pd.DataFrame({"Status": ["In", "Remaining"], "Gram": [st.session_state.eiwit_gegeten, resterend_eiwit]}), hide_index=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1: st.metric(label="Remaining to eat", value=f"{resterend_kcal} kcal", delta=f"Goal: {afval_kcal}")
    with col_m2: st.metric(label="Remaining to drink", value=f"{resterend_water:.1f} L", delta=f"Goal: {doel_water_liters}L")

    st.markdown("### 📋 Checklist")
    st.success("✅ Jawline training completed!") if st.session_state.kaaklijn_gedaan else st.info("❌ You still need to do your jawline exercises.")
    st.success("✅ Strength training registered!") if st.session_state.oefening_gedaan else st.warning("⚠️ Enter your workout for today.")

# --- TAB 2: AI SCANNER (SIMPLE SCAN SIMULATION) ---
with tab2:
    st.header("📸 AI Meal Scanner")
    foto = st.camera_input("Photograph your food")
    if not foto:
        foto = st.file_uploader("Or choose a photo from your gallery", type=["jpg", "jpeg", "png"])
        
    if foto:
        st.success("Photo successfully loaded! AI starts analyzing...")
        # Direct super-fast simulation without complicated API keys
        kcal_gescand = 420
        eiwit_gescand = 28
        st.metric(label="Scanned Calories", value=f"{kcal_gescand} kcal")
        st.metric(label="Scanned Protein", value=f"{eiwit_gescand} g")
        
        if st.button("Add these AI values to your day"):
            st.session_state.kcal_gegeten += kcal_gescand
            st.session_state.eiwit_gegeten += eiwit_gescand
            st.success("Successfully added to your totals!")

# --- TAB 3: PROGRESS ---
with tab3:
    st.header("📈 Progress & Growth")
    vandaag = datetime.date.today()
    st.line_chart(pd.DataFrame({"Date": [vandaag - datetime.timedelta(days=i) for i in range(4, -1, -1)], "Weight (kg)": [user['weight']+1.0, user['weight']+0.7, user['weight']+0.4, user['weight']+0.2, user['weight']]}).set_index("Date"))
    st.subheader("📊 Weekly Body Weight Growth")
    st.line_chart(pd.DataFrame({"Weeks": ["Week 1", "Week 2", "Week 3", "Week 4"], "Chest: Push-ups":, "Back: Pull-ups":, "Legs: Pistol Squats":, "Core: Plank (Sec)":}).set_index("Weeks"))

# --- TAB 4: WATER & CALORIES ---
with tab4:
    st.header("💧 Manual Input")
    ml_toevoegen = st.number_input("Amount of water (ml):", min_value=0, max_value=2000, value=300, step=50)
    if st.button("➕ Register Water"):
        st.session_state.water_ml += ml_toevoegen
        st.toast(f"{ml_toevoegen}ml added!")
        
    st.subheader("🔥 Manual Nutrition")
    hkcal = st.number_input("Calories:", min_value=0, max_value=3000, value=250)
    heiwit = st.number_input("Protein (g):", min_value=0, max_value=150, value=20)
    if st.button("➕ Save Nutrition"):
        st.session_state.kcal_gegeten += hkcal
        st.session_state.eiwit_gegeten += heiwit
        st.success("Manually updated!")

# --- TAB 5: EXERCISES & LIVE JAWLINE TIMER ---
with tab5:
    st.header("🗿 Daily Training")
    st.subheader("Daily Jawline Training")
    st.write("Press the button to start Mewing (5 minute timer):")
    
    # Countdown live timer for Mewing
    if st.button("⏱️ Start 5 Minute Mewing Timer"):
        timer_placeholder = st.empty()
        totale_tijd = 5 * 60
        for resterend in range(totale_tijd, -1, -1):
            mins, secs = divmod(resterend, 60)
            timer_placeholder.metric("Remaining time", f"{mins:02d}:{secs:02d}")
            time.sleep(1)
        st.balloons()
        st.success("Great! You trained for 5 minutes!")
        
    o1 = st.checkbox("Mewing completed")
    o2 = st.checkbox("Chin Tucks — 3 sets")
    if o1 and o2:
        st.session_state.kaaklijn_gedaan = True
        
    st.subheader("Muscle Training Text Input (Own Body Weight)")
    user_oefening = st.text_input("Type in what you've done (e.g. pushups, pullups, planks):", "")
    if st.button("Send workout"):
        if user_oefening:
            st.session_state.oefening_gedaan = True
            st.success("Workout processed!")
            tekst = user_oefening.lower()
            if any(x in tekst for x in ["pushup", "opdrukken"]): st.info("💪 Trained: Chest & Triceps (85%)")
            if any(x in tekst for x in ["squat", "pistol"]): st.info("🍗 Trained: Legs & Glutes (90%)")
            if any(x in tekst for x in ["pullup", "optrekken"]): st.info("🦅 Trained: Back & Biceps (80%)")
            if any(x in tekst for x in ["plank", "buik"]): st.info("🧱 Trained: Abdominals / Core (85%)")
