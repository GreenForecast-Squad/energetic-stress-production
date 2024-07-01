"""Create a Streamlit page to display the consumption forecast.

The Consumption forecast is obtained from the :class:`energy_forecast.consumption_forecast.PredictionForecastAPI` class.
It uses RTE predictions.
"""

from energy_forecast.consumption_forecast import PredictionForecastAPI
from energy_forecast import ROOT_DIR
import pandas as pd
import streamlit as st
import altair as alt
alt.renderers.set_embed_options(time_format_locale="fr-FR", format_locale="fr-FR")

@st.cache
def get_weekly_forecast(secret: str)->pd.DataFrame:
    """Get the weekly forecast for the total electricity consumption.

    Parameters
    ----------
    secret : str
        The secret key to access the RTE API.

    Returns
    -------
    pd.DataFrame
        The weekly forecast for the total electricity consumption.
        The columns are ["time", "predicted_consumption"]
    """
    consumption_forecast_api = PredictionForecastAPI(secret=secret)
    consumption_forecast = consumption_forecast_api.get_weekly_forecast(
        start_date=pd.Timestamp.now().date()
    ).reset_index()
    return consumption_forecast

if __name__ == "__main__":
    env_file = ROOT_DIR / ".env"
    with env_file.open("r") as f:
        secret = f.readline().strip().split("=", 1)[1]
    consumption_forecast = get_weekly_forecast(secret)


    st.title("Prévision de consomation electrique total")
    st.markdown("Prévision de consomation electrique total pour la semaine prochaine"
                " en utilisant les données de RTE.")

    title = alt.Title("Consomation electrique total prévue", anchor="start",
                      subtitle="France métropolitaine")

    consumption_chart = alt.Chart(consumption_forecast, title=title).mark_line().encode(
        y=alt.Y("predicted_consumption:Q", title="Consomation electrique (MW)"),
        x=alt.X("time:T", title="Date")
    )
    st.altair_chart(consumption_chart,
                    use_container_width=True
                )