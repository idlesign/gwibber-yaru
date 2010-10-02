#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing, threading, traceback, json, time
import gobject, dbus, dbus.service, mx.DateTime
import twitter, identica, statusnet, flickr, facebook
import qaiku, friendfeed, digg

import urlshorter
import util, util.couch
import util.keyring
from util import log
from util import resources
from util.couch import Monitor as CouchMonitor
from util.couch import RecordMonitor
from util import exceptions
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord
import re
from util.const import *

try:
  import indicate
except:
  indicate = None

gobject.threads_init()

log.logger.name = "Gwibber Dispatcher"

PROTOCOLS = {
  "twitter": twitter,
  "identica": identica,
  "flickr": flickr,
  "facebook": facebook,
  "friendfeed": friendfeed,
  "statusnet": statusnet,
  "digg": digg,
  "qaiku": qaiku,
}

FEATURES = json.loads(GWIBBER_OPERATIONS)
SERVICES = dict([(k, v.PROTOCOL_INFO) for k, v in PROTOCOLS.items()])
SETTINGS = RecordMonitor(COUCH_DB_SETTINGS, COUCH_RECORD_SETTINGS, COUCH_TYPE_CONFIG, DEFAULT_SETTINGS)

def perform_operation((acctid, opname, args, transient)):
  try:
    stream = FEATURES[opname]["stream"] or opname
    accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
    messages = CouchDatabase(COUCH_DB_MESSAGES, create=True)
    account = dict(accounts.get_record(acctid).items())

    if not 'failed_id' in globals():
      global failed_id
      failed_id = []

    for key, val in account.items():
      if isinstance(val, str) and val.startswith(":KEYRING:"):
        value = util.keyring.get_account_password(account["_id"])

        if value is None:
          if account["_id"] not in failed_id:
            log.logger.debug("Adding %s to failed_id global", account["_id"])
            failed_id.append(account["_id"])
            log.logger.debug("Raising error to resolve failure for %s", account["_id"])
            raise exceptions.GwibberProtocolError("keyring")
          return ("Failure", 0)

        account[key] = value

    logtext = "<%s:%s>" % (account["protocol"], opname)
    log.logger.debug("%s Performing operation", logtext)

    args = dict((str(k), v) for k, v in args.items())
    message_data = PROTOCOLS[account["protocol"]].Client(account)(opname, **args)
    new_messages = []
    text_cleaner = re.compile(u"[: \n\t\r♻♺]+|@[^ ]+|![^ ]+|#[^ ]+") # signs, @nickname, !group, #tag

    if message_data is not None:
      for m in message_data:
        if m.has_key("id"):
          key = (m["id"], m["account"], opname, transient)
          key = "-".join(x for x in key if x)
          if not messages.record_exists(key):
            m["operation"] = opname
            m["stream"] = stream
            m["transient"] = transient
            m["rtl"] = util.isRTL(re.sub(text_cleaner, "", m["text"].decode('utf-8')))
        
            log.logger.debug("%s Adding record", logtext)
            new_messages.append(m)
            messages.put_record(CouchRecord(m, COUCH_TYPE_MESSAGE, key))

    log.logger.debug("%s Finished operation", logtext)
    return ("Success", new_messages)
  except Exception as e:
    if not "logtext" in locals(): logtext = "<UNKNOWN>"
    log.logger.error("%s Operation failed", logtext)
    log.logger.debug("Traceback:\n%s", traceback.format_exc())
    return ("Failure", traceback.format_exc())

class OperationCollector:
  def __init__(self):
    self.accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
    self.settings = CouchDatabase(COUCH_DB_SETTINGS, create=True)
    self.messages = CouchDatabase(COUCH_DB_MESSAGES, create=True)

  def handle_max_id(self, acct, opname, id=None):
    if not id: id = acct["_id"]
    if "sinceid" in SERVICES[acct["protocol"]]["features"]:
      view = self.messages.execute_view("maxid", "messages")
      result = view[[id, opname]][[id, opname]].rows
      if len(result) > 0: return {"since": result[0].value}
    return {}

  def validate_operation(self, acct, opname, enabled="receive_enabled"):
    protocol = SERVICES[acct["protocol"]]
    return acct["protocol"] in PROTOCOLS and \
           opname in protocol["features"] and \
           opname in FEATURES and acct[enabled]

  def stream_to_operation(self, stream):
    account = self.accounts.get_record(stream["account"])
    args = stream["parameters"]
    opname = stream["operation"]
    if self.validate_operation(account, opname):
      args.update(self.handle_max_id(account, opname, stream["_id"]))
      return (stream["account"], stream["operation"], args, stream["_id"])

  def search_to_operations(self, search):
    for account in self.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      account = account.value
      args = {"query": search["query"]}
      if self.validate_operation(account, "search"):
        args.update(self.handle_max_id(account, "search", search["_id"]))
        yield (account["_id"], "search", args, search["_id"])

  def account_to_operations(self, acct):
    if isinstance(acct, basestring):
      acct = dict(self.accounts.get_record(acct).items())
    for opname in SERVICES[acct["protocol"]]["default_streams"]:
      if self.validate_operation(acct, opname):
        args = self.handle_max_id(acct, opname)
        yield (acct["_id"], opname, args, False)

  def get_send_operations(self, message):
    for account in self.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      account = account.value
      if self.validate_operation(account, "send", "send_enabled"):
        yield (account["_id"], "send", {"message": message}, False)

  def get_operation_by_id(self, id):
    if self.settings.record_exists(id):
      item = dict(self.settings.get_record(id).items())
      if item["record_type"] == COUCH_TYPE_STREAM:
        return [self.stream_to_operation(item)]
      if item["record_type"] == COUCH_TYPE_SEARCH:
        return list(self.search_to_operations(item))
        
  def get_operations(self):
    for acct in self.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      acct = acct.value
      for o in self.account_to_operations(acct):
        yield o
      
    for stream in self.settings.get_records(COUCH_TYPE_STREAM, True):
      stream = stream.value
      if self.accounts.record_exists(stream["account"]):
        o = self.stream_to_operation(stream)
        if o: yield o

    for search in self.settings.get_records(COUCH_TYPE_SEARCH, True):
      search = search.value
      for o in self.search_to_operations(search):
        yield o

class StreamMonitor(dbus.service.Object):
  __dbus_object_path__ = "/com/gwibber/Streams"
  
  def __init__(self):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.Streams", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)

    setting_monitor = CouchMonitor(COUCH_DB_SETTINGS)
    setting_monitor.connect("record-updated", self.on_setting_changed)
    setting_monitor.connect("record-deleted", self.on_setting_deleted)

  def on_setting_changed(self, monitor, id):
    if id == "settings": self.SettingChanged()
    else:
      log.logger.debug("Stream changed: %s", id)
      self.StreamChanged(id)

  def on_setting_deleted(self, monitor, id):
    log.logger.debug("Stream closed: %s", id)
    self.StreamClosed(id)

  @dbus.service.signal("com.Gwibber.Streams", signature="s")
  def StreamChanged(self, id): pass

  @dbus.service.signal("com.Gwibber.Streams", signature="s")
  def StreamClosed(self, id): pass

  @dbus.service.signal("com.Gwibber.Streams")
  def SettingChanged(self): pass

class AccountMonitor(dbus.service.Object):
  __dbus_object_path__ = "/com/gwibber/Accounts"

  def __init__(self):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.Accounts", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)

    account_monitor = CouchMonitor(COUCH_DB_ACCOUNTS)
    account_monitor.connect("record-updated", self.on_account_changed)
    account_monitor.connect("record-deleted", self.on_account_deleted)

  def on_account_changed(self, monitor, id):
    log.logger.debug("Account changed: %s", id)
    self.AccountChanged(id)

  def on_account_deleted(self, monitor, id):
    log.logger.debug("Account deleted: %s", id)
    self.AccountDeleted(id)

  @dbus.service.signal("com.Gwibber.Accounts", signature="s")
  def AccountChanged(self, id): pass

  @dbus.service.signal("com.Gwibber.Accounts", signature="s")
  def AccountDeleted(self, id): pass

class MessagesMonitor(dbus.service.Object):
  __dbus_object_path__ = "/com/gwibber/Messages"

  def __init__(self):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.Messages", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)

    self.messages = CouchDatabase(COUCH_DB_MESSAGES, create=True)
    util.couch.init_design_doc(self.messages, "messages", COUCH_VIEW_MESSAGES)
    #util.couch.exclude_databases(["gwibber_messages"])

    self.monitor = CouchMonitor(COUCH_DB_MESSAGES)
    self.monitor.connect("record-updated", self.on_message_updated)

    self.indicator_items = {}
    self.notified_items = []

    if indicate and util.resources.get_desktop_file():
      self.indicate = indicate.indicate_server_ref_default()
      self.indicate.set_type("message.gwibber")
      self.indicate.set_desktop_file(util.resources.get_desktop_file())
      self.indicate.connect("server-display", self.on_indicator_activate)
      self.indicate.show()

  def on_message_updated(self, monitor, id):
    try:
      #log.logger.debug("Message updated: %s", id)
      message = self.messages.get_record(id)
      self.new_message(message)
    except:
      log.logger.error("Message updated: %s, failed", id)
    

  @dbus.service.signal("com.Gwibber.Messages", signature="s")
  def MessageUpdated(self, id): pass

  def on_indicator_activate(self, indicator, timestamp):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    client_bus = dbus.SessionBus()
    log.logger.debug("Raising gwibber client")
    try:
      client_obj = client_bus.get_object("com.GwibberClient",
        "/com/GwibberClient", follow_name_owner_changes = True,
        introspect = False)
      gw = dbus.Interface(client_obj, "com.GwibberClient")
      gw.focus_client(reply_handler=self.handle_focus_reply,
                      error_handler=self.handle_focus_error)
    except dbus.DBusException:
      traceback.print_exc()


  def on_indicator_reply_activate(self, indicator, timestamp):
    log.logger.debug("Raising gwibber client, focusing replies stream")
    client_bus = dbus.SessionBus()
    try:
      client_obj = client_bus.get_object("com.GwibberClient", "/com/GwibberClient")
      gw = dbus.Interface(client_obj, "com.GwibberClient")
      gw.show_replies(reply_handler=self.handle_focus_reply,
                      error_handler=self.handle_focus_error)
      indicator.hide()
    except dbus.DBusException:
      traceback.print_exc()

  def handle_focus_reply(self, *args):
    log.logger.debug("Gwibber Client raised")

  def handle_focus_error(self, *args):
    log.logger.error("Failed to raise client %s", args)

  def new_message(self, message):
    min_time = mx.DateTime.DateTimeFromTicks() - mx.DateTime.TimeDelta(minutes=10.0)
    log.logger.debug("Checking message %s timestamp (%s) to see if it is newer than %s", message["id"], mx.DateTime.DateTimeFromTicks(message["time"]).localtime(), min_time)
    if mx.DateTime.DateTimeFromTicks(message["time"]).localtime()  > mx.DateTime.DateTimeFromTicks(min_time):
      log.logger.debug("Message %s newer than %s, notifying", message["id"], min_time)      
      if indicate and message["to_me"]:
        if message["id"] not in self.indicator_items:
          log.logger.debug("Message %s is a reply, adding messaging indicator", message["id"])
          self.handle_indicator_item(message)
      if message["id"] not in self.notified_items:
        self.notified_items.append(message["id"])
        self.show_notification_bubble(message)

  def handle_indicator_item(self, message):
    indicator = indicate.Indicator() if hasattr(indicate, "Indicator") else indicate.IndicatorMessage()
    indicator.connect("user-display", self.on_indicator_reply_activate)
    indicator.set_property("subtype", "im.gwibber")
    indicator.set_property("sender", message["sender"].get("name", ""))
    indicator.set_property("body", message["text"])
    indicator.set_property_time("time",
        mx.DateTime.DateTimeFromTicks(message["time"]).localtime().ticks())
    self.indicator_items[message["id"]] = indicator
    indicator.show()
    log.logger.debug("Message from %s added to indicator", message["sender"].get("name", ""))

  def show_notification_bubble(self, message):
    if util.can_notify and SETTINGS["show_notifications"]:
      if SETTINGS["notify_mentions_only"] and not message["to_me"]: return
      
      if SETTINGS["show_fullname"]:
        sender_name = message["sender"].get("name", 0) or data["sender"].get("nick", "")
      else:
        sender_name = message["sender"].get("nick", 0) or data["sender"].get("name", "")

      #until image caching is working again, we will post the gwibber icon
      #image = hasattr(message, "image_path") and message["image_path"] or ''
      image = util.resources.get_ui_asset("gwibber.svg")
      expire_timeout = 5000
      n = util.notify(sender_name, message["text"], image, expire_timeout)

class MapAsync(threading.Thread):
  def __init__(self, func, iterable, cbsuccess, cbfailure, timeout=240):
    threading.Thread.__init__(self)
    self.iterable = iterable
    self.callback = cbsuccess
    self.failure = cbfailure
    self.timeout = timeout
    self.daemon = True
    self.func = func
    self.start()

  def run(self):
    try:
      pool = multiprocessing.Pool()
      pool.map_async(self.func, self.iterable, callback=self.callback).get(timeout=self.timeout)
    except Exception as e:
      self.failure(e, traceback.format_exc())

class Dispatcher(dbus.service.Object):
  """
  The Gwibber Dispatcher handles all the backend operations.
  """
  __dbus_object_path__ = "/com/gwibber/Service"

  def __init__(self, loop, autorefresh=True):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.Service", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)
    
    self.collector = OperationCollector()

    self.refresh_count = 0
    self.mainloop = loop

    self.RefreshCreds()
    
    if autorefresh:
      self.refresh()

    self.accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)

  @dbus.service.signal("com.Gwibber.Service")
  def LoadingComplete(self): pass

  @dbus.service.signal("com.Gwibber.Service")
  def LoadingStarted(self): pass

  @dbus.service.method("com.Gwibber.Service")
  def CompactDB(self):
    log.logger.debug("Compacting the database")
    self.collector.messages.db.compact()

  @dbus.service.method("com.Gwibber.Service")
  def Refresh(self):
    """
    Calls the Gwibber Service to trigger a refresh operation
    example:
            import dbus
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            service.Refresh()

    """
    self.refresh()

  @dbus.service.method("com.Gwibber.Service", in_signature="s")
  def PerformOp(self, opdata):
    try: o = json.loads(opdata)
    except: return
    
    log.logger.debug("** Starting Single Operation **")
    self.LoadingStarted()
    
    params = ["account", "operation", "args", "transient"]
    operation = None
    
    if "id" in o:
      operation = self.collector.get_operation_by_id(o["id"])
    elif all(i in o for i in params):
      operation = [tuple(o[i] for i in params)]
    elif "account" in o and self.accounts.record_exists(o["account"]):
      operation = self.collector.account_to_operations(o["account"])

    if operation:
      MapAsync(perform_operation, operation, self.loading_complete, self.loading_failed)

  @dbus.service.method("com.Gwibber.Service", in_signature="s")
  def SendMessage(self, message):
    """
    Posts a message/status update to all accounts with send_enabled = True.  It 
    takes one argument, which is a message formated as a string.
    example:
            import dbus
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            service.SendMessage("Your message")
    """
    self.send(self.collector.get_send_operations(message))

  @dbus.service.method("com.Gwibber.Service", in_signature="s")
  def Send(self, opdata):
    try:
      o = json.loads(opdata)
      if "target" in o:
        args = {"message": o["message"], "target": o["target"]}
        operations = [(o["target"]["account"], "send_thread", args, None)]
      elif "accounts" in o:
        operations = [(a, "send", {"message": o["message"]}, None) for a in o["accounts"]]
      self.send(operations)
    except: pass

  @dbus.service.method("com.Gwibber.Service", out_signature="s")
  def GetServices(self):
    """
    Returns a list of services available as json string
    example:
            import dbus, json
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            services = json.loads(service.GetServices())

    """
    return json.dumps(SERVICES)

  @dbus.service.method("com.Gwibber.Service", out_signature="s")
  def GetFeatures(self):
    """
    Returns a list of features as json string
    example:
            import dbus, json
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            features = json.loads(service.GetFeatures())
    """
    return json.dumps(FEATURES)

  @dbus.service.method("com.Gwibber.Service", out_signature="s")
  def GetAccounts(self): 
    """
    Returns a list of accounts as json string
    example:
            import dbus, json
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            accounts = json.loads(service.GetAccounts())
    """
    all_accounts = []
    for account in self.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      all_accounts.append(account.value)
    return json.dumps(all_accounts)

  @dbus.service.method("com.Gwibber.Service")
  def Quit(self): 
    """
    Shutdown the service
    example:
            import dbus
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            service.Quit()
    """
    log.logger.info("Gwibber Service is being shutdown")
    self.mainloop.quit()

  @dbus.service.method("com.Gwibber.Service")
  def RefreshCreds(self):
    """
    Reload accounts and credentials from Gnome Keyring
    example:
            import dbus
            obj = dbus.SessionBus().get_object("com.Gwibber.Service", "/com/gwibber/Service")
            service = dbus.Interface(obj, "com.Gwibber.Service")
            service.RefreshCreds()
    """
    log.logger.info("Gwibber Service is reloading account credentials")
    util.keyring.get_account_passwords()
    
  def loading_complete(self, output):
    self.refresh_count += 1
    self.LoadingComplete()
    log.logger.info("Loading complete: %s - %s", self.refresh_count, [o[0] for o in output])
    if self.refresh_count % 20 == 0 and self.refresh_count > 1:
      self.CompactDB()

  def loading_failed(self, exception, tb):
    log.logger.error("Loading failed: %s - %s", exception, tb)

  def send(self, operations):
    operations = util.compact(operations)
    if operations:
      self.LoadingStarted()
      log.logger.debug("*** Sending Message ***")
      MapAsync(perform_operation, operations, self.loading_complete, self.loading_failed)

  def refresh(self):
    log.logger.debug("Refresh interval is set to %s", SETTINGS["interval"])
    operations = list(self.collector.get_operations())
    if operations:
      log.logger.debug("** Starting Refresh - %s **", time.asctime())
      self.LoadingStarted()
      MapAsync(perform_operation, operations, self.loading_complete, self.loading_failed)
    gobject.timeout_add(int(60 * 1000 * SETTINGS["interval"]), self.refresh)
    return False

class ConnectionMonitor(dbus.service.Object):
  __dbus_object_path__ = "/com/gwibber/Connection"

  def __init__(self):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.Connection", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)

    self.sysbus = dbus.SystemBus()
    try:
      self.nm = self.sysbus.get_object(NM_DBUS_SERVICE, NM_DBUS_OBJECT_PATH)
      self.nm.connect_to_signal("StateChanged", self.on_connection_changed)
    except:
      pass

  def on_connection_changed(self, state):
    if state == NM_STATE_CONNECTED:
      log.logger.info("Network state changed to Online")
      self.ConnectionOnline(state)
    if state == NM_STATE_DISCONNECTED:
      log.logger.info("Network state changed to Offline")
      self.ConnectionOffline(state)

  @dbus.service.signal("com.Gwibber.Connection", signature="u")
  def ConnectionOnline(self, state): pass

  @dbus.service.signal("com.Gwibber.Connection", signature="u")
  def ConnectionOffline(self, state): pass

  @dbus.service.method("com.Gwibber.Connection")
  def isConnected(self): 
    try:
      if self.nm.state() == NM_STATE_CONNECTED:
        return True
      return False
    except:
      return True

class URLShorten(dbus.service.Object):
  __dbus_object_path__ = "/com/gwibber/URLShorten"

  def __init__(self):
    self.bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.Gwibber.URLShorten", bus=self.bus)
    dbus.service.Object.__init__(self, bus_name, self.__dbus_object_path__)

  @dbus.service.method("com.Gwibber.URLShorten", in_signature="s", out_signature="s")
  def Shorten(self, url):
    """
    Takes a url as a string and returns a shortened url as a string.
    example:
            import dbus
            url = "http://www.example.com/this/is/a/long/url"
            obj = dbus.SessionBus().get_object("com.Gwibber.URLShorten", "/com/gwibber/URLShorten")
            shortener = dbus.Interface(obj, "com.Gwibber.URLShorten")
            short_url = shortener.Shorten(url)
    """
    if SETTINGS["urlshorter"] in urlshorter.PROTOCOLS.keys():
      service = SETTINGS["urlshorter"]
    else:
      service = "is.gd"
    log.logger.info("Shortening URL %s with %s", url, service)
    if self.IsShort(url): return url
    try:
      s = urlshorter.PROTOCOLS[service].URLShorter()
      return s.short(url)
    except: return url

  def IsShort(self, url):
    for us in urlshorter.PROTOCOLS.values():
      if url.startswith(us.PROTOCOL_INFO["fqdn"]):
        return True
    return False
