#! /usr/bin/env python3
"""This script does all the needed steps to predict the tempo class.

Usage
-----
with hatch:
>>> hatch run tempo_prediction

"""

import logging
import pandas as pd

from energy_forecast import ROOT_DIR
from energy_forecast.consumption_forecast import PredictionForecastAPI
from energy_forecast.eco2mix import get_data as get_eco2mix_data
from energy_forecast.enr_production_model import ENRProductionModel
from energy_forecast.meteo import ArpegeSimpleAPI
from energy_forecast.tempo_rte import TempoPredictor, TempoSignalAPI
from energy_forecast.meteo import download_observations_all_departments, aggregates_observations
from energy_forecast.performances import memory, expires_after

logger = logging.getLogger(__name__)
TODAY = pd.Timestamp.now().date()
gold_dir = ROOT_DIR / "data" / "gold"

if not gold_dir.exists():
    gold_dir.mkdir()

@memory.cache(cache_validation_callback=expires_after(days=1))
def fetch_history_data():
    """Return the history data from the eco2mix API.
    
    WARNING : the API is not very reliable and the data is not always returend.
    TODO : add validation to check if the data is returned.
    """
    one_year_ago = TODAY - pd.DateOffset(years=1) - pd.DateOffset(month=9, day=1)
    ecomix_data = get_eco2mix_data(start=one_year_ago, end=TODAY)[
        ["consommation", "eolien", "solaire"]
    ]
    ecomix_data_no_duplicates = ecomix_data[~ecomix_data.index.duplicated()]
    return ecomix_data_no_duplicates

@memory.cache(cache_validation_callback=expires_after(days=1))
def fetch_ret_consumption_forecast():
    """Fetch the consumption forecast from the RTE API.

    TODO : here the function only uses the weekly forecast.
    The short_term forecast could be used as well.
    It should be slightly more accurate.

    However, the short term forecast is only available for the next 2 days (D-1 and D-2).
    Hence a merge with the weekly forecast is needed.

    TODO : also include the historical data to compute the rolling quantiles
    """

    client = PredictionForecastAPI()

    consumption_forecast = client.get_weekly_forecast(TODAY, horizon="2d")[
        "predicted_consumption"
    ]
    return consumption_forecast.rename("consommation")


def fetch_mf_sun_forecast():
    client = ArpegeSimpleAPI(date=TODAY)
    mf_sun_deps = client.departement_sun()
    return mf_sun_deps


def fetch_mf_wind_forecast():
    client = ArpegeSimpleAPI(date=TODAY)
    mf_wind_deps = client.departement_wind()
    return mf_wind_deps

@memory.cache(cache_validation_callback=expires_after(days=1))
def compute_our_enr_forecast():
    """Predict the renewable energy production."""
    # Fetch the forecasts
    sun_forecast = fetch_mf_sun_forecast()
    wind_forecast = fetch_mf_wind_forecast()

    model = ENRProductionModel.load()
    our_enr_forecast = model.predict(sun_flux=sun_forecast, wind_speed=wind_forecast)
    our_enr_forecast = our_enr_forecast.rename(
        columns={
            "sun": "solaire",
            "wind": "eolien",
        }
    )
    return our_enr_forecast.tz_localize("UTC")

@memory.cache(cache_validation_callback=expires_after(days=1))
def fetch_temperature():
    """Limitation : there only the observed temperature is used.
    
    TODO : add the forecasted mean daily temperature.
    TODO : make sure the last day is complete (the observations are not always available for the current day).
    """
    files = download_observations_all_departments()
    cut_before = TODAY - pd.DateOffset(years=1) - pd.DateOffset(month=9, day=1) 
    daily_temperature = aggregates_observations(files, cut_before=cut_before).tz_localize("Europe/Paris")
    return daily_temperature

def get_all_data():
    logger.info("Fetching all the data")
    logger.info("Fetching the history data")
    ecomix_data = fetch_history_data()
    logger.info("Fetching the consumption forecast")
    consumption_forecast = fetch_ret_consumption_forecast()
    logger.info("Fetching the renewable energy forecast")
    our_enr_forecast = compute_our_enr_forecast()
    logger.info("Fetching the temperature")
    daily_temperature = fetch_temperature()
    logger.info("Fetching the tempo signal")
    tempos = get_history_tempo_days()
    logger.info("Merging all the data")
    
    prediction_data = pd.concat([consumption_forecast.resample("h").mean(),
                                 our_enr_forecast], axis=1).dropna()
    all_data = pd.concat([ecomix_data.resample("h").mean(),
                      prediction_data], axis=0)
    all_data.index = pd.to_datetime(all_data.index, utc=True).tz_convert("Europe/Paris")
    origin = all_data.index[0] + pd.DateOffset(hour=6)
    all_daily_data = all_data.resample("h").mean().resample("D", origin=origin).sum()[1:-1]
    all_daily_data.index = all_daily_data.index.floor("D")
    
    
    data = pd.concat([all_daily_data,
                    tempos["value"].rename("Type_de_jour_TEMPO"),
                    daily_temperature.rename("temperature")], axis=1)
    return data

def generate_features(data, inplace=False):
    logger.info("Generating features")
    if not inplace:
        data = data.copy()
    data["production_nette"] = data["consommation"] - (
        data["eolien"] + data["solaire"]
    )
    quantils = data["production_nette"].rolling(365, center=False).aggregate({"q40": lambda x: x.quantile(0.4),
                                                                           "q80": lambda x: x.quantile(0.8)}).bfill()
    data["production_nette_q40"] = quantils["q40"]
    data["production_nette_q80"] = quantils["q80"]
    data["mean_temp_q30"] = data["temperature"].ffill().rolling(365, center=False).aggregate(lambda x: x.quantile(0.3)).bfill().ffill()
    return data

def get_history_tempo_days():
    """Get the tempo signal since the start of the tempo year."""
    client = TempoSignalAPI()
    start_date = TODAY - pd.DateOffset(day=1, month=9)
    after_tomorrow = TODAY + pd.DateOffset(days=2)
    history_tempo = client.get_data(start_date=start_date, end_date=after_tomorrow).sort_index(
        ascending=True
    )
    return history_tempo

def main():
    logger.info("Starting the prediction")
    data = get_all_data()
    data = generate_features(data)
    first_day_of_tempo = (TODAY - pd.DateOffset(month=9, day=1)).tz_localize("Europe/Paris")
    predictor = TempoPredictor(data[first_day_of_tempo:].copy())
    tempo_dummies = predictor.predict()
    our_tempo = pd.from_dummies(tempo_dummies).tz_convert("Europe/Paris").tz_localize(None)
    our_tempo.columns = ["our_tempo"]
    rte_tempo = predictor.data["Type_de_jour_TEMPO"].tz_convert("Europe/Paris").tz_localize(None)
    tempo = pd.concat([rte_tempo, our_tempo], axis=1).dropna(how="all")
    tempo.to_csv(gold_dir / "our_tempo_prediction.csv")
    logger.info("Prediction done, saved to %s", gold_dir / "our_tempo_prediction.csv")

if __name__ == "__main__":
    main()