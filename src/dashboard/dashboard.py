"""Launch a dashboard with two pages: one for the sun flux and one for the wind speed.

This is a simple, first version of the dashboard.

Usage:
>>> python src/dashboard/dashboard.py

This will download the data and display the dashboard in the browser.

"""
from taipy.gui import Gui
import taipy.gui.builder as tgb
from meteo import ArpegeSimpleAPI
import pandas as pd


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
    pv_power = data_sun.copy()
    pv_power["pv_power"] = pv_power["sun_flux"] * 1e-3 / 3
    return pv_power

def compute_data_eolien(data_wind: pd.Series)->pd.Series:
    eolien_power = data_wind.copy()
    eolien_power["eolien_power"] = eolien_power["wind_speed"] *100
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
    from energy import RTESimpleAPI
    r = RTESimpleAPI()
    r.download()
    energy =  r.read_file()

    energy = energy[["Eolien", "Solaire"]]
    energy = energy["2024-06-10":]
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
              title="PV Power",
              y__2="Eolien",
              y__1="Solaire",
              y__3="PV Prediction",
              y__4="Eolien Prediction",
              x="time",
            #   color="red",
            xaxis={"title":"Time"},
            yaxis={"title":"PV Power (kW)"}
              )

pages = {
    "/": root_page,
    "Sun_Flux": page_sun,
    "Wind_Speed": page_wind,
    "PV_Power": page_pv,
    "Energy": page_energy,
}

if __name__ == "__main__":
    Gui(pages=pages).run(
        title="Dynamic chart",
        debug=True,
        use_reloader=True,
        )