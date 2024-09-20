import logging
import time
from pathlib import Path

import pandas as pd
import requests
import xarray as xr
from joblib import Memory
from .constants import departement_names, region_names, france_bounds
from energy_forecast import ROOT_DIR
from energy_forecast.geography import get_mask_departements, get_mask_regions

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

GEO_DIR = ROOT_DIR / "data" / "geo"
bounds_file = GEO_DIR / "france_bounds.yml"


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
                 prefix="/tmp/arpege",):
        self.date = date
        self.time = time
        self.prefix = prefix
        self.min_lon = france_bounds["min_lon"]
        self.max_lon = france_bounds["max_lon"]
        self.min_lat = france_bounds["min_lat"]
        self.max_lat = france_bounds["max_lat"]

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

    @staticmethod
    def read_files_as_xarray(list_files, keys_filter):
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
        return xr.open_mfdataset(list_files,
                                 engine="cfgrib",
                                 backend_kwargs={"filter_by_keys": keys_filter},
                                 )        

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
        """Return the mean sun flux for each region of France.
        
        Returns
        -------
        pd.DataFrame
            The mean sun flux for each region of France
        """
        return self.mask_sun(get_mask_regions(), region_names, "region")
    
    def departement_sun(self):
        """Return the mean sun flux for each department of France.

        Returns
        -------
        pd.DataFrame
            The mean sun flux for each department of France
        """
        return self.mask_sun(get_mask_departements(), departement_names, "departement")
    
    def region_wind(self):
        """Return the mean wind speed for each region of France.

        Returns
        -------
        pd.DataFrame
            The mean wind speed for each region of France
        """
        return self.mask_wind(get_mask_regions(), region_names, "region")
    
    def departement_wind(self):
        """Return the mean wind speed for each department of France.
        
        Returns
        -------
        pd.DataFrame
            The mean wind speed for each department of France
        """
        return self.mask_wind(get_mask_departements(), departement_names, "departement")
    
    def mask_sun(self, masks, names, label):
        """Compute the mean sun flux for each region of France.

        Returns
        -------
        pd.DataFrame
            The mean sun flux for each region of France.
        """
        da_sun = self.read_sspd().ssrd
        df_groups = calculate_mean_group_value(masks, names, label, da_sun, self.min_lon, self.max_lon, self.min_lat, self.max_lat)
        df_unstacked = df_groups["ssrd"].unstack(label)
        df_instant_flux = instant_flux_from_cumul(df_unstacked)
        return df_instant_flux

    
    
    def mask_wind(self, masks, names, label):
        """Compute the mean wind speed for each region of France.

        Returns
        -------
        pd.DataFrame
            The mean wind speed for each region of France.
        """
        da_wind = self.read_wind().si10
        df_groups = calculate_mean_group_value(masks, names, label, da_wind, self.min_lon, self.max_lon, self.min_lat, self.max_lat)
        df_unstacked = df_groups["si10"].unstack(label)
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

def download_historical_forecasts(s3_key,
                                  s3_secret,
                                  s3_entrypoint,
                                  s3_bucket,
                                  prefix="./",
                                  variables="all",
                                  forecast_type="all",
                                  dryrun=False
                                  ):
    """Download the historical forecasts from the S3 bucket.

    Parameters
    ----------
    s3_key : str
        the key to access the S3 bucket.
    s3_secret : str
        the secret to access the S3 bucket.
    s3_entrypoint : str
        the entrypoint of the S3 bucket.
    s3_bucket : str
        the name of the S3 bucket.
    prefix : str
        The prefix where the files are downloaded.
        Should be similar to ``"./data/silver"``.
    variables : str or list[str], optional
        the variables to download.
        Can be ``"wind_speed_hourly"``, ``"sun_flux_downward_hourly"``, or ``"temperature_hourly"``
        or a list of these values.
        Default is ``"all"``, which downloads all the variables.
    forecast_type : str or list[str], optional
        the forecast type to download.
        Can be ``"d0"``, ``"d1"``, ``"d2"``, or ``"d3"``,
        or a list of these values.
        Default is ``"all"``, which downloads all the forecast types.
    dryrun : bool, optional
        if True, do not download the files.
        Default is False.

    Returns
    -------
    list[Path]
        the list of the files downloaded.
    """
    import boto3

    session = boto3.Session(
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
    )
    s3 = session.resource("s3", endpoint_url=s3_entrypoint)
    bucket = s3.Bucket(s3_bucket)
    list_files = []
    key_prefix = "weather_forecasts"
    if variables == "all":
        variables = ["wind_speed_hourly",
                     "sun_flux_downward_hourly",
                     "temperature_hourly"]
    if isinstance(variables, str):
        variables = [variables]
    for var in variables:
        if var not in ["wind_speed_hourly",
                       "sun_flux_downward_hourly",
                       "temperature_hourly"]:
            raise ValueError(f"Unknown variable {var} : must be in ['wind_speed_hourly', 'sun_flux_downward_hourly', 'temperature_hourly']")
    if forecast_type == "all":
        forecast_type = ["d0", "d1", "d2", "d3"]
    if isinstance(forecast_type, str):
        forecast_type = [forecast_type]
    for forecast in forecast_type:
        if forecast not in ["d0", "d1", "d2", "d3"]:
            raise ValueError(f"Unknown forecast type {forecast} : must be in ['d0', 'd1', 'd2', 'd3']")
    
    for var in variables:
        for forecast in forecast_type:
            key = f"{key_prefix}/{var}_{forecast}.nc"
            # test if the key exists
            filename = Path(prefix + "/" + key)
            if filename.exists():
                print(f"{filename} already downloaded, skipping")
                continue
            filename.parent.mkdir(parents=True, exist_ok=True)
            if dryrun:
                print(f"DRY RUN : would Download {key} to {filename}")
                # test if the key exists without downloading it
                try : 
                    s3.Object(s3_bucket, key).load()
                except Exception as e:
                    print(e)
                
            else:
                bucket.download_file(key, filename)
            list_files.append(filename)
    return list_files

def calculate_mean_group_value(masks, names, label, da_value, min_lon, max_lon, min_lat, max_lat):
        """Group the data by the masks and calculate the mean value for each group.

        Parameters
        ----------
        masks : xr.DataArray
            The masks to group the data.
            Must have the same dimensions longitude and Latitude
            as the data.
        names : list[str]
            The names of the groups.
        label : str
            the name of the column to use for the groups.
        da_value : xr.DataArray
            The data to group.

        Returns
        -------
        pd.DataFrame
            The mean value for each group.
        """
        was_valid_time = "valid_time" in da_value.coords
        if was_valid_time:
            # remove the valid_time dimension
            # as it can be recomputed from the time and step
            # and it breaks the groupby
            da_value = da_value.drop("valid_time")
            
        da_france = da_value.sel(
        longitude=slice(min_lon, max_lon), latitude=slice(max_lat, min_lat)
        )
        try :
            da_groups = da_france.groupby(masks).mean(["latitude", "longitude"])
        except ValueError:
            da_groups = da_france.groupby(masks).mean("stacked_longitude_latitude")
        # relabel the regions groups
        da_groups["group"] = names
        # change the name of the groups
        da_groups = da_groups.rename(group=label)
        da_groups.coords["valid_time"] = da_value.coords["time"] + da_value.coords["step"]
        df_groups = da_groups.to_dataframe()
        df_groups = df_groups.set_index("valid_time", append=True)
        df_groups = df_groups.droplevel("step")
        return df_groups

def instant_flux_from_cumul(df_unstacked):
    """Compute the instant flux from the cumulated flux.
    
    This is needed as the Weather Data provide the cumul of the sun flux.
    

    Parameters
    ----------
    df_unstacked : pd.DataFrame
        The DataFrame containing the cumulated flux.
        The index must be a DatetimeIndex or MultiIndex and the columns must be the regions of France.

    Returns
    -------
    pd.DataFrame
        The DataFrame containing the instant flux.
    
    Notes
    -----
    The function changes a lot if the index is a MultiIndex or not.
    Maybe it should be split into two functions ?
    """
    
    if isinstance(df_unstacked.index, pd.MultiIndex):
        times = df_unstacked.index.get_level_values('time').unique()
        zero_pad = pd.DataFrame(data=0,
                                index=pd.MultiIndex.from_arrays([times,
                                                                 times],
                                                                names=['time', 'valid_time']),
                                columns=df_unstacked.columns
        )
    else:
        zero_pad = df_unstacked.iloc[0].copy().to_frame().T
        zero_pad.index = zero_pad.index - pd.Timedelta("1h")
        zero_pad[:] = 0
    
    df_unstacked = pd.concat([zero_pad, df_unstacked], axis=0)
    if isinstance(df_unstacked.index, pd.MultiIndex):
        df_unstacked = df_unstacked.sort_index(level=["time", "valid_time"])
    else:
        df_unstacked = df_unstacked.sort_index()
    df_instant_flux = df_unstacked.diff().dropna()
    if isinstance(df_instant_flux.index, pd.MultiIndex):
        df_instant_flux.index = df_instant_flux.index.set_levels(df_instant_flux.index.levels[1] - pd.Timedelta("1h"),
                                                                 level=1
        )
    else:
        df_instant_flux.index -= pd.Timedelta("1h")
    return df_instant_flux


def download_observations(url, filename):
    """Download the observations from the url and save it in the filename.

    Parameters
    ----------
    url : str
        the url to download the data.
    filename : str
        the filename to save the data.
    """
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)

def download_observations_all_departments(cache_duration="12h",
                                          file_type="latest-2023-2024_RR-T-Vent",
                                          verbose=False):
    """Download the temperature for each department of France."""
    url_template = "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/QUOT/Q_{DEP_ID:0>2}_{file_type}.csv.gz"
    list_files = []
    download_root = ROOT_DIR / "data/bronze/observations"
    download_root.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp("now")
    for dep_id in range(1, 96):
        url = url_template.format(DEP_ID=dep_id, file_type=file_type)
        filename = download_root / "Q_{DEP_ID:0>2}_{file_type}.csv.gz".format(DEP_ID=dep_id, file_type=file_type)
        try:
            if filename.exists():
                modification_time = pd.Timestamp(filename.stat().st_mtime, unit="s")
                if now - modification_time < pd.Timedelta(cache_duration):
                    list_files.append(filename)
                    continue
            if verbose:
                logger.info(f"Downloading {url} to {filename}")
            download_observations(url, filename)
            list_files.append(filename)
        except requests.exceptions.HTTPError:
            logger.warning(f"Could not download {url}")
    return list_files

def aggregates_observations(list_files, cut_before="2022-01-01", verbose=False):
    """Aggregate the observations for each department of France.

    Parameters
    ----------
    list_files : list[str]
        the list of the files to aggregate.

    Returns
    -------
    pd.DataFrame
        the DataFrame containing the observations for each department.
    """
    all_deps = []
    for i, file_name in enumerate(list_files):
        if verbose:
            logger.info(f"Reading {file_name} ({i+1}/{len(list_files)})")
        tem_df = pd.read_csv(file_name, sep=";", usecols=["AAAAMMJJ", "TM"], compression="gzip", date_format="%Y%m%d", parse_dates=["AAAAMMJJ"])
        
        tem_df = (tem_df.set_index("AAAAMMJJ")
                  .dropna(subset=["TM"])
                  .sort_index()
        )
        tem_df = (tem_df
                  .groupby(tem_df.index).mean()
                  
        )[cut_before:]
        all_deps.append(tem_df)
        
    return pd.concat(all_deps, axis=1).mean(axis=1)
        
if __name__ == "__main__":
    logger.info("Fetching data for today")
    warm_cache(logger)
