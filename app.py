import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime

LATITUDE = 40.496
LONGITUDE = 21.205


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,rain"
        "&hourly=temperature_2m,relative_humidity_2m,precipitation"
        "&forecast_days=1"
        "&timezone=auto"
    )

    response = requests.get(url)
    return response.json()


def estimate_leaf_wetness(humidity, rain, precipitation):
    hours = 0

    if humidity >= 90:
        hours += 6
    elif humidity >= 80:
        hours += 4
    elif humidity >= 70:
        hours += 2

    if rain > 0 or precipitation > 0:
        hours += 6

    return hours


def calculate_disease_risk(temp, humidity, rain, precipitation, leaf_wet_hours):
    wet = rain > 0 or precipitation > 0 or humidity >= 90

    if not wet:
        return "LOW RISK - OK"

    if 16 <= temp <= 24 and leaf_wet_hours >= 9:
        return "HIGH RISK - ΨΕΚΑΣΜΟΣ"

    if 10 <= temp < 16 and leaf_wet_hours >= 12:
        return "HIGH RISK - ΨΕΚΑΣΜΟΣ"

    if 6 <= temp < 10 and leaf_wet_hours >= 18:
        return "MEDIUM RISK - ΠΡΟΣΟΧΗ"

    if 24 < temp <= 28 and leaf_wet_hours >= 8:
        return "MEDIUM RISK - ΠΡΟΣΟΧΗ"

    if leaf_wet_hours >= 6 and humidity >= 85:
        return "MEDIUM RISK - ΠΡΟΣΟΧΗ"

    return "LOW RISK - OK"


def protection_status(last_spray_date, protection_days):
    today = date.today()
    days_passed = (today - last_spray_date).days
    days_left = protection_days - days_passed

    if days_left > 0:
        return True, days_passed, days_left
    else:
        return False, days_passed, 0


st.title("🍏 Apple Disease Risk App")
st.write("Πρόβλεψη φουζικλαδίου, infection window, ψεκασμοί και ιστορικό")

st.sidebar.header("⚙️ Ρυθμίσεις ψεκασμού")

last_spray_date = st.sidebar.date_input(
    "Ημερομηνία τελευταίου ψεκασμού",
    value=date.today()
)

protection_days = st.sidebar.number_input(
    "Ημέρες προστασίας φαρμάκου",
    min_value=1,
    max_value=14,
    value=7
)

spray_product = st.sidebar.text_input(
    "Φάρμακο / σκεύασμα",
    value="Δεν δηλώθηκε"
)

spray_notes = st.sidebar.text_area(
    "Σημειώσεις ψεκασμού",
    value=""
)

covered, days_passed, days_left = protection_status(
    last_spray_date,
    protection_days
)


data = get_weather()
current = data["current"]

temp = current["temperature_2m"]
humidity = current["relative_humidity_2m"]
rain = current["rain"]
precipitation = current["precipitation"]

leaf_wet_hours = estimate_leaf_wetness(humidity, rain, precipitation)

risk = calculate_disease_risk(
    temp,
    humidity,
    rain,
    precipitation,
    leaf_wet_hours
)

st.subheader("Τωρινές συνθήκες")

st.metric("Θερμοκρασία", f"{temp} °C")
st.metric("Υγρασία", f"{humidity} %")
st.metric("Βροχή", f"{rain} mm")
st.metric("Precipitation", f"{precipitation} mm")
st.metric("Εκτίμηση βρεγμένου φύλλου", f"{leaf_wet_hours} ώρες")

st.subheader("Κατάσταση προστασίας")

if covered:
    st.success(f"ΚΑΛΥΜΜΕΝΟΣ — απομένουν {days_left} ημέρες προστασίας")
else:
    st.warning(f"ΑΚΑΛΥΠΤΟΣ — πέρασαν {days_passed} ημέρες από τον ψεκασμό")

st.write(f"Σκεύασμα: {spray_product}")

if spray_notes:
    st.write(f"Σημειώσεις: {spray_notes}")


st.subheader("Αποτέλεσμα τώρα")

if "HIGH RISK" in risk:
    st.error(risk)
elif "MEDIUM RISK" in risk:
    st.warning(risk)
else:
    st.success(risk)


st.subheader("Πρόβλεψη επόμενων 12 ωρών")

hourly = data["hourly"]

times = hourly["time"]
temps = hourly["temperature_2m"]
humidities = hourly["relative_humidity_2m"]
precipitations = hourly["precipitation"]

spray_needed = False
infection_start = None
infection_hours = 0
forecast_rows = []
history_rows = []

for i in range(12):
    temp_f = temps[i]
    hum_f = humidities[i]
    rain_f = precipitations[i]

    leaf_wet = estimate_leaf_wetness(hum_f, rain_f, rain_f)

    risk_f = calculate_disease_risk(
        temp_f,
        hum_f,
        rain_f,
        rain_f,
        leaf_wet
    )

    st.write(f"{times[i]} → {risk_f}")

    forecast_rows.append({
        "time": times[i],
        "temperature": temp_f,
        "humidity": hum_f,
        "rain": rain_f,
        "leaf_wet_hours": leaf_wet,
    })

    history_rows.append({
        "Ημερομηνία/Ώρα": times[i],
        "Θερμοκρασία": temp_f,
        "Υγρασία": hum_f,
        "Βροχή": rain_f,
        "Leaf Wet Hours": leaf_wet,
        "Risk": risk_f,
    })

    if "HIGH RISK" in risk_f:
        spray_needed = True

        if infection_start is None:
            infection_start = times[i]

        infection_hours += 1


st.subheader("Infection Window")

if infection_start:
    st.error(f"Έναρξη μόλυνσης: {infection_start}")
    st.write(f"Διάρκεια: {infection_hours} ώρες")
else:
    st.success("Δεν εντοπίστηκε infection window")


st.subheader("⏱️ Χρόνος δράσης")

if infection_start:
    first_hour = None

    for i in range(12):
        temp_f = temps[i]
        hum_f = humidities[i]
        rain_f = precipitations[i]

        leaf_wet = estimate_leaf_wetness(hum_f, rain_f, rain_f)

        risk_f = calculate_disease_risk(
            temp_f,
            hum_f,
            rain_f,
            rain_f,
            leaf_wet
        )

        if "HIGH RISK" in risk_f:
            first_hour = i
            break

    if first_hour is not None:
        if covered:
            st.success(
                f"Υπάρχει κίνδυνος σε {first_hour} ώρες, αλλά είσαι καλυμμένος για {days_left} ημέρες."
            )
        else:
            if first_hour <= 2:
                st.error(f"⚠️ Ψέκασε ΑΜΕΣΑ (σε {first_hour} ώρες)")
            elif first_hour <= 6:
                st.warning(f"⚠️ Ψέκασε σύντομα (σε {first_hour} ώρες)")
            else:
                st.info(f"Έχεις χρόνο — σε {first_hour} ώρες ανεβαίνει ο κίνδυνος")
else:
    st.success("Δεν υπάρχει ανάγκη για άμεση επέμβαση")


st.subheader("📈 Γράφημα καιρού")

df = pd.DataFrame(forecast_rows)
df = df.set_index("time")

st.line_chart(df[["temperature", "humidity", "rain", "leaf_wet_hours"]])


st.subheader("📅 Ιστορικό πρόβλεψης")

history_df = pd.DataFrame(history_rows)
st.dataframe(history_df, use_container_width=True)


st.subheader("Τελική πρόταση")

if spray_needed and not covered:
    st.error("ΠΡΟΤΑΣΗ: ΨΕΚΑΣΜΟΣ ΣΥΝΤΟΜΑ")
elif spray_needed and covered:
    st.success("ΠΡΟΤΑΣΗ: ΥΠΑΡΧΕΙ ΚΙΝΔΥΝΟΣ, ΑΛΛΑ ΕΙΣΑΙ ΚΑΛΥΜΜΕΝΟΣ")
else:
    st.success("ΠΡΟΤΑΣΗ: ΟΚ - ΔΕΝ ΧΡΕΙΑΖΕΤΑΙ ΑΚΟΜΑ")
