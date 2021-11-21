# Copyright 2021 Patrick Mauro and Harrison Hamlin
# Contents are proprietary and confidential.

# ---------------------------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------
from datetime import datetime
import email
import hashlib
import logging
import os
import smtplib
import ssl

from imapclient import IMAPClient

from . import email_creds

LOGGER = logging.getLogger('tphenis')

# ---------------------------------------------------------------------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------------------------------------------------------------------

SMTP_PORT = 465

# ---------------------------------------------------------------------------------------------------------------------
# CLASSES
# ---------------------------------------------------------------------------------------------------------------------


class ForecastRequest:
    def __init__(self, request_time, body_raw):
        self.request_time = request_time
        self.body_raw = body_raw


class ForecastRequestEmail(ForecastRequest):
    def __init__(self, uid, email_address, request_time, body_raw):
        super().__init__(request_time, body_raw)

        self.uid = uid
        self.email_address = email_address

    def get_hash(self):
        hash_input = str(self.uid) + str(self.request_time) + self.body_raw + self.email_address
        return hashlib.sha1(hash_input.encode(), usedforsecurity=False).hexdigest()

    def get_registry_str(self):
        return "{hash}\t{uid}\t{email}\t{timestamp}".format(
            hash=str(self.get_hash()),
            uid=str(self.uid),
            email=self.email_address,
            timestamp=self.request_time.strftime("%Y%m%d %H:%M:%S")
        )


class EmailRegistry:
    def __init__(self, registry_file="email_registry.txt"):
        self._hashes = set()
        self.registry_file = registry_file

    def load(self):
        if not os.path.exists(self.registry_file):
            return

        with open(self.registry_file, "r") as f:
            for line in f.readlines():
                cols = line.split()
                cur_hash = cols[0]
                LOGGER.debug("Reading hash from registry: {}".format(cur_hash))
                self._hashes.add(cur_hash)

    def check(self, fre):
        return fre.get_hash() in self._hashes

    def add_entry(self, fre):
        if self.check(fre):
            return

        with open(self.registry_file, "a") as f:
            f.write(fre.get_registry_str() + "\n")

        self._hashes.add(hash(fre))

# ---------------------------------------------------------------------------------------------------------------------
# METHODS
# ---------------------------------------------------------------------------------------------------------------------


def get_email_text_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type != "text/plain":
                continue
            body = part.get_payload(decode=True).decode()
            return body
    else:
        content_type = msg.get_content_type()
        body = msg.get_payload(decode=True).decode()
        if content_type == "text/plain":
            return body

    return None


def archive_email(client, msg_uid):
    client.move([msg_uid], 'Processed')


def get_imap_client(host=email_creds.IMAP_HOST, username=email_creds.USERNAME, password=email_creds.PASSWORD):
    imap_client = IMAPClient(host)
    imap_client.login(username, password)
    imap_client.select_folder('INBOX')
    return imap_client


def get_smtp_client(host=email_creds.SMTP_HOST, username=email_creds.USERNAME, password=email_creds.PASSWORD):
    context = ssl.create_default_context()
    smtp_client = smtplib.SMTP_SSL(host, SMTP_PORT, context=context)
    smtp_client.login(username, password)
    return smtp_client

def send_response(client, dest_email, message, from_email=email_creds.USERNAME):
    client.sendmail(from_email, dest_email, message)


def get_inbox_messages(imap_client):
    imap_client.noop()
    return imap_client.search('ALL')


def process_inbox_messages(messages, imap_client, fr_registry):
    fre_list = []
    for uid, message_data in imap_client.fetch(messages, "RFC822").items():
        msg = email.message_from_bytes(message_data[b"RFC822"])

        if "Date" not in msg or "From" not in msg:
            LOGGER.warning("Could not parse date or time from email: {}".format(uid))
            continue

        try:
            send_timestamp = datetime.strptime(msg["Date"], "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            LOGGER.warning("Could not parse time: {}".format(msg["Date"]))
            send_timestamp = datetime.now()

        fre = ForecastRequestEmail(uid, msg["From"], send_timestamp, get_email_text_body(msg))

        if fr_registry.check(fre):
            archive_email(imap_client, uid)
            continue

        fre_list.append(fre)

    return fre_list


def process_forecast_requests(fre_list, smtp_client, imap_client, fr_registry):
    for fre in fre_list:
        send_response(smtp_client, fre.email_address, "Bunk is cool.")
        fr_registry.add_entry(fre)
        archive_email(imap_client, fre.uid)