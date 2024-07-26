import logging
import time
from pathlib import Path

import pandas as pd
import requests
import xarray as xr
import yaml
from joblib import Memory

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KEYS_FILTER_SSPD = {
    "typeOfLevel": "surface",
    "cfVarName": "ssrd",
}
KEYS_FILTER_WIND = {
    "typeOfLevel": "heightAboveGround",
    "level": 10,
    "cfVarName": "si10",
}
KEYS_FILTER_T2M = {
    "typeOfLevel": "heightAboveGround",
    "level": 2,
    "cfVarName": "t2m",
}

PROJECT_ROOT = Path(__file__).parent.parent.parent
GEO_DIR = PROJECT_ROOT / "data" / "geo"
bounds_file = GEO_DIR / "france_bounds.yml"
region_name_file = GEO_DIR / "regions_name.yml"
region_mask_file = GEO_DIR / "mask_france_regions.nc"


class ArpegeSimpleAPI():
    """Uses the `meteo.data.gouv.fr <https://meteo.data.gouv.fr>`_ API to fetch weather forecast data.

    It downloads the data in the format GRIB2 and reads it using xarray.
    If the file is already downloaded, it will not download it again.

    Parameters
    ----------
    date : str, optional
        the date at which the weather forecast was computed.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        Default is the current date.
    time : str, optional
        the time at which the weather forecast was computed.
        Can be ``"00:00:00"``, ``"06:00:00"``, ``"12:00:00"``, or ``"18:00:00"``
        Default is ``"00:00:00"``
    prefix : str, optional
        the prefix where the files are downloaded.
        Used to avoid downloading the same file multiple times.
        Default is ``"/tmp/arpege"``
    """

    base_url = "https://object.data.gouv.fr/meteofrance-pnt/pnt/{date}T{time}Z/arpege/01/SP1/arpege__{resolution}__SP1__{forecast}__{date}T{time}Z.grib2"
    forecast_horizons = ["000H012H",
                         "013H024H",
                         "025H036H",
                         "037H048H",
                         "049H060H",
                         "061H072H",
                         "073H084H",
                         "085H096H",
                         "097H102H",
                         ]
    resolution = "01"

    def __init__(self,
                 date=pd.Timestamp("today").strftime("%Y-%m-%d"),
                 time="00:00:00",
                 prefix="/tmp/arpege"):
        self.date = date
        self.time = time
        self.prefix = prefix
        with open(bounds_file, "r") as f:
            bounds = yaml.safe_load(f)
        self.min_lon = bounds["min_lon"]
        self.max_lon = bounds["max_lon"]
        self.min_lat = bounds["min_lat"]
        self.max_lat = bounds["max_lat"]
        with open(region_name_file, "r") as f:
            self.regions_names = yaml.safe_load(f)
        self.masks = xr.load_dataarray(region_mask_file)

    def get_url(self, forecast_horizon):
        """Format the URL to fetch the data."""
        return self.base_url.format(date=self.date,
                                    time=self.time,
                                    resolution=self.resolution,
                                    forecast=forecast_horizon)

    def get_filename(self, forecast_horizon):
        """Format the filename to save the data."""
        return f"{self.prefix}/arpege_{self.resolution}_{self.date}_{self.time}_{forecast_horizon}.grib2"

    def fetch(self):
        """Download the data from the API and save it in the prefix folder.
        All the forecast horizons are downloaded.

        Returns
        -------
        list[Path]
            The list of the files downloaded.
        """
        list_files = []
        for forecast_horizon in self.forecast_horizons:
            logger.debug(f"Fetching {forecast_horizon}")
            url = self.get_url(forecast_horizon=forecast_horizon)
            filename = self.get_filename(forecast_horizon)
            list_files.append(filename)
            if Path(filename).exists():
                continue
            filename = Path(filename)
            filename.parent.mkdir(parents=True, exist_ok=True)
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, "wb") as f:
                f.write(response.content)

        return list_files

    @staticmethod
    def read_file_as_xarray(filename, keys_filter):
        """Open the file as an xarray dataset.

        Parameters
        ----------
        filename : str
            the filename of the file to open.
        keys_filter : dict
            the keys to filter the data.

        Returns
        -------
        xr.Dataset
            the dataset containing the weather forecast data.
        """
        return xr.open_dataset(filename,
                               engine="cfgrib",
                               backend_kwargs={"filter_by_keys": keys_filter},
                               )

    def read_files_as_xarray(self, list_files, keys_filter):
        """Read all the files as an xarray dataset and concatenate them along the step dimension.

        Parameters
        ----------
        list_files : list[str]
            the list of the files to open.
        keys_filter : dict
            the keys to filter the data.

        Returns
        -------
        xr.Dataset
            the dataset containing the weather forecast data.
        """
        list_xr = []
        for filename in list_files:
            list_xr.append(self.read_file_as_xarray(filename, keys_filter))
        return xr.concat(list_xr, dim="step")

    def read_sspd(self):
        """Fetch the data and read the solar radiation.

        Returns
        -------
        xr.Dataset
            the dataset containing the solar radiation data.
        """
        list_files = self.fetch()
        return self.read_files_as_xarray(list_files, KEYS_FILTER_SSPD)

    def read_wind(self):
        """Fetch the data and read the wind speed.

        Returns
        -------
        xr.Dataset
            the dataset containing the wind speed data.
        """
        list_files = self.fetch()
        return self.read_files_as_xarray(list_files, KEYS_FILTER_WIND)

    def region_sun(self):
        """Compute the mean sun flux for each region of France.

        Returns
        -------
        pd.DataFrame
            The mean sun flux for each region of France.
        """
        da_sun = self.read_sspd().ssrd
        da_sun_france = da_sun.sel(
        longitude=slice(self.min_lon, self.max_lon), latitude=slice(self.max_lat, self.min_lat)
        )
        try :
            da_sun_region = da_sun_france.groupby(self.masks).mean(["latitude", "longitude"])
        except ValueError:
            da_sun_region = da_sun_france.groupby(self.masks).mean("stacked_longitude_latitude")
        # relabel the regions groups
        da_sun_region["group"] = self.regions_names
        # change the name of the groups
        da_sun_region = da_sun_region.rename(group="region")
        df_sun_regions = da_sun_region.to_dataframe()
        df_sun_regions = df_sun_regions.set_index("valid_time", append=True)
        df_sun_regions = df_sun_regions.droplevel("step")
        df_unstacked = df_sun_regions["ssrd"].unstack("region")

        zero_pad = df_unstacked.iloc[0].copy().to_frame().T
        zero_pad[:] = 0
        zero_pad.index = zero_pad.index - pd.Timedelta("1h")
        df_unstacked = pd.concat([zero_pad, df_unstacked], axis=0)
        df_instant_flux = df_unstacked.diff().dropna()
        df_instant_flux.index -= pd.Timedelta("1h")
        return df_instant_flux

    def region_wind(self):
        """Compute the mean wind speed for each region of France.

        Returns
        -------
        pd.DataFrame
            The mean wind speed for each region of France.
        """
        da_wind = self.read_wind().si10
        da_wind_france = da_wind.sel(
        longitude=slice(self.min_lon, self.max_lon), latitude=slice(self.max_lat, self.min_lat)
        )
        try :
            da_wind_region = da_wind_france.groupby(self.masks).mean(["latitude", "longitude"])
        except ValueError:
            da_wind_region = da_wind_france.groupby(self.masks).mean("stacked_longitude_latitude")
        # relabel the regions groups
        da_wind_region["group"] = self.regions_names
        # change the name of the groups
        da_wind_region = da_wind_region.rename(group="region")
        df_wind_regions = da_wind_region.to_dataframe()
        df_wind_regions = df_wind_regions.set_index("valid_time", append=True)
        df_wind_regions = df_wind_regions.droplevel("step")
        df_unstacked = df_wind_regions["si10"].unstack("region")

        return df_unstacked



memory = Memory("/tmp/cache/energy_forecast", verbose=0)

@memory.cache
def get_region_sun(date: str)->pd.DataFrame:
    """Retrun the mean sun flux for each hour of the day.

    This is a simple wrapper around :py:meth:`ArpegeSimpleAPI.region_sun`.
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
        The index is a DatetimeIndex and the columns are the regions of France:

        - ``"Île-de-France"``
        - ``"Centre-Val de Loire"``
        - ``"Bourgogne-Franche-Comté"``
        - ``"Normandie"``
        - ``"Hauts-de-France"``
        - ``"Grand Est"``
        - ``"Pays de la Loire"``
        - ``"Bretagne"``
        - ``"Nouvelle-Aquitaine"``
        - ``"Occitanie"``
        - ``"Auvergne-Rhône-Alpes"``
        - ``"Provence-Alpes-Côte d'Azur"``
        - ``"Corse"``

    .. seealso::
        :func:`get_region_wind`
    """
    sun_data = ArpegeSimpleAPI(date).region_sun()
    return sun_data

@memory.cache
def get_region_wind(date: str)->pd.DataFrame:
    """Retrun the mean wind speed for each hour of the day.

    This is a simple wrapper around :py:meth:`ArpegeSimpleAPI.region_wind`.
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
        The index is a DatetimeIndex and the columns are the regions of France:

        - ``"Île-de-France"``
        - ``"Centre-Val de Loire"``
        - ``"Bourgogne-Franche-Comté"``
        - ``"Normandie"``
        - ``"Hauts-de-France"``
        - ``"Grand Est"``
        - ``"Pays de la Loire"``
        - ``"Bretagne"``
        - ``"Nouvelle-Aquitaine"``
        - ``"Occitanie"``
        - ``"Auvergne-Rhône-Alpes"``
        - ``"Provence-Alpes-Côte d'Azur"``
        - ``"Corse"``

    .. seealso::
        :func:`get_region_sun`
    """
    sun_data = ArpegeSimpleAPI(date).region_wind()
    return sun_data

def warm_cache(logger, date=None, max_counter=30, sleep_duration=600):
    """Try to fetch the data from the API until it is successful.

    Parameters
    ----------
    logger : logging.Logger
        the logger to use.
    date : str, optional
        the date at which the weather forecast was computed.
        Must be a valid date format, e.g. ``"YYYY-MM-DD"``
        Default is the current date.
    max_counter : int, optional
        the maximum number of attempts.
        Default is 30.
    sleep_duration : int, optional
        the duration to sleep between each attempt in seconds.
        Default is 600 (10 minutes).

    Raises
    ------
    TimeoutError
        if the maximum number of attempts is reached.

    """
    date = date or pd.Timestamp("today").strftime("%Y-%m-%d")
    client = ArpegeSimpleAPI(date)
    counter=0
    while True:
        logger.info(f"Attempt {counter}")
        try :
            client.fetch()
            break
        except requests.exceptions.HTTPError as e:
            logger.warning(e)
            logger.info(f"Sleeping for {sleep_duration} seconds")
            time.sleep(sleep_duration)
            counter += 1
            if counter > max_counter:
                raise TimeoutError("Max counter reached")

if __name__ == "__main__":
    logger.info("Fetching data for today")
    warm_cache(logger)