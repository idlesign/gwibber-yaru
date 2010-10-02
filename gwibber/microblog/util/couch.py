#!/usr/bin/env python

import gobject, dbus
import desktopcouch, pycurl, oauth, threading, urllib, re, json
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord
from desktopcouch.replication_services import ubuntuone
from couchdb.design import ViewDefinition as CouchView

OAUTH_DATA = desktopcouch.local_files.get_oauth_tokens()
FIND_ID = re.compile('"id":"([^"]+)"')

def request(path, params={}, odata=OAUTH_DATA):
  url = "http://localhost:%s/%s?%s" %  (desktopcouch.find_port(), path, urllib.urlencode(params))
  oconsumer = oauth.oauth.OAuthConsumer(odata["consumer_key"], odata["consumer_secret"])
  otoken = oauth.oauth.OAuthToken(odata["token"], odata["token_secret"])
  oreq = oauth.oauth.OAuthRequest.from_consumer_and_token(oconsumer, otoken, None, None, "GET", url, params)
  oreq.sign_request(oauth.oauth.OAuthSignatureMethod_HMAC_SHA1(), oconsumer, otoken)
  return oreq.to_url()

class Monitor(gobject.GObject, threading.Thread):
  __gsignals__ = {
    "record-updated": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,)),
    "record-deleted": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,))
  }

  def __init__(self, database_name):
    gobject.GObject.__init__(self)
    threading.Thread.__init__(self)
    self.daemon = True
    self.database_name = database_name
    self.database = CouchDatabase(database_name, create=True)
    self.start()

  def on_receive_data(self, data):
    if data.strip():
      match = FIND_ID.search(data)
      if match:
        id = match.group(1)
        if self.database.record_exists(id):
          self.emit("record-updated", id)
        else: self.emit("record-deleted", id)

  def get_last_id(self):
    # Reduce overhead by only parsing what we need
    query = urllib.urlopen(request("%s/_changes" % self.database_name))
    data = json.loads("{" + query.read().strip().rsplit(",",1)[-1])
    return data["last_seq"]

  def run(self):
    # Get latest update ID to avoid notifying of past updates
    seq = self.get_last_id()

    # Build the change notification API call URL
    params = {"feed": "continuous", "heartbeat": "10000", "since": seq}
    url = request("%s/_changes" % self.database_name, params)

    # Invoke callback method when updates are detected
    self.curl = pycurl.Curl()
    self.curl.setopt(pycurl.URL, url)
    self.curl.setopt(pycurl.WRITEFUNCTION, self.on_receive_data)
    self.curl.perform()

class RecordMonitor(dict):
  def __init__(self, dbname, recordid, record_type, defaults = {}):
    self.database = CouchDatabase(dbname, create=True)
    self.dbname = dbname
    self.defaults = defaults
    self.id = recordid

    # Guarantee that the record exists
    if not self.database.record_exists(recordid):
      self.database.put_record(CouchRecord({}, record_type, recordid))

    self.setup_monitor()
    self.refresh()
  
  def setup_monitor(self):
    monitor = Monitor(self.dbname)
    monitor.connect("record-updated", self.on_record_update)

  def refresh(self):
    print "Updating..."
    self.update(self.database.get_record(self.id)._data)

  def save(self):
    data = self.database.get_record(self.id)._data
    for key, value in self.items():
      if key not in data and value == self.defaults[key]:
        if key in self: del self[key]
    self.database.update_fields(self.id, self)

  def on_record_update(self, monitor, id):
    if id == self.id: self.refresh()

  def __getitem__(self, key):
    if key in self: return dict.__getitem__(self, key)
    if key in self.defaults: return self.defaults[key]
    else: raise KeyError(key)

def init_design_doc(database, design, contents):
  views = []

  for name, f in contents.items():
    view = CouchView(design, name, f["map"], f.get("reduce", None))
    views.append(view)

  if isinstance(database, str):
    database = CouchDatabase(database, create=True)
  
  CouchView.sync_many(database.db, views)

def exclude_databases(names):
  try:  
    excl = ubuntuone.ReplicationExclusion()
  except ValueError:
    excl = None   # We are not an Ubuntu One user.

  if excl is not None:
    if "ubuntuone" not in excl.all_exclusions():
      for name in names:
        excl.exclude(name)

