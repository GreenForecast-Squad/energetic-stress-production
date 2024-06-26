import streamlit as st

st.set_page_config(
    page_title="ENR Forecast",
    page_icon="🌞",
)

st.markdown("""# Welcome to Energy Forecast! 🌞
This App is a demo of a simple energy forecast dashboard.

It is divided into three sections:

- <a href="weather" target = "_self">Weather Forecast</a>
- <a href="power_generation" target = "_self">Energy Forecast</a>
- <a href="consumption_prediction" target = "_self">Consumption Forecast</a>
- <a href="prediction_tempo" target = "_self">Prediction Tempo</a>
""", unsafe_allow_html=True)

st.sidebar.success("Select a demo above.")