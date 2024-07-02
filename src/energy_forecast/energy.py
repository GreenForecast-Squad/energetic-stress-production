"""Download and read data from RTE Eco2Mix."""
import requests
import pandas as pd
from pathlib import Path
import os

class RTEZipFileDownloader:
    """Provide the functionality to download and unzip a zip file from RTE.

    If the file is already downloaded, a cache mechanism is used to avoid downloading it again.
    """

    cache_validation_time = "1h"  # used to invalidate the cache after 1 hour

    def __init__(self, url, filename_zip, filename_xls, prefix="/tmp/rte", cache_validation_time = "1h"):
        self.url = url
        self.prefix = Path(prefix)
        self.filename_zip = self.prefix / filename_zip
        self.filename_xls = self.prefix / filename_xls
        self.cache_validation_time = cache_validation_time

    def download(self):
        """Download the zip file if not already downloaded."""

        if self.filename_xls.exists():
            time = self.filename_xls.stat().st_mtime
            time = pd.Timestamp(time, unit="s")
            now = pd.Timestamp("now")
            if time + pd.Timedelta(self.cache_validation_time) > now:
                return
        self.filename_zip.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(self.url)
        response.raise_for_status()
        with open(self.filename_zip, "wb") as f:
            f.write(response.content)
        self.unzip()
        return

    def unzip(self):
        """unzip the downloaded zip file."""
        import zipfile
        with zipfile.ZipFile(self.filename_zip, 'r') as zip_ref:
            zip_ref.extractall(self.prefix)
        os.remove(self.filename_zip)
        return

class TempoCalendarDownloader(RTEZipFileDownloader):
    """Download the Tempo Calendar from RTE."""

    def __init__(self, start_year=2014, end_year=2024, prefix="/tmp/rte/tempo"):
        start_year_last_digit = str(start_year)[2:]
        end_year_last_digit = str(end_year)[2:]
        url = f"https://eco2mix.rte-france.com/curves/downloadCalendrierTempo?season={start_year_last_digit}-{end_year_last_digit}"
        filename_zip = f"eCO2mix_RTE_tempo_{start_year}-{end_year}.zip"
        filename_xls = f"eCO2mix_RTE_tempo_{start_year}-{end_year}.xls"
        super().__init__(url, filename_zip=filename_zip,
                         filename_xls=filename_xls,
                         prefix=prefix,
                         cache_validation_time="1D",
                         )

    def read_file(self):
        df = pd.read_csv(
            self.filename_xls,
            sep="\t",
            skipfooter=1,
            engine="python",
            parse_dates=["Date"],
            index_col="Date",
            dtype="category",
        )
        df.rename(columns={"Type de jour TEMPO": "tempo_type"}, inplace=True)
        return df

class ECO2MixDownloader(RTEZipFileDownloader):

    empty_column = [" Stockage batterie", "Déstockage batterie", "Eolien terrestre", "Eolien offshore"]

    def __init__(self, year, prefix="/tmp/rte/eco2mix"):

        current_year = pd.Timestamp("now").year
        last_year = current_year - 1
        if year < last_year:
            filename_zip = f"eCO2mix_RTE_Annuel-Definitif_{year}.zip"
            filename_xls = f"eCO2mix_RTE_Annuel-Definitif_{year}.xls"
            cache_validation_time = "356d"
        elif year == last_year:
            filename_zip = "eCO2mix_RTE_En-cours-Consolide.zip"
            filename_xls = "eCO2mix_RTE_En-cours-Consolide.xls"
            cache_validation_time = "30d"
        elif year == current_year:
            filename_zip = "eCO2mix_RTE_En-cours-TR.zip"
            filename_xls = "eCO2mix_RTE_En-cours-TR.xls"
            cache_validation_time = "1h"
        else:
            raise ValueError("Year must be in the past or current year")

        url = f"http://eco2mix.rte-france.com/download/eco2mix/{filename_zip}"

        super().__init__(url,
                         filename_zip=filename_zip,
                         filename_xls=filename_xls,
                         prefix=prefix,
                         cache_validation_time=cache_validation_time,)

    def read_file(self):
        skipfooter = 1
        if self.filename_xls.name == "eCO2mix_RTE_En-cours-TR.xls":
            skipfooter = 2
        data =  pd.read_csv(self.filename_xls,
                            index_col=False,
                            skipfooter=skipfooter,
                            engine="python",
                            sep="\t",
                            encoding="latin1",
                            usecols=lambda x: x not in self.empty_column,
                            )

        data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
        data["Heures"] = pd.to_timedelta(data["Heures"] + ":00")
        data["time"] = data["Date"] + data["Heures"]
        return data.set_index("time")

if __name__ == "__main__":
    r = ECO2MixDownloader(year=2024)
    r.download()
    data = r.read_file()
    print(data.head())