from desktopcouch.records.server import CouchDatabase
from const import *

import atexit
import ctypes
import gnomekeyring

passwords = {}

def get_account_passwords():
    global passwords

    accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)

    ids = [a['id'] for a in accounts.get_records(COUCH_TYPE_ACCOUNT, True).rows]

    for id in ids:
        account = dict(accounts.get_record(id).items())
        for key, val in account.items():
            if isinstance(val, str) and val.startswith(":KEYRING:"):
                try:
                    value = gnomekeyring.find_items_sync(
                        gnomekeyring.ITEM_GENERIC_SECRET,
                        {"id": str("%s/%s" % (account["_id"], key))})[0].secret
                    mlock(value)
                except gnomekeyring.NoMatchError:
                    value = None

                passwords[id] = value

def get_account_password(accountid):
    global passwords

    return passwords.get(accountid, None)

libc = ctypes.CDLL("libc.so.6")

def mlock(var):
    libc.mlock(var, len(var))

def munlock(var):
    libc.munlock(var, len(var))

def munlock_passwords():
    global passwords

    for acctid in passwords.keys():
        munlock(passwords[acctid])

atexit.register(munlock_passwords)
