import streamlit as st
import requests

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
    data = response.json()

    return data


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
    risk = 0

    if 15 <= temp <= 25:
        risk += 2
    elif 10 <= temp < 15 or 25 < temp <= 30:
        risk += 1

    if humidity >= 90:
        risk += 3
    elif humidity >= 80:
        risk += 2
    elif humidity >= 70:
        risk += 1

    if rain > 0 or precipitation > 0:
        risk += 3

    if leaf_wet_hours >= 12:
        risk += 3
    elif leaf_wet_hours >= 6:
        risk += 2
    elif leaf_wet_hours >= 3:
        risk += 1

    if risk >= 8:
        return "HIGH RISK - ΨΕΚΑΣΜΟΣ"
    elif risk >= 5:
        return "MEDIUM RISK - ΠΡΟΣΟΧΗ"
    else:
        return "LOW RISK - OK"


st.title("🍏 Apple Disease Risk App")
st.write("Πρόβλεψη κινδύνου ασθενειών για το χωράφι σου")

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
st.metric("Leaf Wet Hours", leaf_wet_hours)

st.subheader("Αποτέλεσμα")

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

    if "HIGH RISK" in risk_f:
        spray_needed = True


st.subheader("Τελική πρόταση")

if spray_needed:
    st.error("ΠΡΟΤΑΣΗ: ΨΕΚΑΣΜΟΣ ΣΥΝΤΟΜΑ")
else:
    st.success("ΠΡΟΤΑΣΗ: ΟΚ - ΔΕΝ ΧΡΕΙΑΖΕΤΑΙ ΑΚΟΜΑ")