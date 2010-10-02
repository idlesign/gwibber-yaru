#!/usr/bin/env python

from util.const import *
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord

class CouchMessageStorage:
  def __init__(self):
    self.messages = CouchDatabase(COUCH_DB_MESSAGES, create=True)

    if not self.messages.view_exists("sender", "messages"):
      viewfn = 'function(doc) { emit([doc.sender.nick, doc.account], doc); }'
      self.messages.add_view("sender", viewfn, None, "messages")

    if not self.messages.view_exists("message", "messages"):
      viewfn = 'function(doc) { emit([doc.id, doc.account, doc.operation], doc); }'
      self.messages.add_view("message", viewfn, None, "messages")

    if not self.messages.view_exists("maxid", "messages"):
      viewfn = 'function(doc) { emit([doc.account, doc.operation], doc.id); }'
      reducefn = 'function(key, value, rereduce) { return Math.max.apply(Math, value); }'
      self.messages.add_view("maxid", viewfn, reducefn, "messages")

    if not self.messages.view_exists("max_message_time", "messages"):
      viewfn = 'function(doc) { emit([doc.account, doc.operation], doc.time); }'
      reducefn = 'function(key, value, rereduce) { return Math.max.apply(Math, value); }'
      self.messages.add_view("max_message_time", viewfn, reducefn, "messages")

  def get_highest_id(self, acctid, opname):
    output = self.messages.execute_view("maxid", "messages")[[acctid, opname]]
    results = output[[acctid, opname]].rows
    if len(results) > 0: return results[0].value

  def get_last_message_time(self, acctid, opname):
    output = self.messages.execute_view("max_message_time", "messages")[[acctid, opname]]
    results = output[[acctid, opname]].rows
    if len(results) > 0: return results[0].value

MessageStore = CouchMessageStorage
