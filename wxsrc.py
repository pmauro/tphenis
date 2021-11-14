# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------

import logging
import re
import requests

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

from util.enums import *

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


class ParsedForecast:
    def __init__(self):
        self.location = None
        self.source = None

        self.source_text = None
        self.time_issued = None

        self.synopsis = None
        self.period_fcsts_text = None
        self.period_fcsts = dict()
        self.elev_forecasts = dict()

        self.notes = []

    def __str__(self):
        def clean_print(text, def_text=""): return text if text else def_text

        return "{location}\n" \
               "{source_text} ({source})\n" \
               "{time_issued}\n" \
               "{synopsis}\n" \
               "{pf_text}".format(
            location=clean_print(self.location),
            source_text=clean_print(self.source_text),
            source=clean_print(self.source),
            time_issued=clean_print(self.time_issued),
            synopsis=clean_print(self.synopsis),
            pf_text=clean_print(self.period_fcsts_text)
        )


class ForecastParser(ABC):
    @staticmethod
    @abstractmethod
    def get_empty_pf():
        pass

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

    @staticmethod
    def clean_string(raw_string):
        # todo remove any instances of back-to-back spaces, replacing them with a single space
        return raw_string

    def parse_period_forecasts(self, pf_string):
        # 1) Separate date and TOD qualifier from forecast text
        # 2) Convert day of week to date; convert TOD qualifier and near-term/extended to Enums
        # 3) Push parsed forecast onto list?  Or should we keep this structure as a dict?
        pass

    def parse_forecast(self, text):
        pf = MountRainierRecForecast.get_empty_pf()

        bs = BeautifulSoup(text, 'html.parser')

        pf.source_text = bs.b.contents[2].strip()

        # Time Issued
        raw_time = bs.b.contents[4].strip()
        pf.time_issued = raw_time
        # todo parse this into a datetime object
        # pf.time_issued = parsed_time()

        fcst_body = str(bs.pre)
        fcst_body_stripped = fcst_body.replace("\n", " ")

        # Synopsis
        # We're looking for all data between '.SYNOPSIS...' and the first '&amp;&amp;'
        match = re.search("\.SYNOPSIS\.\.\.(.*?)&amp;&amp;", fcst_body_stripped)
        if match and len(match.groups()) == 1:
            raw_syn_string = match.group(1)
            pf.synopsis = MountRainierRecForecast.clean_string(raw_syn_string)
        else:
            logging.warning("Could not parse synopsis from forecast.")

        # Period forecasts
        # These are split between two areas, the near-term forecast (between '&amp;&amp;' and '&amp;&amp;')
        # and between '.Extended Forecast...' and '$$'
        match = re.search("&amp;&amp;(.*?)&amp;&amp;", fcst_body_stripped)
        if match and len(match.groups()) == 1:
            raw_ntef_string = match.group(1)
            print(raw_ntef_string)
            #pf.synopsis = MountRainierRecForecast.clean_string(raw_syn_string)
        else:
            logging.warning("Could not parse near-term daily forecasts.")
        #print(fcst_body)

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
