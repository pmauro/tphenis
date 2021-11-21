# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime
import logging
import time

import util.email_io as email_io

LOGGER = logging.getLogger('tphenis')
logging.basicConfig(format='%(asctime)s %(levelname)-8s - %(module)s.%(funcName)s() - %(message)s ',
                    datefmt= '%Y%m%d %H:%M:%S')
LOGGER.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------


MAX_IMAP_SESSION = 1200  # in seconds, must be < 1800 to avoid server timeouts
POLL_INTERVAL = 10


# ---------------------------------------------------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------------------------------------------------

# todo Make this take command line arguments, which will set the max session length, poll interval, log level

registry = email_io.EmailRegistry()
registry.load()

smtp_client, imap_client = None, None

# Get the client for outgoing mail
try:
    smtp_client = email_io.get_smtp_client()

    # Get the client for incoming mail
    imap_client = email_io.get_imap_client()
    imap_client_start_t = datetime.now()

    # On startup, process whatever messages we found in the mailbox
    msgs = email_io.get_inbox_messages(imap_client)
    LOGGER.info("Found {} unprocessed messages on startup.".format(len(msgs)))
    forecast_requests = email_io.process_inbox_messages(msgs, imap_client, registry)
    email_io.process_forecast_requests(forecast_requests, smtp_client, imap_client, registry)

    LOGGER.info("Polling for new messages every {} seconds.".format(POLL_INTERVAL))
    # This was implemented to avoid putting the server into IDLE mode, but that decision was arbitrary.  Consider
    # reimplementing this using IDLE.
    while True:
        # Every so often, we need to reet the imap_client login so that we avoid leaking memory and file
        # descriptors and avoid socket closure.
        time_delta = datetime.now() - imap_client_start_t
        if time_delta.seconds >= MAX_IMAP_SESSION:
            LOGGER.debug("Resetting imap connection.")
            imap_client.logout()

            imap_client = email_io.get_imap_client()
            imap_client_start_t = datetime.now()

        time.sleep(POLL_INTERVAL)
        try:
            msgs = email_io.get_inbox_messages(imap_client)
            LOGGER.debug("Found {:2d} inbox messages on poll.".format(len(msgs)))
            if len(msgs) > 0:
                forecast_requests = email_io.process_inbox_messages(msgs, imap_client, registry)
                LOGGER.info("Processing {} new messages.".format(len(forecast_requests)))
                email_io.process_forecast_requests(forecast_requests, smtp_client, imap_client, registry)
        except KeyboardInterrupt:
            break

finally:
    if smtp_client is not None:
        smtp_client.close()

    if imap_client is not None:
        imap_client.logout()
