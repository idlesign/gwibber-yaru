import re, network, util
from gettext import lgettext as _
from util import log
from util import exceptions
log.logger.name = "StatusNet"

PROTOCOL_INFO = {
  "name": "StatusNet",
  "version": 1.0,
  
  "config": [
    "private:password",
    "username",
    "domain",
    "color",
    "receive_enabled",
    "send_enabled",
  ],

  "authtype": "login",
  "color": "#4E9A06",

  "features": [
    "send",
    "receive",
    "search",
    "tag",
    "reply",
    "responses",
    "private",
    "public",
    "delete",
    "retweet",
    "like",
    "send_thread",
    "user_messages",
    "sinceid",
  ],

  "default_streams": [
    "receive",
    "responses",
    "private",
  ],
}

class Client:
  def __init__(self, acct):
    self.account = acct

    pref = "" if self.account["domain"].startswith("http") else "https://"
    self.url_prefix = pref + self.account["domain"]

  def _common(self, data):
    m = {}
    m["id"] = str(data["id"])
    m["protocol"] = "statusnet"
    m["account"] = self.account["_id"]
    m["time"] = util.parsetime(data["created_at"])
    m["source"] = data.get("source", False)
    m["text"] = data["text"]
    m["to_me"] = ("@%s" % self.account["username"]) in data["text"]

    m["html"] = util.linkify(m["text"],
      ((util.PARSE_HASH, '#<a class="hash" href="%s#search?q=\\1">\\1</a>' % self.url_prefix),
      (util.PARSE_NICK, '@<a class="nick" href="%s/\\1">\\1</a>' % self.url_prefix)))

    m["content"] = util.linkify(m["text"],
      ((util.PARSE_HASH, '#<a class="hash" href="gwibber:/tag?acct=%s&query=\\1">\\1</a>' % m["account"]),
      (util.PARSE_NICK, '@<a class="nick" href="gwibber:/user?acct=%s&name=\\1">\\1</a>' % m["account"])))

    if data.get("attachments", 0):
      m["images"] = []
      for a in data["attachments"]:
        mime = a.get("mimetype", "")
        if mime and mime.startswith("image") and a.get("url", 0):
          m["images"].append({"src": a["url"], "url": a["url"]})

    return m

  def _message(self, data):
    m = self._common(data)
    
    if data.get("in_reply_to_status_id", 0) and data.get("in_reply_to_screen_name", 0):
      m["reply"] = {}
      m["reply"]["id"] = data["in_reply_to_status_id"]
      m["reply"]["nick"] = data["in_reply_to_screen_name"]
      m["reply"]["url"] = "/".join((self.url_prefix, "notice", str(m["reply"]["id"])))

    user = data.get("user", data.get("sender", 0))
    
    m["sender"] = {}
    m["sender"]["name"] = user["name"]
    m["sender"]["nick"] = user["screen_name"]
    m["sender"]["id"] = user["id"]
    m["sender"]["location"] = user["location"]
    m["sender"]["followers"] = user["followers_count"]
    m["sender"]["image"] = user["profile_image_url"]
    m["sender"]["url"] = "/".join((self.url_prefix, m["sender"]["nick"]))
    m["sender"]["is_me"] = m["sender"]["nick"] == self.account["username"]
    m["url"] = "/".join((self.url_prefix, "notice", m["id"]))
    return m

  def _private(self, data):
    m = self._message(data)
    m["private"] = True
    return m

  def _result(self, data):
    m = self._common(data)
    
    if data["to_user_id"]:
      m["reply"] = {}
      m["reply"]["id"] = data["to_user_id"]
      m["reply"]["nick"] = data["to_user"]

    m["sender"] = {}
    m["sender"]["nick"] = data["from_user"]
    m["sender"]["id"] = data["from_user_id"]
    m["sender"]["image"] = data["profile_image_url"]
    m["sender"]["url"] = "/".join((self.url_prefix, m["sender"]["nick"]))
    m["url"] = "/".join((self.url_prefix, "notice", m["id"]))
    return m

  def _get(self, path, parse="message", post=False, single=False, **args):
    url = "/".join((self.url_prefix, "api", path))
    data = network.Download(url, util.compact(args), post,
        self.account["username"], self.account["password"]).get_json()

    if isinstance(data, dict) and data.get("error", 0):
      if "authenticate" in data["error"]:
        print data["error"], type(data["error"])
        raise exceptions.GwibberProtocolError("auth", self.account["protocol"], self.account["username"], data["error"])

    if single: return [getattr(self, "_%s" % parse)(data)]
    if parse: return [getattr(self, "_%s" % parse)(m) for m in data]
    else: return []

  def _search(self, **args):
    data = network.Download("%s/api/search.json" % self.url_prefix, util.compact(args))
    data = data.get_json()["results"]
    return [self._result(m) for m in data]

  def __call__(self, opname, **args):
    return getattr(self, opname)(**args)
  
  def receive(self, count=util.COUNT, since=None):
    return self._get("statuses/friends_timeline.json", count=count, since_id=since)

  def user_messages(self, id=None, count=util.COUNT, since=None):
    return self._get("statuses/user_timeline.json", id=id, count=count, since_id=since)

  def responses(self, count=util.COUNT, since=None):
    return self._get("statuses/mentions.json", count=count, since_id=since)

  def private(self, count=util.COUNT, since=None):
    return self._get("direct_messages.json", "private", count=count, since_id=since)

  def public(self):
    return self._get("statuses/public_timeline.json")

  def search(self, query, count=util.COUNT, since=None):
    return self._search(q=query, rpp=count, since_id=since)

  def tag(self, query, count=util.COUNT, since=None):
    return self._search(q="#%s" % query, count=count, since_id=since)

  def delete(self, message):
    self._get("statuses/destroy/%s.json" % message["id"], None, post=True, do=1)
    return []

  def like(self, message):
    self._get("favorites/create/%s.json" % message["id"], None, post=True, do=1)
    return []

  def send(self, message):
    return self._get("statuses/update.json", post=True, single=True,
        status=message, source="Gwibber")

  def send_thread(self, message, target):
    return self._get("statuses/update.json", post=True, single=True,
        status=message, source="gwibber", in_reply_to_status_id=target["id"])
