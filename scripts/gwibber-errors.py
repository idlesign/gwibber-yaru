#!/usr/bin/env python

import dbus, time

bus = dbus.SessionBus()
obj = bus.get_object("com.Gwibber", "/com/gwibber/Messages")
messages = dbus.Interface(obj, "com.Gwibber")

for e in messages.get_errors():
  print e["type"]
  print "ERROR %s <%s:%s:%s>:\n%s" % (
      time.ctime(e["time"]),
      e["op"]["source"],
      e["op"]["protocol"],
      e["op"]["opname"],
      e["traceback"])
