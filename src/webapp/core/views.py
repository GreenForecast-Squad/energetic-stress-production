from django.shortcuts import render
from .models import WeatherForecastMeanDepartment
from datetime import date, timedelta
from django.http import HttpResponse

from .data_management.etl_weather import run_etl_pipeline

def landing_page(request):
    pass
    #return render(request, 'landing_page.html', {'forecasts': forecasts})



def check_and_load_data(request):
    # Check if data exists
    today = date.today()
    # check if data exists for today
    if WeatherForecastMeanDepartment.objects.filter(valid_time__date=today).exists():
        return HttpResponse("Data already exists for today.")
    else :
        # Run ETL pipeline if data does not exist
        run_etl_pipeline()
    
    # Load data from the database
    data = WeatherForecastMeanDepartment.objects.all()
    
    # Render the data in a template or return as a response
    return HttpResponse(f"Loaded {data.count()} records from the database.")
