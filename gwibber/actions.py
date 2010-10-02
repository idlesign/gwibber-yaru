import gtk, gwui, microblog, resources, util, json
from microblog.util.const import *
import gwibber.microblog.util
import mx.DateTime

from gettext import lgettext as _

class MessageAction:
  icon = None
  label = None

  @classmethod
  def get_icon_path(self, size=16, use_theme=True):
    return resources.icon(self.icon, size, use_theme)
    
  @classmethod
  def include(self, client, msg):
    return self.__name__ in client.model.services[msg["protocol"]]["features"]

  @classmethod
  def action(self, w, client, msg):
    pass

class reply(MessageAction):
  icon = "mail-reply-sender"
  label = _("_Reply")

  @classmethod
  def action(self, w, client, msg):
    client.reply(msg)
    
class thread(MessageAction):
  icon = "mail-reply-all"
  label = _("View reply t_hread")

  @classmethod
  def action(self, w, client, msg):
    tab_label = msg["original_title"] if msg.has_key("original_title") else msg["text"]
    client.add_transient_stream(msg.account, "thread",
        "message:/" + msg.gwibber_path, "Thread")

class retweet(MessageAction):
  icon = "mail-forward"
  label = _("R_etweet")

  @classmethod
  def action(self, w, client, msg):
    if "retweet" in client.model.services[msg["protocol"]]["features"]:
      text = RETWEET_FORMATS[client.model.settings["retweet_style"]]
      symbol = "RD" if msg["protocol"] == "identica" else "RT"
      text = text.format(text=msg["text"], nick=msg["sender"]["nick"], R=symbol)

      if not client.model.settings["global_retweet"]:
        client.message_target.set_target(msg, "repost")
        
      client.input.set_text(text)
      client.input.textview.grab_focus()
      buf = client.input.textview.get_buffer()
      buf.place_cursor(buf.get_end_iter())

class like(MessageAction):
  icon = "bookmark_add"
  label = _("_Like this message")

  @classmethod
  def action(self, w, client, msg):
    client.service.PerformOp(json.dumps({
      "account": msg["account"],
      "operation": "like",
      "args": {"message": msg},
      "transient": False,
    }))
    
    image = resources.get_ui_asset("gwibber.svg")
    expire_timeout = 5000
    n = gwibber.microblog.util.notify(_("Liked"), _("You have marked this message as liked."), image, expire_timeout)

class delete(MessageAction):
  icon = "gtk-delete"
  label = _("_Delete this message")

  @classmethod
  def action(self, w, client, msg):
    client.service.PerformOp(json.dumps({
      "account": msg["account"],
      "operation": "delete",
      "args": {"message": msg},
      "transient": False,
    }))

    image = resources.get_ui_asset("gwibber.svg")
    expire_timeout = 5000
    n = gwibber.microblog.util.notify(_("Deleted"), _("The message has been deleted."), image, expire_timeout)

  @classmethod
  def include(self, client, msg):
    if "delete" in client.model.services[msg["protocol"]]["features"]:
      if msg.get("sender", {}).get("is_me", 0):
        return True

class search(MessageAction):
  icon = "gtk-find"
  label = _("_Search for a query")

  @classmethod
  def action(self, w, client, query=None):
    pass

class read(MessageAction):
  icon = "mail-read"
  label = _("View _Message")

  @classmethod
  def action(self, w, client, msg):
    if msg.has_key("url"):
      util.load_url(msg["url"])
    elif msg.has_key("images"):
      util.load_url(msg["images"][0]["url"])

  @classmethod
  def include(self, client, msg):
    return "url" in msg

class user(MessageAction):
  icon = "face-monkey"
  label = _("View user _Profile")
  
  @classmethod
  def action(self, w, client, acct=None, name=None):
    client.add_stream({
      "name": name,
      "account": acct,
      "operation": "user_messages",
      "parameters": {"id": name, "count": 50},
    })

class menu(MessageAction):
  @classmethod
  def action(self, w, client, msg):
    client.on_message_action_menu(msg)

class tag(MessageAction):
  @classmethod
  def action(self, w, client, acct, query):
    client.add_stream({
      "name": "#%s" % query,
      "query": "#%s" % query,
    }, COUCH_TYPE_SEARCH)

class group(MessageAction):
  icon = "face-monkey"

  @classmethod
  def action(self, w, client, acct, query):
    client.add_transient_stream(acct, "group", query)
    print "Searching for group", query

class tomboy(MessageAction):
  icon = "tomboy"
  label = _("Save to _Tomboy")

  @classmethod
  def action(self, w, client, msg):
    util.create_tomboy_note(
      _("%(protocol_name)s message from %(sender)s at %(time)s\n\n%(message)s\n\nSource: %(url)s") % {
        "protocol_name": client.model.services[msg["protocol"]]["name"],
        "sender": msg["sender"]["name"],
        "time": mx.DateTime.DateTimeFromTicks(msg["time"]).localtime().strftime(),
        "message": msg["text"],
        "url": msg["url"]
    })

  @classmethod
  def include(self, client, msg):
    return gwibber.microblog.util.service_is_running("org.gnome.Tomboy")

MENU_ITEMS = [reply, retweet, read, user, like, delete, tomboy]
