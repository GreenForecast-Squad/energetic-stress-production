
import requests
import pandas as pd
from .consumption_forecast import RTEAPROAuth2
from typing import TypedDict

class ProductionForecastOneEntry(TypedDict):
    """The type of the production forecast."""
    start_date: str
    end_date: str
    updated_date: str
    value: int

class ProductionForecastOneDay(TypedDict):
    start_date: str
    end_date: str
    type: str
    production_type: str
    sub_type: str
    values: list[ProductionForecastOneEntry]

class ProductionForecast(TypedDict):
    forecasts: list[ProductionForecastOneDay]

class ProductionForecastAPI(RTEAPROAuth2):
    """Access the RTE API to get the daily forecast of production."""
    url_api = "https://digital.iservices.rte-france.com/open_api/generation_forecast/v2/forecasts"

    def get_raw_data(self) -> ProductionForecast:
        parameters = {}
        req = requests.get(self.url_api,
                           headers=self.headers,
                            params=parameters)
        req.raise_for_status()
        return req.json()