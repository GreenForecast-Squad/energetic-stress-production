import urllib.request
import rasterio
import numpy as np
from datetime import datetime
import pygrib
from subprocess import Popen, DEVNULL
import shlex
from calendar import monthrange
from tqdm import tqdm
import os


BASE_URL = 'http://hackathon.fede-meteo.org/{date}/arpege-world-v1-tmp/00/{params}/{horizons}.grib2'
DATE_FMT = '%Y-%m-%d'
DATA_OF_INTEREST = [
    '10 metre wind direction', '10 metre wind speed',
    '2 metre relative humidity', '2 metre temperature',
    'Surface short-wave (solar) radiation downwards'
]
N_HORIZONS = 34
HORIZONS_SLICES = {
    '00H24H': slice(0, 9), '27H48H': slice(9, 17), '51H72H': slice(17, 25), '75H102H': slice(25, 34)
}
FRANCE_GEOJSON = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/metropole.geojson'


def get_path(date):
    return f"tmp_data/{date.strftime('%Y%m%d')}.grib"


def download_arpege(date: datetime, horizon):
    path = get_path(date)
    if os.path.exists(path):
        return True
    url = BASE_URL.format(
        date=date.strftime(DATE_FMT), params='SP1', horizons=horizon
    )
    urllib.request.urlretrieve(url, path)
    return path


def parse_arpege(path, mask):
    data = {feat: [] for feat in DATA_OF_INTEREST}
    with pygrib.open(path) as arpege_grib:
        for grb in arpege_grib:
            if grb.nameECMF in DATA_OF_INTEREST:
                data[grb.nameECMF].append(np.mean(grb.values[mask]))
    data = {feat: np.array(data[feat]) for feat in data}
    return data


def get_horizon_data(date, horizon, mask):
    try:
        path = download_arpege(date, horizon)
        data = parse_arpege(path, mask)
    except:
        return {}
    return data


def get_mask():
    urllib.request.urlretrieve(FRANCE_GEOJSON, 'tmp_data/france.geojson')
    cmd = 'gdal_rasterize -burn 1 -te -180 -90 180 90 -ts 720 361 tmp_data/france.geojson tmp_data/france.tif'
    exit_code = Popen(shlex.split(cmd), stdout=DEVNULL).wait()
    with rasterio.open('tmp_data/france.tif') as src:
        mask = src.read(1)
    return np.concatenate([mask[:, mask.shape[1] // 2:], mask[:, :mask.shape[1] // 2]], axis=1).astype(bool)


def get_daily_data(year, month, day, mask):
    daily_data = np.full((N_HORIZONS, len(DATA_OF_INTEREST)), np.nan, dtype=np.float32)
    date = datetime(year, month, day)
    for horizon, sl in HORIZONS_SLICES.items():
        data = get_horizon_data(date, horizon, mask)
        for e_f, feat in enumerate(DATA_OF_INTEREST):
            if feat not in data:
                continue
            if feat == 'Surface short-wave (solar) radiation downwards' and horizon == '00H24H':
                sl_solar = slice(sl.start + 1, sl.stop)
                daily_data[sl_solar, e_f] = data[feat]
            else:
                daily_data[sl, e_f] = data[feat]
    return daily_data


def build_monthly_data(year, month):
    mask = get_mask()
    _, max_day = monthrange(year, month)
    monthly_data = np.stack([get_daily_data(year, month, day, mask) for day in tqdm(range(1, max_day + 1))], axis=0)
    np.save(f'tmp_data/{year}_{month}.npy', monthly_data)
    return True


if __name__ == '__main__':
    # y_m = [(2022, m) for m in range(3, 13)]
    # y_m.extend([(2023, m) for m in range(1, 13)])
    y_m = [(2024, m) for m in range(1, 5)]
    for y, m in y_m:
        print(y, m)
        build_monthly_data(y, m)
