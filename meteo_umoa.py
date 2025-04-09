import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
from datetime import datetime, timedelta
import numpy as np

# Config Streamlit
st.set_page_config(page_title="Tableau de bord Météo", layout="wide")

# Chargement des données toutes les heures
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv("weather_data_umoa.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["sunrise"] = pd.to_datetime(df["sunrise"])
    df["sunset"] = pd.to_datetime(df["sunset"])
    return df

df = load_data()

# Thématisation
st.markdown("""
    <style>
        .main {
            background-color: #e3f2fd;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🌤️ Tableau de bord météo UMAO")

# Filtres interactifs
pays = st.selectbox("🌍 Choisissez un pays :", sorted(df["country"].unique()))
df_pays = df[df["country"] == pays]
ville = st.selectbox("🏙️ Choisissez une ville :", sorted(df_pays["city"].unique()))
df_ville = df_pays[df_pays["city"] == ville].sort_values("date")
latest = df_ville.iloc[-1]

# Section météo actuelle
with st.container():
    colA1, colA2 = st.columns([1, 3])
    with colA1:
        st.markdown("### ")
        st.markdown(f"""
        <div style='background-color: #90caf9; padding: 30px; border-radius: 10px; text-align: center;'>
            <h1 style='color: white;'>{latest['temp']} °C</h1>
            <h3 style='color: white;'>{latest['description'].capitalize()}</h3>
            <p style='color: white;'>⬆️ Max : {df_ville['temp'].max():.1f} °C</p>
            <p style='color: white;'>⬇️ Min : {df_ville['temp'].min():.1f} °C</p>
            <p style='color: white;'>{latest['date'].strftime('%A %d %B %Y, %H:%M')}</p>
            <p style='color: white;'>📍 {latest['city']}, {latest['country']}</p>
            <p style='color: white;'>Lat: {latest['latitude']:.2f} | Lon: {latest['longitude']:.2f}</p>
            <p style='color: white;'>🌅 Lever du soleil : {latest['sunrise'].strftime('%H:%M')}</p>
            <p style='color: white;'>🌇 Coucher du soleil : {latest['sunset'].strftime('%H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)

    with colA2:
        st.subheader("🌡️ Température horaire")
        fig_hourly = px.line(df_ville, x="date", y="temp", markers=True,
                             labels={"date": "Heure", "temp": "Température (°C)"},
                             title=f"Évolution de la température à {ville}")
        st.plotly_chart(fig_hourly, use_container_width=True)

# Zone Faits saillants
st.markdown("### 🔍 Faits saillants météo")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("💧 Humidité")
    st.metric("Humidité", f"{latest['humidity']} %")
    st.progress(int(min(latest['humidity'], 100)))

with col2:
    st.subheader("👁️ Visibilité")
    visibility_km = latest["visibility"] / 1000
    st.metric("Distance", f"{visibility_km:.1f} km")
    st.progress(int(min(visibility_km * 2.5, 100)))

with col3:
    st.subheader("🌬️ Vent")
    st.metric("Direction", f"{latest['wind_deg']}°")
    st.metric("Vitesse", f"{latest['wind_speed']} km/h")

# Carte
st.markdown("### 🗺️ Carte de la ville sélectionnée")
st.map(pd.DataFrame({"lat": [latest["latitude"]], "lon": [latest["longitude"]]}), zoom=6)

# PRÉVISIONS AVEC SÉLECTEUR DE JOUR
st.markdown("### 🔮 Prévisions météo horaires (7 jours)")
try:
    df_pred = pd.read_csv("previsions_meteo_7jours_horaire.csv")
    df_pred["date"] = pd.to_datetime(df_pred["date"])
    df_pred_ville = df_pred[(df_pred["city"] == ville) & (df_pred["country"] == pays)].sort_values("date")

    jour_unique = df_pred_ville["date"].dt.date.unique()
    jour_selectionne = st.selectbox("📅 Choisissez un jour :", jour_unique)

    heures_du_jour = df_pred_ville[df_pred_ville["date"].dt.date == jour_selectionne]

    heure_min = int(heures_du_jour["date"].dt.hour.min())
    heure_max = int(heures_du_jour["date"].dt.hour.max())

    plage_heures = st.slider("🕒 Sélectionnez la plage horaire :", min_value=heure_min, max_value=heure_max, value=(heure_min, heure_max))

    df_plage = heures_du_jour[(heures_du_jour["date"].dt.hour >= plage_heures[0]) & (heures_du_jour["date"].dt.hour <= plage_heures[1])]

    st.subheader(f"🌡️ Prévisions de {ville} le {jour_selectionne.strftime('%A %d %B %Y')} entre {plage_heures[0]}h et {plage_heures[1]}h")
    st.dataframe(df_plage[["date", "temp", "humidity", "wind_speed", "wind_deg", "visibility", "sunrise", "sunset", "description"]])

    fig_pred = px.line(df_plage, x="date", y="temp", markers=True,
                       labels={"date": "Heure", "temp": "Température (°C)"},
                       title="Prévisions horaires de la température")
    st.plotly_chart(fig_pred, use_container_width=True)

except Exception as e:
    st.warning(f"⚠️ Aucune prévision disponible. Erreur : {e}")
