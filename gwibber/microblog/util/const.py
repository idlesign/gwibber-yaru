
from os.path import join, isdir, realpath
from os import mkdir

import xdg.BaseDirectory

CACHE_DIR = realpath(join(xdg.BaseDirectory.xdg_cache_home, "gwibber"))
if not isdir(CACHE_DIR):
  mkdir(CACHE_DIR)

from os import environ
if environ.has_key("FB_APP_KEY"):
  FB_APP_KEY = environ["FB_APP_KEY"]
else:
  FB_APP_KEY = "71b85c6d8cb5bbb9f1a3f8bbdcdd4b05"

TWITTER_OAUTH_KEY = "VDOuA5qCJ1XhjaSa4pl76g"
TWITTER_OAUTH_SECRET = "BqHlB8sMz5FhZmmFimwgiIdB0RiBr72Y0bio49IVJM"

# Gwibber
MAX_MESSAGE_LENGTH = 140

DEFAULT_SETTINGS = {
  "interval": 5,
  "view": "SingleStreamUi",
  "streams": [{"stream": "messages", "account": None}],
  "show_notifications": True,
  "notify_mentions_only": True,
  "presence_check": True,
  "show_fullname": True,
  "shorten_urls": True,
  "urlshorter": "is.gd",
  "reply_append_colon": True,
  "retweet_style": "recycle",
  "global_retweet": False,
  "theme": "default",
}

LOCAL_SETTINGS = {
  "window_size":  (500, 580),
  "window_position": (0, 24),
  "window_splitter": 450,
  "sidebar_splitter": 40,
}

RETWEET_FORMATS = {
  "via": "{text} (via @{nick})",
  "RT": "RT @{nick}: {text}",
  "RD": "RD @{nick}: {text}",
  "/via": "{text} /via @{nick}",
  "/by": "{text} /by @{nick}",
  "recycle": u"\u267a @{nick}: {text}",
  "service": "{R} @{nick}: {text}",
}

VERSION_NUMBER = "2.30.2"
GCONF_CLIENT_DIR = "/apps/gwibber/client/"

BUG_URL = "https://bugs.launchpad.net/gwibber/+filebug"
QUESTIONS_URL = "https://answers.launchpad.net/gwibber"
TRANSLATE_URL = "https://translations.launchpad.net/gwibber"

# Setup some Network Manager stuff to query for online state
NM_DBUS_SERVICE = "org.freedesktop.NetworkManager"
NM_DBUS_OBJECT_PATH = "/org/freedesktop/NetworkManager"
NM_DBUS_INTERFACE = "org.freedesktop.NetworkManager"
NM_STATE_UNKNOWN = 0
NM_STATE_ASLEEP = 1
NM_STATE_CONNECTING = 2
NM_STATE_CONNECTED = 3
NM_STATE_DISCONNECTED = 4

# Databases
COUCH_DB_MESSAGES = "gwibber_messages"
COUCH_DB_ACCOUNTS = "gwibber_accounts"
COUCH_DB_SETTINGS = "gwibber_preferences"

# Record types
COUCH_TYPE_ACCOUNT = "http://gwibber.com/couch/account"
COUCH_TYPE_MESSAGE = "http://gwibber.com/couch/message"
COUCH_TYPE_STREAM = "http://gwibber.com/couch/stream"
COUCH_TYPE_SEARCH = "http://gwibber.com/couch/search"
COUCH_TYPE_CONFIG = "http://gwibber.com/couch/settings"

# Records
COUCH_RECORD_SETTINGS = "settings"

# Views
COUCH_VIEW_MESSAGES = {
  "message": {
    "map": "function(doc) { emit([doc.id, doc.account, doc.operation], null); }"
  },
  "home": {
    "map": "function(doc) { if(!doc.transient) emit([doc.time], null); }"
  },
  "maxid": {
    "map": "function(doc) { emit([doc.transient ? doc.transient : doc.account, doc.operation], doc.id); }",
    "reduce": "function(key, value, rereduce) { return Math.max.apply(Math, value); }"
  },
  "sender": {
    "map": "function(doc) { emit([doc.sender.nick, doc.account], null); }"
  },
  "account_stream_time": {
    "map": "function(doc) { emit([doc.account, doc.stream, doc.time], null); }"
  },
  "account_time": {
    "map": "function(doc) { if(!doc.transient) emit([doc.account, doc.time], null); }"
  },
  "stream_time": {
    "map": "function(doc) { if(!doc.transient) emit([doc.stream, doc.time], null); }"
  },
  "transient_time": {
    "map": "function(doc) { if(doc.transient) emit([doc.transient, doc.time], null); }"
  },
  "search_transient_time": {
    "map": "function(doc) { if(doc.stream == \"search\") emit([doc.transient, doc.time], null); }"
  },
  "search_time": {
    "map": "function(doc) { if(doc.stream == \"search\") emit(doc.time, null); }"
  },
  "user_protocol_time": {
    "map": """function(doc) {
      if(doc.transient) emit([doc.sender.nick, doc.protocol, doc.time], null);
      if(doc.sender.is_me && doc.reply) emit([doc.reply.nick, doc.protocol, doc.time], null);
    }"""
  },
  "mine_account": {
    "map": "function(doc) { if(doc.sender.is_me) emit([doc.account, doc.time], null); }",
  },
  "mine": {
    "map": "function(doc) { if(doc.sender.is_me) emit([doc.time], null); }",
  },
  "max_message_time": {
      "map": "function(doc) { emit([doc.account, doc.operation], doc.time); }",
      "reduce": "function(key, value, rereduce) { return Math.max.apply(Math, value); }"
  },
}

GWIBBER_OPERATIONS = """
{
  "delete": {
    "account_tree": false,
    "dynamic": false,
    "enabled": null,
    "first_only": false,
    "function": null,
    "return_value": false,
    "search": false,
    "stream": null,
    "transient": false
  },

  "favorites": {
    "account_tree": true,
    "dynamic": true,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "favorites",
    "transient": false
  },

  "group": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "group",
    "transient": true
  },

  "like": {
    "account_tree": false,
    "dynamic": false,
    "enabled": null,
    "first_only": false,
    "function": null,
    "return_value": false,
    "search": false,
    "stream": null,
    "transient": false
  },

  "private": {
    "account_tree": true,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "private",
    "transient": false
  },
  
  "public": {
    "account_tree": true,
    "dynamic": true,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "public",
    "transient": false
  },
 
  "receive": {
    "account_tree": true,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "messages",
    "transient": false
  },

  "images": {
    "account_tree": true,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "images",
    "transient": false 
  },

  "reply": {
    "account_tree": false,
    "dynamic": false,
    "enabled": null,
    "first_only": true,
    "function": "send",
    "return_value": false,
    "search": false,
    "stream": null,
    "transient": false
  },

  "responses": {
    "account_tree": true,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "replies",
    "transient": false
  },

  "retweet": {
    "account_tree": false,
    "dynamic": false,
    "enabled": null,
    "first_only": false,
    "function": null,
    "return_value": false,
    "search": false,
    "stream": null,
    "transient": false
  },
 
  "search": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "search",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": true,
    "stream": "search",
    "transient": true
  },
  
  "search_url": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "search",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": true,
    "stream": "search",
    "transient": true
  },

  "send": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "send",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "messages",
    "transient": false
  },

  "send_thread": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "send",
    "first_only": false,
    "function": null,
    "return_value": false,
    "search": false,
    "stream": null,
    "transient": false
  },
  
  "tag": {
    "account_tree": false,
    "dynamic": false,
    "enabled": null,
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": null,
    "transient": false
  },

  "thread": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "thread",
    "transient": true
  },
  
  "user_messages": {
    "account_tree": false,
    "dynamic": false,
    "enabled": "receive",
    "first_only": false,
    "function": null,
    "return_value": true,
    "search": false,
    "stream": "user",
    "transient": true
  }
}
"""
