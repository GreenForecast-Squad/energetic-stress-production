import os

import pandas as pd

in_relative_path = "../energetic-stress-production/data/silver/"
in_absolute_path = os.path.abspath(os.path.join(os.getcwd(), in_relative_path))
out_relative_path = "../energetic-stress-production/data/silver//rte_2014_2024.csv"
out_absolute_path = os.path.abspath(os.path.join(os.getcwd(), out_relative_path))

def rte_tempo_join(rte_df, tempo_df) -> pd.DataFrame:
    """
    On formatte les dates de la même façon sur les deux dataframes
    puis on les join sur la colonne date
    => "Left" donc colonne "type_tempo" vide si pas de jour tempo.

    :param rte_df: dataframe des données aggrégées de prod / conso RTE
    :param tempo_df: dataframe des jours tempo aggrégés
    :return: dataframe des données aggrégées de prod / conso RTE avec une nouvelle colonne "type_tempo"
    """
    rte_df["Date"] = pd.to_datetime(rte_df['Date'], format='%Y-%m-%d')
    tempo_df['Date'] =  pd.to_datetime(tempo_df['Date'], format='%Y-%m-%d %H:%M:%S')
    return pd.merge(rte_df, tempo_df, on="Date", how="left")

def write_data(df):
    print(f"Wrtting data to '{out_absolute_path}'...")
    df.to_csv(out_absolute_path, index=False)



def __init__():
    rte_df = pd.read_csv(f"{in_absolute_path}/rte_production.csv", index_col=False, engine='python')
    tempo_df = pd.read_csv(f"{in_absolute_path}/tempo_2014_2024.csv", index_col=False)
    joined_df = rte_tempo_join(rte_df, tempo_df)
    write_data(joined_df)


__init__()
