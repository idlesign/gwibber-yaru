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
# Accounts interface for Gwibber
#

import pygtk
try:
    pygtk.require("2.0") 
except:
    print "Requires pygtk 2.0 or later"
    exit

try:
  import gnomekeyring
except:
  gnomekeyring = None

import gettext
from gettext import lgettext as _
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('gwibber','UTF-8')
gettext.textdomain('gwibber')

from . import resources
import gtk, gconf
import json, uuid
import gwibber.lib
import gwibber.gwui
import gwibber.microblog.util
from gwibber.lib.gtk import *

from microblog.util.const import *

from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import string

class GwibberAccountManager(object):

    def __init__(self):
        self.pub = gwibber.lib.GwibberPublic()
        self.ui = gtk.Builder()
        self.ui.set_translation_domain ("gwibber")
        self.ui.add_from_file (resources.get_ui_asset("gwibber-accounts-dialog.ui"))
        self.ui.connect_signals(self)
        dialog = self.ui.get_object("accounts_dialog")
        dialog.set_icon_from_file(resources.get_ui_asset("gwibber.svg"))
        self.accounts_tree = self.ui.get_object("accounts_tree")

        #self.pub.MonitorAccountChanged(self.load_accounts)
        #self.pub.MonitorAccountDeleted(self.load_accounts)

        dialog.show_all()
        
        # hide the help button until we have help :)
        button_help = self.ui.get_object("button_help")
        button_help.hide()

        self.protocols = json.loads(self.pub.GetServices())

        self.gwibber_service = gwibber.microblog.util.getbus("Service")

        # FIXME: this should check for configured accounts, and if there are any hide this
        self.ui.get_object('frame_new_account').hide()
        self.ui.get_object('vbox_save').hide()
        self.ui.get_object('vbox_create').hide()

        self.load_accounts()
        self.icon_column = gtk.TreeViewColumn('Icon') 
        self.name_column = gtk.TreeViewColumn('Account') 
        self.celltxt = gtk.CellRendererText() 
        self.celltxtproblem = gtk.CellRendererText() 
        self.cellimg = gtk.CellRendererPixbuf()
        self.icon_column.pack_start(self.cellimg, False) 
        self.name_column.pack_start(self.celltxt, True) 
        self.icon_column.add_attribute(self.cellimg, 'pixbuf', 1) 
        self.icon_column.add_attribute(self.cellimg, 'cell-background', 3) 
        self.name_column.add_attribute(self.celltxt, 'text', 0) 
        self.name_column.add_attribute(self.celltxt, 'cell-background', 3) 
        self.accounts_tree.append_column(self.icon_column)
        self.accounts_tree.append_column(self.name_column)
        if len(self.accounts_tree.get_model()) > 0:
            self.accounts_tree.set_cursor(0)


    def account_verify(self, account):
        for required in self.protocols[account['protocol']]['config']:
            try:
                required = required.split(":")[1]
            except:
                pass
            if not self.account.has_key(required):
                return False
        return True

    def load_accounts(self, *args):
        accounts_store = gtk.TreeStore(
            str, # Account name
            gtk.gdk.Pixbuf, # Icon
            str, # Protocol properties
            str) # color background
        self.accounts_tree.set_model(accounts_store)
        self.accounts = json.loads(self.pub.GetAccounts())
        if len(self.accounts) == 0:
            self.add_account()
            return
	for self.account in self.accounts:
            #if self.account_verify(self.account):
                try:
                    icf = resources.icon(self.account["protocol"], use_theme=False) or resources.get_ui_asset("icons/breakdance/16x16/%s.png" % self.account["protocol"])
                    icon = gtk.gdk.pixbuf_new_from_file(icf)
                except:
                    icf = resources.get_ui_asset("gwibber.svg")
                    icon = gtk.icon_theme_add_builtin_icon("gwibber", 22,
                                                           gtk.gdk.pixbuf_new_from_file_at_size(
                                                           resources.get_ui_asset("gwibber.svg"), 16, 16))
                has_secret = True
                for config in self.protocols[self.account["protocol"]]["config"]:
                    is_private = config.startswith("private:")
                    config = config.replace("private:", "")
                    if is_private:
                        if not self.account.has_key(config): self.account[config] = ":KEYRING:MISSING"
                        if self.account[config].startswith(":KEYRING:"):
                            try:
                                value = gnomekeyring.find_items_sync(gnomekeyring.ITEM_GENERIC_SECRET, {"id": str("%s/%s" % (self.account["_id"], config))})[0].secret
                            except gnomekeyring.NoMatchError:
                                has_secret = False

                bg_color = None
                if not has_secret:
                    bg_color = "pink"
                
                accounts_store.append(None, [self.account["protocol"] + " (" + self.account["username"] + ")", icon, self.account, bg_color])
        if len(self.accounts_tree.get_model()) > 0:
            self.accounts_tree.set_cursor(0)
        else:
            self.add_account()    

    def on_edit_account(self, widget, data=None):
        self.ui.get_object('vbox_save').show()
        self.ui.get_object('vbox_create').hide()

    def on_edit_account_cancel(self, widget):
        self.ui.get_object('vbox_save').hide()
        self.ui.get_object('vbox_create').hide()
        if len(self.accounts_tree.get_model()) > 0:
            self.accounts_tree.set_cursor(0)
        else:
            self.add_account()    

    def on_account_delete(self, widget):
        accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
        if self.account.has_key("_id"):
            if accounts.record_exists(self.account["_id"]):
                accounts.delete_record(self.account["_id"])
        self.load_accounts()
        if len(self.accounts_tree.get_model()) > 0:
            self.accounts_tree.set_cursor(0)
        else:
            self.add_account()    
        
    def on_edit_account_save(self, widget):
        print "Saving..."
        self.get_account_data()
        accounts = CouchDatabase(COUCH_DB_ACCOUNTS, create=True)
        if not self.account_verify(self.account):
            return False

        if not accounts.record_exists(self.account["_id"]) and \
            self.account["_id"] in accounts.db:
              print "CouchDB ID collision encountered, deleting old account"
              del accounts.db[self.account["_id"]]

        if accounts.record_exists(self.account["_id"]):
            accounts.update_fields(self.account["_id"], self.account)
        else:
            accounts.put_record(CouchRecord(self.account, COUCH_TYPE_ACCOUNT, self.account["_id"]))
        self.gwibber_service.RefreshCreds()
        self.gwibber_service.PerformOp('{"account": "%s"}' % self.account["_id"])
        self.ui.get_object('vbox_save').hide()
        self.ui.get_object('vbox_create').hide()
        # refresh the account tree
        self.load_accounts()

        # Set the autostart gconf key so we get loaded on login
        gc = gconf.client_get_default()
        if gc.get("/apps/gwibber/autostart") is None:
            gc.set_bool("/apps/gwibber/autostart", True)

        return True

    def on_button_add_activate(self, widget=None, data=None):
        self.add_account()

    def add_account(self):
        # Populate protocols combobox
        self.ui.get_object('frame_new_account').show()
        self.ui.get_object('vbox_details').hide()
        self.ui.get_object('vbox_account').hide()
        self.ui.get_object('vbox_save').hide()
        self.ui.get_object('vbox_create').hide()
        protocol_combobox = self.ui.get_object("protocol_combobox")
        protocol_store = gtk.ListStore(
            str, # Protocol title
            gtk.gdk.Pixbuf, # Icon
            str) # Protocol properties

        for name, properties in self.protocols.items():
            icf = resources.icon(name, use_theme=False) or resources.get_ui_asset("icons/breakdance/16x16/%s.png" % name)
            icon = gtk.gdk.pixbuf_new_from_file(icf)
            protocol_store.append((properties['name'], icon, dict([('name', name), ('properties', properties)])))
        protocol_combobox.clear()
        protocol_combobox.set_model(protocol_store)
        self.protocol_cell_txt = gtk.CellRendererText()
        self.protocol_cell_img = gtk.CellRendererPixbuf()
        protocol_combobox.pack_start(self.protocol_cell_img, False)
        protocol_combobox.pack_start(self.protocol_cell_txt, False)
        protocol_combobox.add_attribute(self.protocol_cell_img, 'pixbuf', 1)
        protocol_combobox.add_attribute(self.protocol_cell_txt, 'text', 0)
        protocol_combobox.set_active(0)
        # End populate protocols combobox

    def on_button_create_clicked(self, widget, data=None):
        model = widget.get_model()
        iter = widget.get_active_iter()
        protocol_title = model.get_value(iter, 0)
        icon = model.get_value(iter, 1)
        protocol = eval(model.get_value(iter, 2))
        self.account_show(protocol=protocol, icon=icon)

    def account_show(self, protocol=None, icon=None):
        if protocol is not None:
            new_account = True
        else:
            new_account = False
            protocol = dict([('name', self.account['protocol']), ('properties', self.protocols[self.account['protocol']])])

        vbox_account = self.ui.get_object('vbox_account')
        for child in vbox_account.get_children():
            child.destroy()
        vbox_details = self.ui.get_object('vbox_details')
        self.ui.get_object('vbox_details').show()
        self.ui.get_object('vbox_account').show()
        self.ui.get_object('frame_new_account').hide()
        label = self.ui.get_object('label_name')
        image_type = self.ui.get_object('image_type')
        label.set_label(protocol["properties"]["name"])
        if icon:
            image_type.set_from_pixbuf(icon)
        try:
          if not new_account:
              self.aw = eval(protocol["name"]).AccountWidget(self.account, self.ui)
          else:
              self.aw = eval(protocol["name"]).AccountWidget(None, self.ui)
          self.aw.show()
	except NameError:
          print ("%s not available", protocol["name"])
        vbox_account.pack_start(self.aw, False, False)
        vbox_account.show()
        if new_account:
            self.account = {}
            self.account["protocol"] = protocol["name"]
            #self.ui.get_object('vbox_create').show()
        self.aw.account = self.account
        self.populate_account_data()

    def populate_account_data(self):
        # set the default color based on default defined by the service module
        if self.protocols[self.account["protocol"]].has_key("color"):
            self.aw.ui.get_object("color").set_color(gtk.color_selection_palette_from_string(self.protocols[self.account["protocol"]]["color"])[0])
        try:
            for config in self.protocols[self.account["protocol"]]["config"]:
                #if config == "private:password": config = "password"
                is_private = config.startswith("private:")
                config = config.replace("private:", "")

                if isinstance (self.aw.ui.get_object(config), gtk.Entry):
                    value = self.account[config]

                    if is_private:
                        if self.account[config].startswith(":KEYRING:"):
                            try:
                                value = gnomekeyring.find_items_sync(
                                    gnomekeyring.ITEM_GENERIC_SECRET,
                                    {"id": str("%s/%s" % (self.account["_id"], config))})[0].secret
                            except gnomekeyring.NoMatchError:
                                value = None
                                self.aw.ui.get_object(config).modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("pink"))
                                self.aw.ui.get_object(config).connect("changed", self.on_edit_account)
                                continue

                    self.aw.ui.get_object(config).set_text(value)
                    self.aw.ui.get_object(config).connect("changed", self.on_edit_account)
 
                if isinstance (self.aw.ui.get_object(config), gtk.CheckButton):
                    self.aw.ui.get_object(config).set_active(self.account[config])
                    self.aw.ui.get_object(config).connect("toggled", self.on_edit_account)
                if isinstance (self.aw.ui.get_object(config), gtk.ColorButton):
                    self.aw.ui.get_object(config).set_color(gtk.color_selection_palette_from_string(self.account[config])[0])
                    self.aw.ui.get_object(config).connect("color-set", self.on_edit_account)
        except:
            pass

    def get_account_data(self):
        try:
            del self.account["_rev"]
        except:
            pass
        
        try:
            for value in self.aw.account:
                self.account[value] = self.aw.account[value]
        except:
            pass

        for config in self.protocols[self.account["protocol"]]["config"]:
            if not config.startswith("private:"):
                widget = self.aw.ui.get_object(config)
                value = [getattr(widget.props, p) for p in ["text", "active", "color"] if widget and hasattr(widget.props, p)]

                if value: 
                  if isinstance(value[0], gtk.gdk.Color):
                    self.account[config] = gtk.color_selection_palette_to_string(
                        gtk.color_selection_palette_from_string(value[0].to_string()))
                  else:
                    self.account[config] = value[0]
                else:
                    print "Could not identify preference:", config


        if "_id" not in self.account:
            #self.account["_id"] = uuid.uuid4().hex
            aId = "%s-%s" % (self.account["protocol"], self.account["username"])
            if self.account["protocol"] == "statusnet":
                aId = "%s-%s" % (aId, self.account["domain"])
    
            valid = string.ascii_letters + string.digits + "-"
            self.account["_id"] = "".join((x for x in aId if x in valid)).lower()
        
        for config in self.protocols[self.account["protocol"]]["config"]:
            if config.startswith("private:"):
                config = config.replace("private:", "")
                widget = self.aw.ui.get_object(config)
                if widget:
                    value = widget.get_text()
                    
                    if len(value) > 0:
                        self.account[config] = ":KEYRING:%s" % gnomekeyring.item_create_sync(
                            gnomekeyring.get_default_keyring_sync(),
                            gnomekeyring.ITEM_GENERIC_SECRET,
                            "Gwibber pref: %s/%s" % (self.account["_id"], config),
                            {"id": str("%s/%s" % (self.account["_id"], config))},
                            str(value), True)

    def on_accounts_dialog_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_accounts_tree_row_activated(self, widget, data=None):
        icon = None
        model, rows = widget.get_selection().get_selected_rows()
	if rows:
            for row in rows:
                iter = model.get_iter(row)
            self.account = eval(model.get_value(iter, 2))
            icon = model.get_value(iter, 1)
        self.ui.get_object('vbox_save').hide()
        self.ui.get_object('vbox_create').hide()
        self.account_show(icon=icon)

    def on_button_close_clicked(self, widget, data=None):
        self.gwibber_service.RefreshCreds()
        gtk.main_quit()  
