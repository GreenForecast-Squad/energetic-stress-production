from django.db import models
from energy_forecast.constants import departements

HORIZON_CHOICES = [
    ('D0', 'D0'),
    ('D1', 'D1'),
    ('D2', 'D2'),
    ('D3', 'D3')
]

# Create your models here.
class WeatherForecastMeanDepartment(models.Model):
    # set valide_time as datetime 
    # set sun_flux as a float
    # set department as a category
    # set the horizon forcast type : D0, D1, D2, D3
    # use datetime and department as a index
    valid_time = models.DateTimeField()
    department = models.CharField(max_length=50, choices=[(d, d) for d in departements])
    horizon_forecast = models.CharField(max_length=2, choices=HORIZON_CHOICES)
    sun_flux = models.FloatField()
    wind_speed = models.FloatField()
    temperature = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=['valid_time', 'horizon_forecast']),
        ]
    
    def __str__(self):
        return f"{self.valid_time} - {self.horizon_forecast} - {self.department} - {self.sun_flux} "

class Forecast(models.Model):
    date = models.DateField()
    forecast_data = models.TextField()

    def __str__(self):
        return f"{self.date}: {self.forecast_data}"
