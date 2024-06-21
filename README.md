# Forecast of French electric mix

The aim of this project is to forecast the French electric mix for the next few days.

The electric mix is the relative proportion of each energy source used to produce electricity. The main energy sources are: nuclear, wind, solar, hydraulic, coal, gas, bioenergy and waste.

The Wind and solar energy sources are green, but they are intermittent and depend on the weather. The hydraulic energy source is also dependent on the weather, but to a lesser extent.

Hence, the weather directly impacts the CO2 emissions of the electry consumption.
Knowing the CO2 emission forecast can help plan the time of use of electric devices to reduce the carbon footprint.

## Description of the project

The project is divided into 2 parts:
1. Analysis of the historical data
2. Forecast of the electric mix

### 1. Analysis of the historical data
We gathered the data from the French electricity transmission system operator RTE (Réseau de Transport d'Electricité) and the French meteorological service Météo France.
The data start in 2022 and end in 2024.

We used the data to:
- train a model to predict the electric mix
- assess the performance of the model
- identify the main factors influencing the electric mix

### 2. Forecast of the electric mix
We will use the model trained in the first part to forecast the electric mix for the next few days.

The forecast is updated every day.

A website will be created to display the forecast.

## Installation

We need [hatch](https://hatch.pypa.io) to manage the project.

### Interactive mode

You can use Hatch to activate the virtual environment and install the dependencies with:
```bash
hatch shell
```
This will open a shell with the virtual environment activated.
The dependencies listed in the `pyproject.toml` file will be installed automatically.

### Run the tests
You can run the tests with:
```bash
hatch test
```
This will run the tests in the virtual environment.

### Serve the Dashboard

You can serve the dashboard with:
```bash
hatch serve:prod
```
This will serve the dashboard on `http://localhost:8000`.

## The dashboard
The dashoard is developed with [Taipy](https://docs.taipy.io/en/latest/).
Lauchind the app will automaticaly
- Download the weather forecast
- Download the electricity mix history
- Display the forecast