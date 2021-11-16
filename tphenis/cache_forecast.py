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
logging.basicConfig(format='%(asctime)s %(levelname)-8s - %(module)s.%(funcName)s() - %(message)s ',
                    datefmt= '%Y%m%d %H:%M:%S')

# ---------------------------------------------------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------------------------------------------------


def main():
    arg_parser = argparse.ArgumentParser(description="Request a raw forecast and cache it if it's new.")

    arg_parser.add_argument('--src', action='store', required=True, help='forecast source')
    arg_parser.add_argument('--loc', action='store', required=True, help='forecast location')
    arg_parser.add_argument('--log-level', action='store', required=False, default='INFO',
                            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            help="Set the logging level",
                            dest='loglevel')

    args = arg_parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper())
    if numeric_level is None:
        LOGGER.critical("Invalid log level specified: {}".format(args.loglevel))
        exit(1)
    LOGGER.setLevel(numeric_level)

    # Validate user input for the ForecastSource and Location
    try:
        source = wxenums.ForecastSource[args.src]
    except KeyError:
        LOGGER.critical("Invalid forecast source specified: {}".format(args.src))
        exit(1)

    try:
        location = wxenums.Location[args.loc]
    except KeyError:
        LOGGER.critical("Invalid forecast location specified: {}".format(args.loc))
        exit(1)

    # todo Create an option to force an overwrite?
    fcast_cache.get_raw_forecast(source, location, use_cache=False, save_forecast=True)


main()
