# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------
import logging
import requests

from .enums import *

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------

SOURCE_PATHS = {
    ForecastSource.MORA_REC_FCST: {
        Location.MORA: "https://a.atmos.washington.edu/data/rainier_report.html"
    }
}

# ---------------------------------------------------------------------------------------------------------------------
# METHODS
# ---------------------------------------------------------------------------------------------------------------------


def get_source_path(source, location):
    if source not in SOURCE_PATHS or location not in SOURCE_PATHS[source]:
        return None

    return SOURCE_PATHS[source][location]


def scrape_url(url):
    page = requests.get(url)
    return page.text


def get_raw_forecast(source, location):
    fcast_path = get_source_path(source, location)

    if fcast_path is None:
        # todo print a warning
        pass

    return scrape_url(fcast_path)