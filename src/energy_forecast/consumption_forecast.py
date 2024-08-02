from typing import TypedDict

import pandas as pd

from energy_forecast.rte_api_core import RTEAPROAuth2


class OneValue(TypedDict):
    start_date: str
    end_date: str
    value: int

class PeakValue(TypedDict):
    peak_hour: str
    value: int
    temperature: float
    temperature_deviation: float

class DayForecast(TypedDict):
    updated_date: str
    values: list[OneValue]
    start_date: str
    end_date: str
    peak: PeakValue

class PredictionForecast(TypedDict):
    weekly_forecasts: list[DayForecast]


class PredictionForecastAPI(RTEAPROAuth2):
    """Access the RTE API to get the weekly forecast of consumption."""

    url_api = "https://digital.iservices.rte-france.com/open_api/consumption/v1/weekly_forecasts"



    def get_raw_data(self,
                     start_date: str | pd.Timestamp |None=None,
                     end_date: str | pd.Timestamp|None=None,
                     horizon="1w") -> PredictionForecast:
        """Retrieve the raw data from the API.

        Parameters
        ----------
        start_date : str, Timestamp
            the start date of the forecast.
        end_date : str, Timestamp, optional
            the end of the forecast, by default None
            If None, the forecast is for the next ``horizon``.
        horizon : str, Timedelta, optional
            If ``end_date`` is none, the duration of the forecast from ``start_date`` , by default "1w"

        Returns
        -------
        PredictionForecast
            The raw data from the API.

        """
        start_date, end_date = self.check_start_end_dates(start_date, end_date, horizon)
        params = {
            "start_date": self.format_date(start_date),
            "end_date": self.format_date(end_date),
        }
        req = self.fetch_response(params)
        return req.json()

    def get_weekly_forecast(self, start_date, end_date=None, horizon="1w"):
        """Retrieve the weekly forecast of consumption.

        Parameters
        ----------
        start_date : str, Timestamp
            the start date of the forecast.
        end_date : str, Timestamp, optional
            the end of the forecast, by default None
            If None, the forecast is for the next ``horizon``.
        horizon : str, Timedelta, optional
            If ``end_date`` is none, the duration of the forecast from ``start_date`` , by default "1w"

        Returns
        -------
        pd.DataFrame
            The weekly forecast of consumption.

        See Also
        --------
        - :py:meth:`get_raw_data`
        - :py:meth:`format_weekly_data`

        """
        raw_json = self.get_raw_data(start_date, end_date)
        return self.format_weekly_data(raw_json)

    def format_weekly_data(self, json_data: PredictionForecast) -> pd.DataFrame:
        """Format the raw data from the API into a DataFrame.

        Parameters
        ----------
        json_data : PredictionForecast
            The raw data from the API.

        Returns
        -------
        pd.DataFrame
            The formatted data. The Index is the date of the prediction.
            Includes the columns:

            - predicted_consumption: the predicted consumption in MW
            - predicted_at: the date when the prediction was calculated

        """
        values = {}
        for day_data in json_data["weekly_forecasts"]:
            for pred in day_data["values"]:
                values[pred["start_date"]] = {"predicted_consumption":pred["value"],
                                              "predicted_at": day_data["updated_date"]}

        data = pd.DataFrame.from_dict(values, orient="index")
        data.index = pd.to_datetime(data.index)
        data["predicted_at"] = pd.to_datetime(data["predicted_at"])

        data.index.name = "time"
        return data.sort_index()