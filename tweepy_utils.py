from utils.configuration import Configurable, InstanceConfigurable
from utils.log import Logging
from utils.credentials import Credential, Credentials
import utils.validation as validation
from utils.uuid import uuidv4

import tweepy


class TwitterHarvester(Logging, Configurable):
    _harvesters = {}

    def __init__(self, name: str = None):
        if name is not None:
            validation.validate_string(
                name, 'harvester name', min_len=1, max_len=36)

            if name in TwitterHarvester._harvesters:
                raise Exception(
                    "Harvester names must be globally unique; cannot instantiate another harvester named '%s'." % name)
        else:
            name = uuidv4()
            while name in TwitterHarvester._harvesters:
                name = uuidv4()

        super(InstanceConfigurable, self).__init__()

        self.name = name
        TwitterHarvester._harvesters[name] = self

        self._api_init = False

    def init(self, cred: Credential):
        if self._api_init:
            raise Exception(
                "Harvester API access already initialized; if attempting to change credentials, please create a new harvester.")

        if not cred.format == Credentials.OAuthConsumer:
            raise Exception(
                "Harvester only accepts OAuthConsumer type credentials.")

        auth = tweepy.AppAuthHandler(
            cred.details['key'], cred.details['secret'])
        self.api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True)
        self._api_init = True
