from pathlib import Path
import pandas as pd
from sklearn import pipeline, linear_model
from energy_forecast import ROOT_DIR
from joblib import dump, load

class ENRProductionModel:
    """Model to predict the production of renewable energy sources.
    
    Implements a pair of linear regression models to predict the production of solar and wind energy
    from France regions weather data.
    
    Parameters
    ----------
    model_wind : sklearn.pipeline.Pipeline | None
        Model to predict the wind energy production.
    model_sun : sklearn.pipeline.Pipeline | None
        Model to predict the solar energy production.
    
    Examples
    --------
    >>> model = ENRProductionModel()
    >>> model.fit(sun_flux, wind_speed, energy_data)
    >>> predictions = model.predict(sun_flux, wind_speed)
    >>> model.save("path/to/save")
    """
    
    def __init__(self, model_wind=None, model_sun=None) -> None:
        self.model_wind = model_wind or pipeline.Pipeline([
            ("model", linear_model.LinearRegression(positive=True, fit_intercept=False))
        ])
        self.model_sun = model_sun or pipeline.Pipeline([
            ("model", linear_model.LinearRegression(positive=True, fit_intercept=False))
        ])
        
    @staticmethod
    def pre_process_sun_flux(sun_flux:pd.DataFrame) -> pd.DataFrame:
        return sun_flux
    
    @staticmethod
    def pre_process_wind_speed(wind_speed:pd.DataFrame) -> pd.DataFrame:
        X_squared = wind_speed ** 2
        X_squared.columns = [f"{col}_squared" for col in X_squared.columns]
        X_cubed = wind_speed ** 3
        X_cubed.columns = [f"{col}_cubed" for col in X_cubed.columns]

        wind_speed = pd.concat([wind_speed, X_squared, X_cubed], axis=1)

        return wind_speed
    
    def fit(self, sun_flux:pd.DataFrame, wind_speed:pd.DataFrame, productions:pd.DataFrame) -> None:
        wind_speed_preprocessed = self.pre_process_wind_speed(wind_speed)
        self.model_wind.fit(wind_speed_preprocessed, productions["wind"])
        sun_flux_preprocessed = self.pre_process_sun_flux(sun_flux)
        self.model_sun.fit(sun_flux_preprocessed, productions["sun"])
    
    def predict(self, sun_flux:pd.DataFrame, wind_speed:pd.DataFrame) -> pd.DataFrame:
        self.predictions = pd.DataFrame()
        wind_speed_preprocessed = self.pre_process_wind_speed(wind_speed)
        self.predictions["wind"] = self.model_wind.predict(wind_speed_preprocessed)
        sun_flux_preprocessed = self.pre_process_sun_flux(sun_flux)
        self.predictions["sun"] = self.model_sun.predict(sun_flux_preprocessed)
        return self.predictions
    
    def save(self, path:str | Path | None=None) -> None:
        path = path or ROOT_DIR / "data" / "production_prediction"
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        dump(self, path / "model.pkl")
    
    @classmethod
    def load(cls, path:str | Path | None=None) -> "ENRProductionModel":
        path = path or ROOT_DIR / "data" / "production_prediction"
        path = Path(path)
        instance = load(path / "model.pkl")
        return instance
    
