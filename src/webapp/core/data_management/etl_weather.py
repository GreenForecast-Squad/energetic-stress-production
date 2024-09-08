"""This module contains the fonctionalities to extract, transform and load weather data."""

import pandas as pd
from pathlib import Path
from core.models import WeatherForecastMeanDepartment
from energy_forecast.meteo import ArpegeSimpleAPI

def run_etl_pipeline():
    """Run the ETL pipeline to load weather data into the database."""
    
    # extract
    arpege_client = ArpegeSimpleAPI()
    departements_sun_flux = arpege_client.departement_sun()
    departements_wind_speed = arpege_client.departement_wind()
    
    all_data = departements_sun_flux.join(departements_wind_speed, how='inner').reset_index()
    print(all_data)
    for _, row in all_data.iterrows():
        WeatherForecastMeanDepartment.objects.create(
            valid_time=row['valid_time'],
            department=row['departement'],
            horizon_forecast='D1',
            sun_flux=row['sun_flux'],
            temperature=row['temperature'],
            wind_speed=row['wind_speed']
        )
