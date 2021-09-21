# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------

import requests

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from enum import Enum, auto

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------

MORA_REC_FCST_URL = "https://a.atmos.washington.edu/data/rainier_report.html"

# ---------------------------------------------------------------------------------------------------------------------
# METHODS
# ---------------------------------------------------------------------------------------------------------------------


def scrape_url(url):
    page = requests.get(url)
    return page.text


# ---------------------------------------------------------------------------------------------------------------------
# CLASSES
# ---------------------------------------------------------------------------------------------------------------------

class Location(Enum):
    MORA = auto()


class ForecastSource(Enum):
    MORA_REC_FCST = auto()


class ParsedForecast:
    def __init__(self):
        self.location = None
        self.source = None

        self.source_text = None
        self.time_issued = None

        self.synopsis = None
        self.period_fcsts = dict()
        self.elev_forecasts = dict()

        self.notes = []

    def __str__(self):
        return "{location}\n" \
               "{source_text} ({source})".format(
            location=self.location,
            source_text=self.source_text,
            source=self.source
        )


class ForecastParser(ABC):
    @abstractmethod
    def parse_forecast(self, text):
        pass


class MountRainierRecForecast(ForecastParser):
    def __init__(self):
        pass

    @staticmethod
    def get_empty_pf():
        pf = ParsedForecast()
        pf.location = Location.MORA
        pf.source = ForecastSource.MORA_REC_FCST
        return pf

    def parse_forecast(self, text):
        pf = MountRainierRecForecast.get_empty_pf()

        bs = BeautifulSoup(text, 'html.parser')

        pf.source_text = bs.b.contents[2].strip()

        raw_time = bs.b.contents[4].strip()
        # todo parse this into a datetime object
        # pf.time_issued = parsed_time()

        return pf

# ---------------------------------------------------------------------------------------------------------------------
# TEST CODE
# ---------------------------------------------------------------------------------------------------------------------


def main():
    raw_text = scrape_url(MORA_REC_FCST_URL)
    fcst_parser = MountRainierRecForecast()

    pf = fcst_parser.parse_forecast(raw_text)

    print(pf)

if __name__ == "__main__":
    main()
