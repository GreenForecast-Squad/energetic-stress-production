"""Landing page for the Energy Forecast dashboard."""
import streamlit as st

if __name__ == "__main__":
    st.set_page_config(
        page_title="Prévision ENR",
        page_icon="🌞",
    )

    st.markdown("""# Bienvenue dans Energy Forecast! 🌞
Cette application est une démonstration d'un tableau de bord de prévision énergétique simple.

Il est divisé en trois sections:

- <a href="weather" target = "_self">Prévision météo</a>
- <a href="power_generation" target = "_self">Prévision énergétique</a>
- <a href="consumption_prediction" target = "_self">Prévision de consommation</a>
- <a href="prediction_tempo" target = "_self">Prédiction Tempo</a>
"""
    , unsafe_allow_html=True)

    st.sidebar.success("Sélectionnez une démo ci-dessus.")