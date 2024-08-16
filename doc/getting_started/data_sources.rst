Data Sources
============

This Page lists the different data sources available, and the corresponding way to access them.

Energy Data Sources
-------------------

Predicted consumption computed by RTE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The total consumption of France is computed by RTE.

The corresponding API is named  `Consumption <https://data.rte-france.com/catalog/-/api/consumption/Consumption/v1.2>`_
You can use it to access

- "short_term" : the expected consumption for today, tomorrow (D-1) and the day after tomorrow (D-2) 
- "weekly_forecasts" : the expected consumption for D-3 to D-9

When requesting dates in the past, the history of the forecasts is available.

To access it, use the class ``energy_forecast.consumption_forecast.PredictionForecastAPI``

Predicted Productions computed by RTE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Solar and Eolian productions in France is computed by RTE.

The corresponding API is named `Generation Forecast <https://data.rte-france.com/catalog/-/api/generation/Generation-Forecast/v2.1>`_
You can use it to access

- "SOLAR" : the expected solar production for today (D-0), and tomorrow (D-1)
- "WIND_ONSHORE" : the expected eolian production for today (D-0), and tomorrow (D-1)

Other production means are available, some with a longer forecast horizon (D-2 to D-3)

When requesting dates in the past, the history of the forecasts is available.
However, the API is limited to 21 days of history per call, so a lot of calls are needed to get a long history.


When requesting dates in the past, the history of the forecasts is available.

To access it, use the class ``energy_forecast.production_forecast.ProductionForecastAPI``

Tempo labels computed by RTE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Tempo labels are provided by RTE.
The corresponding API is named `Tempo Like Supply Contract <https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1>`_

You can use it to access the tempo labels for the current day, and the next day, and all the history of the tempo labels.

To access it, use the class ``energy_forecast.tempo_rte.TempoSignalAPI``

About Eco2mix
-------------

Eco2mix is a service provided by RTE, which provides a lot of data about the energy production and consumption in France.
Some are the same as the ones provided by the APIs above, but some are not.

In particular, the historical regional production and consumption are available.

You can access it using the function ``energy_forecast.eco2mix.get_data`` (Refactoring in progress)

Weather Data Sources
--------------------

Weather forecasts
~~~~~~~~~~~~~~~~~

The weather forecasts are provided by Meteo France with different levels of details, corresponding to different model names.

The raw files can be downloaded from `meteo.data.gouv.fr <https://meteo.data.gouv.fr>`_

You can access the Arpege model forecasts using the class ``energy_forecast.meteo.ArpegeSimpleAPI``
This client class download the data as Grib2 files, which requier Xarray and cfgrib to be read.

Historical weather forecasts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The historical weather forecasts are not publicly available.
Fortunately, this data as beed stored by a french assosiation of amateur meteorologists.

The interesting parameters has been extected from the raw data, and are stored in ``data/silver/weather``.

To ge the data the first time, you need to download it from S3 using ``energy_forecast.meteo.download_historical_forecasts``.
To do so, the S3 credentials are needed, contact the project's owner.

Up to D+3 forecasts are available from the model Arpege, from 2022-01-01 to 2024-04-01.

