import requests
import pandas as pd
from typing import TypedDict

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

class PredictionForecastAPI:
    """Access the RTE API to get the weekly forecast of consumption."""

    url_token = "https://digital.iservices.rte-france.com/token/oauth/"
    url_api = "https://digital.iservices.rte-france.com/open_api/consumption/v1/weekly_forecasts"
    def __init__(self, secret):
        """Initialize the API with the secret.

        Parameters
        ----------
        secret : str
            The Base64 encoded secret to access the API.
            See the documentation of the API to get the secret.

        """
        self.secret = secret
        self.token = None
        self.token_type = None
        self.token_expires_in = None
        self.token_expires_at = None
        self.get_token()

    def get_token(self):
        """Get a token to access the API.
        """
        headers_token = {
            "Authorization": "Basic {}".format(self.secret),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        req = requests.post(self.url_token,
                            headers=headers_token
                            )
        req.raise_for_status()
        self.token = req.json()["access_token"]
        self.token_type = req.json()["token_type"]
        self.token_expires_in = req.json()["expires_in"]
        self.token_expires_at = pd.Timestamp("now") + pd.Timedelta(self.token_expires_in, unit="s")

    def check_token(self):
        """Check if the token is still valid. If not, get a new one."""
        if self.token_expires_at < pd.Timestamp("now"):
            self.get_token()

    def get_raw_data(self, start_date, end_date=None, horizon="1w") -> PredictionForecast:
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
        self.check_token()
        start_date = pd.Timestamp(start_date)
        if end_date is None:
            end_date = start_date + pd.Timedelta(horizon)
        else:
            end_date = pd.Timestamp(end_date)
        headers = {
            "Host": "digital.iservices.rte-france.com",
            "Authorization": "Bearer {}".format(self.token),
        }
        params = {
            "start_date": start_date.strftime("%Y-%m-%dT00:00:00+02:00"),
            "end_date": end_date.strftime("%Y-%m-%dT00:00:00+02:00"),
        }
        req = requests.get(self.url_api,
                           headers=headers,
                           params=params)
        req.raise_for_status()
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