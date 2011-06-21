#! /usr/bin/env python

import os

from subprocess import Popen
from setuptools.command import easy_install
from distutils.dir_util import copy_tree, remove_tree
from distutils.log import set_verbosity

def print_title(title):
    print ''
    print '-' * 50
    print title
    print ''

def install():
    print '\nStarting yaru Gwibber plugin install...'

    print_title('Installing required pyyaru library...')
    easy_install.main(['-U', 'pyyaru'])

    dest_plugin = '/usr/share/gwibber/plugins/yaru/'
    dest_plugin_exists = os.path.exists(dest_plugin)

    if dest_plugin_exists:
        set_verbosity(1)
        print_title('Previous plugin installation found. Reinstall initiated...')
        remove_tree(dest_plugin, 1)

    copy_tree('gwibber/microblog/plugins/yaru/', dest_plugin, verbose=1)
    copy_tree('ui/', '/usr/share/gwibber/ui/', verbose=1)

    print_title('Killing gwibber-service...')

    subproc = Popen('killall -v gwibber-service', shell=True)
    subproc.wait()

    print_title('Done.')

if __name__ == '__main__':
    install()
  