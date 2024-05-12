import os

import pandas as pd

in_relative_path = "../energetic-stress-production/raw_datasets/rte/"
in_absolute_path = os.path.abspath(os.path.join(os.getcwd(), in_relative_path))
out_relative_path = "../energetic-stress-production/clean_datasets/"
out_absolute_path = os.path.abspath(os.path.join(os.getcwd(), out_relative_path))

empty_column = [" Stockage batterie", "Déstockage batterie", "Eolien terrestre", "Eolien offshore"]


def get_all_definitive_paths() -> list:
    """
    Récupère le path de tout les fichiers annuel définitifs

    :return: Une liste avec tout les paths
    """
    all_rte_path = []
    for y in range(2014, 2021):
        all_rte_path.append(in_absolute_path + f"/eCO2mix_RTE_Annuel-Definitif_{y}.xls")
    return all_rte_path


def join_defintive_data(paths: list) -> pd.DataFrame:
    data = pd.DataFrame()
    for path in paths:
        temporary_df = pd.read_csv(
            os.path.join("raw_datasets", path),
            skipfooter=1,
            engine="python",
            index_col=False,
            skiprows=lambda x: x % 2 != 1 if x != 0 else False,
            encoding="latin-1",
            sep="\t",
        )
        data = pd.concat([data, temporary_df])
    return data


def get_definitive_data() -> pd.DataFrame:
    """
    Récupère toutes les données annuelles définitives.
    Concatène dans un seul dataframe Pandas.

    :return: Dataframe avec les données définitives
    """
    definitive_paths = get_all_definitive_paths()
    data = join_defintive_data(definitive_paths)
    return data


def get_consolid_data() -> pd.DataFrame:
    """
    Retourne les données consolidées dans un dataframe Pandas.

    On filtre uniquement pour garder les rows à la demi-heure.
    (on a une prédiction toute les 15 min mais on l'enlève)

    :return: Dataframe avec les données consolidées
    """
    data = pd.read_csv(
        f"{in_absolute_path}/eCO2mix_RTE_En-cours-Consolide.xls",
        skipfooter=0,
        index_col=False,
        engine="python",
        encoding="latin-1",
        sep="\t",
        usecols=lambda col: col not in empty_column,
    )
    data = data[data["Heures"].str.contains(":30|:00")]
    data["Date"] = data["Date"].str.replace("/", "-")
    data["Date"] = pd.to_datetime(data["Date"], format="%d-%m-%Y").dt.date
    return data


def get_en_cours_data() -> pd.DataFrame:
    """
    TODO: Filtrer les données inutiles (on a beaucoup de NaN sur les derniers rows)

    :return: Dataframe "en cours" RTE
    """
    data = pd.read_csv(
        f"{in_absolute_path}/eCO2mix_RTE_En-cours-TR.xls",
        skipfooter=0,
        index_col=False,
        engine="python",
        encoding="latin-1",
        sep="\t",
        usecols=lambda col: col not in empty_column,
    )
    return data


def write_data(data: pd.DataFrame):
    data = data.rename(columns={"Type de jour TEMPO": "type_tempo"})
    data.to_csv(f"{out_absolute_path}/rte_production.csv", index=False)


def __init__():
    """
    1. Getting definitive RTE data "RTE_Annuel-Defintif_YYYY.xls"
    2. Getting consolidated RTE data "RTE_En-cours-Consolide.xls"
    3. Getting definitive RTE data "RTE_En-cours-TR.xls"
    4. Concat all 3
    5. Writes data
    """
    definitive_data = get_definitive_data()
    consolid_data = get_consolid_data()
    en_cours_data = get_en_cours_data()
    data = pd.concat([definitive_data, consolid_data, en_cours_data])
    write_data(data)


__init__()
