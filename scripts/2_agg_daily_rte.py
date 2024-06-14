import os

import numpy as np
import pandas as pd

pd.options.mode.copy_on_write = True


in_relative_path = "../energetic-stress-production/data/silver/"
in_absolute_path = os.path.abspath(os.path.join(os.getcwd(), in_relative_path))
out_relative_path = "../energetic-stress-production/data/gold/rte_daily_2014_2024.csv"
out_absolute_path = os.path.abspath(os.path.join(os.getcwd(), out_relative_path))

# Suppression des colonnes détails d'energies
columns_to_keep = [
    "Nature",
    "Date",
    "type_tempo",
    "Consommation",
    "Prévision J-1",
    "Prévision J",
    "Fioul",
    "Charbon",
    "Gaz",
    "Nucléaire",
    "Eolien",
    "Solaire",
    "Hydraulique",
    "Pompage",
    "Bioénergies",
    "Ech. physiques",
    "Taux de Co2",
    "Ech. comm. Angleterre",
    "Ech. comm. Espagne",
    "Ech. comm. Italie",
    "Ech. comm. Suisse",
    "Ech. comm. Allemagne-Belgique",
]

# Pour concat des echanges commerciaux
list_exchange_cols = [
    "Ech. comm. Angleterre",
    "Ech. comm. Espagne",
    "Ech. comm. Italie",
    "Ech. comm. Suisse",
    "Ech. comm. Allemagne-Belgique",
]

# GroupBy
groupby = ["Date", "Nature", "type_tempo"]
column_aggregations = {
    "Consommation": "sum",
    "Prévision_J-1": "sum",
    "Prévision_J": "sum",
    "Fioul": "sum",
    "Charbon": "sum",
    "Gaz": "sum",
    "Nucléaire": "sum",
    "Eolien": "sum",
    "Solaire": "sum",
    "Hydraulique": "sum",
    "Pompage": "sum",
    "Bioénergies": "sum",
    "Ech_physiques": "sum",
    "Taux_de_Co2": "sum",
    "Ech_comm": "sum",
}


def transform_rte(rte_df: pd.DataFrame) -> pd.DataFrame:
    """
    Make transformations to clean rte_df
    Filter out few columns
    Sum all commercials exchange with neighboors
    Clean columns names
    """
    rte_df = rte_df[columns_to_keep]
    for col in rte_df.columns:
        if col not in ["Date", "Nature", "type_tempo"]:
            rte_df[col] = rte_df[col].replace("ND", None).astype(float)
    rte_df["Ech_comm"] = rte_df[list_exchange_cols].sum(axis=1)

    rte_df.columns = rte_df.columns.str.replace(" ", "_")
    rte_df.columns = rte_df.columns.str.replace(".", "")
    return rte_df


def groupby_daily(rte_df):
    """
    Groupby rte_df by date & type_tempo - sum all others columns
    For 'Données consolidées' and 'Données définitives' we have
    a point every 30min => we have to divide by 2
    for 'Données temps réel' we have a point every 15 min
    => we have to divide by 4

    :param rte_df: _description_
    """
    rte_daily_df = rte_df.groupby(groupby).agg(column_aggregations).reset_index()
    for col in set(rte_daily_df.columns) - set(groupby):
        rte_daily_df[col] = np.where(
            rte_daily_df["Nature"] == "Données temps réel",
            rte_daily_df[col] / 4,
            rte_daily_df[col] / 2,
        )
        rte_daily_df[col] = rte_daily_df[col].astype(float) / 2
    return rte_daily_df


def merge_rte_solar_wind(rte_daily_df: pd.DataFrame, solar_wind_df: pd.DataFrame):
    rte_daily_df["Date"] = pd.to_datetime(rte_daily_df["Date"])
    solar_wind_df["Date"] = pd.to_datetime(solar_wind_df["Date"])
    return pd.merge(rte_daily_df, solar_wind_df, on="Date", how="left")


def write_data(df):
    print(f"Wrtting data to '{out_absolute_path}'...")
    df.to_csv(out_absolute_path, index=False)


def __init__():
    rte_df = pd.read_csv(f"{in_absolute_path}/rte_2014_2024.csv", index_col=False, engine="python")

    rte_df = transform_rte(rte_df)
    rte_daily_df = groupby_daily(rte_df)

    solar_wind_df = pd.read_csv(f"{in_absolute_path}/solar_wind_data.csv")

    rte_daily_df = merge_rte_solar_wind(rte_daily_df, solar_wind_df)

    write_data(rte_daily_df)


__init__()
