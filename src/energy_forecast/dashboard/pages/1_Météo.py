"""This Page is used to display the weather forecast data."""
from matplotlib import pyplot as plt
from energy_forecast.meteo import get_region_sun, get_region_wind, memory, ArpegeSimpleAPI
from energy_forecast.constants import france_bounds
import pandas as pd
import streamlit as st
import altair as alt
import locale
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
alt.renderers.set_embed_options(time_format_locale="fr-FR.UTF-8", format_locale="fr-FR.UTF-8")


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

@memory.cache
def get_noon_wind_map(date: str, step="12h")->xr.DataArray:
    """Return the mean wind speed at noon for a given date.

    Parameters
    ----------
    date : str
        the date at which the weather forecast is requested.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        or a ``datetime.date`` object.

    Returns
    -------
    float
        The mean wind speed at noon.

    Examples
    --------
    >>> get_noon_wind("2024-06-28")
    2.0

    """
    client = ArpegeSimpleAPI(date=date)
    wind = client.read_wind()
    
    return wind.sel(step=pd.Timedelta(step)).si10

def get_sun_map(date: str, step="12h")->xr.DataArray:
    """Return the mean sun flux at noon for a given date.

    Parameters
    ----------
    date : str
        the date at which the weather forecast is requested.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        or a ``datetime.date`` object.

    Returns
    -------
    float
        The mean sun flux at noon.

    Examples
    --------
    >>> get_sun_map("2024-06-28")
    1000.0

    """
    client = ArpegeSimpleAPI(date=date)
    sun = client.read_sspd().ssrd.diff("step")
    #set long_name for the variable
    sun["long_name"] = "Flux solaire"
    
    return sun.sel(step=pd.Timedelta(step))
if __name__ == "__main__":

    st.title("Prévision meteo")
    st.markdown("Cette page affiche les prévisions météorologiques pour les prochains jours."
                " Les données sont obtenues à partir de [Météo France](https://www.meteofrance.com/).")
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    wind_data = compute_data_wind(date)


    wind_barplot = alt.Chart(wind_data).mark_bar().encode(
        y=alt.Y("wind_speed:Q").title("Vitesse du vent (m/s)"),
        x=alt.X("time:T").title("Date")
    ).properties(title="Vitesse moyenne du vent en France.")
    st.altair_chart(wind_barplot,
                    use_container_width=True
                )

    sun_data = compute_data_sun(date)
    sun_data["sun_flux"] = sun_data["sun_flux"] / 1000
    sun_barplot = alt.Chart(sun_data).mark_bar().encode(
        y=alt.Y("sun_flux:Q").title("Flux solaire (kW/m²)"),
        x=alt.X("time:T").title("Date")
    ).properties(title="Flux solaire moyen en France.")
    st.altair_chart(sun_barplot,
                    use_container_width=True
                )

    # hide the section below
    st.markdown("## Cartes des prévisions météorologiques\n"
                "Les cartes ci-dessous montrent les prévisions météorologiques pour la France.")
    with st.expander("Afficher les cartes"):
        # slider to select the step from 00h00 to 23h00
        step = st.slider("Sélectionner l'heure de la journée", 0, 23, 12)
        
        min_lon, max_lon = france_bounds["min_lon"], france_bounds["max_lon"]
        min_lat, max_lat = france_bounds["min_lat"], france_bounds["max_lat"]
        noon_wind = get_noon_wind_map(date, step=f"{step}h").sel(
            longitude=slice(min_lon, max_lon), latitude=slice(max_lat, min_lat)
            )
        
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        
        wind_data = noon_wind.plot(ax=ax, transform=ccrs.PlateCarree())
        #change the colorbar label
        wind_data.colorbar.set_label("Vitesse du Vent (W/m²)")
        # zoom on France
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=":")
        ax.add_feature(cfeature.STATES, linestyle=":")
        ax.set_title(noon_wind.long_name + "\n Le " + f"{pd.Timestamp(noon_wind.valid_time.values):%Y-%m-%d %H:%M}")

        st.pyplot(fig)

        sun_noon = get_sun_map(date, step=f"{step}h").sel(
            longitude=slice(min_lon, max_lon), latitude=slice(max_lat, min_lat)
            )
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        sun_data = sun_noon.plot(ax=ax, transform=ccrs.PlateCarree())
        #change the colorbar label
        sun_data.colorbar.set_label("Flux solaire (W/m²)")
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=":")
        ax.add_feature(cfeature.STATES, linestyle=":")
        ax.set_title("Flux solair\n Le " + f"{pd.Timestamp(sun_noon.valid_time.values):%Y-%m-%d %H:%M}")
        
        st.pyplot(fig)
