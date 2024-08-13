Description of the project
==========================

This page describes the project and its goals.

Summary
-------
The project uses weather forecast to estimate the France electricity Tempo category for the next four days.

To do it, we first predict the Solar and Eolien production for the next days.
Then, combining the production forecast with the consumption forecast provided by RTE, we estimate the Tempo category.

Both step are done using machine learning models, first a regression model to predict the production, then a classification model to predict the Tempo category.


Introduction
------------

In France, there is a electricity contract available name "Tempo", where 22 days per year the electricity is five times more expensive than the rest of the year. 
The days are classified in three categories: 

- red, 22 days a year between November and March
- white, 43 days a year between October and September
- and blue, all the other days of the year.
 
The red days are the most expensive, the blue days are the cheapest and the white days are in between.

The type of day is provided by RTE, the French electricity transmission system operator, the day before at 11am.

This horizon is too short to adapt the activities, and hence the consumption.
Hence, this project aims to predict the Tempo category for the next days, to help the user to adapt its consumption.

Tempo categorisation
--------------------

The Tempo categories (Blue, White, Red) are defined by RTE. 
The exact algorithm is not public, but a simplified model is available in the `RTE documentation <https://www.services-rte.com/files/live/sites/services-rte/files/pdf/20160106_Methode_de_choix_des_jours_Tempo.pdf>`_.

The main algorithm is based on the difference between the expected consumption, and the expected renewable production that define the "net consumption".

The net consumption is then compared to two thresholds, and the category is defined based on this comparison.
The thresholds depends on the number of days already used this year.

Then, a number of rules are applied to correct the category:

- if the day is a weekend, the category cannot be red
- if the day is a Sunday, the category cannot be white



.. image:: /_static/tempo_graph.png
    :width: 400px
    :align: center
    :alt: Tempo categories
    

Hence, in order to predict the Tempo category, we need to predict the consumption and the renewable production.

Consumption forecast
--------------------

Fortunately, RTE provides a forecast of the consumption for the next days.
The forecast is available for the next nine days.

Hence, in this project, we will use this forecast to predict the Tempo category.

Production forecast
-------------------

Unfortunately, RTE does not provide a forecast of the renewable production.
At least, not for the next nine days: only the next day is available.

Hence, we need to predict the renewable production for the next days ourselves.

The renewable production is composed of:

- The Solar production, linked to the sun flux at the surface
- The Eolien production, related to the wind speed

Thus, to forecast ourselve the renewable production, we will use the weather forecast.

Weather forecast
----------------

The French weather service, Météo France, provides a forecast of the weather for the next days.
Two models are available:
- ARPEGE : with a longer forecast horizon, but less accurate
- AROME : with a shorter forecast horizon, but more accurate

For even longer forecast, we can use the American model GFS, but it is even less accurate.

Method
======

There is a description of the method used to predict the Tempo category.

Training data
-------------

We have access to a few years of historical weather prediction ARPEGE : from 2022 to 2024.
We also have access to the historical production and consumption data for the same period.

However, is is more interesting to use the historical production and consumption forecasts.
Fortunately, RTE API allows to access the forecast for the last years.

Hence, we will uses these data to trains the two models:
- historical ARPEGE forecast and historical production forecast to train the production model
- historical production and consumption forecast to train the Tempo model

Limitations
-----------
One limitation is the fact that the renewable production is directly linked to ground installations.
Days after days, there are more and more installations, and the production is increasing.

Hence, the model should be retrained regularly to take into account the new installations, with higher weights for the most recent data.


In Production
=============

In order to predict the Tempo category, every day at 11am, the model will:
- get the weather forecast for the next days
- get the consumption forecast for the next days
- get the Tempo category for tomorrow
- predict the production for the next days
- predict the Tempo category for the next days
- store the results in a database
- send an email to the user with the results
- send an email to the user if the category changes
- display the results in a web interface

