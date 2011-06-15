import gettext
import gtk
import webkit
import gnomekeyring
import urlparse
import pango

from gettext import gettext as _

from pyyaru import pyyaru

from gwibber.microblog.util import resources

if hasattr(gettext, "bind_textdomain_codeset"):
    gettext.bind_textdomain_codeset("gwibber", "UTF-8")

gettext.textdomain("gwibber")

gtk.gdk.threads_init()


class AccountWidget(gtk.VBox):
    """AccountWidget: A widget that provides a user interface
    for configuring Ya.ru accounts in Gwibber.

    """

    def __init__(self, account=None, dialog=None):
        """Creates account configuration panel for configuring Ya.ru accounts."""

        gtk.VBox.__init__(self, False, 20)
        self.ui = gtk.Builder()
        self.ui.set_translation_domain("gwibber")
        self.ui.add_from_file(resources.get_ui_asset("gwibber-accounts-yaru.ui"))
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
            if self.account.has_key("access_token") and self.account.has_key("username") and has_secret_key and not self.dialog.condition:
                self.ui.get_object("hbox_yaru_auth").hide()
                self.ui.get_object("yaru_auth_done_label").set_label(_("%s has been authorized by Ya.ru") % self.account["username"])
                self.ui.get_object("hbox_yaru_auth_done").show()
            else:
                self.ui.get_object("hbox_yaru_auth_done").hide()
                if self.dialog.ui:
                    self.dialog.ui.get_object("vbox_create").hide()
        except:
            self.ui.get_object("hbox_yaru_auth_done").hide()
            if self.dialog.ui:
                self.dialog.ui.get_object("vbox_create").hide()


    def on_yaru_auth_clicked(self, widget, data=None):
        """Event bound to auth button click."""

        self.winsize = self.window.get_size()

        web = webkit.WebView()
        web.get_settings().set_property("enable-plugins", False)
        web.load_html_string(_("<p>Please wait...</p>"), "file:///")

        url = "https://oauth.yandex.ru/authorize?client_id=dfd2f087d37e46ceba2f04a1299506b4&response_type=token&display=popup"

        web.load_uri(url)
        web.set_size_request(550, 400)
        web.connect("title-changed", self.on_yaru_auth_title_change)

        self.scroll = gtk.ScrolledWindow()
        self.scroll.add(web)

        self.pack_start(self.scroll, True, True, 0)
        self.show_all()

        self.ui.get_object("vbox1").hide()
        self.ui.get_object("vbox_advanced").hide()
        self.dialog.infobar.set_message_type(gtk.MESSAGE_INFO)


    def on_yaru_auth_title_change(self, web=None, title=None, data=None):

        saved = False

        url = web.get_main_frame().get_uri()

        if url.find('#') > -1:
            data = urlparse.parse_qs(url.split("#", 1)[1])

            if hasattr(self.dialog, "infobar_content_area"):
                for child in self.dialog.infobar_content_area.get_children(): child.destroy()

            self.dialog.infobar_content_area = self.dialog.infobar.get_content_area()
            self.dialog.infobar_content_area.show()
            message_label = gtk.Label(_("Verifying"))
            message_label.set_use_markup(True)
            message_label.set_ellipsize(pango.ELLIPSIZE_END)
            self.dialog.infobar_content_area.add(message_label)

            if 'access_token' in data:
                # token granted

                self.dialog.infobar.show()
                self.dialog.infobar.show_all()
                self.scroll.hide()

                self.ui.get_object("vbox1").show()
                self.ui.get_object("vbox_advanced").show()

                pyyaru.ACCESS_TOKEN = data["access_token"][0]
                my_profile = pyyaru.yaPerson("/me/").get()

                self.account["access_token"] = data["access_token"][0]
                self.account["username"] = my_profile.name
                self.account["user_id"] = my_profile.id

                saved = self.dialog.on_edit_account_save()

                if saved:
                    message_label.set_text(_("Successful"))
                    self.dialog.infobar.set_message_type(gtk.MESSAGE_INFO)

                self.ui.get_object("hbox_yaru_auth").hide()
                self.ui.get_object("yaru_auth_done_label").set_label(_("%s has been authorized by Ya.ru") % str(self.account["username"]))
                self.ui.get_object("hbox_yaru_auth_done").show()

                if self.dialog.ui and self.account.has_key("id") and not saved:
                    self.dialog.ui.get_object("vbox_save").show()
                elif self.dialog.ui and not saved:
                    self.dialog.ui.get_object("vbox_create").show()

            self.window.resize(*self.winsize)

            if 'error' in data:
                # no token

                web.hide()
                self.dialog.infobar.set_message_type(gtk.MESSAGE_ERROR)
                message_label.set_text(_("Authorization failed. Please try again."))
                self.dialog.infobar.show_all()

                self.ui.get_object("vbox1").show()
                self.ui.get_object("vbox_advanced").show()
                self.window.resize(*self.winsize)
