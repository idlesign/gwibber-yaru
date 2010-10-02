import log
import os, subprocess
import xdg, time

class GwibberError(Exception):
    """Base class for exceptions in gwibber."""
    pass

class GwibberProtocolError(GwibberError):
    """Exception raised for errors from protocols.

    Attributes:
        protocol
        username
        message
        kind
    """
    def __init__(self, kind="UNKNOWN", protocol="UNKNOWN", username="UNKNOWN", message="UNKNOWN"):
        if kind == "keyring":
            log.logger.error("Failed to find credentials in the keyring")
            accounts_error = os.path.join(xdg.BaseDirectory.xdg_cache_home, "gwibber", ".accounts_error")
            if os.path.exists(accounts_error) and os.path.getmtime(accounts_error) > time.time()-600:
                log.logger.info("gwibber-accounts was raised less than 600 seconds")
                return
            else:
                open(accounts_error, 'w').close() 
        else:
            log.logger.error("%s failure: %s:%s - %s", kind, protocol, username, message)

        display_message = "There was an %s failure from %s for account %s, error was %s" % (kind, protocol, username, message)
        title = "Gwibber"
        level = "info"
        if kind == "auth":
            display_message = "Authentication error from %s for account %s" % (protocol, username)
            title = "Gwibber Authentication Error"
            level = "error"
        if kind == "network":
            display_message = "There was a network error communicating with %s" % message
            title = "Gwibber Network Error"
            level = "error"

        if os.path.exists(os.path.join("bin", "gwibber-error")):
            cmd = os.path.join("bin", "gwibber-error")
        else:
            cmd = "gwibber-error"
        ret = subprocess.Popen([cmd, '-m', display_message, '-t', title, '-c', level, '-p', protocol, '-u', username, '-e', kind], shell=False)
