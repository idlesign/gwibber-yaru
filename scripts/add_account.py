#!/usr/bin/env python

from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord

COUCH_DB_ACCOUNTS = "gwibber_accounts"
COUCH_TYPE_ACCOUNT = "http://gwibber.com/couch/account"

data = {
  "authtype": "login",
  "color": "#4E9A06",
  "username": "username",
  "password": "password",
  "protocol": "identica",
  "receive_enabled": True,
  "send_enabled": True,
}

accounts = CouchDatabase("gwibber_accounts", create=True)
print accounts.put_record(CouchRecord(data, COUCH_TYPE_ACCOUNT))

