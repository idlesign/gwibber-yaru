#!/usr/bin/env python

import urllib, pycurl, json, StringIO
import traceback
from util import log
from util import exceptions

class CurlDownloader:
  def __init__(self, url, params=None, post=False, username=None, password=None):
    self.curl = pycurl.Curl()
  
    if params:
      if post:
        self.curl.setopt(pycurl.HTTPPOST, [(x, str(y)) for x,y in params.items()])
      else:
        url = "?".join((url, urllib.urlencode(params)))
    
    self.curl.setopt(pycurl.URL, str(url))
    
    if username and password:
      self.curl.setopt(pycurl.USERPWD, "%s:%s" % (username, password))

    self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
    self.curl.setopt(pycurl.MAXREDIRS, 5)
    self.curl.setopt(pycurl.TIMEOUT, 150)
    self.curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)

    self.content = StringIO.StringIO()
    self.curl.setopt(pycurl.WRITEFUNCTION, self.content.write)
    
    try:
      self.curl.perform()
    except:
      traceback.print_exc()
      log.logger.error("Failed to communicate with %s", str(url))
      #raise exceptions.GwibberProtocolError("network", str(url))
  
  def get_json(self):
    try:
      return json.loads(self.get_string())
    except ValueError as e:
      log.logger.error("Failed to parse the response, error was: %s", str(e))
      return str(e)

  def get_string(self):
    return self.content.getvalue()

Download = CurlDownloader


