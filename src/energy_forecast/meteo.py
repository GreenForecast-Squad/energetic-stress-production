from pathlib import Path
import pandas as pd
import xarray as xr
import requests
import yaml
import logging

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
    base_url = "https://object.data.gouv.fr/meteofrance-pnt/pnt/{date}T{time}Z/arpege/01/SP1/arpege__{resolution}__SP1__{forecast}__{date}T{time}Z.grib2"
    forecast_horizons = ["000H012H",
                         "013H024H",
                         "025H036H",
                         "037H048H",
                         "049H060H",
                         "061H072H",
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
        return self.base_url.format(date=self.date,
                                    time=self.time,
                                    resolution=self.resolution,
                                    forecast=forecast_horizon)

    def get_filename(self, forecast_horizon):
        return f"{self.prefix}/arpege_{self.resolution}_{self.date}_{self.time}_{forecast_horizon}.grib2"

    def fetch(self):
        list_files = []
        for forecast_horizon in self.forecast_horizons:
            logger.debug(f"Fetching {forecast_horizon}")
            url = self.get_url(forecast_horizon)
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

    def read_file_as_xarray(self, filename, keys_filter):
        return xr.open_dataset(filename,
                               engine="cfgrib",
                               backend_kwargs={"filter_by_keys": keys_filter},
                               )

    def read_files_as_xarray(self, list_files, keys_filter):
        list_xr = []
        for filename in list_files:
            list_xr.append(self.read_file_as_xarray(filename, keys_filter))
        return xr.concat(list_xr, dim="step")

    def read_sspd(self):
        list_files = self.fetch()
        return self.read_files_as_xarray(list_files, KEYS_FILTER_SSPD)

    def read_wind(self):
        list_files = self.fetch()
        return self.read_files_as_xarray(list_files, KEYS_FILTER_WIND)

    def region_sun(self):
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