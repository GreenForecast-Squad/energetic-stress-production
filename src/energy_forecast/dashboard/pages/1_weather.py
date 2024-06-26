from energy_forecast.meteo import ArpegeSimpleAPI
from energy_forecast.energy import ECO2MixDownloader
from energy_forecast.consumption_forecast import PredictionForecastAPI
import pandas as pd
import streamlit as st
import altair as alt

def compute_data_sun()->pd.Series:
    sun_data = ArpegeSimpleAPI().region_sun()
    data = sun_data.sum(axis=1).to_frame()
    data.reset_index(inplace=True)
    data.columns = ["time", "sun_flux"]
    # data.name = "sun_flux"
    return data

def compute_data_wind()->pd.Series:
    wind_data = ArpegeSimpleAPI().region_wind()
    data = wind_data.sum(axis=1).to_frame()
    data.reset_index(inplace=True)
    data.columns = ["time", "wind_speed"]
    return data

st.title("Prévision meteo")

wind_data = compute_data_wind()

wind_barplot = alt.Chart(wind_data).mark_bar().encode(
    y="wind_speed",
    x="time"

)
st.altair_chart(wind_barplot,
                use_container_width=True
             )

sun_data = compute_data_sun()
sun_barplot = alt.Chart(sun_data).mark_bar().encode(
    y="sun_flux",
    x="time"
)
st.altair_chart(sun_barplot,
                use_container_width=True
             )