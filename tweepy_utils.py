from utils.configuration import Configurable
from utils.logging import Loggable

import tweepy


class TwitterHarvester(Configurable, Loggable):
    pass


_configurable = {
    'default': {

    },
    'auth': {
        'key': {
            'type': str,
            'match': '<some-regex>'
        },
        'secret': {
            'type': str,
            'match': '<some-regex>'
        }
    },
    'api': {
        'key': {
            'type': str,
            'match': '<some-regex>'
        },
        'secret': {
            'type': str,
            'match': '<some-regex>'
        }
    }
}
