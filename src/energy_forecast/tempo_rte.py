
import pandas as pd
import requests

from energy_forecast.rte_api_core import RTEAPROAuth2


class TempoSignalAPI(RTEAPROAuth2):
    """Class to interact with the Tempo Signal API from RTE.

    Example
    -------
    >>> r = TempoSignalAPI(secret="my_secret")
    >>> r.get_data("2021-01-01")
                end_date  value  updated_date
    start_date
    2022-01-01 2022-01-02  BLUE  2021-12-31 10:20:00+01:00
    """
    url_api = "https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"

    def get_data(self, start_date, end_date=None, fallback=True):
        """Get the tempo signal data from the API.

        Parameters
        ----------
        start_date : str, Timestamp
            the start date of the forecast.
        end_date : str, Timestamp, optional
            the end of the forecast, by default None
            If None, the forecast is for the next ``day``.
        fallback : bool, optional
            if True, the status of the fallback is returned,
            by default True.
        Returns
        -------
        DataFrame
            The tempo signal data.
        """
        start_date, end_date = self.check_start_end_dates(start_date, end_date, "2D")

        params = {
            "start_date": self.format_date(start_date),
            "end_date": self.format_date(end_date),
            "fallback_status":fallback
        }
        self.headers["Accept"] = "application/json"
        req = self.fetch_response(params)
        try:
            data =  pd.DataFrame(req.json()["tempo_like_calendars"]["values"]).set_index("start_date")
            data.index = pd.to_datetime(data.index)
            data["end_date"] = pd.to_datetime(data["end_date"])
            data["updated_date"] = pd.to_datetime(data["updated_date"])
            return data
        except requests.JSONDecodeError:
            return req.content
