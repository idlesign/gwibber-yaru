import gconf
import gwibber.lib, gwibber.util
from gwibber.microblog.util.const import *
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord

class GwibberAccountMigrate():
  def __init__(self):
    pass
    
  def run(self):
    GCONF_DIR = "/apps/gwibber"
    gc = gconf.client_get_default()
    account_ids = self.get_value(gc.get(GCONF_DIR + "/accounts/index"))
    self.protocols = eval(gwibber.lib.GwibberPublic().GetServices())
    migrated = False

    for id in account_ids:
      entries = gc.all_entries("/".join((GCONF_DIR, "accounts", id)))
      account = {}
      for entry in entries:
        #print entry.key.split("/")[-1], "-", self.get_value(entry.value)
        if entry.key.split("/")[-1] == "message_color":
          account["color"] = gwibber.util.Color.from_gtk_color(self.get_value(entry.value)).hex
        else:
          account[entry.key.split("/")[-1]] = self.get_value(entry.value)
      if self.account_save(account):
        print "Migrated ", account['protocol'], " - ", account['username']
        migrated = True
    return migrated
  
  def get_value(self, value):
    if not hasattr(value, "type"):
      return ""
    if value.type.value_nick == "list":
      return [self.get_value(item) for item in value.get_list()]
    else:
      return {
        "string": value.get_string,
        "int": value.get_int,
        "float": value.get_float,
        "bool": value.get_bool,
        "list": value.get_list
      }[value.type.value_nick]()

  def account_verify(self, account):
    if self.protocols.has_key(account['protocol']):
      for required in self.protocols[account['protocol']]['config']:
        try:
          required = required.split(":")[1]
        except:
          pass
        if not account.has_key(required):
          return False
      return True
    return False

  def account_save(self, account):
    accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
    if not self.account_verify(account):
      return False
    records = accounts.get_records().rows
    for record in records:
      if account['protocol'] == record['value']['protocol'] and account['username'] == record['value']['username']:
        return False
    accounts.put_record(CouchRecord(account, record_type=COUCH_TYPE_ACCOUNT))
    return True



