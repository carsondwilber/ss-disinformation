import logging
from utils.configuration import Configurable
from utils.types import strict


class Loggable(Configurable):
    debug = strict(bool, True)

    _configurable = {
        'default': {
            'debug': {
                'type': bool
            }
        }
    }

    def info(self, content):
        super().log(logging.INFO, content)
