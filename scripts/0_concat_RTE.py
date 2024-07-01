from pathlib import Path
from energy_forecast.energy import ECO2MixDownloader
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR.parent / "data/bronze/rte"
OUT_FILE = CURRENT_DIR.parent / "data/silver/rte_production.csv"
CURRENT_YEAR = pd.Timestamp("now").year

def get_list_years(start_year=2014, end_year=CURRENT_YEAR) -> list[int]:
    """Return a list of years from start_year to the end_year.

    end_year is included in the list.

    :return: Une liste avec toutes les années (int)
    """
    return list(range(start_year, end_year + 1))

def get_one_year_data(year: int) -> pd.DataFrame:
    """Télécharge et lit les données RTE pour une année donnée.

    :param year: Année pour laquelle on veut les données
    :return: Dataframe avec les données RTE
    """
    downloader = ECO2MixDownloader(year)
    downloader.download()
    data = downloader.read_file()
    return data

def join_yearly_data(years: list) -> pd.DataFrame:
    """Joint les données pour plusieurs années."""
    list_data = []
    for year in years:
        temporary_df = get_one_year_data(year)
        list_data.append(temporary_df)
    return pd.concat(list_data)

def prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données pour l'écriture.

    Ne garde que les heures pleines et enlève les lignes avec uniquement des NaN.

    """
    data = data[data.index.minute == 0]
    data = data.dropna(how="all")
    return data


def write_data(data: pd.DataFrame):
    print(f"Wrtting data to '{OUT_FILE}'...")
    data.to_csv(OUT_FILE, index=True)


def main():
    """
    1. Getting definitive RTE data "RTE_Annuel-Defintif_YYYY.xls"
    2. Getting consolidated RTE data "RTE_En-cours-Consolide.xls"
    3. Getting definitive RTE data "RTE_En-cours-TR.xls"
    4. Join all data
    5. Filter data
    5. Writes data
    """
    data = join_yearly_data(get_list_years())
    data = prepare_data(data)
    write_data(data)

if __name__ == "__main__":
    main()
