from energy_forecast.energy import TempoCalendarDownloader
import pandas as pd
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR.parent / "data/bronze/tempo"
OUT_FILE = CURRENT_DIR.parent / "data/silver/tempo_2014_2024.csv"

def download_tempo_data():
    """Download the Tempo data from RTE."""
    downloader = TempoCalendarDownloader()
    downloader.download()
    return downloader.read_file()

def write_data(data: pd.DataFrame):
    """Save the data to a CSV file."""
    print(f"Wrtting data to '{OUT_FILE}'...")
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT_FILE, index=False)

def main():
    data = download_tempo_data()
    write_data(data)


if __name__ == "__main__":
    main()