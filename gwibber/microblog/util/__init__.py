
import os, locale, re, mx.DateTime, cgi
import log
import resources
from couch import RecordMonitor
import dbus
from const import * 


COUNT = 200

def parsetime(t):
  locale.setlocale(locale.LC_TIME, '')
  loc = locale.setlocale(locale.LC_TIME)
  locale.setlocale(locale.LC_TIME, 'C')
  result = mx.DateTime.Parser.DateTimeFromString(t)
  locale.setlocale(locale.LC_TIME, loc)
  return result.ticks()

URL_SCHEMES = ('http', 'https', 'ftp', 'mailto', 'news', 'gopher',
               'nntp', 'telnet', 'wais', 'prospero', 'aim', 'webcal')

URL_FORMAT = (r'(?<!\w)((?:%s):' # protocol + :
    '/*(?!/)(?:' # get any starting /'s
    '[\w$\+\*@&=\-/]' # reserved | unreserved
    '|%%[a-fA-F0-9]{2}' # escape
    '|[\?\.:\(\),;!\'\~](?!(?:\s|$))' # punctuation
    '|(?:(?<=[^/:]{2})#)' # fragment id
    '){2,}' # at least two characters in the main url part
    ')') % ('|'.join(URL_SCHEMES),)

PARSE_LINK = re.compile(URL_FORMAT)
PARSE_NICK = re.compile("\B@([A-Za-z0-9_]+|@[A-Za-z0-9_]$)")
PARSE_HASH = re.compile("\B#([A-Za-z0-9_\-]+|@[A-Za-z0-9_\-]$)")
PARSE_URLS = re.compile(r"<[^<]*?/?>") 

def strip_urls(text):
  return PARSE_URLS.sub("", text)

def linkify(text, subs=[], escape=True):
  if escape: text = cgi.escape(text)
  for f, r in subs: text = f.sub(r, text)
  return PARSE_LINK.sub('<a href="\\1">\\1</a>', text)

def compact(data):
  if isinstance(data, dict):
    return dict([(x, y) for x,y in data.items() if y])
  elif isinstance(data, list):
    return [i for i in data if i]
  else: return data

first = lambda fn, lst: next((x for x in i if fn(x)))

def isRTL(s):
	""" is given text a RTL content? """
	if len(s)==0 :
		return False
	cc = ord(s[0]) # character code
	if cc>=1536 and cc<=1791 : # arabic, persian, ...
		return True
	if cc>=65136 and cc<=65279 : # arabic peresent 2
		return True
	if cc>=64336 and cc<=65023 : # arabic peresent 1
		return True
	if cc>=1424 and cc<=1535 : # hebrew
		return True
	if cc>=64256 and cc<=64335 : # hebrew peresent
		return True
	if cc>=1792 and cc<=1871 : # Syriac
		return True
	if cc>=1920 and cc<=1983 : # Thaana
		return True
	if cc>=1984 and cc<=2047 : # NKo
		return True
	if cc>=11568 and cc<=11647 : # Tifinagh
		return True
	return False

try:
  import pynotify
  pynotify.init("Gwibber")

  def notify(title, text, icon = None, timeout = None):
    if icon is None:
      icon = resources.get_ui_asset("gwibber.svg")
    caps = pynotify.get_server_caps()
    notification = pynotify.Notification(title, text, icon)
    if timeout:
      notification.set_timeout(timeout)
    if "x-canonical-append" in caps:
      notification.set_hint('x-canonical-append', 'allowed')
    return notification.show()

  can_notify = True
except:
  can_notify = False


def getbus(path, address="com.Gwibber"):
  if not path.startswith("/"):
    path = "/com/gwibber/%s" % path
    if len(path.split('gwibber/')[1]) > 1:
      address = "com.Gwibber.%s" % path.split('wibber/')[1]
  bus = dbus.SessionBus()
  obj = bus.get_object(address, path,
      follow_name_owner_changes = True)
  return dbus.Interface(obj, address)

def service_is_running(name):
  return name in dbus.Interface(dbus.SessionBus().get_object(
    "org.freedesktop.DBus", "/org/freedesktop/DBus"),
      "org.freedesktop.DBus").ListNames()

class SettingsMonitor(RecordMonitor):
  def __init__(self):
    RecordMonitor.__init__(self,
        COUCH_DB_SETTINGS,
        COUCH_RECORD_SETTINGS,
        COUCH_TYPE_CONFIG,
        DEFAULT_SETTINGS)

  def setup_monitor(self):
    if service_is_running("com.Gwibber.Streams"):
      getbus("Streams").connect_to_signal("SettingChanged", self.refresh)
    else:
      print "No dbus monitor yet"
      RecordMonitor.setup_monitor(self)

