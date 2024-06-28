"""This Page is used to display the weather forecast data."""
from energy_forecast.meteo import get_region_sun, get_region_wind, memory
import pandas as pd
import streamlit as st
import altair as alt


@memory.cache
def compute_data_sun(date: str)->pd.DataFrame:
    """Retrun the mean sun flux for each hour of the day.

    Solar radiation is in W/m^2.

    .. note::
        The function is cached to avoid multiple computation for the same date.
        The cache is persistent (saved on the disk at ``/tmp/cache/energy_forecast``)

    Parameters
    ----------
    date : str
        the date at which the weather forecast is requested.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        or a ``datetime.date`` object.

    Returns
    -------
    pd.DataFrame
        The mean sun flux for each hour of the day.
        The columns are ["time", "sun_flux"]

    Examples
    --------
    >>> compute_data_sun("2024-06-28")
    time                sun_flux
    2024-06-28 00:00:00 0.0
    2024-06-28 01:00:00 0.0
    2024-06-28 02:00:00 0.0
    ...
    2024-06-30 23:00:00 0.0

    .. seealso::
        :func:`compute_data_wind`
    """
    sun_data = get_region_sun(date)
    data = sun_data.mean(axis=1).to_frame()
    data.reset_index(inplace=True)
    data.columns = ["time", "sun_flux"]
    return data

@memory.cache
def compute_data_wind(date: str)->pd.DataFrame:
    """Retrun the mean wind speed for each hour of the day.

    Wind speed is in m/s.

    .. note::
        The function is cached to avoid multiple computation for the same date.
        The cache is persistent (saved on the disk at ``/tmp/cache/energy_forecast``)

    Parameters
    ----------
    date : str
        the date at which the weather forecast is requested.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        or a ``datetime.date`` object.

    Returns
    -------
    pd.DataFrame
        The mean wind speed for each hour of the day.
        The columns are ["time", "wind_speed"]

    Examples
    --------
    >>> compute_data_wind("2024-06-28")
    time                wind_speed
    2024-06-28 00:00:00 0.0
    2024-06-28 01:00:00 0.0
    2024-06-28 02:00:00 0.0
    ...
    2024-06-30 23:00:00 0.0

    .. seealso::
        :func:`compute_data_sun`

    """
    wind_data = get_region_wind(date)
    data = wind_data.mean(axis=1).to_frame()
    data.reset_index(inplace=True)
    data.columns = ["time", "wind_speed"]
    return data

if __name__ == "__main__":
    st.title("Prévision meteo")
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    wind_data = compute_data_wind(date)

    wind_barplot = alt.Chart(wind_data).mark_bar().encode(
        y="wind_speed",
        x="time"
    )
    st.altair_chart(wind_barplot,
                    use_container_width=True
                )

    sun_data = compute_data_sun(date)
    sun_barplot = alt.Chart(sun_data).mark_bar().encode(
        y="sun_flux",
        x="time"
    )
    st.altair_chart(sun_barplot,
                    use_container_width=True
                )