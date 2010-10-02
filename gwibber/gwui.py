
import os, json, urlparse, resources, util
import gtk, gobject, pango, webkit, time, gconf
import gwibber.microblog.util

import gettext
from gettext import lgettext as _
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('gwibber','UTF-8')
gettext.textdomain('gwibber')

from mako.template import Template
from mako.lookup import TemplateLookup

from microblog.util.const import *
from microblog.util.couch import Monitor as CouchMonitor

from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord

gtk.gdk.threads_init()

if "gwibber" not in urlparse.uses_query:
  urlparse.uses_query.append("gwibber")

class Model(gobject.GObject):
  __gsignals__ = {
    "changed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, ()),
  }
  def __init__(self):
    gobject.GObject.__init__(self)

    self.daemon = gwibber.microblog.util.getbus("Service")

    self.account_monitor = gwibber.microblog.util.getbus("Accounts")
    self.account_monitor.connect_to_signal("AccountChanged", self.on_stream_changed)
    self.account_monitor.connect_to_signal("AccountDeleted", self.on_stream_changed)

    self.streams_monitor = gwibber.microblog.util.getbus("Streams")
    self.streams_monitor.connect_to_signal("StreamChanged", self.on_stream_changed)
    self.streams_monitor.connect_to_signal("StreamClosed", self.on_stream_changed)

    self.settings = gwibber.microblog.util.SettingsMonitor()
    self.services = json.loads(self.daemon.GetServices())
    self.features = json.loads(self.daemon.GetFeatures())
    self.messages = CouchDatabase(COUCH_DB_MESSAGES, create=True)
    self.accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
    self.streams = CouchDatabase(COUCH_DB_SETTINGS, create=True)

    self.model = None
    self.model_valid = False

  def on_stream_changed(self, id):
    self.model_valid = False
    self.emit("changed")

  @classmethod
  def to_state(self, item):
    if not item: return {}
    return dict((x, item[x]) for x in ["transient", "account", "stream"])

  @classmethod
  def match(self, d1, d2):
    return all(k in d1 and d1[k] == v for k, v in d2.items())

  def find(self, **params):
    for i in self.find_all(**params):
      return i

  def find_all(self, **params):
    for stream in self.get_streams():
      if self.match(stream, params): yield stream

      if "items" in stream:
        for stream in stream["items"]:
          if self.match(stream, params): yield stream

  def get_streams(self):
    if not self.model_valid: self.refresh()
    return self.model

  def refresh(self):
    self.model = self.generate_streams()
    self.model_valid = True

  def generate_streams(self):
    items = []
    transients = self.streams.get_records(COUCH_TYPE_STREAM, True)

    items.append({
      "name": _("Home"),
      "stream": "home",
      "view": self.messages.execute_view("home", "messages")[[{}]:[0]],
      "account": None,
      "transient": False,
      "color": None,
    })

    items.append({
      "name": _("Messages"),
      "stream": "messages",
      "view": self.messages.execute_view("stream_time", "messages")[["messages", {}]:["messages", 0]],
      "account": None,
      "transient": False,
      "color": None,
    })

    items.append({
      "name": _("Replies"),
      "stream": "replies",
      "view": self.messages.execute_view("stream_time", "messages")[["replies", {}]:["replies", 0]],
      "account": None,
      "transient": False,
      "color": None,
    })

    items.append({
      "name": _("Images"),
      "stream": "images",
      "view": self.messages.execute_view("stream_time", "messages")[["images", {}]:["images", 0]],
      "account": None,
      "transient": False,
      "color": None,
    })

    items.append({
      "name": _("Private"),
      "stream": "private",
      "view": self.messages.execute_view("stream_time", "messages")[["private", {}]:["private", 0]],
      "account": None,
      "transient": False,
      "color": None,
    })


    items.append({
      "name": _("Sent"),
      "stream": "sent",
      "view": self.messages.execute_view("mine", "messages")[[{}]:[0]],
      "account": None,
      "transient": False,
      "color": None,
    })

    for account in self.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      account = account.value
      aId = account["_id"]

      item = {
          "name": account.get("username", "None"),
          "account": aId,
          "stream": None,
          "view": self.messages.execute_view("account_time", "messages")[[aId, {}]:[aId, 0]],
          "transient": False,
          "color": util.Color(account["color"]),
          "protocol": account["protocol"],
          "items": [],
      }

      default_streams = self.services[account["protocol"]]["default_streams"]

      if len(default_streams) > 1:
        for feature in default_streams:
          aname = self.features[feature]["stream"]
          item["items"].append({
            "name": _(aname.capitalize()),
            "account": aId,
            "stream": aname,
            "view": self.messages.execute_view("account_stream_time", "messages")[[aId, aname, {}]:[aId, aname, 0]],
            "transient": False,
            "color": util.Color(account["color"]),
            "protocol": account["protocol"],
          })

        item["items"].append({
          "name": "Sent",
          "account": aId,
          "stream": "sent",
          "view": self.messages.execute_view("mine_account", "messages")[[aId, {}]:[aId, 0]],
          "transient": False,
          "color": util.Color(account["color"]),
          "protocol": account["protocol"],
        })

      for transient in transients:
        transient = transient.value
        tId = transient["_id"]

        if transient["account"] == aId:
          if transient["operation"] == "user_messages" and account["protocol"] in ["twitter", "identica"]:
            uId = transient["parameters"]["id"]
            view = self.messages.execute_view("user_protocol_time", "messages")[[uId, account["protocol"], {}]:[uId, account["protocol"], 0]]
          else:
            view = self.messages.execute_view("transient_time", "messages")[[tId, {}]:[tId, 0]]

          item["items"].append({
            "name": transient["name"],
            "account": aId,
            "stream": self.features[transient["operation"]]["stream"],
            "view": view,
            "transient": tId,
            "color": util.Color(account["color"]),
            "protocol": account["protocol"],
          })

      items.append(item)

    searches = {
        "name": "Search",
        "account": None,
        "stream": "search",
        "view": self.messages.execute_view("search_time", "messages")[{}:0],
        "transient": False,
        "color": None,
        "items": [],
    }

    for search in self.streams.get_records(COUCH_TYPE_SEARCH, True):
      search = search.value
      sId = search["_id"]
      searches["items"].append({
        "name": search["name"],
        "account": None,
        "view": self.messages.execute_view("transient_time", "messages")[[sId, {}]:[sId, 0]],
        "stream": "search",
        "transient": sId,
        "color": None,
      })

    items.append(searches)
    return items

class WebUi(webkit.WebView):
  __gsignals__ = {
    "action": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str, object)),
  }

  def __init__(self):
    webkit.WebView.__init__(self)
    self.web_settings = webkit.WebSettings()
    self.set_settings(self.web_settings)
    self.gc = gconf.client_get_default()

    self.connect("navigation-requested", self.on_click_link)
    self.connect("populate-popup", self.on_popup)
    self.template = None

  def on_popup(self, view, menu):
    menu.destroy()

  def on_click_link(self, view, frame, req):
    uri = req.get_uri()

    if uri.startswith("file:///"): return False
    elif uri.startswith("gwibber:"):
      url = urlparse.urlparse(uri)
      cmd = url.path.split("/")[1]
      query = urlparse.parse_qs(url.query)
      query = dict((x,y[0]) for x,y in query.items())
      self.emit("action", uri, cmd, query)
    else: util.load_url(uri)
    return True

  def render(self, theme, template, **kwargs):
    default_font = self.gc.get_string("/desktop/gnome/interface/font_name")
    font_name, font_size = default_font.rsplit(None, 1)
    self.web_settings.set_property("sans-serif-font-family", font_name)
    self.web_settings.set_property("default-font-size", float(font_size))

    if not resources.theme_exists(theme):
      theme = "default"

    theme_path = resources.get_theme_path(theme)
    template_path = resources.get_template_path(template, theme)
    lookup_paths = list(resources.get_template_dirs()) + [theme_path]

    template = open(template_path).read()
    template = Template(template, lookup=TemplateLookup(directories=lookup_paths))
    content = template.render(theme=util.get_theme_colors(), resources=resources, _=_, **kwargs)

    # Avoid navigation redraw crashes
    if isinstance(self, Navigation) and not self.get_property("visible"):
      return content

    self.load_html_string(content, "file://%s/" % os.path.dirname(template_path))
    return content

class Navigation(WebUi):
  __gsignals__ = {
    "stream-selected": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (object,)),
    "stream-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str)),
  }

  def __init__(self, model):
    WebUi.__init__(self)

    self.model = model
    self.model.connect("changed", self.on_model_update)
    self.connect("action", self.on_perform_action)

    self.selected_stream = None
    self.tree_enabled = False
    self.small_icons = False

  def render(self):
    return WebUi.render(self, self.model.settings["theme"], "navigation.mako",
      streams=self.model.get_streams(),
      tree=self.tree_enabled,
      selected=self.selected_stream,
      small_icons=self.small_icons)

  def on_model_update(self, model):
    self.render()

  def on_perform_action(self, w, uri, cmd, query):
    if cmd == "close" and "transient" in query:
      self.emit("stream-closed", query["transient"], "transient")

    if cmd == "stream":
      query = dict((k, None if v == "None" else v) for k, v in query.items())
      target = self.model.find(**query)
      if target: self.emit("stream-selected", target)

class SingleStreamUi(gtk.VBox):
  __gsignals__ = {
    "action": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str, object)),
    "stream-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str)),
    "stream-changed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (object,)),
    "search": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,)),
  }
  def __init__(self, model):
    gtk.VBox.__init__(self)
    self.model = model

    self.gc = gconf.client_get_default()

    # Build the side navigation bar
    self.navigation = Navigation(self.model)
    self.navigation.connect("stream-selected", self.on_stream_change)
    self.navigation.connect("stream-closed", self.on_stream_closed)
    self.navigation.render()

    self.navigation_scroll = gtk.ScrolledWindow()
    self.navigation_scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
    self.navigation_scroll.add(self.navigation)

    # Build the main message view
    self.message_view = MessageStreamView(self.model)
    self.message_view.connect("action", self.on_action)

    self.search_box = GwibberSearch()
    self.search_box.connect("search", self.on_search)

    self.message_scroll = gtk.ScrolledWindow()
    self.message_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.message_scroll.set_shadow_type(gtk.SHADOW_IN)
    self.message_scroll.add(self.message_view)

    layout = gtk.VBox(spacing=5)
    layout.pack_start(self.search_box, False)
    layout.pack_start(self.message_scroll, True)

    # Build the pane layout
    self.splitter = gtk.HPaned()
    self.splitter.add1(self.navigation_scroll)
    self.splitter.add2(layout)

    self.sidebar_splitter = self.gc.get_int(GCONF_CLIENT_DIR + "sidebar_splitter") or LOCAL_SETTINGS["sidebar_splitter"]
    self.splitter.set_position(self.sidebar_splitter)
    self.handle_splitter_position_change(self.sidebar_splitter)
    self.splitter.connect("notify", self.on_splitter_drag)

    self.pack_start(self.splitter, True)

  def handle_splitter_position_change(self, pos):
    if pos < 70 and self.navigation.tree_enabled:
      #self.navigation_scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
      self.navigation_scroll.set_shadow_type(gtk.SHADOW_NONE)
      self.navigation.tree_enabled = False
      self.navigation.render()

    if pos > 70 and not self.navigation.tree_enabled:
      #self.navigation_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
      self.navigation_scroll.set_shadow_type(gtk.SHADOW_IN)
      self.navigation.tree_enabled = True
      self.navigation.render()

    if pos < 30 and not self.navigation.small_icons:
      self.navigation.small_icons = True
      self.navigation.render()

    if pos > 30 and self.navigation.small_icons:
      self.navigation.small_icons = False
      self.navigation.render()

    if pos < 25:
      self.splitter.set_position(25)

  def on_splitter_drag(self, pane, ev):
    if ev.name == 'position':
      pos = pane.get_position()
      self.handle_splitter_position_change(pos)

  def on_stream_closed(self, widget, id, kind):
    self.emit("stream-closed", id, kind)

  def on_stream_change(self, widget, stream):
    self.navigation.selected_stream = stream
    self.emit("stream-changed", stream)
    self.update_search_visibility()
    self.update()

  def update_search_visibility(self):
    stream = self.navigation.selected_stream
    if stream is not None:
      is_search = stream["stream"] == "search" and stream["name"] == "Search"
      self.search_box.set_visible(not is_search)

  def on_action(self, widget, uri, cmd, query):
    self.emit("action", uri, cmd, query)

  def on_search(self, widget, query):
    self.emit("search", query)

  def update(self, *args):
    if self.navigation.selected_stream:
      self.message_view.render([self.navigation.selected_stream["view"]])

  def get_state(self):
    return [self.model.to_state(self.navigation.selected_stream)]

  def new_stream(self, state=None):
    if state: self.set_state([state])

  def set_state(self, streams):
    self.navigation.selected_stream = self.model.find(**streams[0]) or self.model.find(stream="home", account=None)
    self.navigation.render()
    self.update_search_visibility()
    self.update()


class MultiStreamUi(gtk.HBox):
  __gsignals__ = {
    "action": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str, object)),
    "stream-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str)),
    "stream-changed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (object,)),
    "pane-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (int,)),
    "search": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,)),
  }
  def __init__(self, model):
    gtk.HBox.__init__(self)
    self.model = model

    self.container = gtk.HBox(spacing=5)
    self.container.set_border_width(5)

    self.scroll = gtk.ScrolledWindow()
    self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
    self.scroll.add_with_viewport(self.container)

    self.pack_start(self.scroll, True)

  def on_stream_closed(self, widget, id, kind):
    self.emit("stream-closed", id, kind)

  def on_pane_closed(self, widget):
    widget.destroy()
    self.emit("pane-closed", len(self.container))

  def on_search(self, widget, query):
    self.emit("search", query)

  def on_action(self, widget, uri, cmd, query):
    self.emit("action", uri, cmd, query)

  def new_stream(self, state={"stream": "messages", "account": None}):
    item = MultiStreamPane(self.model)
    item.set_property("width-request", 350)
    item.connect("search", self.on_search)
    item.connect("action", self.on_action)
    item.connect("stream-closed", self.on_stream_closed)
    item.connect("pane-closed", self.on_pane_closed)
    item.show_all()

    item.search_box.hide()
    if state: item.set_state(state)
    self.container.pack_start(item)
    return item

  def set_state(self, state):
    for item in self.container: item.destroy()
    for item in state: self.new_stream(item)

  def get_state(self):
    return [pane.get_state() for pane in self.container]

  def update(self):
    for stream in self.container:
      stream.update()

class MultiStreamPane(gtk.VBox):
  __gsignals__ = {
    "action": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str, object)),
    "stream-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, str)),
    "pane-closed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, ()),
    "search": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,)),
  }

  def __init__(self, model):
    gtk.VBox.__init__(self, spacing = 2)
    self.model = model
    self.selected_stream = None

    # Build the top navigation bar
    close_icon = gtk.image_new_from_stock("gtk-close", gtk.ICON_SIZE_MENU)
    down_arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)

    btn_arrow = gtk.Button()
    btn_arrow.set_relief(gtk.RELIEF_NONE)
    btn_arrow.add(down_arrow)
    btn_arrow.connect("clicked", self.on_dropdown)

    self.arrow = gtk.EventBox()
    self.arrow.add(btn_arrow)

    btn_close = gtk.Button()
    btn_close.set_relief(gtk.RELIEF_NONE)
    btn_close.set_image(close_icon)
    btn_close.connect("clicked", self.on_close)

    self.icon_protocol = gtk.Image()
    self.icon_stream = gtk.Image()
    self.nav_label = gtk.Label()

    self.search_box = GwibberSearch()
    self.search_box.connect("search", self.on_search)

    self.navigation_bar = gtk.HBox(spacing=5)
    self.navigation_bar.pack_start(self.arrow, False)
    self.navigation_bar.pack_start(self.icon_protocol, False)
    self.navigation_bar.pack_start(self.icon_stream, False)
    self.navigation_bar.pack_start(self.nav_label, False)
    self.navigation_bar.pack_end(btn_close, False)

    # Build the main message view
    self.message_view = MessageStreamView(self.model)
    self.message_view.connect("action", self.on_action)

    self.message_scroll = gtk.ScrolledWindow()
    self.message_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.message_scroll.set_shadow_type(gtk.SHADOW_IN)
    self.message_scroll.add(self.message_view)

    self.pack_start(self.navigation_bar, False)
    self.pack_start(self.search_box, False)
    self.pack_start(self.message_scroll, True)

  def on_close(self, *args):
    self.emit("pane-closed")

  def on_dropdown(self, button):
    w, h = self.arrow.window.get_geometry()[2:4]
    x, y = self.arrow.window.get_origin()

    window = gtk.Window()
    window.move(x, y + h)
    window.set_decorated(False)
    window.set_property("skip-taskbar-hint", True)
    window.set_property("skip-pager-hint", True)
    window.set_events(gtk.gdk.FOCUS_CHANGE_MASK)
    window.connect("focus-out-event", lambda w,x: w.destroy())

    def on_change(widget, stream):
      self.set_stream(stream)
      self.update()
      window.destroy()

    def on_stream_close(widget, id, kind):
      self.emit("stream-closed", id, kind)

    navigation = Navigation(self.model)
    navigation.connect("stream-selected", on_change)
    navigation.connect("stream-closed", on_stream_close)
    navigation.selected_stream = self.selected_stream
    navigation.tree_enabled = True
    navigation.small_icons = True
    navigation.show()
    navigation.render()

    window.add(navigation)
    window.show_all()
    window.grab_focus()

  def set_stream(self, stream):
    self.selected_stream = stream
    self.nav_label.set_text(stream["name"])

    is_search = stream["stream"] == "search" and stream["name"] == "Search"
    self.search_box.set_visible(not is_search)

    if stream["account"]:
      fname = resources.get_ui_asset("icons/breakdance/16x16/%s.png" % stream["protocol"])
      self.icon_protocol.set_from_file(fname)
    else: self.icon_protocol.clear()

    if stream["stream"]:
      fname = resources.get_ui_asset("icons/streams/16x16/%s.png" % stream["stream"])
      self.icon_stream.set_from_file(fname)
    else: self.icon_stream.clear()

  def on_search(self, widget, query):
    self.emit("search", query)

  def on_action(self, widget, uri, cmd, query):
    self.emit("action", uri, cmd, query)

  def update(self, *args):
    if self.selected_stream:
      self.message_view.render([self.selected_stream["view"]])

  def get_state(self):
    return self.model.to_state(self.selected_stream)

  def set_state(self, stream):
    self.set_stream(self.model.find(**stream) or self.model.find(stream="home", account=None))
    self.update()

class AccountTargetBar(gtk.HBox):
  __gsignals__ = {
      "canceled": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, ())
  }

  def __init__(self, model):
    gtk.HBox.__init__(self, spacing=5)
    self.model = model
    self.model.connect("changed", self.on_account_changed)
    self.accounts = []

    self.target = None
    self.action = None

    self.targetbar = WebUi()
    self.targetbar.connect("action", self.on_action)
    self.targetbar.set_size_request(0, 24)
    self.pack_start(self.targetbar, True)

    self.populate()
    self.render()

  def set_target(self, message, action="reply"):
    self.target = message
    self.target["account_data"] = dict(self.model.accounts.get_record(message["account"]).items())
    self.action = action
    self.render()

  def end(self):
    self.emit("canceled")
    self.target = None
    self.action = None
    self.render()

  def on_action(self, w, uri, cmd, query):
    if cmd == "cancel": return self.end()
    if cmd == "account" and "id" in query and \
        self.model.accounts.record_exists(query["id"]):

      if "send_enabled" in query:
        self.model.accounts.update_fields(query["id"],
            {"send_enabled": bool(query["send_enabled"] == "true")})

  def on_account_changed(self, id):
    self.populate()
    self.render()

  def populate(self):
    self.accounts = []
    for account in self.model.accounts.get_records(COUCH_TYPE_ACCOUNT, True):
      if "send" in self.model.services[account.value["protocol"]]["features"]:
        self.accounts.append(account.value)

  def render(self):
    return self.targetbar.render(self.model.settings["theme"], "targetbar.mako",
        services=self.model.services,
        target=self.target,
        action=self.action,
        accounts=self.accounts)

class MessageStreamView(WebUi):
  def __init__(self, model):
    WebUi.__init__(self)
    self.model = model

  def render(self, views):
    accounts = CouchDatabase(COUCH_DB_ACCOUNTS).get_records(COUCH_TYPE_ACCOUNT, True)

    accounts = dict((a.id, a.value) for a in accounts)
    messages = []
    seen = {}

    for view in views:
      view.options["descending"] = True
      view.options["limit"] = 100
      view.options["include_docs"] = True
      view._fetch()

      for item in view:
        message = item['doc']
        message["dupes"] = []
        message["txtid"] = util.remove_urls(message["text"]).strip()[:MAX_MESSAGE_LENGTH] or None
        message["color"] = util.Color(accounts.get(message["account"], {"color": "#5A5A5A"})["color"])
        message["time_string"] = util.generate_time_string(message["time"])
        messages.append(message)

    def dupematch(item, message):
      if item["protocol"] == message["protocol"] and item["id"] == message["id"]:
        return True

      for item in item["dupes"]:
        if item["protocol"] == message["protocol"] and item["id"] == message["id"]:
          return True

    # Detect duplicates
    for n, message in enumerate(messages):
      message["is_dupe"] = message["txtid"] in seen
      if message["is_dupe"]:
        item = messages[seen[message["txtid"]]]
        if not dupematch(item, message):
          item["dupes"].append(message)
      else:
        if message["txtid"]:
          seen[message["txtid"]] = n

    WebUi.render(self, self.model.settings["theme"], "template.mako",
        message_store=messages,
        preferences=self.model.settings,
        services=self.model.services,
        accounts=accounts)

class GwibberSearch(gtk.HBox):
  __gsignals__ = {
    "search": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str,)),
  }

  def __init__(self):
    gtk.HBox.__init__(self, spacing=2)

    self.entry = gtk.Entry()
    self.entry.connect("activate", self.on_search)
    self.entry.connect("changed", self.on_changed)

    self.button = gtk.Button(_("Search"))
    self.button.connect("clicked", self.on_search)

    self.pack_start(self.entry, True)
    self.pack_start(self.button, False)

    try:
      self.entry.set_property("primary-icon-stock", gtk.STOCK_FIND)
      self.entry.connect("icon-press", self.on_icon_press)
    except: pass

  def on_search(self, *args):
    self.emit("search", self.entry.get_text())
    self.clear()

  def clear(self):
    self.entry.set_text("")

  def on_icon_press(self, w, pos, e):
    if pos == 1: return self.clear()

  def on_changed(self, widget):
    self.entry.set_property("secondary-icon-stock",
      gtk.STOCK_CLEAR if self.entry.get_text().strip() else None)

  def set_visible(self, value):
    if value: self.hide()
    else: self.show_all()

  def focus(self):
    self.entry.grab_focus()

class Input(gtk.Frame):
  __gsignals__ = {
    "submit": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, int)),
    "changed": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, (str, int))
  }

  def __init__(self):
    gtk.Frame.__init__(self)

    self.textview = InputTextView()
    self.textview.connect("submit", self.do_submit_event)
    self.textview.get_buffer().connect("changed", self.do_changed_event)

    scroll = gtk.ScrolledWindow()
    scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scroll.add(self.textview)
    self.add(scroll)

    self.set_focus_child(scroll)
    scroll.set_focus_child(self.textview)

  def get_text(self):
    return self.textview.get_text()

  def set_text(self, t):
    self.textview.get_buffer().set_text(t)

  def clear(self):
    self.set_text("")

  def do_changed_event(self, tb):
    text = self.textview.get_text()
    chars = self.textview.get_char_count()
    self.emit("changed", text, chars)

  def do_submit_event(self, tv):
    text = tv.get_text()
    chars = tv.get_char_count()
    self.emit("submit", text, chars)

class InputTextView(gtk.TextView):
  __gsignals__ = {
    "submit": (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, None, ())
  }

  def __init__(self):
    gtk.TextView.__init__(self)
    self.drawable = None
    self.model = Model()

    self.overlay_color = util.get_theme_colors()["text"].darker(3).hex
    self.overlay_text = '<span weight="bold" size="xx-large" foreground="%s">%s</span>'

    self.shortener = gwibber.microblog.util.getbus("URLShorten")

    self.connection = gwibber.microblog.util.getbus("Connection")
    self.connection.connect_to_signal("ConnectionOnline", self.on_connection_online)
    self.connection.connect_to_signal("ConnectionOffline", self.on_connection_offline)

    self.get_buffer().connect("insert-text", self.on_add_text)
    self.get_buffer().connect("changed", self.on_text_changed)
    self.connect("expose-event", self.expose_view)
    self.connect("size-allocate", self.on_size_allocate)

    # set properties
    self.set_border_width(0)
    self.set_accepts_tab(True)
    self.set_editable(True)
    self.set_cursor_visible(True)
    self.set_wrap_mode(gtk.WRAP_WORD_CHAR)
    self.set_left_margin(2)
    self.set_right_margin(2)
    self.set_pixels_above_lines(2)
    self.set_pixels_below_lines(2)

    self.base_color = util.get_style().base[gtk.STATE_NORMAL]
    self.error_color = gtk.gdk.color_parse("indianred")

    # set state online/offline
    if not self.connection.isConnected():
      self.set_sensitive(False)

    if util.gtkspell:
      try:
        self.spell = util.gtkspell.Spell(self, None)
      except:
        pass

  def get_text(self):
    buf = self.get_buffer()
    return buf.get_text(*buf.get_bounds()).strip()

  def get_char_count(self):
    return len(unicode(self.get_text(), "utf-8"))

  def on_add_text(self, buf, iter, text, tlen):
    if self.model.settings["shorten_urls"]:
      if text and text.startswith("http") and not " " in text \
          and len(text) > 30:

        buf = self.get_buffer()
        buf.stop_emission("insert-text")

        def add_shortened(shortened_url):
            "Internal add-shortened-url-to-buffer function: a closure"
            iter_start = buf.get_iter_at_mark(mark_start)
            iter_end = buf.get_iter_at_mark(mark_end)
            buf.delete(iter_start, iter_end)
            buf.insert(iter_start, shortened_url)
        def error_shortened(dbus_exc):
            "Internal shortening-url-died function: a closure"
            iter = buf.get_iter_at_mark(mark)
            buf.insert(iter, text) # shortening failed

        # set a mark at iter, so that the callback knows where to insert
        mark_start = buf.create_mark(None, iter, True)
        # insert a placeholder character
        buf.insert(iter, u"\u2328")
        # can't just get_insert() because that gets the *named* mark "insert"
        # and we want an anonymous mark so it won't get changed later
        iter_end = buf.get_iter_at_mark(buf.get_insert())
        mark_end = buf.create_mark(None, iter_end, True)
        self.shortener.Shorten(text,
            reply_handler=add_shortened,
            error_handler=error_shortened)

  def set_overlay_text(self, text):
    self.pango_overlay.set_markup(self.overlay_text % (self.overlay_color, text))

  def on_size_allocate(self, *args):
    if self.drawable: self.drawable.show()

  def expose_view(self, window, event):
    if not self.drawable:
      self.drawable = self.get_window(gtk.TEXT_WINDOW_TEXT)
      self.pango_overlay = self.create_pango_layout("")
      self.set_overlay_text(MAX_MESSAGE_LENGTH)

    gc = self.drawable.new_gc()
    ww, wh = self.drawable.get_size()
    tw, th = self.pango_overlay.get_pixel_size()
    self.drawable.draw_layout(gc, ww - tw - 2, wh - th, self.pango_overlay)

  def on_text_changed(self, w):
    chars = self.get_char_count()
    color = self.error_color if chars > MAX_MESSAGE_LENGTH else self.base_color
    self.modify_base(gtk.STATE_NORMAL, color)

  def on_connection_online(self, w):
    self.set_sensitive(True)

  def on_connection_offline(self, w):
    self.set_sensitive(False)

gtk.binding_entry_add_signal(InputTextView, gtk.keysyms.Return, 0, "submit")
gtk.binding_entry_add_signal(InputTextView, gtk.keysyms.KP_Enter, 0, "submit")
