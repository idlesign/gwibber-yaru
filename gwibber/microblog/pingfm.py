
"""

Ping.fm interface for Gwibber
SegPhault (Ryan Paul) - 11/09/2008

"""
from . import can
import urllib2, urllib

PROTOCOL_INFO = {
  "name": "Ping.fm",
  "version": 0.1,
  
  "config": [
    "private:app_key",
    "send_enabled"
  ],

  "features": [
    can.SEND,
  ],
}

API_KEY = "7c3d2c111be8979ac236eecddf6679e7"

class Client:
  def __init__(self, acct):
    self.account = acct

  def send_enabled(self):
    return self.account["send_enabled"] and self.account["app_key"]

  def connect(self, url, data = None):
    data.update({"api_key": API_KEY, "user_app_key": self.account["private:app_key"]})
    urllib2.urlopen(urllib2.Request(url, urllib.urlencode(data))).read()

  def send(self, message):
    return self.connect("http://api.ping.fm/v1/user.post",
      {"post_method": "microblog", "body": message})
