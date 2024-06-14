"""This script is an adaptation of the notebook 0_grib_to_xarray.ipynb

Use it to run the ETL of all the data from the ARPEGE model."""
import os
from multiprocessing import freeze_support
from pathlib import Path
import pandas as pd
import xarray as xr
import numpy as np
from tqdm.auto import tqdm
from shapely.geometry import Point, Polygon, MultiPolygon
import geojson
from functools import partial
import dask
from dask.distributed import Client
from dask.distributed import LocalCluster
import time

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# add stream handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

if __name__ == "__main__":
    freeze_support()

logger.info("starting cluster")
cluster = LocalCluster(memory_limit="3GiB",
                       n_workers=4,
                       threads_per_worker=2,
                       processes=False,
)
client = cluster.get_client()
logger.info(client)
start_date = "2022-02-01"
end_date = "2024-04-08"
list_date = pd.date_range(start=start_date, end=end_date, freq="D")
list_date = list_date.strftime("%Y-%m-%d")
cases_forecast = {
    "J+0": ["00H12H", "13H24H"],
    "J+1": ["25H36H", "37H48H"],
    "J+2": ["49H60H", "61H72H"],
    "J+3": ["73H84H", "85H96H"],
}
cases = cases_forecast["J+0"]
filename_to_save_template = (
    "/shared/home/antoine-2etavant/data/arpege/{date}_SP1_{case}.grib2"
)


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
logger.info("Opening the first GeoJson to get the coordinates")
metropole_geojson_file = "./notebooks/datascience/metropole.geojson"
metropole = geojson.load(open(metropole_geojson_file))
polys_france = [Polygon(geo[0]) for geo in metropole["geometry"]["coordinates"]]
areas = [p.area for p in polys_france]

min_area = 0.2  # threshold to remove small islands
polys_france = [p for p, area in zip(polys_france, areas) if area > min_area]
poly_france = MultiPolygon(polys_france)
# poly_france = polys_france[0]  # france metropolitan

bouns = poly_france.envelope.bounds
min_lon = bouns[0]
max_lon = bouns[2]
min_lat = bouns[1]
max_lat = bouns[3]

def select_region(ds, min_lon, max_lon, min_lat, max_lat):
    """Check if 'step' is in the dataset's coordinates
    and return the dataset with the selected region.
    """
    if "step" not in ds.coords:
        print("step not in coords")
        print(ds.encoding["source"])
        return None
    if "longitude" not in ds.coords:
        print("longitude not in coords")
        return None
    if "latitude" not in ds.coords:
        print("latitude not in coords")
        return None
    return ds.sel(longitude=slice(min_lon, max_lon), latitude=slice(max_lat, min_lat))


select_france = partial(
    select_region, min_lon=min_lon, max_lon=max_lon, min_lat=min_lat, max_lat=max_lat
)

logger.info("Opening the second GeoJson to get the regions")
filename = "./notebooks/datascience/regions.geojson"
polys = geojson.load(open(filename))

names_to_keep = [
    "Bretagne",
    "Centre-Val de Loire",
    "Grand Est",
    "Hauts-de-France",
    "Île-de-France",
    "Normandie",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Pays de la Loire",
    "Provence-Alpes-Côte d'Azur",
    "Bourgogne-Franche-Comté",
    "Auvergne-Rhône-Alpes",
    "Corse",
]

polys_region = {}
for feature in tqdm(polys["features"]):
    name = feature["properties"]["nom"]
    if name not in names_to_keep:
        continue
    if feature["geometry"]["type"] == "Polygon":
        polys_region[name] = Polygon(feature["geometry"]["coordinates"][0])
    elif feature["geometry"]["type"] == "MultiPolygon":
        # keeping the largest polygon
        tmp_list = [Polygon(geo[0]) for geo in feature["geometry"]["coordinates"]]
        largest = max(tmp_list, key=lambda x: x.area)
        polys_region[name] = Polygon(largest)

def which_region(lon, lat, polygons_regions: dict[MultiPolygon]):
    for i, (name, poly) in enumerate(polygons_regions.items()):
        if poly.contains(Point(lon, lat)):
            return i
    else:
        return np.nan

logger.info("Opening the first Temperature file to compute the masks")
da = xr.open_mfdataset(
    filename_to_save_template.format(date=list_date[0], case=cases[0]),
    engine="cfgrib",
    # parallel=True,
    backend_kwargs={"filter_by_keys": KEYS_FILTER_T2M},
    concat_dim="time",
    combine="nested",
    preprocess=select_france,
    # chunks={"time": 1},
).t2m.drop_vars("heightAboveGround")
da
logger.info("Compute the masks")

mask = xr.apply_ufunc(
    which_region,
    da.longitude,
    da.latitude,
    kwargs={"polygons_regions": polys_region},
    vectorize=True,
    dask="parallelized",
)


def process_wind(number_of_days_to_process=10, run_dask_parallel=True):

    list_of_filenames_from_case = [
        [
            filename_to_save_template.format(date=date, case=case)
            for date in list_date[:number_of_days_to_process]
        ]
        for case in ["00H12H", "13H24H", "25H36H", "37H48H", "49H60H", "61H72H", "73H84H", "85H96H"]
    ]

    list_of_filenames_from_case_exists = [
        [filename for filename in filenames if Path(filename).exists()]
        for filenames in list_of_filenames_from_case
    ]
    logger.info("Open the Wind Data")

    da_wind_10m = xr.concat(
        [xr.open_mfdataset(
            filenames,
            engine="cfgrib",
            parallel=run_dask_parallel,
            backend_kwargs={"filter_by_keys": KEYS_FILTER_WIND},
            concat_dim="time",
            preprocess=select_france,
            combine="nested",
            chunks={"time": 10},
        ).si10.drop_vars("heightAboveGround")
        for filenames in list_of_filenames_from_case_exists
        ],
        dim="step",
    )
    logger.info("Compute the groups means for the wind data")

    group_means_wind = da_wind_10m.groupby(mask).mean()
    group_means_wind["group"] = list(polys_region.keys())
    group_means_wind = group_means_wind.rename(group="region")
    ddf: dask.DataFrame = group_means_wind.unify_chunks().to_dask_dataframe()
    ddf.to_csv("/shared/shared/etudes_hors_programme/enr_forecast/group_mean_wind.csv",
               single_file=True)

    return group_means_wind

def process_ssrd(number_of_days_to_process=10, run_dask_parallel=True):

    min_chunksize = 2
    max_chunksize = 5
    # create chunks of the list_date to avoid memory error
    reduced_list_date = list_date[:number_of_days_to_process]
    list_date_chunks = []
    for i in range(0, len(reduced_list_date), max_chunksize):
        logger.info(f"Creating chunk {i+1}/{len(reduced_list_date)}")
        logger.info(f"Processing dates: {reduced_list_date[i:i + max_chunksize]}")
        list_date_chunks.append(reduced_list_date[i:i + max_chunksize])
    if len(list_date_chunks[-1]) < min_chunksize:
        logger.info("Merging the last two chunks")
        list_date_chunks[-2] = list(list_date_chunks[-2]) + list(list_date_chunks[-1])
        list_date_chunks.pop()
    logger.info(f"Last chunk: {list_date_chunks[-1]}")
    for i, tmp_list_date in tqdm(enumerate(list_date_chunks), total=len(list_date_chunks), smoothing=0.9):
        if i < 124:
            time.sleep(0.01)
            continue
        logger.info(f"Processing chunk {i+1}/{len(list_date_chunks)}")
        logger.info(f"Processing dates: {tmp_list_date}")
        list_of_filenames_from_case = [
            [
                filename_to_save_template.format(date=date, case=case)
                for date in tmp_list_date
            ]
            for case in ["00H12H", "13H24H", "25H36H", "37H48H", "49H60H", "61H72H", "73H84H", "85H96H"]
        ]

        list_of_filenames_from_case_exists = [
            [filename for filename in filenames if Path(filename).exists()]
            for filenames in list_of_filenames_from_case
        ]
        if len(list_of_filenames_from_case_exists[0]) == 0:
            logger.info("No file exists for this chunk")
            continue
        logger.info("Open the SSRD Data")
        list_of_da_ssrd = []
        for list_files in list_of_filenames_from_case_exists:
            try:
                tmp_da = xr.open_mfdataset(
                    list_files,
                    engine="cfgrib",
                    parallel=run_dask_parallel,
                    backend_kwargs={"filter_by_keys": KEYS_FILTER_SSPD},
                    concat_dim="time",
                    combine="nested",
                    preprocess=select_france,
                    chunks={"time": 1},
                ).ssrd.drop_vars("surface")
            except Exception as e:
                logger.error(f"Error while opening the files: {list_files}")
                logger.error(e)
                continue
            list_of_da_ssrd.append(tmp_da)
        da_ssrd = xr.concat(list_of_da_ssrd,dim="step")
        logger.info("Compute the groups means for the ssrd data")
        # Grouping as fast as possible to speed the other operations
        da_ssrd_groups = da_ssrd.groupby(mask).mean()
        da_ssrd_groups["group"] = list(polys_region.keys())
        da_ssrd_groups = da_ssrd_groups.rename(group="region").persist()
        # insert a value of zero at the index step = 0
        logger.info("Compute the diff to get the hourly data")
        logger.info("adding a zero value at the beginning of the dataset")
        zero_da = xr.zeros_like(da_ssrd_groups.isel(step=0))
        zero_da["step"] = pd.Timedelta("0h")
        zero_da["valid_time"] -= pd.Timedelta("1h")
        logger.info("Concatenating the zero value with the groups means")
        da_ssrd_padded = xr.concat([zero_da, da_ssrd_groups], dim="step")
        # compute the diff along the step dimension
        logger.info("Computing the diff")
        da_ssrd_hourly = da_ssrd_padded.diff("step")
        logger.info("Reindexing the time dimension")
        da_ssrd_hourly["step"] = da_ssrd_padded.step[:-1]
        da_ssrd_hourly["valid_time"] -= pd.Timedelta("1h")
        logger.info("Writing the data to csv")
        ddf: dask.DataFrame = da_ssrd_hourly.unify_chunks().to_dask_dataframe()
        filename = "/shared/shared/etudes_hors_programme/enr_forecast/group_mean_sun.csv"
        if i == 0:
            mode = "w"
        else:
            mode = "a"
            with open(filename, mode="rb") as f:
                number_of_lines_in_file = sum(1 for _ in f)
            #reindex ddf to start at the last index of the previous ddf
            ddf.index = ddf.index + number_of_lines_in_file
        ddf.to_csv(filename,
                   mode=mode,
                   single_file=True)
        if i > 0:
            # remove the useless header line of the csv file
            # using sed and remove the line number "number_of_lines_in_file+1"
            os.system(f"sed -i '{number_of_lines_in_file+1}d' {filename}")



    return da_ssrd_hourly

print("Processing wind and ssrd data")
print("processing wind")
# group_means_wind = process_wind(-1)
# del group_means_wind
print("processing ssrd")
da_ssrd_hourly = process_ssrd(-1)
print("Done!")
