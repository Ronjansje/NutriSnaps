# --- TAB 5: OEFENINGEN & SPIERTRAINING ---
with tab5:
    st.title("🗿 Dagelijkse Routines & Training")
    
    # Initialiseer workout geschiedenis in de sessie als deze nog niet bestaat
    if "workout_history" not in st.session_state:
        st.session_state.workout_history = {}

    st.subheader("🤖 AI Spiertraining Analysator")
    st.caption("Typ in wat voor oefeningen je vandaag hebt gedaan. De app berekent welke spiergroepen je hebt aangepakt.")

    # Tekstinput voor de gebruiker
    user_workout_input = st.text_area("Wat heb je getraind? (Bijv: '3 sets push-ups en daarna pull-ups tot falen')", placeholder="Ik heb vandaag...")

    if st.button("Analyseer & Log Workout"):
        if user_workout_input:
            with st.spinner("Spiergroepen analyseren..."):
                time.sleep(1) # Korte animatie voor de ervaring
                
                # Slimme trefwoorden-scanner voor spiergroepen
                input_lower = user_workout_input.lower()
                spieren_gedetecteerd = []
                intensiteit_score = "Matig 🔥"
                
                # Logica voor spieractivatie
                if any(x in input_lower for x in ["push-up", "pushup", "drukken", "bench", "chest", "borst"]):
                    spieren_gedetecteerd.append({"Spiergroep": "Borst 🦍", "Functie": "Duwen", "Impact": "Hoog"})
                    spieren_gedetecteerd.append({"Spiergroep": "Triceps 💪", "Functie": "Arm strekken", "Impact": "Medium"})
                
                if any(x in input_lower for x in ["pull-up", "pullup", "chin-up", "row", "rug", "back", "lats"]):
                    spieren_gedetecteerd.append({"Spiergroep": "Rug 🦅", "Functie": "Trekken", "Impact": "Hoog"})
                    spieren_gedetecteerd.append({"Spiergroep": "Biceps 💪", "Functie": "Arm buigen", "Impact": "Medium"})
                    
                if any(x in input_lower for x in ["squat", "pistol", "benen", "legs", "lunge", "kuit"]):
                    spieren_gedetecteerd.append({"Spiergroep": "Bovenbenen 🍗", "Functie": "Knie strekken", "Impact": "Hoog"})
                    spieren_gedetecteerd.append({"Spiergroep": "Billen / Hamstrings", "Functie": "Heup strekken", "Impact": "Medium"})
                    
                if any(x in input_lower for x in ["plank", "abs", "buik", "core", "leg raise"]):
                    spieren_gedetecteerd.append({"Spiergroep": "Buikspieren (Core) 🛡️", "Functie": "Stabilisatie", "Impact": "Hoog"})

                if any(x in input_lower for x in ["zwaar", "falen", "max", "intensief", "30", "40", "50"]):
                    intensiteit_score = "Slopend 🔥🔥🔥"
                elif any(x in input_lower for x in ["licht", "rustig", "warmup"]):
                    intensiteit_score = "Herstel 🌱"

                # Als er niks herkend is, geef een algemene herkenning
                if not spieren_gedetecteerd:
                    spieren_gedetecteerd.append({"Spiergroep": "Algemeen Lichaam 🏃‍♂️", "Functie": "Conditie / Cardio", "Impact": "Medium"})

                # Opslaan in het logboek met de datum van vandaag
                vandaag_str = str(datetime.date.today())
                st.session_state.workout_history[vandaag_str] = {
                    "beschrijving": user_workout_input,
                    "spieren": spieren_gedetecteerd,
                    "intensiteit": intensiteit_score
                }
                st.success("Workout succesvol geanalyseerd en opgeslagen voor vandaag!")

    # Toon het resultaat van vandaag als er een workout is ingevoerd
    vandaag_str = str(datetime.date.today())
    if vandaag_str in st.session_state.workout_history:
        huidige_workout = st.session_state.workout_history[vandaag_str]
        
        st.markdown("### 📊 Jouw Getrainde Spiergroepen Vandaag")
        st.info(f"**Totale Intensiteit:** {huidige_workout['intensiteit']}")
        
        # Zet de resultaten om in een nette overzichtelijke dataframe/tabel (visuele weergave)
        df_spieren = pd.DataFrame(huidige_workout["spieren"])
        st.dataframe(df_spieren, use_container_width=True, hide_index=True)
        
        # Een visuele CSS-indicator die laat zien welke zones geactiveerd zijn
        st.markdown("#### 🎯 Geactiveerde Zones:")
        cols = st.columns(3)
        actieve_spieren = [s["Spiergroep"] for s in huidige_workout["spieren"]]
        
        with cols[0]:
            st.button("Bovenlichaam (Push)", type="primary" if any(x in ["Borst 🦍", "Triceps 💪"] for x in actieve_spieren) else "secondary", disabled=True, use_container_width=True)
        with cols[1]:
            st.button("Bovenlichaam (Pull)", type="primary" if any(x in ["Rug 🦅", "Biceps 💪"] for x in actieve_spieren) else "secondary", disabled=True, use_container_width=True)
        with cols[2]:
            st.button("Onderlichaam / Core", type="primary" if any(x in ["Bovenbenen 🍗", "Buikspieren (Core) 🛡️"] for x in actieve_spieren) else "secondary", disabled=True, use_container_width=True)

    # --- HISTORIE OVERZICHT ---
    st.markdown("---")
    st.subheader("📅 Trainingslogboek (Geschiedenis)")
    if st.session_state.workout_history:
        for datum, data in sorted(st.session_state.workout_history.items(), reverse=True):
            with st.expander(f"🗓️ {datum} — Intensiteit: {data['intensiteit']}"):
                st.write(f"**Gedane oefeningen:** *{data['beschrijving']}*")
                st.write("**Geraakte spieren:**")
                for spier in data["spieren"]:
                    st.markdown(f"- {spier['Spiergroep']} ({spier['Impact']} impact)")
    else:
        st.caption("Je hebt nog geen trainingen gelogd. Typ hierboven je eerste workout!")

    # --- OUDE STATISCHE FUNCTIES (BEHOUDEN) ---
    st.markdown("---")
    st.subheader("🗿 Dagelijkse Gewoontes")
    if not st.session_state.kaaklijn_gedaan:
        if st.button("✅ Markeer Kaaklijn Training (Mewing) als Voltooid"):
            st.session_state.kaaklijn_gedaan = True
            st.rerun()
    else:
        st.success("🎉 Je hebt je kaaklijntraining vandaag al afgerond!")
