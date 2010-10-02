#!/usr/bin/env python
#
# setup.py for gnuConcept

from distutils.core import setup
from DistUtilsExtra.command import *
from glob import glob

setup(name="gwibber",
      version="2.30.2", # UPDATE gwibber/microblog/util/const.py too
      author="Ryan Paul",
      author_email="segphault@arstechnica.com",
      url="http://launchpad.net/gwibber/",
      license="GNU General Public License (GPL)",
      packages=['gwibber', 'gwibber.microblog', 'gwibber.microblog.util',
          'gwibber.microblog.support', 'gwibber.microblog.urlshorter', 'gwibber.lib', 
          'gwibber.lib.gtk'],
      data_files=[
    ('share/gwibber/ui', glob("ui/*.ui")),
    ('share/gwibber/ui', glob("ui/*.png")),
    ('share/gwibber/ui/templates', glob("ui/templates/*.mako")),
    ('share/gwibber/ui/templates', glob("ui/templates/*.js")),
    ('share/gwibber/ui/themes/compact', glob("ui/themes/compact/*")),
    ('share/gwibber/ui/themes/gwilouche', glob("ui/themes/gwilouche/*")),
    ('share/gwibber/ui/themes/default', glob("ui/themes/default/*")),
    ('share/gwibber/ui/themes/simple', glob("ui/themes/simple/*")),
    ('share/gwibber/ui/themes/flat', glob("ui/themes/flat/*")),
    ('share/gwibber/ui/themes/ubuntu', glob("ui/themes/ubuntu/*.*")),
    ('share/gwibber/ui/themes/ubuntu/images', glob("ui/themes/ubuntu/images/*")),
    ('share/gwibber/ui', ['ui/progress.gif']),
    ('share/gwibber/ui', ['ui/gwibber.svg']),
    ('share/pixmaps', ['ui/gwibber.svg']),
    ('share/dbus-1/services', ['com.Gwibber.Service.service']),
    ('share/dbus-1/services', ['com.GwibberClient.service']),
    ('share/gwibber/ui/icons/breakdance', glob("ui/icons/breakdance/*.png")),
    ('share/gwibber/ui/icons/breakdance', glob("ui/icons/breakdance/*.svg")),
    ('share/gwibber/ui/icons/breakdance/16x16', glob("ui/icons/breakdance/16x16/*.png")),
    ('share/gwibber/ui/icons/breakdance/16x16', glob("ui/icons/breakdance/16x16/*.svg")),
    ('share/gwibber/ui/icons/breakdance/22x22', glob("ui/icons/breakdance/22x22/*.png")),
    ('share/gwibber/ui/icons/breakdance/22x22', glob("ui/icons/breakdance/22x22/*.svg")),
    ('share/gwibber/ui/icons/breakdance/scalable', glob("ui/icons/breakdance/scalable/*.png")),
    ('share/gwibber/ui/icons/breakdance/scalable', glob("ui/icons/breakdance/scalable/*.svg")),
    ('share/gwibber/ui/icons/streams', glob("ui/icons/streams/*.png")),
    ('share/gwibber/ui/icons/streams', glob("ui/icons/streams/*.svg")),
    ('share/gwibber/ui/icons/streams/16x16', glob("ui/icons/streams/16x16/*.png")),
    ('share/gwibber/ui/icons/streams/16x16', glob("ui/icons/streams/16x16/*.svg")),
    ('share/gwibber/ui/icons/streams/24x24', glob("ui/icons/streams/24x24/*.png")),
    ('share/gwibber/ui/icons/streams/24x24', glob("ui/icons/streams/24x24/*.svg")),
    ('share/gwibber/ui/icons/streams/scalable', glob("ui/icons/streams/scalable/*.png")),
    ('share/gwibber/ui/icons/streams/scalable', glob("ui/icons/streams/scalable/*.svg")),
    ('/usr/share/indicators/messages/applications', ['indicator/gwibber']),
    ],
      scripts=['bin/gwibber', 'bin/gwibber-service', 'bin/gwibber-poster', 'bin/gwibber-accounts', 'bin/gwibber-preferences', 'bin/gwibber-error'],
      cmdclass = { "build" :  build_extra.build_extra,
                   "build_i18n" :  build_i18n.build_i18n,
                   "build_help" :  build_help.build_help,
                   "build_icons" :  build_icons.build_icons
                 }
)
