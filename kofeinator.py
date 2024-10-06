# Import necessary libraries
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, time, timedelta

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')

# Define the PK model function
def calculate_plasma_concentration(dose, F, Ka, Ke, Vd, t):
    """
    Calculate plasma concentration over time using a one-compartment model with first-order absorption and elimination.

    Parameters:
    - dose: Dose administered (mg)
    - F: Bioavailability (unitless)
    - Ka: Absorption rate constant (hr^-1)
    - Ke: Elimination rate constant (hr^-1)
    - Vd: Volume of distribution (L)
    - t: Time after dose (hr), array or scalar

    Returns:
    - C: Plasma concentration (mg/L) at time t
    """
    C = (F * dose * Ka) / (Vd * (Ka - Ke)) * (np.exp(-Ke * t) - np.exp(-Ka * t))
    C = np.maximum(C, 0)  # Ensure concentration doesn't go negative
    return C

# Main function for the Streamlit app
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

    # Coffee types and their average caffeine content
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
        "Vlastní dávka": None  # User can input custom caffeine content
    }

    # User inputs
    st.sidebar.header("Osobní parametry")
    weight = st.sidebar.number_input("Váha (kg)", min_value=30, max_value=150, value=70, help="Vaše váha ovlivňuje, jak je kofein distribuován ve vašem těle a jak rychle je metabolizován.")
    gender = st.sidebar.selectbox("Pohlaví", options=["muž", "žena"], help="Ženy mohou mít nižší distribuční objem pro kofein než muži, což může vést k vyšším koncentracím v plazmě.")
    smoking_status = st.sidebar.selectbox("Kouření", options=["nekuřák", "kuřák"], help="Kouření může zvýšit rychlost eliminace kofeinu až o 50 %.")
    liver_function = st.sidebar.selectbox("Funkce jater", options=["normální", "mírně snížená", "výrazně snížená"], help="Snížená funkce jater zpomaluje rychlost eliminace kofeinu.")
    metabolism_status = st.sidebar.selectbox("Metabolismus", options=["normální", "pomalý metabolizátor", "rychlý metabolizátor"], help="Pomalí metabolizátoři eliminují kofein pomaleji, což může prodloužit jeho účinky.")

    col1, col2, col3, col4 = st.columns([1, 0.2, 2, 0.2])
    # Coffee selection
    coffee_choice = col1.selectbox("Vyberte typ kávy", options=list(coffee_options.keys()))
    
    if coffee_choice != "Vlastní dávka":
        caffeine_per_serving = coffee_options[coffee_choice]
        servings = col1.number_input("Počet káv", min_value=1, max_value=10, value=1, step=1)
        total_caffeine = caffeine_per_serving * servings
        col1.write(f"Celková dávka kofeinu: {total_caffeine:.1f} mg")
        dosing_interval = 0
        if servings > 1:
            dosing_interval = col1.number_input("Interval mezi kávami (hodiny)", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
    else:
        # Custom caffeine content
        caffeine_per_serving = col1.number_input("Vepište dávku kofeinu (mg)", min_value=1, max_value=1000, value=200)
        servings = col1.number_input("Počet dávek", min_value=1, max_value=10, value=1)
        total_caffeine = caffeine_per_serving * servings
        col1.write(f"Celková dávka kofeinu: {total_caffeine:.1f} mg")
        dosing_interval = 0
        if servings > 1:
            dosing_interval = col1.number_input("Interval mezi dávkami (hodiny)", min_value=0.5, max_value=24.0, value=2.0, step=0.5)

    # Input for first dose time (using time_input)
    first_dose_time = col1.time_input("Čas prvního šálku", value=time(8, 0))

    col3.image("img/coffee.JPEG", width=550)

    st.sidebar.header("Časové rozpětí simulace")
    simulation_time_hours = st.sidebar.number_input("Celkový čas simulace (hodiny)", min_value=1, max_value=23, value=23)
    time_step_hours = st.sidebar.number_input("Časové kroky (minuty)", min_value=1, max_value=60, value=15)

    # Pharmacokinetic Parameters
    F = 1.0  # Bioavailability
    Ka = 1.2  # Absorpční rychlostní konstanta (hr^-1)
    Vd_standard = 0.6  # Distribuční objem (L/kg)
    CL_standard = 0.06  # Clearance (L/hr/kg)

    # Adjust Vd and CL based on personal parameters
    Vd = Vd_standard * weight  # Upravený distribuční objem (L)
    CL = CL_standard * weight  # Upravená clearance (L/hr)

    # Adjustments based on metabolism status
    if metabolism_status == "pomalý metabolizátor":
        CL *= 0.3  # Snížení clearance o 50%
    elif metabolism_status == "rychlý metabolizátor":
        CL *= 1.3  # Zvýšení clearance o 50%

    # Adjustments based on smoking status
    if smoking_status == "kuřák":
        CL *= 1.5  # Zvýšení clearance o 50%

    # Adjustments based on gender
    if gender == "žena":
        Vd *= 0.85  # Females may have lower Vd due to higher body fat percentage
        CL *= 0.85  # Females may have slightly lower clearance

    # Adjustments based on liver function
    if liver_function == "mírně snížená":
        CL *= 0.8  # Snížení clearance o 20%
    elif liver_function == "výrazně snížená":
        CL *= 0.5  # Snížení clearance o 50%

    # Recalculate Ke and t1/2
    Ke = CL / Vd  # Eliminační rychlostní konstanta (hr^-1)

    # Time array adjusted to start from first dose time
    simulation_start_time = datetime.combine(datetime.today(), first_dose_time)
    simulation_end_time = simulation_start_time + timedelta(hours=simulation_time_hours)
    
    # Create time points using numpy.arange
    t_hours = np.arange(0, simulation_time_hours + (time_step_hours / 60), (time_step_hours / 60))
    time_points = [simulation_start_time + timedelta(hours=th) for th in t_hours]
    
    # Initialize concentration array
    C = np.zeros_like(t_hours)

    # Simulate multiple doses
    for i in range(int(servings)):
        dose_time = simulation_start_time + timedelta(hours=i * dosing_interval)
        # Calculate time after dose for each time point
        time_since_dose = np.array([(tp - dose_time).total_seconds() / 3600 for tp in time_points])
        time_since_dose = np.maximum(time_since_dose, 0)
        # Calculate concentration for each dose
        C_dose = calculate_plasma_concentration(
            dose=total_caffeine,
            F=F,
            Ka=Ka,
            Ke=Ke,
            Vd=Vd,
            t=time_since_dose
        )
        C += C_dose  # Accumulate concentration from each dose

    # Convert datetime objects to strings for plotting
    time_labels = [tp.strftime('%H:%M') for tp in time_points]

    # Create a DataFrame for plotting
    data = pd.DataFrame({
        'Čas': time_labels,
        'Koncentrace v plazmě (mg/L)': C
    })

    # Plotting with Plotly
    st.subheader("Výsledky simulace")

    with st.expander("Kolik kofeinu budu mít v těle?"):
        # Educational content about the plot
        st.write("""
        - **Terapeutický účinek (nad 2 mg/L):** V této oblasti můžete pociťovat zvýšenou bdělost a soustředění.
        - **Možné nežádoucí účinky (nad 10 mg/L):** Mohou se objevit symptomy jako nervozita, neklid nebo zvýšená srdeční frekvence.
        - **Riziko toxicity (nad 20 mg/L):** Takto vysoké hladiny jsou vzácné z běžné konzumace kávy, ale mohou být nebezpečné.
        """)
        # Plot with thresholds
        fig_threshold = px.line(
            data,
            x='Čas',
            y='Koncentrace v plazmě (mg/L)',
            title='Koncentrace v plazmě s prahovými hodnotami',
            labels={'Koncentrace v plazmě (mg/L)': 'Koncentrace v plazmě (mg/L)', 'Čas': 'Čas'}
        )

        # Add threshold lines
        fig_threshold.add_hline(y=2, line_dash="dash", line_color="green", annotation_text="Terapeutický účinek", annotation_position="bottom right")
        fig_threshold.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Možné nežádoucí účinky", annotation_position="bottom right")
        fig_threshold.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Riziko toxicity", annotation_position="bottom right")

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
        fig_sleep.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Práh narušení spánku (1 mg/L)", annotation_position="bottom right")

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
                annotation_text="Čas spánku",
                annotation_position="top right"
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

