import os

import pandas as pd

in_relative_path = "../energetic-stress-production/raw_datasets/tempo/"
in_absolute_path = os.path.abspath(os.path.join(os.getcwd(), in_relative_path))
out_relative_path = "../energetic-stress-production/clean_datasets/"
out_absolute_path = os.path.abspath(os.path.join(os.getcwd(), out_relative_path))


def get_all_paths(in_absolute_path: str) -> list:
    all_tempo_path = []
    for y in range(2014, 2024):
        all_tempo_path.append(in_absolute_path + f"/eCO2mix_RTE_tempo_{y}-{y+1}.xlsx")
    return all_tempo_path


def join_data(paths: list) -> pd.DataFrame:
    data = pd.DataFrame()
    for path in paths:
        temporary_df = pd.read_excel(path)
        temporary_df = temporary_df.drop(temporary_df.tail(1).index)
        data = pd.concat([data, temporary_df])
    return data


def write_data(data: pd.DataFrame):
    data = data.rename(columns={"Type de jour TEMPO": "type_tempo"})
    data.to_csv(f"{out_absolute_path}/tempo_2014_2024.csv", index=False)


def __init__():
    paths = get_all_paths(in_absolute_path)
    data = join_data(paths)
    write_data(data)


__init__()
