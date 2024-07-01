"""Create a dashboard page to display the energy production and the predictions.

- the energy production is obtained from the RTE API
- the predictions are computed using the weather data and linear models.
"""
from energy_forecast.energy import ECO2MixDownloader
from energy_forecast import ROOT_DIR
from energy_forecast.meteo import get_region_sun, get_region_wind, memory
import pandas as pd
import streamlit as st
import altair as alt
alt.renderers.set_embed_options(time_format_locale="fr-FR", format_locale="fr-FR")

@memory.cache
def compute_data_pv_power(date: str)->pd.DataFrame:
    """Estimate the power generated by solar panels.

    Use the data from :func:`get_region_sun` and a linear model to estimate the power generated by solar panels.

    Parameters
    ----------
    date : str
        The date at which the power is estimated.

    Returns
    -------
    pd.DataFrame
        The power generated by solar panels for each hour of the day.
        The columns are ["time", "pv_power"]
    """
    sun_data = get_region_sun(date)
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

@memory.cache
def compute_data_eolien(date)->pd.DataFrame:
    """Estimate the power generated by eolien.

    Use the data from :func:`get_region_swind` and a linear model to estimate the power generated by wind turbines.

    Parameters
    ----------
    date : str
        The date at which the power is estimated.

    Returns
    -------
    pd.DataFrame
        The power generated by solar panels for each hour of the day.
        The columns are ["time", "eolien_power"]
    """
    wind_data = get_region_wind(date)
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


@memory.cache
def compute_energy(date:str):
    """Concatenate the energy production data with the predictions.

    Energy production data is downloaded from RTE and the predictions are computed using the models from :func:`compute_data_pv_power` and :func:`compute_data_eolien`.

    TODO
    ----
    - Use the RTE API instead of the File Zip Download for Realtime data

    Parameters
    ----------
    date : str
        The date at which the energy production is estimated.

    Returns
    -------
    pd.DataFrame
        The energy production for each region and the predictions for solar and wind power.
        The columns are:
        - ``"time"``: the time of the data (pd.Timestamp)
        - ``"Eolien"``: the wind power production (historical data from RTE)
        - ``"Solaire"``: the solar power production (historical data from RTE)
        - ``"PV Prediction"``: the solar power production prediction (from linear model using weather date)
        - ``"Eolien Prediction"``: the wind power production prediction (from linear model using weather date)

    """
    pv_power = compute_data_pv_power(date)
    eolien_power = compute_data_eolien(date)
    current_year = pd.Timestamp(date).year
    r = ECO2MixDownloader(year=current_year)
    r.download()
    energy =  r.read_file()

    energy = energy[["Eolien", "Solaire"]]
    energy.rename(columns={"Eolien": "Eolien Production", "Solaire": "PV Production"}, inplace=True)
    offset_days = 5
    history_start = pd.Timestamp(date) - pd.Timedelta(f"{offset_days} days")
    energy = energy[history_start:]
    energy.index = energy.index.tz_localize("Europe/Paris").tz_convert("UTC").tz_localize(None)
    energy = pd.concat([
        energy,
        pv_power.set_index("time").rename(columns={"pv_power": "PV Prediction"}),
        eolien_power.set_index("time").rename(columns={"eolien_power": "Eolien Prediction"})
    ], axis=1).reset_index()

    return energy

if __name__ == "__main__":

    date_input = st.sidebar.date_input("Date", pd.Timestamp.now())

    # date = pd.Timestamp.now().strftime("%Y-%m-%d")
    energy = compute_energy(date_input)
    # keep only full hours, needed to plot the data without empty spaces
    energy = energy[energy["time"].dt.minute == 0]

    st.title("Prévision de production ENR")
    st.markdown("Cette page affiche les prévisions de production d'énergie renouvelable pour la date sélectionnée."
                " Les données sont obtenues à partir de [RTE](https://www.rte-france.com/eco2mix/la-production-delectricite-en-temps-reel).")


    energy_long = energy.melt(id_vars="time", var_name="source", value_name="power")
    eolen_long = energy_long[energy_long["source"].str.contains("Eolien")]
    pv_long = energy_long[energy_long["source"].str.contains("PV")]

    eolen_title = alt.Title("Production Eolien",
                            subtitle="Production historique et prévisionnelle")

    eolen_chart = alt.Chart(eolen_long, title=eolen_title).mark_line().encode(
        x=alt.X("time:T", title="Date"),
        y=alt.Y("power:Q", title="Production (MW)"),
        color=alt.Color("source:N", title="Type de production"),
    )

    st.altair_chart(eolen_chart,
                    use_container_width=True
                )

    sun_title = alt.Title("Production Solaire",
                          subtitle="Production historique et prévisionnelle")
    sun_chart = alt.Chart(pv_long, title=sun_title).mark_line().encode(
        x=alt.X("time:T", title="Date"),
        y=alt.Y("power:Q", title="Production (MW)"),
        color=alt.Color("source:N", title="Type de production"),
    )
    st.altair_chart(sun_chart,
                    use_container_width=True
                )