"""Launch a dashboard with two pages: one for the sun flux and one for the wind speed.

This is a simple, first version of the dashboard.

Usage:
>>> python src/dashboard/dashboard.py

This will download the data and display the dashboard in the browser.

"""
from taipy.gui import Gui
import taipy.gui.builder as tgb
from energy_forecast.meteo import ArpegeSimpleAPI
from energy_forecast.energy import ECO2MixDownloader
from energy_forecast.consumption_forecast import PredictionForecastAPI
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent

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

def compute_data_pv_power(data_sun: pd.Series)->pd.Series:
    sun_data = ArpegeSimpleAPI().region_sun()
    sun_data.columns = [
        c.replace(" ", "_").replace("'", "_").replace("-", "_").lower()
        for c in sun_data.columns
    ]
    model_params = pd.read_csv("notebooks/datascience/sun_model_2_params.csv")
    model_params.columns = ["region", "coef"]
    model_params_ser = model_params.set_index("region").iloc[:, 0]
    production = sun_data * model_params_ser
    pv_power = production.sum(axis=1).to_frame() / 24
    pv_power.reset_index(inplace=True)
    pv_power.columns = ["time", "pv_power"]
    return pv_power

def compute_data_eolien(data_wind: pd.Series)->pd.Series:
    wind_data = ArpegeSimpleAPI().region_wind()
    wind_data.columns = [
        c.replace(" ", "_").replace("'", "_").replace("-", "_").lower()
        for c in wind_data.columns
    ]
    model_params = pd.read_csv("notebooks/datascience/wind_model_2_params.csv")
    model_params.columns = ["region", "coef"]
    model_params_ser = model_params.set_index("region").iloc[:, 0]
    production = wind_data * model_params_ser
    eolien_power = production.sum(axis=1).to_frame() / 24
    eolien_power.reset_index(inplace=True)
    eolien_power.columns = ["time", "eolien_power"]
    return eolien_power

data_sun = compute_data_sun()
data_wind = compute_data_wind()

pv_power = compute_data_pv_power(data_sun)
eolien_power = compute_data_eolien(data_wind)

# Add a navbar to switch from one page to the other
with tgb.Page() as root_page:
    tgb.text("# Predictions", mode="md")
    tgb.navbar()


with tgb.Page() as page_sun:
    tgb.text(value="Sun Flux" , mode="md")
    tgb.chart(data="{data_sun}",
              type="line",
              title="Sun Flux",
              y="sun_flux",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"Sun Flux (W/m²)"}
              )

with tgb.Page() as page_wind:
    tgb.text(value="Wind Speed" , mode="md")
    tgb.chart(data="{data_wind}",
              type="line",
              title="Wind Speed",
              y="wind_speed",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"Wind Speed (m/s)"}
              )

with tgb.Page() as page_pv:
    tgb.text(value="PV Power" , mode="md")
    tgb.chart(data="{pv_power}",
              type="line",
              title="PV Power",
              y="pv_power",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"PV Power (kW)"}
              )

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

with tgb.Page() as page_energy:
    tgb.text(value="Energy" , mode="md")
    tgb.chart(data="{energy}",
              type="line",
              title="ENR Production and Prediction",
              y__2="Eolien",
              y__1="Solaire",
              y__3="PV Prediction",
              y__4="Eolien Prediction",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"Power (kW)"}
              )

env_file = ROOT_DIR / ".env"
with env_file.open("r") as f:
    secret = f.readline().strip().split("=", 1)[1]

consumption_forecast_api = PredictionForecastAPI(secret=secret)
consumption_forecast = consumption_forecast_api.get_weekly_forecast(
    start_date=pd.Timestamp.now().date()
)

with tgb.Page() as page_consumption:
    tgb.text(value="Consumption" , mode="md")
    tgb.chart(data="{consumption_forecast.reset_index()}",
              type="line",
              title="Consumption Forecast",
              y="predicted_consumption",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"Consumption (MW)"}
              )

pages = {
    "/": root_page,
    "Sun_Flux": page_sun,
    "Wind_Speed": page_wind,
    "PV_Power": page_pv,
    "Prediction": page_energy,
    "Consumption": page_consumption,
}

if __name__ == "__main__":
    Gui(pages=pages).run(
        title="Energetic Stress Production",
        # debug=True,
        use_reloader=True,
        )