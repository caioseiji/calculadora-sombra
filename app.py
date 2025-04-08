import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from pvlib.location import Location

st.set_page_config(page_title="Calculadora de Sombra Solar", layout="centered")

st.title("🧱 Calculadora de Sombra de Muro com Sol e Terreno Inclinado")

# Entrada de dados
cidade = st.text_input("🌍 Nome da cidade", value="Cuiabá")
data_hora_str = st.text_input("🕓 Data e hora (AAAA-MM-DD HH:MM)", value="2025-04-08 09:00")
altura_muro = st.number_input("📏 Altura do muro (em metros)", value=2.5, step=0.1)
inclinacao_graus = st.number_input("🪨 Inclinação do terreno (graus)", value=5.0, step=0.1)
direcao_inclinacao_graus = st.number_input("🧭 Direção da inclinação (azimute)", value=180.0, step=1.0)

if st.button("Calcular sombra"):
    try:
        # Localização
        geolocator = Nominatim(user_agent="sombra_web")
        location = geolocator.geocode(cidade)
        if not location:
            st.error("Cidade não encontrada.")
            st.stop()
        latitude, longitude = location.latitude, location.longitude

        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=latitude, lng=longitude)
        data_hora = pd.Timestamp(data_hora_str).tz_localize(timezone)

        # Cálculo solar
        local = Location(latitude, longitude)
        posicao_sol = local.get_solarposition(data_hora)
        elevacao = posicao_sol['elevation'].values[0]
        azimute = posicao_sol['azimuth'].values[0]

        st.success(f"☀️ Sol a {elevacao:.2f}° de elevação e {azimute:.2f}° de azimute")

        # Cálculo de sombra
        theta = np.radians(elevacao)
        phi = np.radians(azimute)
        incl = np.radians(inclinacao_graus)
        dir_incl = np.radians(direcao_inclinacao_graus)

        S = np.array([
            np.cos(theta) * np.sin(phi),
            np.cos(theta) * np.cos(phi),
            np.sin(theta)
        ])
        n = np.array([
            np.sin(incl) * np.sin(dir_incl),
            np.sin(incl) * np.cos(dir_incl),
            np.cos(incl)
        ])
        P0 = np.array([0, 0, altura_muro])
        d = -S

        numerador = np.dot(n, P0)
        denominador = np.dot(n, S)
        t = numerador / denominador
        P_sombra = P0 - t * S

        distancia_horizontal = np.linalg.norm(P_sombra[:2])

        st.markdown(f"""
        ### 📍 Resultado:
        - **Ponto da sombra no terreno**:  
          X = `{P_sombra[0]:.2f} m`, Y = `{P_sombra[1]:.2f} m`, Z = `{P_sombra[2]:.2f} m`
        - **Comprimento horizontal da sombra**: `{distancia_horizontal:.2f} m`
        """)

        # Gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot([P0[0], P_sombra[0]], [P0[2], P_sombra[2]], label="Sombra", color="orange")
        ax.vlines(0, 0, altura_muro, color='black', label="Muro")
        ax.hlines(0, -distancia_horizontal - 1, distancia_horizontal + 1, linestyles='dashed', colors='gray')
        ax.set_xlabel("Posição (X)")
        ax.set_ylabel("Altura (Z)")
        ax.set_title("Sombra do muro")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
