import pandas as pd
import requests


class RTEAPROAuth2:
    url_token = "https://digital.iservices.rte-france.com/token/oauth/"
    url_api: str
    def __init__(self, secret: str) -> None:
        self.secret = secret
        self.token: str
        self.token_type: str
        self.token_expires_in: str
        self.token_expires_at: pd.Timestamp

        self.get_token()

    def get_token(self) -> None:
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
        self.headers: dict[str, str] = {
            "Host": "digital.iservices.rte-france.com",
            "Authorization": "Bearer {}".format(self.token),
        }
    def check_token(self) -> None:
        """Check if the token is still valid. If not, get a new one."""
        if self.token_expires_at - pd.Timestamp("now") < pd.Timedelta(10, unit="s"):
            self.get_token()

    @staticmethod
    def format_date(date: pd.Timestamp) -> str:
        return date.strftime("%Y-%m-%dT00:00:00+02:00")

    def fetch_response(self, params: dict) -> requests.Response:
        """Fetch the response from the API.

        Uses :
        - :py:attr:`url_api` for the API endpoint
        - :py:attr:`headers` for the headers to pass to the API, including the token.

        The token is checked before making the request.

        Parameters
        ----------
        params : dict
            the parameters to pass to the API.

        Returns
        -------
        requests.Response
            The response from the API.

        """
        self.check_token()
        req = requests.get(self.url_api,
                           headers=self.headers,
                           params=params)
        req.raise_for_status()
        return req

    @staticmethod
    def check_start_end_dates(start_date: str | pd.Timestamp |None=None, end_date: str | pd.Timestamp|None=None, horizon="7D", default_start="now") -> tuple[pd.Timestamp, pd.Timestamp]:
        start_date = start_date or default_start
        start_date = pd.Timestamp(start_date)
        if end_date is None:
            end_date = start_date + pd.Timedelta(horizon)
        else:
            end_date = pd.Timestamp(end_date)
        return start_date, end_date