import logging
import time
from datetime import datetime
import random
import sys
from functools import partial

from utils.configuration import Configurable, TriggerableConfiguration
from utils.types import strict

_stdout = logging.StreamHandler(sys.stdout)
_sttime = time.time()


def _path(log_path, key, uuid):
    if '$key' in log_path:
        if len(key) < 4 or len(key) > 5:
            raise Exception(
                "Log file key must be 'num' or 'hex' followed by length between 1 and 32 (inclusive). e.g. num8, hex16")

        ktype = key[:3]
        if ktype.lower() not in ['hex', 'num']:
            raise Exception(
                "Log file key must be 'num' or 'hex' ('HEX' for uppercase).")

        units = int(key[3:])
        if units < 1 or units > 32:
            raise Exception(
                "Log file key length must be between 1 and 32 (inclusive).")

        if ktype.lower() == 'num':
            knum = str(uuid)
            while len(knum) < units:
                knum += knum
            log_path = log_path.replace('$key$', knum[:units])

        else:  # ktype.lower() == 'hex':
            khex = hex(uuid)[2:units]
            while len(khex) < units:
                khex += khex
            log_path = log_path.replace(
                '$key$', khex.upper()[:units] if ktype == 'HEX' else khex[:units])

    dt = datetime.fromtimestamp(_sttime)
    log_path = dt.strftime(log_path)

    return log_path


class Logging(Configurable):
    debug = strict(bool, True)
    path = strict(str, None)
    key = strict(str, None)

    _configurable = {
        'default': {
            'debug': {
                'type': bool
            },
            'path': {
                'type': str
            },
            'key': {
                'type': str,
                'regex': '(num|hex)[0-9]{1,2}'
            }
        }
    }

    def __init__(self, level=logging.DEBUG):
        def log(level, content):
            self.logger.log(level, content)

        for (name, level) in [
            ('debugging', logging.DEBUG),
            ('info', logging.INFO),
            ('warn', logging.WARN),
            ('error', logging.ERROR),
            ('critical', logging.CRITICAL)
        ]:
            setattr(self, name, partial(log, level))

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level)

        self.formatter = logging.Formatter(
            fmt='{asctime} [{levelname:1.1s}] {message}',
            style='{',
            datefmt='%c'
        )

        self.handler = logging.FileHandler(
            filename=_path(self.path, self.key, id(Logging)),
            delay=True
        )

        self.handler.formatter = self.formatter
        self.logger.addHandler(self.handler)
        self.logger.addHandler(_stdout)

        self.add_trigger('key', self._path_trigger)
        self.add_trigger('path', self._path_trigger)
        self.add_trigger('debug', self._debug_trigger)

    def _path_trigger(self, *args):
        self.logger.removeHandler(self.handler)

        self.handler = logging.FileHandler(
            filename=_path(self.path, self.key, id(Logging)),
            delay=True
        )

        self.handler.formatter = self.formatter

        self.logger.addHandler(self.handler)

    def _debug_trigger(self, *args):
        if self.debug and _stdout not in self.logger.handlers:
            self.logger.addHandler(_stdout)
        elif not self.debug and _stdout in self.logger.handlers:
            self.logger.removeHandler(_stdout)
