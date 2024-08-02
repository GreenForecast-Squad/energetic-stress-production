
import logging
from typing import Literal, TypedDict

import pandas as pd
import requests

from energy_forecast.rte_api_core import RTEAPROAuth2

logger = logging.getLogger(__name__)

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

AvailableProductionType = Literal[
    "AGGREGATED_PROGRAMMABLE_FRANCE",
    "AGGREGATED_NON_PROGRAMMABLE_FRANCE",
    "WIND_ONSHORE",
    "WIND_OFFSHORE",
    "SOLAR",
    "AGGREGATED_CPC",
    "MDSETRF",
    "MDSESTS",
]
AvailableForcastType = Literal["CURRENT", "ID", "D-1", "D-2", "D-3"]

class ProductionForecastAPI(RTEAPROAuth2):
    """Access the RTE API to get the daily forecast of production.

    Example
    -------
    >>> r = ProductionForecastAPI(secret)
    >>> r.get_raw_data("SOLAR", "D-1", "2021-01-01", "2021-01-10")
    """
    url_api = "https://digital.iservices.rte-france.com/open_api/generation_forecast/v2/forecasts"

    def assert_duration(self, start_date: pd.Timestamp, end_date: pd.Timestamp, autofix: bool = False) -> tuple[pd.Timestamp, pd.Timestamp]:
        duration = end_date - start_date
        if duration <= pd.Timedelta("21D"):
            return start_date, end_date
        if autofix:
            logger.warning("The duration of the forecast cannot be more than 21 days. Fixing the end date.")
            end_date = start_date + pd.Timedelta("21D")
            return start_date, end_date
        raise ValueError("The duration of the forecast cannot be more than 21 days.")

    def get_raw_data(self,
                     production_type: AvailableProductionType | None=None,
                     type: AvailableForcastType | None = None,
                     start_date: str | pd.Timestamp | None=None,
                     end_date: str | pd.Timestamp|None=None,
                     horizon="1d",
                     ) -> ProductionForecast:
        start_date, end_date = self.check_start_end_dates(start_date, end_date, horizon)
        start_date, end_date = self.assert_duration(start_date, end_date, autofix=True)
        parameters = {"production_type": production_type,
                      "type": type,
                      "start_date": self.format_date(start_date),
                      "end_date": self.format_date(end_date),
                      }
        req = requests.get(self.url_api,
                           headers=self.headers,
                            params=parameters)
        req.raise_for_status()
        return req.json()