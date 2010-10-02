from time import mktime

from pyyaru import pyyaru

import util
#from util import log, exceptions

util.log.logger.name = "Ya.ru"

APP_KEY = 'dfd2f087d37e46ceba2f04a1299506b4'

PROTOCOL_INFO = {
  "name": "Ya.ru",
  "version": 0.1,
  
  "config": [
    "username",
    "private:access_token",
    "color",
    "receive_enabled",
    "send_enabled",
  ],
 
  "authtype": "oauth2",
  "color": "#729FCF",

  "features": [
    "receive",
    "send",
  ],

  "default_streams": [
    "receive",
  ],
}


class Client:
    def __init__(self, acct):
        if not acct.has_key("access_token"):
            raise util.exceptions.GwibberServiceError("keyring")
        self.account = acct
        pyyaru.ACCESS_TOKEN = acct["access_token"]

    def __call__(self, opname, **args):
        print '%s method called' % opname
        return getattr(self, opname)(**args)

    def _common(self, entry):
        m = {}
        try:
            m['id'] = entry.id
            m['protocol'] = 'yaru'
            m['account'] = self.account['_id']
            m['time'] = mktime(entry.updated.timetuple())
            m['text'] = entry.content
            m['to_me'] = ('@%s' % self.account['username']) in entry.content
            m['html'] = util.linkify(entry.content)
            m['content'] = util.linkify(entry.content)
            m['url'] = entry.links['alternate']
        except: 
            util.log.logger.error('%s failure - %s', PROTOCOL_INFO['name'], entry)
            
        return m

    def _user(self, user):
        return {
            'name': user['name'],
            'nick': user['name'],
            'id': user['id'],
            'image': user['links']['userpic'],
            'url': user['uri'],
            'is_me': user['id'] == self.account['user_id'],
        }

    def _message(self, entry):
        message = self._common(entry)
        message['source'] = 'http://my.ya.ru'
        if entry.original is not None:
            message['source'] = entry.original
        message['sender'] = self._user(entry.author)
        return message

    def receive(self, count=util.COUNT, since=None):
        """Fetch friend status posts. Fall silently."""
        messages = []
        try:
            me = pyyaru.yaPerson('/me/').get()
            entries = me.friends_entries('status')
            for entry in entries.objects:
                message = self._message(entry)
                messages.append(message)
        except:
            pass
        
        return messages
    
    def send(self, message):
        """Post new status message."""
        me = pyyaru.yaPerson('/me/').get()
        me.set_status(message)
        return []