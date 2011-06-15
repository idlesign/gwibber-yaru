from time import mktime
from urllib import quote

from pyyaru import pyyaru

from gwibber.microblog.util import exceptions, linkify, log, getbus, COUNT

log.logger.name = "yaru"

APP_KEY = "dfd2f087d37e46ceba2f04a1299506b4"

PROTOCOL_INFO = {
    "name": "Ya.ru",
    "version": "0.4",

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
        "send",
        "receive",
        "delete",
        "user_messages",
        ],

    "default_streams": [
        "receive",
        ],
    }

class Client:
    def __init__(self, acct):
        log.logger.debug('init')
        self.service = getbus("Service")

        if not acct.has_key("access_token"):
            raise exceptions.GwibberServiceError("keyring")
        self.account = acct

        pyyaru.ACCESS_TOKEN = acct["access_token"]

    def __call__(self, opname, **args):
        log.logger.debug('%s method called' % opname)
        return getattr(self, opname)(**args)

    def _common(self, entry):
        m = {}

        try:
            m['mid'] = entry.id
            m['service'] = 'yaru'
            m['account'] = self.account['id']
            m['time'] = mktime(entry.updated.timetuple())
            m['text'] = entry.content
            m['to_me'] = ('@%s' % self.account['username']) in entry.content
            m['html'] = linkify(entry.content)
            m['content'] = linkify(entry.content)
            m['url'] = entry.links['alternate']
        except:
            log.logger.error('%s failure - %s', PROTOCOL_INFO['name'], entry)

        return m

    def _user(self, user):
        if isinstance(user, pyyaru.yaPerson):
            url = user['links']['www']
        else:
            url = user['uri']

        return {
            'name': user['name'],
            'nick': user['name'],
            'id': user['id'],
            'image': user['links']['userpic'],
            'url': url,
            'is_me': user['id'] == self.account['user_id'],
            }


    def _message(self, entry, sender=None):
        message = self._common(entry)
        message['source'] = 'http://my.ya.ru'
        if entry.original is not None:
            message['source'] = entry.original

        if sender is not None:
            message['sender'] = sender
        else:
            message['sender'] = self._user(entry.author)
        return message

    def receive(self, count=COUNT, since=None):
        """Fetch friend status posts."""
        messages = []

        me = pyyaru.yaPerson('/me/').get()
        entries = me.friends_entries('status')
        for entry in entries.objects:
            message = self._message(entry)
            messages.append(message)

        return messages

    def user_messages(self, id=None, count=COUNT, since=None):
        """Gets entries of a certain person.
        id param here is not an id, as someone like me might think,
        it is a nick of a person. Funny it is.

        """
        messages = []
        person = pyyaru.yaPerson('https://api-yaru.yandex.ru/person/%s' % quote(id.encode('utf-8'))).get()
        entries = person.entries('status')

        for entry in entries.objects:
            message = self._message(entry, self._user(person))
            messages.append(message)

        return messages

    def delete(self, message):
        """Deletes status message from server.
        According to Gwibber creators we should always return
        empty list and I'm inclined to think that it is a kind
        of subtle humor.

        """
        try:
            pyyaru.yaEntry(message['mid']).delete()
        except pyyaru.yaError, e:
            log.logger.info('Ya.ru delete error: %s' % e)
        return []

    def send(self, message):
        """Posts new status message.
        So much fun - it always returns empty list, no matter
        how or what.

        """
        try:
            pyyaru.yaPerson('/me/').set_status(message)
        except pyyaru.yaError, e:
            log.logger.info('Ya.ru publish error: %s' % e)
        self.receive()
        return []