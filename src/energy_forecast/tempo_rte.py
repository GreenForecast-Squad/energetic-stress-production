
import numpy as np
import pandas as pd
import requests
from pandas import DataFrame

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

class TempoPredictor:
    """Class to predict the tempo signal for the next day.

    Example
    -------
    >>> r = TempoPredict(data)
    >>> r.predict()
    """
    prevision_consumtion_f = "Prévision_J-1"
    production_solar_f = "Solaire"
    production_eolien_f = "Eolien"
    production_nette_f = "Production_nette"
    known_jour_tempo_f = "Type_de_jour_TEMPO"
    production_normed_f = "Production_norm"

    def __init__(self, data: pd.DataFrame):
        """Initialize the class.

        Parameters
        ----------
        data : pd.DataFrame
            The data to use for the prediction.
            Should contain the following columns:
            - Prévision_J-1 : the forecasted consumption
            - Solaire : the solar production (forecasted)
            - Eolien : the wind production (forecasted)
            - Type_de_jour_TEMPO : the known tempo signal (used for the training and stock calculation)

        Note
        ----
        The data should start from the 1st of September, and last one year.
        """
        self.data: DataFrame = data
        self.data[self.production_nette_f] = self.data[self.prevision_consumtion_f] - (self.data[self.production_eolien_f] + self.data[self.production_solar_f])

        self.q80 = data[self.production_nette_f].quantile(0.8)  # TODO : should instead be computed on rolling window of 1 year, using data from previous season
        self.q40 = data[self.production_nette_f].quantile(0.4)  # TODO : should instead be computed on rolling window of 1 year, using data from previous season
        self.qtemp30 = 9  # TODO : should instead be computed on rolling window of 1 year, using data from previous season of the 30th percentile of the temperature
        self.gamma = -0.1176
        self.kappa = 8.3042
        self.data[self.production_normed_f] = (self.data[self.production_nette_f] - self.q40) / ( (self.q80 - self.q40) * np.exp(self.gamma * (self.kappa - self.qtemp30)))
        self.categories: DataFrame = pd.get_dummies(data[self.known_jour_tempo_f]).astype(int)
        self.start_BLANC = 43
        self.start_ROUGE = 22
        self.start_blanc_rouge = self.start_BLANC + self.start_ROUGE
        self.data["stock_rouge"] = self.start_ROUGE - self.categories["ROUGE"].cumsum().shift(1).fillna(0)
        self.data["stock_blanc"] = self.start_BLANC - self.categories["BLANC"].cumsum().shift(1).fillna(0)
        self.data["stock_blanc_rouge"] = data["stock_rouge"] + data["stock_blanc"]
        self.data["jour_tempo"] = range(1, len(data) + 1)  # Not sur if start from 0 or 1

        self.A_rouge = 3.15
        self.B_rouge = -0.010
        self.C_rouge = -0.031
        self.A_blanc_rouge = 4
        self.B_blanc_rouge = -0.015
        self.C_blanc_rouge = -0.026

        self.data["seuil_rouge"] = (
            self.A_rouge
            + self.B_rouge * ( data["jour_tempo"] -1 )
            + self.C_rouge * data["stock_rouge"]
        )
        self.data.loc[ self.data["stock_rouge"] == 0  ,"seuil_rouge"] = 2

        data["seuil_blanc_rouge"] = (
            self.A_blanc_rouge
            + self.B_blanc_rouge * (data["jour_tempo"] - 1)
            + self.C_blanc_rouge * data["stock_blanc_rouge"]
        )
        data.loc[ data["stock_blanc_rouge"] == 0  ,"seuil_blanc_rouge"] = 2

    def predict(self):
        """Predict the tempo signal for the next day.

        Returns
        -------
        DataFrame
            The tempo signal data.
        """
        self.prediction_rouge = self.data[self.production_normed_f] > self.data["seuil_rouge"]
        start_ROUGE_allowed =  (self.prediction_rouge.index[0] + pd.DateOffset(month=10, day=31))  #    "2015-10-31"
        end_ROUGE_allowed = (self.prediction_rouge.index[-1] + pd.DateOffset(month=4, day=1) )  #"2016-04-01"
        self.prediction_rouge[:start_ROUGE_allowed] = False
        self.prediction_rouge[end_ROUGE_allowed:] = False
        self.prediction_rouge[self.data["stock_rouge"] < 0] = False

        sundays = self.data.index.weekday == 6  # type: ignore
        saturdays = self.data.index.weekday == 5  # type: ignore
        self.prediction_rouge[sundays] = False
        self.prediction_rouge[saturdays] = False

        prediction_blanc_rouge = self.data[self.production_normed_f] > self.data["seuil_blanc_rouge"]
        prediction_blanc = prediction_blanc_rouge & ~self.prediction_rouge
        prediction_blanc[sundays] = False

        prediction_blanc[self.data["stock_blanc"] < 0] = False

        predictions = pd.DataFrame({
            "prediction_rouge": self.prediction_rouge,
            "prediction_blanc": prediction_blanc,
            "prediction_bleu": ~(self.prediction_rouge | prediction_blanc)
        })
        return predictions

    def confusion_matrix(self, data_true: pd.Series | None=None, data_pred: pd.Series | pd.DataFrame | None= None) -> pd.DataFrame:
        """Compute the confusion matrix.

        Parameters
        ----------
        data_true : pd.Series, optional
            The true data.
        data_pred : pd.Series
            The predicted data.

        Returns
        -------
        pd.DataFrame
            The confusion matrix.
        """
        if data_true is None:
            data_true = self.data["Type_de_jour_TEMPO"]
        if data_pred is None:
            data_pred = self.predict()
        if isinstance(data_pred, pd.DataFrame):
            data_pred = data_pred.idxmax(axis=1)

        confusion_matrix = pd.crosstab(data_true, data_pred)
        return confusion_matrix