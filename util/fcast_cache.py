# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime
import os.path
import logging

import glob
import hashlib
from pytz import timezone

from enums import *
import fcast_ingest

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------

CACHE_DIR_NAME = "fcache"
STANDARD_TIMEZONE = "US/Pacific"

# ---------------------------------------------------------------------------------------------------------------------
# METHODS
# ---------------------------------------------------------------------------------------------------------------------


def get_cache_base_dir():
    # todo Allow shell variable to take precedence if set
    bdir = os.path.abspath(os.path.join(__file__, "../../{}".format(CACHE_DIR_NAME)))
    return bdir


def get_YYYYMMDD(tgt_time=datetime.now()):
    pacific_tz = timezone(STANDARD_TIMEZONE)
    tgt_date = datetime.date(pacific_tz.localize(tgt_time))
    return tgt_date.strftime("%Y%m%d")


# source, location, YYYYMM, date.[index].txt
def get_cache_path(source, location, date=get_YYYYMMDD()):
    cpath = os.path.join(get_cache_base_dir(),
                         str(source.name).lower(),
                         str(location.name).lower(),
                         date[:-2])
    return cpath


def hash_forecast(fcast_str):
    return hashlib.md5(fcast_str.encode()).hexdigest()


def get_cache_paths(base_cache_dir, yyyymmdd):
    if not os.path.exists(base_cache_dir):
        return []

    glob_str = "{}.*.txt".format(yyyymmdd)
    return glob.glob(os.path.join(base_cache_dir, glob_str))


def get_raw_forecast(source, location, use_cache=True, cache_timeout=300, save_forecast=True):
    yyyymmdd = get_YYYYMMDD()
    cache_dir = get_cache_path(source, location, yyyymmdd)

    if use_cache:
        logging.debug("Searching through forecast cache.")
        smallest_delta = None
        most_recent_file = None
        for cur_file_path in get_cache_paths(cache_dir, yyyymmdd):
            # This is the time delta (in seconds) since this file was cached
            time_delta = datetime.now().timestamp() - os.path.getctime(cur_file_path)

            # This shouldn't happen!
            if time_delta < 0:
                logging.warning("Cached file has a creation timestamp in the future: {}".format(cur_file_path))
                continue
            elif cache_timeout == -1 or time_delta < cache_timeout:
                if smallest_delta is None or time_delta < smallest_delta:
                    smallest_delta = time_delta
                    most_recent_file = cur_file_path

        if most_recent_file is not None:
            logging.info("Loading forecast from cache: {:.0f}\t{}".format(smallest_delta, most_recent_file))
            with open(most_recent_file, 'r') as f:
                return f.read()

    logging.info("Getting new forecast.")
    new_fcast_str = fcast_ingest.get_raw_forecast(source, location)

    if not save_forecast:
        return new_fcast_str

    new_fcst_hash = hash_forecast(new_fcast_str)
    cache_paths = get_cache_paths(cache_dir, yyyymmdd)
    for cur_file_path in cache_paths:
        with open(cur_file_path, 'r') as f:
            cached_fcast_str = f.read()
        if hash_forecast(cached_fcast_str) == new_fcst_hash:
            logging.debug("New forecast matches cached forecast: {}".format(cur_file_path))
            return new_fcast_str

    # If we got here, we didn't match a previous forecast
    c_fpath = os.path.join(cache_dir, "{}.{}.txt".format(yyyymmdd, len(cache_paths) + 1))
    logging.info("Writing forecast to cache: {}".format(c_fpath))
    os.makedirs(os.path.dirname(c_fpath), exist_ok=True)
    with open(c_fpath, 'w') as f:
        f.write(new_fcast_str)

    return new_fcast_str


forecast_str = get_raw_forecast(ForecastSource.MORA_REC_FCST, Location.MORA)
