#
# Copyright (C) 2010 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2010 Ken VanDine <ken.vandine@canonical.com>
#
# Preferences interface for Gwibber
#

import pygtk
try:
    pygtk.require("2.0") 
except:
    print "Requires pygtk 2.0 or later"
    exit

from gwibber import resources
from gwibber.microblog import util
import gtk, gconf

import gettext
from gettext import lgettext as _
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('gwibber','UTF-8')
gettext.textdomain('gwibber')

from microblog.util.const import *
from microblog.urlshorter import PROTOCOLS as urlshorters

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

class GwibberPreferences(object):
    def __init__(self):
        self.ui = gtk.Builder()
	self.ui.set_translation_domain ("gwibber")
        self.ui.add_from_file (resources.get_ui_asset("gwibber-preferences-dialog.ui"))
        self.ui.connect_signals(self)
        self.gc = gconf.client_get_default()
        dialog = self.ui.get_object("prefs_dialog")
        dialog.set_icon_from_file(resources.get_ui_asset("gwibber.svg"))

        self.settings = util.SettingsMonitor()
        self.populate_settings_data(self)
        dialog.show_all()

    def populate_settings_data(self, widget, data=None):
        self.ui.get_object("interval").set_value(self.settings["interval"])
        
        for setting in "show_notifications", "notify_mentions_only", "show_fullname", "shorten_urls", "reply_append_colon", "global_retweet":
            if isinstance(self.settings[setting], str) and self.settings[setting].lower() == "true":
                self.settings[setting] = True
                self.settings.save()
            if isinstance(self.settings[setting], str) and self.settings[setting].lower() == "false":
                self.settings[setting] = False
                self.settings.save()
        self.ui.get_object("autostart").set_active(self.gc.get_bool("/apps/gwibber/autostart"))
        self.ui.get_object("show_notifications").set_active(self.settings["show_notifications"])
        self.ui.get_object("notify_mentions_only").set_active(self.settings["notify_mentions_only"])
        self.ui.get_object("show_fullname").set_active(self.settings["show_fullname"])
        self.ui.get_object("shorten_urls").set_active(self.settings["shorten_urls"])
        self.ui.get_object("reply_append_colon").set_active(self.settings["reply_append_colon"])
        self.ui.get_object("global_retweet").set_active(self.settings["global_retweet"])

        self.theme_selector = gtk.combo_box_new_text()
        for theme in sorted(resources.get_themes()): self.theme_selector.append_text(theme)
        self.ui.get_object("theme_container").pack_start(self.theme_selector, True, True)
        self.theme_selector.set_active_iter(dict([(x[0].strip(), x.iter) for x in self.theme_selector.get_model()]).get(self.settings["theme"], self.theme_selector.get_model().get_iter_root()))
        self.theme_selector.show_all()

        self.urlshorter_selector = gtk.combo_box_new_text()
        for urlshorter in urlshorters.keys(): self.urlshorter_selector.append_text(urlshorter)
        self.ui.get_object("urlshorter_container").pack_start(self.urlshorter_selector, True, True)
        if not self.settings["urlshorter"] in urlshorters.keys():
          self.settings["urlshorter"] = DEFAULT_SETTINGS["urlshorter"]
          self.settings.save()
        self.urlshorter_selector.set_active_iter(dict([(x[0].strip(), x.iter) for x in self.urlshorter_selector.get_model()]).get(self.settings["urlshorter"], self.urlshorter_selector.get_model().get_iter_root()))
        self.urlshorter_selector.show_all()

        self.retweet_style_selector = gtk.combo_box_new_text()
        for format in RETWEET_FORMATS: self.retweet_style_selector.append_text(format)
        self.ui.get_object("retweet_style_container").pack_start(self.retweet_style_selector, True, True)
        self.retweet_style_selector.set_active_iter(dict([(x[0].strip(), x.iter) for x in self.retweet_style_selector.get_model()]).get(self.settings["retweet_style"], self.retweet_style_selector.get_model().get_iter_root()))
        self.retweet_style_selector.show_all()

    def on_save_button_clicked(self, widget, data=None):
        self.settings["interval"] = int(self.ui.get_object("interval").get_value())
        
        # Only change autostart if it was already set before or if the user enabled it
        if self.gc.get("/apps/gwibber/autostart") is None:
            if self.ui.get_object("autostart").get_property("active"):
                self.gc.set_bool("/apps/gwibber/autostart", self.ui.get_object("autostart").get_property("active"))
        else:
            self.gc.set_bool("/apps/gwibber/autostart", self.ui.get_object("autostart").get_property("active"))
        self.settings["show_notifications"] = self.ui.get_object("show_notifications").get_property("active")
        self.settings["notify_mentions_only"] = self.ui.get_object("notify_mentions_only").get_property("active")
        self.settings["show_fullname"] = self.ui.get_object("show_fullname").get_property("active")
        self.settings["shorten_urls"] = self.ui.get_object("shorten_urls").get_property("active")
        self.settings["reply_append_colon"] = self.ui.get_object("reply_append_colon").get_property("active")
        self.settings["global_retweet"] = self.ui.get_object("global_retweet").get_property("active")
        self.settings["theme"] = self.theme_selector.get_active_text()
        self.settings["urlshorter"] = self.urlshorter_selector.get_active_text()
        self.settings["retweet_style"] = self.retweet_style_selector.get_active_text()
        self.settings.save()
        gtk.main_quit()

        
    def on_cancel_button_clicked(self, widget, data=None):
        gtk.main_quit()
        
    def on_prefs_dialog_destroy_event(self, widget, data=None):
        gtk.main_quit()

