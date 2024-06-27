from energy_forecast.energy import ECO2MixDownloader
from energy_forecast import ROOT_DIR
from energy_forecast.meteo import ArpegeSimpleAPI
from energy_forecast.consumption_forecast import PredictionForecastAPI
import pandas as pd
import streamlit as st
import altair as alt


def compute_data_pv_power()->pd.Series:
    sun_data = ArpegeSimpleAPI().region_sun()
    sun_data.columns = [
        c.replace(" ", "_").replace("'", "_").replace("-", "_").lower()
        for c in sun_data.columns
    ]
    model_params = pd.read_csv(ROOT_DIR / "data/silver/sun_model_2_params.csv")
    model_params.columns = ["region", "coef"]
    model_params_ser = model_params.set_index("region").iloc[:, 0]
    production = sun_data * model_params_ser
    pv_power = production.sum(axis=1).to_frame() / 24
    pv_power.reset_index(inplace=True)
    pv_power.columns = ["time", "pv_power"]
    return pv_power

def compute_data_eolien()->pd.Series:
    wind_data = ArpegeSimpleAPI().region_wind()
    wind_data.columns = [
        c.replace(" ", "_").replace("'", "_").replace("-", "_").lower()
        for c in wind_data.columns
    ]
    model_params = pd.read_csv(ROOT_DIR / "data/silver/wind_model_2_params.csv")
    model_params.columns = ["region", "coef"]
    model_params_ser = model_params.set_index("region").iloc[:, 0]
    production = wind_data * model_params_ser
    eolien_power = production.sum(axis=1).to_frame() / 24
    eolien_power.reset_index(inplace=True)
    eolien_power.columns = ["time", "eolien_power"]
    return eolien_power


pv_power = compute_data_pv_power()
eolien_power = compute_data_eolien()
print(pv_power)

def compute_energy():
    r = ECO2MixDownloader(year=2024)
    r.download()
    energy =  r.read_file()

    energy = energy[["Eolien", "Solaire"]]
    energy = energy["2024-06-17":]
    energy.index = energy.index.tz_localize("Europe/Paris").tz_convert("UTC").tz_localize(None)
    energy = pd.concat([
        energy,
        pv_power.set_index("time").rename(columns={"pv_power": "PV Prediction"}),
        eolien_power.set_index("time").rename(columns={"eolien_power": "Eolien Prediction"})
    ], axis=1).reset_index()

    return energy

energy = compute_energy()
# keep only full hours
energy = energy[energy["time"].dt.minute == 0]

st.title("Prévision de production ENR")


wind_history = alt.Chart(energy).mark_line().encode(
    y="Eolien",
    x="time"
)
wind_prediction = alt.Chart(energy).mark_line(color="red").encode(
    y="Eolien Prediction",
    x="time"
)
wind_barplot = wind_prediction + wind_history
st.altair_chart(wind_barplot,
                use_container_width=True
             )

sun_history = alt.Chart(energy).mark_line().encode(
    y="Solaire",
    x="time"
)
sun_prediction = alt.Chart(energy).mark_line(color="red").encode(
    y="PV Prediction",
    x="time"
)
sun_barplot = sun_prediction + sun_history
st.altair_chart(sun_barplot,
                use_container_width=True
             )