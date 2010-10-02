
"""

Jaiku interface for Gwibber
SegPhault (Ryan Paul) - 01/05/2008

"""

from . import support
import urllib2, urllib, re, simplejson, urlparse

PROTOCOL_INFO = {
  "name": "Jaiku",
  "version": 0.3,
  
  "config": [
    "private:password",
    "username",
    "message_color",
    "comment_color",
    "receive_enabled",
    "send_enabled"
  ],

  "features": [
    "send",
    "receive",
    "reply",
    "thread",
    "send_thread",
  ],
}

NONCE_PARSE = re.compile('.*_nonce" value="([^"]+)".*', re.M | re.S)
LINK_MARKUP_PARSE = re.compile("\[([^\]]+)\]\(([^)]+)\)")

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    if "id" in data: self.id = data["id"]
    self.sender = "%s %s" % (data["user"]["first_name"], data["user"]["last_name"])
    self.sender_nick = data["user"]["nick"]
    self.sender_id = data["user"]["nick"]

    # Jaiku's timestamp format is lousy
    d, t = data["created_at"].split("T")
    self.time = support.parse_time(d + t.replace("-", ":"))

    self.text = ""
    if "title" in data:
      self.text = data["title"]
      #self.html_string = LINK_MARKUP_PARSE.sub('<a href="\\2">\\1</a>', self.text.replace(
      #  "&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    self.image = data["user"]["avatar"]
    self.bgcolor = "message_color"
    self.url = data["url"]
    self.profile_url = "http://%s.jaiku.com" % data["user"]["nick"]
    if "icon" in data and data["icon"] != "": self.icon = data["icon"]
    self.can_thread = True
    self.is_reply = (re.compile("@%s[\W]+|@%s$" % (self.username, self.username)).search(self.text) != None) or \
      (urlparse.urlparse(self.url)[1].split(".")[0].strip() == self.username and \
        self.sender_nick != self.username)

class Comment(Message):
  def __init__(self, client, data):
    Message.__init__(self, client, data)
    self.text = data["content"]
    self.bgcolor = "comment_color"
    self.is_comment = True

    self.text = data["content"]
    #self.html_string = support.LINK_PARSE.sub('<a href="\\1">\\1</a>', LINK_MARKUP_PARSE.sub('<a href="\\2">\\1</a>', self.text.replace(
    #  "&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")))

    if "entry_title" in data:
      self.original_title = data["entry_title"]
      self.title = "<small>Comment by</small> %s <small>on %s</small>" % (
        self.sender, support.truncate(data["entry_title"],
          client.account["comment_title_length"] or 20))

    if "comment_id" in data:
      self.id = data["comment_id"]
    else: self.id = data["id"]

class Client:
  def __init__(self, acct):
    self.account = acct

  def send_enabled(self):
    return self.account["send_enabled"] and \
      self.account["username"] != None and \
      self.account["private:password"] != None

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["username"] != None and \
      self.account["private:password"] != None

  def get_messages(self):
    return simplejson.loads(urllib2.urlopen(urllib2.Request(
      "http://%s.jaiku.com/contacts/feed/json" % self.account["username"],
        urllib.urlencode({"user": self.account["username"],
          "personal_key":self.account["private:password"]}))).read())

  def get_thread_data(self, msg):
    return simplejson.loads(urllib2.urlopen(urllib2.Request(
      "%s/json" % ("#" in msg.url and msg.url.split("#")[0] or msg.url),
        urllib.urlencode({"user": self.account["username"],
          "personal_key":self.account["private:password"]}))).read())

  def thread(self, msg):
    thread_content = self.get_thread_data(msg)
    yield Message(self, thread_content)
    for data in thread_content["comments"]:
      yield Comment(self, data)

  def receive(self):
    for data in self.get_messages()["stream"]:
      if "id" in data: yield Message(self, data)
      else: yield Comment(self, data)

  def send_thread(self, message, target):
    print urllib2.urlopen(urllib2.Request("http://api.jaiku.com/json",
      urllib.urlencode({
        "method": "entry_add_comment",
        "user": self.account["username"],
        "personal_key":self.account["private:password"],
        "stream": "stream/%s@jaiku.com/comments" % self.account["username"],
        "entry": "stream/%s@jaiku.com/presence/%s" % (target.sender_nick, target.id),
        "nick": "%s@jaiku.com" % self.account["username"],
        "content": message
      }))).read()

  def send(self, message):
    urllib2.urlopen(urllib2.Request(
      "http://api.jaiku.com/json", urllib.urlencode({"user": self.account["username"],
      "personal_key":self.account["private:password"],
      "message": message, "method": "presence.send"}))).read()

