import gettext
import gtk
import webkit
import gnomekeyring
import urlparse
import string
from gettext import gettext as _

from pyyaru import pyyaru

import gwibber.microblog
from gwibber.microblog.yaru import APP_KEY

if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('gwibber', 'UTF-8')
    
gettext.textdomain('gwibber')

gtk.gdk.threads_init()

class AccountWidget(gtk.VBox):
    """AccountWidget: A widget that provides a user interface 
    for configuring Ya.ru accounts in Gwibber.
      
    """
    def __init__(self, account=None, dialog=None):
        """Creates account configuration panel for configuring Ya.ru accounts"""
        gtk.VBox.__init__(self, False, 20)
        self.ui = gtk.Builder()
        self.ui.set_translation_domain ("gwibber")
        self.ui.add_from_file (gwibber.resources.get_ui_asset("gwibber-accounts-yaru.ui"))
        self.ui.connect_signals(self)
        self.vbox_settings = self.ui.get_object("vbox_settings")
        self.pack_start(self.vbox_settings, False, False)
        self.show_all()
        
        self.account = account or {}
        self.dialog = dialog
        has_secret_key = True
        if self.account.has_key("id"):
            try:
                value = gnomekeyring.find_items_sync(gnomekeyring.ITEM_GENERIC_SECRET, {"id": str("%s/%s" % (self.account["id"], "access_token"))})[0].secret
            except gnomekeyring.NoMatchError:
                has_secret_key = False
        
        try:
            if self.account.has_key("access_token") and self.account.has_key("username") and has_secret_key:
                self.ui.get_object("hbox_yaru_auth").hide()
                self.ui.get_object("fb_auth_done_label").set_label(_("%s has been authorized by Ya.ru") % self.account["username"])
                self.ui.get_object("hbox_yaru_auth_done").show()
            else:
                self.ui.get_object("hbox_yaru_auth_done").hide()
                self.ui.get_object("yaru_auth_button").modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
                if self.dialog:
                    self.dialog.get_object('vbox_create').hide()
        except:
            self.ui.get_object("hbox_yaru_auth_done").hide()
            if self.dialog:
                self.dialog.get_object("vbox_create").hide()


    def on_yaru_auth_clicked(self, widget, data=None):
        """Event bound to auth button click."""
        self.winsize = self.window.get_size()
        
        web = webkit.WebView()
        web.get_settings().set_property("enable-plugins", False)
        web.load_html_string(_("<p>Please wait...</p>"), "file:///")
        
        url = "https://oauth.yandex.ru/authorize?client_id=%s&response_type=token" % APP_KEY
        
        web.open(url)
        web.set_size_request(650, 500)
        web.connect("load-finished", self.on_yaru_load_finished)
        
        scroll = gtk.ScrolledWindow()
        scroll.add(web)
        
        self.pack_start(scroll, True, True, 0)
        self.show_all()
        
        self.ui.get_object("vbox1").hide()
        self.ui.get_object("expander1").hide()
    
    def on_yaru_load_finished(self, web=None, title=None, data=None):
        url = web.get_main_frame().get_uri()
        
        if url.find('#') > -1:
            data = urlparse.parse_qs(url.split("#", 1)[1])
            
            if 'refresh_token' in data and 'access_token' in data:
                # token granted
                try:
                    pyyaru.ACCESS_TOKEN = data['access_token'][0]
                    my_profile = pyyaru.yaPerson('/me/').get()
                    
                    self.account["access_token"] = data['access_token'][0]
                    self.account["username"] = my_profile.name
                    self.account["user_id"] = my_profile.id
                    
                    self.ui.get_object("hbox_yaru_auth").hide()
                    self.ui.get_object("fb_auth_done_label").set_label(_("%s has been authorized by Ya.ru") % str(self.account["username"]))
                    self.ui.get_object("hbox_yaru_auth_done").show()
                    if self.dialog and self.account.has_key("id"):
                      self.dialog.get_object("vbox_save").show()
                    elif self.dialog:
                      self.dialog.get_object("vbox_create").show()
                except:
                    pass
                  
                web.hide()
                self.window.resize(*self.winsize)
                self.ui.get_object("vbox1").show()
                self.ui.get_object("expander1").show()
              
            if 'error' in data:
                # no token
                d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, _("Authorization failed. Please try again."))
                if d.run():
                    d.destroy()
                
                web.hide()
                self.window.resize(*self.winsize)
