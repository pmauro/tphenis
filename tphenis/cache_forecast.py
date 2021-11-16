# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------

import argparse
import logging

import util.wxenums as wxenums
import util.fcast_cache as fcast_cache

LOGGER = logging.getLogger('tphenis')
logging.basicConfig(format='%(asctime)s %(levelname)s - %(module)s.%(funcName)s() - %(message)s ',
                    datefmt= '%Y%m%d %H:%M:%S')

# ---------------------------------------------------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------------------------------------------------

source = wxenums.ForecastSource.MORA_REC_FCST
location = wxenums.Location.MORA
log_level = logging.INFO
# todo Get source and location from command line, log level too

LOGGER.setLevel(log_level)

# todo Create an option to force an overwrite?
fcast_cache.get_raw_forecast(source, location, use_cache=False, save_forecast=True)

