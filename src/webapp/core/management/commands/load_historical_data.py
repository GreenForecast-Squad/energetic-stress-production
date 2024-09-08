from django.core.management.base import BaseCommand
from core.models import WeatherForecastMeanDepartment
from energy_forecast import ROOT_DIR
import pandas as pd

class Command(BaseCommand):
    help = 'Load weather forecasts from a CSV file into the database'

    def handle(self, *args, **kwargs):
        data_root = ROOT_DIR / 'data' / 'silver' / 'weather_forecasts'
        sun_flux_file = data_root / 'sun_flux_downward_hourly_d1_departements.csv'
        temperature_file = data_root / 'temperature_hourly_d1_departements.csv'
        wind_speed_file = data_root / 'wind_speed_hourly_d1_departements.csv'
        
        sun_flux_df = pd.read_csv(sun_flux_file)[['valid_time', 'departement', 'sun_flux']].set_index(['valid_time', 'departement'])
        # temperature_df = pd.read_csv(temperature_file)[['valid_time', 'departement', 'temperature']].set_index(['valid_time', 'departement'])
        wind_speed_df = pd.read_csv(wind_speed_file)[['valid_time', 'departement', 'wind_speed']].set_index(['valid_time', 'departement'])
        print(sun_flux_df)
        # print(temperature_df)
        print(wind_speed_df)
        all_data = sun_flux_df.join(wind_speed_df, how='inner').reset_index()
        print(all_data)
        for _, row in all_data.iterrows():
            WeatherForecastMeanDepartment.objects.create(
                valid_time=row['valid_time'],
                department=row['departement'],
                horizon_forecast='D1',
                sun_flux=row['sun_flux'],
                temperature=0,
                wind_speed=row['wind_speed']
            )
        
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded weather forecasts'))
