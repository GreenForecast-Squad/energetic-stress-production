"""Create a Streamlit page to display the consumption forecast.

The Consumption forecast is obtained from the :class:`energy_forecast.consumption_forecast.PredictionForecastAPI` class.
It uses RTE predictions.
"""

from energy_forecast.consumption_forecast import PredictionForecastAPI
from energy_forecast import ROOT_DIR
import pandas as pd
import streamlit as st
import altair as alt

if __name__ == "__main__":
    env_file = ROOT_DIR / ".env"
    with env_file.open("r") as f:
        secret = f.readline().strip().split("=", 1)[1]

    consumption_forecast_api = PredictionForecastAPI(secret=secret)
    consumption_forecast = consumption_forecast_api.get_weekly_forecast(
        start_date=pd.Timestamp.now().date()
    ).reset_index()

    st.title("Prévision de consomation electrique total")



    consumption_chart = alt.Chart(consumption_forecast).mark_line().encode(
        y="predicted_consumption",
        x="time"
    ).interactive()
    st.altair_chart(consumption_chart,
                    use_container_width=True
                )