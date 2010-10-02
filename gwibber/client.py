#!/usr/bin/env python

import gtk, gobject, gwui, util, resources, actions, json, gconf
import microblog.util
import subprocess, os
import time, datetime

import gettext
from gettext import lgettext as _
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('gwibber','UTF-8')
gettext.textdomain('gwibber')

from microblog.util.couch import RecordMonitor
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord
from gwibber.microblog.util import log
from microblog.util.const import *
from dbus.mainloop.glib import DBusGMainLoop
import dbus, dbus.service

DBusGMainLoop(set_as_default=True)

class GwibberClient(gtk.Window):
  def __init__(self):
    gtk.Window.__init__(self)
    self.ui = gtk.Builder()
    self.ui.set_translation_domain ("gwibber")

    self.model = gwui.Model()

    self.service = self.model.daemon
    self.service.connect_to_signal("LoadingStarted", self.on_loading_started)
    self.service.connect_to_signal("LoadingComplete", self.on_loading_complete)

    self.connection = microblog.util.getbus("Connection")
    self.connection.connect_to_signal("ConnectionOnline", self.on_connection_online)
    self.connection.connect_to_signal("ConnectionOffline", self.on_connection_offline)

    microblog.util.getbus("Streams").connect_to_signal("SettingChanged", self.on_setting_changed)

    if len(json.loads(self.service.GetAccounts())) == 0:
      import upgrade
      account_migrate = upgrade.GwibberAccountMigrate()
      if not account_migrate.run():
        if os.path.exists(os.path.join("bin", "gwibber-accounts")):
          cmd = os.path.join("bin", "gwibber-accounts")
        else:
          cmd = "gwibber-accounts"
        ret = 1
        while ret != 0:
          ret = subprocess.call([cmd])
      self.service.Refresh()

    self.gc = gconf.client_get_default()
    self.gc.add_dir("/desktop/gnome/interface/font_name", gconf.CLIENT_PRELOAD_NONE)
    self.gc.notify_add("/desktop/gnome/interface/font_name", self.on_font_changed)

    self.setup_ui()

    # set state online/offline
    if not self.connection.isConnected():
      log.logger.info("Setting to Offline")
      self.actions.get_action("refresh").set_sensitive(False)

  def on_setting_changed(self):
    self.update_view()

  def on_font_changed(self, *args):
    self.update_view()

  def setup_ui(self):
    self.set_title(_("Social broadcast messages"))
    self.set_icon_from_file(resources.get_ui_asset("gwibber.svg"))
    self.connect("delete-event", self.on_window_close)

    # Load the application menu
    menu_ui = self.setup_menu()
    self.add_accel_group(menu_ui.get_accel_group())

    # Create animated loading spinner
    self.loading_spinner = gtk.Image()
    menu_spin = gtk.ImageMenuItem("")
    menu_spin.set_right_justified(True)
    menu_spin.set_sensitive(False)
    menu_spin.set_image(self.loading_spinner)

    # Force the spinner to show in newer versions of Gtk
    if hasattr(menu_spin, "set_always_show_image"):
      menu_spin.set_always_show_image(True)

    menubar = menu_ui.get_widget("/menubar_main")
    menubar.append(menu_spin)

    view_class = getattr(gwui,
        "MultiStreamUi" if len(self.model.settings["streams"]) > 1
        else "SingleStreamUi")

    self.stream_view = view_class(self.model)
    self.stream_view.connect("action", self.on_action)
    self.stream_view.connect("search", self.on_perform_search)
    self.stream_view.connect("stream-changed", self.on_stream_changed)
    self.stream_view.connect("stream-closed", self.on_stream_closed)
    if isinstance(self.stream_view, gwui.MultiStreamUi):
      self.stream_view.connect("pane-closed", self.on_pane_closed)

    self.input = gwui.Input()
    self.input.connect("submit", self.on_input_activate)
    self.input.connect("changed", self.on_input_changed)

    self.input_splitter = gtk.VPaned()
    self.input_splitter.pack1(self.stream_view, resize=True)
    self.input_splitter.pack2(self.input, resize=False)

    self.input_splitter.set_focus_child(self.input)

    self.button_send = gtk.Button(_("Send"))
    self.button_send.connect("clicked", self.on_button_send_clicked)

    self.message_target = gwui.AccountTargetBar(self.model)
    self.message_target.pack_end(self.button_send, False)
    #self.message_target.pack_end(self.character_count, False)
    self.message_target.connect("canceled", self.on_reply_cancel)

    content = gtk.VBox(spacing=5)
    content.pack_start(self.input_splitter, True)
    content.pack_start(self.message_target, False)
    content.set_border_width(5)

    layout = gtk.VBox()
    layout.pack_start(menubar, False)
    layout.pack_start(content, True)

    self.add(layout)

    self.window_size = self.gc.get_list(GCONF_CLIENT_DIR + "window_size", gconf.VALUE_INT) or LOCAL_SETTINGS["window_size"]
    self.window_position = self.gc.get_list(GCONF_CLIENT_DIR + "window_position", gconf.VALUE_INT) or LOCAL_SETTINGS["window_position"]
    self.window_splitter = self.gc.get_int(GCONF_CLIENT_DIR + "window_splitter") or LOCAL_SETTINGS["window_splitter"]
    # Apply the user's settings 
    self.resize(self.window_size[0], self.window_size[1])
    self.move(self.window_position[0], self.window_position[1])
    self.input_splitter.set_position(self.window_splitter)
    self.show_all()

    self.stream_view.set_state(self.model.settings["streams"] or DEFAULT_SETTINGS["streams"])
    self.update_menu_availability()

  def set_view(self, view=None):
    state = None
    if view: self.view_class = getattr(gwui, view)
    if self.stream_view:
      state = self.stream_view.get_state()
      self.stream_view.destroy()

    self.stream_view = self.view_class(self.model)
    self.stream_view.connect("action", self.on_action)
    self.stream_view.connect("search", self.on_perform_search)
    self.stream_view.connect("stream-changed", self.on_stream_changed)
    self.stream_view.connect("stream-closed", self.on_stream_closed)

    if isinstance(self.stream_view, gwui.MultiStreamUi):
      self.stream_view.connect("pane-closed", self.on_pane_closed)

    self.input_splitter.add1(self.stream_view)
    self.stream_view.show_all()
    if state: self.stream_view.set_state(state)

  def setup_menu(self):
    ui_string = """
    <ui>
      <menubar name="menubar_main">
        <menu action="menu_gwibber">
          <menuitem action="refresh" />
          <menuitem action="search" />
          <separator/>
          <menuitem action="new_stream" />
          <menuitem action="close_window" />
          <menuitem action="close_stream" />
          <separator/>
          <menuitem action="quit" />
        </menu>

        <menu action="menu_edit">
          <menuitem action="accounts" />
          <menuitem action="preferences" />
        </menu>

        <menu action="menu_help">
          <menuitem action="help_online" />
          <menuitem action="help_translate" />
          <menuitem action="help_report" />
          <separator/>
          <menuitem action="about" />
        </menu>
      </menubar>

      <popup name="menu_tray">
        <menuitem action="refresh" />
        <separator />
        <menuitem action="accounts" />
        <menuitem action="preferences" />
        <separator />
        <menuitem action="quit" />
      </popup>
    </ui>
    """

    self.actions = gtk.ActionGroup("Actions")
    self.actions.add_actions([
      ("menu_gwibber", None, _("_Gwibber")),
      ("menu_edit", None, _("_Edit")),
      ("menu_help", None, _("_Help")),

      ("refresh", gtk.STOCK_REFRESH, _("_Refresh"), "<ctrl>R", None, self.on_refresh),
      ("search", gtk.STOCK_FIND, _("_Search"), "<ctrl>F", None, self.on_search),
      ("accounts", None, _("_Accounts"), "<ctrl><shift>A", None, self.on_accounts),
      ("preferences", gtk.STOCK_PREFERENCES, _("_Preferences"), "<ctrl>P", None, self.on_preferences),
      ("about", gtk.STOCK_ABOUT, _("_About"), None, None, self.on_about),
      ("quit", gtk.STOCK_QUIT, _("_Quit"), "<ctrl>Q", None, self.on_quit),

      ("new_stream", gtk.STOCK_NEW, _("_New Stream"), "<ctrl>n", None, self.on_new_stream),
      ("close_window", gtk.STOCK_CLOSE, _("_Close Window"), "<ctrl><shift>W", None, self.on_window_close),
      ("close_stream", gtk.STOCK_CLOSE, _("_Close Stream"), "<ctrl>W", None, self.on_close_stream),

      ("help_online", None, _("Get Help Online..."), None, None, lambda *a: util.load_url(QUESTIONS_URL)),
      ("help_translate", None, _("Translate This Application..."), None, None, lambda *a: util.load_url(TRANSLATE_URL)),
      ("help_report", None, _("Report A Problem..."), None, None, lambda *a: util.load_url(BUG_URL)),
    ])


    ui = gtk.UIManager()
    ui.insert_action_group(self.actions, pos=0)
    ui.add_ui_from_string(ui_string)
    return ui

  def update_menu_availability(self):
    state = self.stream_view.get_state()
    if state:
      a = self.actions.get_action("close_stream")
      a.set_visible(bool(state[0].get("transient", False)))

  def update_view(self):
    self.stream_view.update()

  def reply(self, message):
    features = self.model.services[message["protocol"]]["features"]
    if "reply" in features:
      if message["sender"].get("nick", 0) and not "thread" in features:
        s = "@%s: " if self.model.settings["reply_append_colon"] else "@%s "
        self.input.set_text(s % message["sender"]["nick"])

      self.message_target.set_target(message)
      self.input.textview.grab_focus()
      buf = self.input.textview.get_buffer()
      buf.place_cursor(buf.get_end_iter())

  def on_reply_cancel(self, widget):
    self.input.clear()

  def get_message(self, id):
    return dict(self.model.messages.get_record(id).items())

  def on_refresh(self, *args):
    self.service.Refresh()

  def add_stream(self, data, kind=COUCH_TYPE_STREAM):
    id = self.model.streams.put_record(CouchRecord(data, kind))
    self.model.refresh()
    self.service.PerformOp('{"id": "%s"}' % id)

    if "operation" in data:
      stream = str(self.model.features[data["operation"]]["stream"])
    else: stream = "search"

    self.stream_view.new_stream({
      "stream": stream,
      "account": data.get("account", None),
      "transient": id,
    })
    self.update_menu_availability()

  def save_window_settings(self):
    if str(LOCAL_SETTINGS["window_size"]) != str(self.get_size()):
      self.gc.set_list(GCONF_CLIENT_DIR + "window_size", gconf.VALUE_INT, list(self.get_size()))
    if str(LOCAL_SETTINGS["window_position"]) != str(self.get_position()):
      self.gc.set_list(GCONF_CLIENT_DIR + "window_position", gconf.VALUE_INT, list(self.get_position()))
    if str(LOCAL_SETTINGS["window_splitter"]) != str(self.input_splitter.get_position()):
      self.gc.set_int(GCONF_CLIENT_DIR + "window_splitter",  int(self.input_splitter.get_position()))

    if hasattr(self.stream_view, "splitter"):
      if str(LOCAL_SETTINGS["sidebar_splitter"]) != str(self.stream_view.splitter.get_position()):
        self.gc.set_int(GCONF_CLIENT_DIR + "sidebar_splitter",  int(self.stream_view.splitter.get_position()))

    self.model.settings["streams"] =  self.stream_view.get_state()
    self.model.settings.save()

  def on_pane_closed(self, widget, count):
    if count < 2 and isinstance(self.stream_view, gwui.MultiStreamUi):
      self.set_view("SingleStreamUi")

  def on_window_close(self, *args):
    self.save_window_settings()
    log.logger.info("Gwibber Client closed")
    gtk.main_quit()

  def on_quit(self, *args):
    self.service.Quit()
    log.logger.info("Gwibber Client quit")
    self.on_window_close()

  def on_search(self, *args):
    self.stream_view.set_state([{
      "stream": "search",
      "account": None,
      "transient": False,
    }])

    self.stream_view.search_box.focus()

  def on_perform_search(self, widget, query):
    self.add_stream({
      "name": query,
      "query": query,
    }, COUCH_TYPE_SEARCH)

  def on_accounts(self, *args):
    if os.path.exists(os.path.join("bin", "gwibber-accounts")):
      cmd = os.path.join("bin", "gwibber-accounts")
    else:
      cmd = "gwibber-accounts"
    return subprocess.Popen(cmd, shell=False)

  def on_preferences(self, *args):
    if os.path.exists(os.path.join("bin", "gwibber-preferences")):
      cmd = os.path.join("bin", "gwibber-preferences")
    else:
      cmd = "gwibber-preferences"
    return subprocess.Popen(cmd, shell=False)

  def on_about(self, *args):
    self.ui.add_from_file (resources.get_ui_asset("gwibber-about-dialog.ui"))
    about_dialog = self.ui.get_object("about_dialog")
    about_dialog.set_version(str(VERSION_NUMBER))
    about_dialog.connect("response", lambda *a: about_dialog.hide())
    about_dialog.show_all()

  def on_close_stream(self, *args):
    state = self.stream_view.get_state()
    if state and state[0].get("transient", 0):
      id = state[0]["transient"]
      if self.model.streams.record_exists(id):
        self.model.streams.delete_record(id)
        self.stream_view.set_state([{"stream": "messages", "account": None}])

  def on_message_action_menu(self, msg):
    theme = gtk.icon_theme_get_default()
    menu = gtk.Menu()

    for a in actions.MENU_ITEMS:
      if a.include(self, msg):
        image = gtk.image_new_from_icon_name(a.icon, gtk.ICON_SIZE_MENU)
        mi = gtk.ImageMenuItem()
        mi.set_label(a.label)
        mi.set_image(image)
        mi.set_property("use_underline", True)
        mi.connect("activate", a.action, self, msg)
        menu.append(mi)

    menu.show_all()
    menu.popup(None, None, None, 3, 0)

  def on_action(self, widget, uri, cmd, query):
    if hasattr(actions, cmd):
      if "msg" in query:
        query["msg"] = self.get_message(query["msg"])
      getattr(actions, cmd).action(None, self, **query)

  def on_stream_closed(self, widget, id, kind):
    if self.model.streams.record_exists(id):
      self.model.streams.delete_record(id)

  def on_stream_changed(self, widget, stream):
    self.update_menu_availability()

  def on_input_changed(self, w, text, cnt):
    self.input.textview.set_overlay_text(str(MAX_MESSAGE_LENGTH - cnt))

  def on_input_activate(self, w, text, cnt):
    self.send_message(text)
    self.input.clear()

  def on_button_send_clicked(self, w):
    self.send_message(self.input.get_text())
    self.input.clear()

  def send_message(self, text):
    target = self.message_target.target
    action = self.message_target.action

    if target:
      if action == "reply":
        data = {"message": text, "target": target}
        self.service.Send(json.dumps(data))
      elif action == "repost":
        data = {"message": text, "accounts": [target["account"]]}
        self.service.Send(json.dumps(data))
      self.message_target.end()
    else: self.service.SendMessage(text)

  def on_new_stream(self, *args):
    if isinstance(self.stream_view, gwui.MultiStreamUi):
      self.stream_view.new_stream()
    else:
      self.set_view("MultiStreamUi")
      self.stream_view.new_stream()

  def on_loading_started(self, *args):
    self.loading_spinner.set_from_animation(
      gtk.gdk.PixbufAnimation(resources.get_ui_asset("progress.gif")))

  def on_loading_complete(self, *args):
    self.loading_spinner.clear()
    self.update_view()

  def on_connection_online(self, *args):
    log.logger.info("Setting to Online")
    self.actions.get_action("refresh").set_sensitive(True)

  def on_connection_offline(self, *args):
    log.logger.info("Setting to Offline")
    self.actions.get_action("refresh").set_sensitive(False)

class Client(dbus.service.Object):
  __dbus_object_path__ = "/com/GwibberClient"

  def __init__(self):
    # Setup a Client dbus interface
    self.bus = dbus.SessionBus()
    self.bus_name = dbus.service.BusName("com.GwibberClient", self.bus)
    dbus.service.Object.__init__(self, self.bus_name, self.__dbus_object_path__)

    # Methods the client exposes via dbus, return from the list method
    self.exposed_methods = [
                       'focus_client',
                       'show_replies',
                      ]

    self.w = GwibberClient()

  @dbus.service.method("com.GwibberClient", in_signature="", out_signature="")
  def focus_client(self):
    """
    This method focuses the client UI displaying the default view.
    Currently used when the client is activated via dbus activation.
    """
    self.w.present_with_time(int(time.mktime(datetime.datetime.now().timetuple())))
    try:
      self.w.move(*self.w.model.settings["window_position"])
    except:
      pass

  @dbus.service.method("com.GwibberClient", in_signature="", out_signature="")
  def show_replies(self):
    """
    This method focuses the client UI and displays the replies view.
    Currently used when activated via the messaging indicator.
    """
    self.w.present_with_time(int(time.mktime(datetime.datetime.now().timetuple())))
    self.w.move(*self.w.model.settings["window_position"])
    # FIXME: we need to be able to select the stream to view
    #self.w.account_tree.get_selection().unselect_all()
    #self.w.account_tree.get_selection().select_path((2,))

  @dbus.service.method("com.GwibberClient")
  def list(self):
    """
    This method returns a list of exposed dbus methods
    """
    return self.exposed_methods
