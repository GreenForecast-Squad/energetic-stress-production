"""Download and read data from RTE Eco2Mix."""
import requests
import pandas as pd
from pathlib import Path

class RTESimpleAPI:

    url = "http://eco2mix.rte-france.com/download/eco2mix/eCO2mix_RTE_En-cours-TR.zip"
    cache_validation_time = "1h"  # used to invalidate the cache after 1 hour
    empty_column = [" Stockage batterie", "Déstockage batterie", "Eolien terrestre", "Eolien offshore"]

    def __init__(self, prefix="/tmp/rte"):
        self.prefix = Path(prefix)
        filename = f"{self.prefix}/eCO2mix_RTE_En-cours-TR.zip"
        filename_xls = f"{self.prefix}/eCO2mix_RTE_En-cours-TR.xls"
        self.filename = Path(filename)
        self.filename_xls = Path(filename_xls)

    def download(self):
        """Download the zip file if not already downloaded."""

        if self.filename.exists():
            time = self.filename.stat().st_mtime
            time = pd.Timestamp(time, unit="s")
            now = pd.Timestamp("now")
            if time + pd.Timedelta(self.cache_validation_time) > now:
                print("Using cache")
                return
        print("Downloading")
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(self.url)
        response.raise_for_status()
        with open(self.filename, "wb") as f:
            f.write(response.content)
        self.unzip
        return

    def unzip(self):
        """unzip the downloaded zip file."""

        import zipfile
        with zipfile.ZipFile(self.filename, 'r') as zip_ref:
            zip_ref.extractall(self.prefix)
        return

    def read_file(self):
        data =  pd.read_csv(self.filename_xls,
                            index_col=False,
                            sep="\t",
                            encoding="latin1",
                            usecols=lambda x: x not in self.empty_column,
                            )
        data.drop(data.tail(1).index, inplace=True)
        data = data[data["Heures"].str.contains(":30|:00")]
        data = data[data["Heures"].str.contains(":00")]  # On ne garde que les heures pleines
        # data["Date"] = data["Date"].str.replace("/", "-")
        data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
        data["Heures"] = pd.to_timedelta(data["Heures"] + ":00")
        data["time"] = data["Date"] + data["Heures"]
        return data.set_index("time")

if __name__ == "__main__":
    r = RTESimpleAPI()
    r.download()
    data = r.read_file()
    print(data.head())