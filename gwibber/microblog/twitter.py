import network, util, htmllib, re
import gnomekeyring
from oauth import oauth
from util import log, exceptions
from gettext import lgettext as _
log.logger.name = "Twitter"

PROTOCOL_INFO = {
  "name": "Twitter",
  "version": "1.0",
  
  "config": [
    "private:secret_token",
    "access_token",
    "username",
    "color",
    "receive_enabled",
    "send_enabled",
  ],
 
  "authtype": "oauth1a",
  "color": "#729FCF",

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

URL_PREFIX = "https://twitter.com"
API_PREFIX = "https://api.twitter.com/1"

def unescape(s):
  p = htmllib.HTMLParser(None)
  p.save_bgn()
  p.feed(s)
  return p.save_end()

class Client:
  def __init__(self, acct):
    if not acct.has_key("access_token") and not acct.has_key("secret_token"):
      raise exceptions.GwibberProtocolError("keyring")
    if acct.has_key("secret_token") and acct.has_key("password"): acct.pop("password")
    self.account = acct
    self.sigmethod = oauth.OAuthSignatureMethod_HMAC_SHA1()
    self.consumer = oauth.OAuthConsumer(*util.resources.get_twitter_keys())
    self.token = oauth.OAuthToken(acct["access_token"], acct["secret_token"])

  def _common(self, data):
    m = {}; 
    try:
      m["id"] = str(data["id"])
      m["protocol"] = "twitter"
      m["account"] = self.account["_id"]
      m["time"] = util.parsetime(data["created_at"])
      m["text"] = unescape(data["text"])
      m["to_me"] = ("@%s" % self.account["username"]) in data["text"]

      m["html"] = util.linkify(data["text"],
        ((util.PARSE_HASH, '#<a class="hash" href="%s#search?q=\\1">\\1</a>' % URL_PREFIX),
        (util.PARSE_NICK, '@<a class="nick" href="%s/\\1">\\1</a>' % URL_PREFIX)), escape=False)

      m["content"] = util.linkify(data["text"],
        ((util.PARSE_HASH, '#<a class="hash" href="gwibber:/tag?acct=%s&query=\\1">\\1</a>' % m["account"]),
        (util.PARSE_NICK, '@<a class="nick" href="gwibber:/user?acct=%s&name=\\1">\\1</a>' % m["account"])), escape=False)
    except: 
      log.logger.error("%s failure - %s", PROTOCOL_INFO["name"], data)
 
    return m

  def _message(self, data):
    if type(data) == type(None):
      return []

    m = self._common(data)
    m["source"] = data.get("source", False)
    
    if "in_reply_to_status_id" in data and data["in_reply_to_status_id"]:
      m["reply"] = {}
      m["reply"]["id"] = data["in_reply_to_status_id"]
      m["reply"]["nick"] = data["in_reply_to_screen_name"]
      m["reply"]["url"] = "/".join((URL_PREFIX, m["reply"]["nick"], "statuses", str(m["reply"]["id"])))

    user = data["user"] if "user" in data else data["sender"]
    
    m["sender"] = {}
    m["sender"]["name"] = user["name"]
    m["sender"]["nick"] = user["screen_name"]
    m["sender"]["id"] = user["id"]
    m["sender"]["location"] = user["location"]
    m["sender"]["followers"] = user["followers_count"]
    m["sender"]["image"] = user["profile_image_url"]
    m["sender"]["url"] = "/".join((URL_PREFIX, m["sender"]["nick"]))
    m["sender"]["is_me"] = m["sender"]["nick"] == self.account["username"]
    m["url"] = "/".join((m["sender"]["url"], "statuses", str(m["id"])))

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
    m["sender"]["url"] = "/".join((URL_PREFIX, m["sender"]["nick"]))
    m["sender"]["is_me"] = m["sender"]["nick"] == self.account["username"]
    m["url"] = "/".join((m["sender"]["url"], "statuses", str(m["id"])))
    return m

  def _get(self, path, parse="message", post=False, single=False, **args):
    url = "/".join((API_PREFIX, path))

    request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, self.token,
        http_method=post and "POST" or "GET", http_url=url, parameters=util.compact(args))
    request.sign_request(self.sigmethod, self.consumer, self.token)
    
    if post:
      data = network.Download(request.to_url(), util.compact(args), post).get_json()
    else:
      data = network.Download(request.to_url(), None, post).get_json()

    if isinstance(data, dict) and data.get("errors", 0):
      if "authenticate" in data["errors"][0]["message"]:
        raise exceptions.GwibberProtocolError("auth",
            self.account["protocol"], self.account["username"], data["errors"][0]["message"])
      else:
        for error in data["errors"]:
          log.logger.info("Twitter failure - %s", error["message"])
        return []
    elif isinstance(data, dict) and data.get("error", 0):
      log.logger.error("%s failure - %s", PROTOCOL_INFO["name"], data["error"])
      return []
    elif isinstance(data, str):
      log.logger.error("%s unexpected result - %s", PROTOCOL_INFO["name"], data)
      return []
    
    if single: return [getattr(self, "_%s" % parse)(data)]
    if parse: return [getattr(self, "_%s" % parse)(m) for m in data]
    else: return []

  def _search(self, **args):
    data = network.Download("http://search.twitter.com/search.json", util.compact(args))
    data = data.get_json()["results"]
    return [self._result(m) for m in data]

  def __call__(self, opname, **args):
    return getattr(self, opname)(**args)
  
  def receive(self, count=util.COUNT, since=None):
    return self._get("statuses/home_timeline.json", count=count, since_id=since)

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
    return self._get("statuses/destroy/%s.json" % message["id"], None, post=True, do=1)

  def like(self, message):
    return self._get("favorites/create/%s.json" % message["id"], None, post=True, do=1)

  def send(self, message):
    return self._get("statuses/update.json", post=True, single=True,
        status=message)
  
  def send_thread(self, message, target):
    return self._get("statuses/update.json", post=True, single=True,
        status=message, in_reply_to_status_id=target["id"])
