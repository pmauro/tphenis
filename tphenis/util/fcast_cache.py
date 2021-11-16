# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime, timedelta
import os.path
import logging

import glob
import hashlib
from pytz import timezone

from . import fcast_ingest

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------

CACHE_DIR_NAME = "data"
STANDARD_TIMEZONE = "US/Pacific"
LOGGER = logging.getLogger('tphenis')

# ---------------------------------------------------------------------------------------------------------------------
# METHODS
# ---------------------------------------------------------------------------------------------------------------------


def get_cache_base_dir():
    # todo Allow shell variable to take precedence if set
    bdir = os.path.abspath(os.path.join(__file__, "../../../{}".format(CACHE_DIR_NAME)))
    return bdir


def get_YYYYMMDD(tgt_time=datetime.now(), delta=0):
    pacific_tz = timezone(STANDARD_TIMEZONE)
    tgt_date = datetime.date(pacific_tz.localize(tgt_time)) + timedelta(days=delta)
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


def look_for_hash(cache_paths, tgt_hash):
    for cur_file_path in cache_paths:
        with open(cur_file_path, 'r') as f:
            cached_fcast_str = f.read()
        if hash_forecast(cached_fcast_str) == tgt_hash:
            return cur_file_path
    return None


def look_for_symlinks(cache_paths):
    count = 0
    for path in cache_paths:
        if os.path.islink(path):
            count += 1

    return count


def get_raw_forecast(source, location, use_cache=True, cache_timeout=300, save_forecast=True):
    time_now = datetime.now()
    yyyymmdd_today = get_YYYYMMDD(tgt_time=time_now)
    yyyymmdd_yesterday = get_YYYYMMDD(tgt_time=time_now, delta=-1)

    cache_dir = get_cache_path(source, location, yyyymmdd_today)

    if use_cache:
        LOGGER.debug("Searching through forecast cache")
        smallest_delta = None
        most_recent_file = None
        for cur_file_path in get_cache_paths(cache_dir, yyyymmdd_today):
            # This is the time delta (in seconds) since this file was cached
            time_delta = datetime.now().timestamp() - os.path.getctime(cur_file_path)

            # This shouldn't happen!
            if time_delta < 0:
                LOGGER.warning("Cached file has a creation timestamp in the future: {}".format(cur_file_path))
                continue
            elif cache_timeout == -1 or time_delta < cache_timeout:
                if smallest_delta is None or time_delta < smallest_delta:
                    smallest_delta = time_delta
                    most_recent_file = cur_file_path

        if most_recent_file is not None:
            LOGGER.info("Loading forecast from cache: {:.0f}\t{}".format(smallest_delta, most_recent_file))
            with open(most_recent_file, 'r') as f:
                return f.read()

    LOGGER.debug("Getting new forecast")
    new_fcast_str = fcast_ingest.get_raw_forecast(source, location)

    if not save_forecast:
        return new_fcast_str

    LOGGER.debug("Attempting to save forecast")
    new_fcst_hash = hash_forecast(new_fcast_str)
    cache_paths_today = get_cache_paths(cache_dir, yyyymmdd_today)

    # If we don't have a forecast saved for today, see if there's one from yesterday that is identical, and create
    # a symlink.  This happens because forecast are issued in the mid-afternoon and mid-morning, so the mid-afternoon
    # forecast will carry over after midnight.
    if len(cache_paths_today) == 0:
        # If the forecast is the same as a forecast from yesterday, make a symlink with the '0' index
        cache_paths_yesterday = get_cache_paths(cache_dir, yyyymmdd_yesterday)
        cache_match = look_for_hash(cache_paths_yesterday, new_fcst_hash)
        if cache_match is not None:
            LOGGER.info("Current forecast matches cached forecast: {}".format(cache_match))

            c_fpath = os.path.join(cache_dir, "{}.0.txt".format(yyyymmdd_today))
            if os.path.exists(c_fpath):
                LOGGER.error("Symlink path already exists: {}".format(c_fpath))
            else:
                LOGGER.info("Making symlink: {}".format(c_fpath))
                os.makedirs(os.path.dirname(c_fpath), exist_ok=True)
                os.symlink(os.path.relpath(cache_match, start=cache_dir), c_fpath)

            return new_fcast_str

    # If we have a match from today, do nothing
    cache_match = look_for_hash(cache_paths_today, new_fcst_hash)
    num_symlinks = look_for_symlinks(cache_paths_today)
    if cache_match is not None:
        LOGGER.info("Current forecast matches cached forecast: {}".format(cache_match))
        return new_fcast_str

    index_offset = 1
    if num_symlinks > 1:
        LOGGER.error("More than 1 symlink for date: {}".format(yyyymmdd_today))
    elif num_symlinks == 1:
        index_offset = 0

    # If we got here, we didn't match a previous forecast
    c_fpath = os.path.join(cache_dir, "{}.{}.txt".format(yyyymmdd_today, len(cache_paths_today) + index_offset))
    if os.path.exists(c_fpath):
        LOGGER.error("Cached file already exists:  {}".format(c_fpath))
    else:
        LOGGER.info("Writing forecast to cache: {}".format(c_fpath))
        os.makedirs(os.path.dirname(c_fpath), exist_ok=True)
        with open(c_fpath, 'w') as f:
            f.write(new_fcast_str)
        os.chmod(c_fpath, 0o400)

    return new_fcast_str
