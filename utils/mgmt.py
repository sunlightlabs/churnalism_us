# -*- coding: utf-8 -*-

from __future__ import division, print_function

import logging
from optparse import make_option

from django.core.management.base import BaseCommand

__all__ = ['LoggableMgmtCommand']

class LoggableMgmtCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--loglevel',
                    action='store',
                    dest='loglevel',
                    choices=('debug', 'info',
                             'warn', 'warning',
                             'error', 'critical'),
                    default='warning',
                    help='Log verbosity.'),
        make_option('--log',
                    action='store',
                    dest='log',
                    default='-',
                    help='Where to write the log.')
    )

    def handle(self, *args, **options):
        loglevel = getattr(logging, options['loglevel'].upper())
        logconfig = {
            'level': loglevel
        }
        if options['log'] is not None and options['log'] != '-':
            logconfig['filename'] = options['log']
        logging.basicConfig(**logconfig)

