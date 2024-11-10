import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, time, timedelta

import warnings
warnings.filterwarnings('ignore')


def calculate_plasma_concentration(dose, F, Ka, Ke, Vd, t):
    C = (F * dose * Ka) / (Vd * (Ka - Ke)) * (np.exp(-Ke * t) - np.exp(-Ka * t))
    C = np.maximum(C, 0)
    return C


def main():
    st.set_page_config(
        page_title="Kofeinátor",
        page_icon="☕️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Už jste si dali ranní ☕️?")
    st.write("""
    Přemýšleli jste někdy, jak se Vaše tělo vyrovnává s kofeinem v kávě? 

    Vlevo upravte osobní parametry (jako věk, váhu a životní styl) a sledujte jejich vliv na cestu kofeinu — jak ho vaše tělo zpracovává a jak na vás působí. 

    Objevte vědu za svým povzbuzením a personalizujte svůj kofeinový zážitek!
    """)

    coffee_options = {
        "Espresso (30 ml)": 63,
        "Drip (240 ml)": 95,
        "French Press (240 ml)": 100,
        "Cold Brew (240 ml)": 120,
        "Instantní káva (240 ml)": 65,
        "Decaf (240 ml)": 5,
        "Cappuccino (240 ml)": 75,
        "Latte (240 ml)": 75,
        "Americano (1 dávka espressa)": 63,
        "Mocha (240 ml)": 80,
        "Turecká káva (60 ml)": 60,
        "Vlastní dávka": None
    }

    st.sidebar.header("Osobní parametry")
    weight = st.sidebar.number_input("Váha (kg)", min_value=30, max_value=150, value=70)
    gender = st.sidebar.selectbox("Pohlaví", options=["muž", "žena"])
    smoking_status = st.sidebar.selectbox("Kouření", options=["nekuřák", "kuřák"])
    liver_function = st.sidebar.selectbox("Funkce jater", options=["normální", "mírně snížená", "výrazně snížená"])
    metabolism_status = st.sidebar.selectbox("Metabolismus", options=["normální", "pomalý metabolizátor", "rychlý metabolizátor"])

    st.header("Přidat dávku kávy")
    entries = []

    if 'coffee_entries' not in st.session_state:
        st.session_state.coffee_entries = []

    with st.form("coffee_form", clear_on_submit=True):
        coffee_choice = st.selectbox("Vyberte typ kávy", options=list(coffee_options.keys()))
        servings = st.number_input("Počet dávek", min_value=1, max_value=10, value=1)
        dose_time = st.time_input("Čas konzumace", value=time(8, 0))
        add_entry = st.form_submit_button("Přidat")

        if add_entry:
            caffeine_per_serving = coffee_options.get(coffee_choice, 0)
            total_caffeine = caffeine_per_serving * servings
            st.session_state.coffee_entries.append({
                "type": coffee_choice,
                "dose": total_caffeine,
                "time": dose_time
            })

    # Display added entries
    st.subheader("Zadané dávky kávy")
    if st.session_state.coffee_entries:
        for idx, entry in enumerate(st.session_state.coffee_entries):
            st.write(f"{idx + 1}. {entry['type']} - {entry['dose']} mg v {entry['time'].strftime('%H:%M')}")

        remove_last = st.button("Odstranit poslední dávku")
        if remove_last:
            st.session_state.coffee_entries.pop()

    st.sidebar.header("Parametry simulace")
    simulation_time_hours = st.sidebar.number_input("Celkový čas simulace (hodiny)", min_value=1, max_value=23, value=23)
    time_step_hours = st.sidebar.number_input("Časové kroky (minuty)", min_value=1, max_value=60, value=15)

    F = 1.0
    Ka = 1.2
    Vd_standard = 0.6
    CL_standard = 0.06

    Vd = Vd_standard * weight
    CL = CL_standard * weight

    if metabolism_status == "pomalý metabolizátor":
        CL *= 0.3
    elif metabolism_status == "rychlý metabolizátor":
        CL *= 1.3

    if smoking_status == "kuřák":
        CL *= 1.5

    if gender == "žena":
        Vd *= 0.85
        CL *= 0.85

    if liver_function == "mírně snížená":
        CL *= 0.8
    elif liver_function == "výrazně snížená":
        CL *= 0.5

    Ke = CL / Vd

    simulation_start_time = datetime.combine(datetime.today(), time(0, 0))
    simulation_end_time = simulation_start_time + timedelta(hours=simulation_time_hours)

    t_hours = np.arange(0, simulation_time_hours + (time_step_hours / 60), (time_step_hours / 60))
    time_points = [simulation_start_time + timedelta(hours=th) for th in t_hours]
    C = np.zeros_like(t_hours)

    for entry in st.session_state.coffee_entries:
        dose = entry['dose']
        dose_time = datetime.combine(datetime.today(), entry['time'])
        time_since_dose = np.array([(tp - dose_time).total_seconds() / 3600 for tp in time_points])
        time_since_dose = np.maximum(time_since_dose, 0)
        C_dose = calculate_plasma_concentration(dose, F, Ka, Ke, Vd, time_since_dose)
        C += C_dose

    time_labels = [tp.strftime('%H:%M') for tp in time_points]
    data = pd.DataFrame({'Čas': time_labels, 'Koncentrace v plazmě (mg/L)': C})

    # Plotting with Plotly
    st.subheader("Výsledky simulace")

    with st.expander("Kolik kofeinu budu mít v těle?"):
        # Educational content about the plot
        st.write("""
        - **Terapeutický účinek (nad 2 mg/L):** V této oblasti můžete pociťovat zvýšenou bdělost a soustředění.
        - **Možné nežádoucí účinky (nad 10 mg/L):** Mohou se objevit symptomy jako nervozita, neklid nebo zvýšená srdeční frekvence.
        - **Riziko toxicity (nad 20 mg/L):** Takto vysoké hladiny jsou vzácné z běžné konzumace kávy, ale mohou být nebezpečné.
        """)

        # Create a line plot of plasma concentration over time
        fig_threshold = px.line(
            data,
            x='Čas',
            y='Koncentrace v plazmě (mg/L)',
            title='Koncentrace v plazmě s prahovými hodnotami',
            labels={'Koncentrace v plazmě (mg/L)': 'Koncentrace v plazmě (mg/L)', 'Čas': 'Čas'}
        )

        # Add threshold lines for therapeutic effect, side effects, and toxicity risk
        fig_threshold.add_hline(
            y=2, line_dash="dash", line_color="green",
            annotation_text="Terapeutický účinek", annotation_position="bottom right"
        )
        fig_threshold.add_hline(
            y=10, line_dash="dash", line_color="orange",
            annotation_text="Možné nežádoucí účinky", annotation_position="bottom right"
        )
        fig_threshold.add_hline(
            y=20, line_dash="dash", line_color="red",
            annotation_text="Riziko toxicity", annotation_position="bottom right"
        )

        # Display the plot in Streamlit
        st.plotly_chart(fig_threshold, use_container_width=True)


    with st.expander("Jak bude ovliněn můj spánek?"):
        st.write("""
        Hladiny kofeinu nad 1 mg/L mohou narušit kvalitu vašeho spánku, prodloužit dobu usínání a snížit celkovou efektivitu spánku.

        Graf spánku znázorňuje, jak se koncentrace kofeinu ve vašem těle mění v průběhu dne a zda může ovlivnit váš spánek na základě času konzumace kávy.

        Zhodnocením tohoto grafu můžete lépe naplánovat svůj příjem kofeinu tak, aby jeho hladiny byly v době spánku dostatečně nízké a minimalizovaly tak riziko narušení spánku.
        """)

        col5, col6 = st.columns([1, 1])
        # User input for bedtime (using time_input)
        bedtime = col5.time_input("Obvyklý čas spánku", value=time(22, 0))

        # Convert bedtime to datetime
        bedtime_datetime = datetime.combine(datetime.today(), bedtime)
        if bedtime_datetime < simulation_start_time:
            bedtime_datetime += timedelta(days=1)  # Adjust for next day if bedtime is before simulation start

        # Find index of bedtime
        idx_bedtime = min(range(len(time_points)), key=lambda i: abs(time_points[i] - bedtime_datetime))
        caffeine_at_bedtime = C[idx_bedtime]

        # Display message
        col5.write(f"Koncentrace kofeinu v době spánku ({bedtime.strftime('%H:%M')}): {caffeine_at_bedtime:.2f} mg/L")

        # Provide interpretation
        if caffeine_at_bedtime > 1.0:
            col5.warning("Vysoká hladina kofeinu může narušit váš spánek.")
        else:
            col5.success("Hladina kofeinu je dostatečně nízká pro kvalitní spánek.")

        # Plot Sleep Disruption Risk Indicator
        fig_sleep = px.line(
            data,
            x='Čas',
            y='Koncentrace v plazmě (mg/L)',
            title='Koncentrace kofeinu a riziko narušení spánku',
            labels={'Koncentrace v plazmě (mg/L)': 'Koncentrace v plazmě (mg/L)', 'Čas': 'Čas'}
        )

        # Add sleep disruption threshold line
        fig_sleep.add_hline(
            y=1.0, line_dash="dash", line_color="red",
            annotation_text="Práh narušení spánku (1 mg/L)", annotation_position="bottom right"
        )

        # Determine x0 and x1 for bedtime shading
        x0 = bedtime.strftime('%H:%M')
        x1 = time_labels[-1]

        # If bedtime is after the end of simulation, do not shade
        if bedtime_datetime <= simulation_end_time:
            fig_sleep.add_vrect(
                x0=x0,
                x1=x1,
                fillcolor="blue",
                opacity=0.1,
                layer="below",
                line_width=0,
                annotation_text="Čas spánku", annotation_position="top right"
            )

        st.plotly_chart(fig_sleep, use_container_width=True)


    st.subheader("Další zdroje")
    st.write("""
    - **Fredholm BB, et al.** (1999). *Actions of caffeine in the brain with special reference to factors that contribute to its widespread use.* Pharmacological Reviews, 51(1), 83-133.
    - **Nawrot P, et al.** (2003). *Effects of caffeine on human health.* Food Additives & Contaminants, 20(1), 1-30.
    - **Institute of Medicine.** (2001). *Caffeine for the Sustainment of Mental Task Performance: Formulations for Military Operations.* Washington, DC: The National Academies Press.
    """)


if __name__ == "__main__":
    main()
