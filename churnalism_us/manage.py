#!/usr/bin/env python
from django.core.management import execute_manager
import sys
import imp
try:
    imp.find_module('settings') # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import settings

def unload(name):
    try:
        del sys.modules[name]
    except KeyError:
        pass

if __name__ == "__main__":
    from gevent import monkey
    monkey.patch_all()
    execute_manager(settings)
    unload('threading')
    unload('thread')
