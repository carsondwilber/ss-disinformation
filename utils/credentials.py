import re
from typing import Union, IO
import secrets
import os
import configparser

from utils.configuration import Configurable
from utils.log import Logging
from utils.hybrid import hybridmethod
from utils.uuid import uuidv4
import utils.validation as validation


class CredentialFormat:
    pass


class CredentialManager:
    pass


class Credential:

    def __init__(self, platform: str, domain: str, endpoint: str, format: CredentialFormat, register: bool = True, **details):
        validation.validate_string(platform, 'credential platform', regex=re.compile(
            f'^{validation.regex.partial.basics}+$'))

        # TODO: add endpoint URI validation
        validation.validate_string(endpoint, 'credential endpoint')

        format.validate(**details)

        self.format = format
        self.platform = platform
        self.endpoint = endpoint
        self.details = details

        self.domain = CredentialManager.domain(domain)
        if register:
            self.domain.register(self)


class CredentialFormat:
    _id = 0
    _cf = {}

    @classmethod
    def _validate_details(cls, **details):
        # TODO: validate that details meet format requirements, else throw exception
        pass

    def __init__(self, name: str, pathname: str = None, parent: CredentialFormat = None, **details):
        validation.validate_string(name, 'credential format name', min_len=1,
                                   max_len=32, regex=re.compile(f'^{validation.regex.partial.basics}{{1,32}}$'))

        if pathname is not None:
            validation.validate_string(pathname, 'credential format path name',
                                       regex=validation.regex.complete.snakes, min_len=1, max_len=32)

        self._validate_details(**details)

        self.id = CredentialFormat._id
        CredentialFormat._id += 1

        self.name = name
        self.qual = pathname.lower() if pathname is not None else name.lower().replace(' ', '_')
        self.ancestry = [self]

        if parent is not None:
            if not isinstance(parent, CredentialFormat):
                raise Exception(
                    "Credential format parent must be a CredentialFormat.")
            self.ancestry = parent.ancestry + [self]

        self.path = '.'.join([cf.qual for cf in self.ancestry])
        if self.path in CredentialFormat._cf:
            raise Exception(
                "Credential format must generate a globally unique path; '%s' already defined." % self.path)
        CredentialFormat._cf[self.path] = self

        self.details = details

    def __call__(self, platform: str, domain: str, endpoint: str, **kwargs):
        return Credential(platform, domain, endpoint, self, **kwargs)

    def validate(self, **kwargs):
        for key in kwargs:
            if key not in self.details:
                raise Exception(
                    "Unknown field '%s' for credential format %s." % (key, self.path))
        for key in self.details:
            if not key in kwargs:
                raise Exception(
                    "Missing required field '%s' for credential format %s." % (key, self.path))

    @classmethod
    def format(cls, path):
        if not path in cls._cf:
            raise Exception("Unknown credential format %s." % path)
        return cls._cf[path]


class Credentials:
    OAuth = CredentialFormat('OAuth')

    OAuthConsumer = CredentialFormat(
        'OAuth Consumer',
        pathname='consumer',
        parent=OAuth,
        key={'type': str, 'regex': f'^{validation.regex.partial.urlb64}+$'},
        secret={'type': str, 'regex': f'^{validation.regex.partial.urlb64}+$'}
    )

    OAuthUser = CredentialFormat(
        'OAuth User Context',
        pathname='user',
        parent=OAuth,
        token={'type': str, 'regex': f'^{validation.regex.partial.urlb64}+$'},
        secret={'type': str, 'regex': f'^{validation.regex.partial.urlb64}+$'}
    )


class CredentialDomain:
    def __init__(self, domain: str):
        validation.validate_string(
            domain, 'credential domain', regex=validation.regex.complete.lowdot)
        self.domain = domain
        self.credentials = {}

    def register(self, credential: Union[Credential, CredentialFormat], name: str = None, *properties, **details):
        if name is not None:
            validation.validate_string(
                name, 'credential name', regex=validation.regex.complete.kebabs, min_len=1, max_len=36)

            if name in self.credentials:
                if credential != self.credentials[name]:
                    raise Exception("Cannot register multiple credentials of the same name for the same domain; %s already has credential '%s'." % (
                        self.domain, name))
        else:
            name = uuidv4()
            while name in self.credentials:
                name = uuidv4()

        if isinstance(credential, Credential):
            if len(properties) != 0 or len(details) != 0:
                raise Exception(
                    "Cannot register an existing credential with new properties or details.")
        elif isinstance(credential, CredentialFormat):
            if len(properties) != 3:
                raise Exception(
                    "Cannot register a new credential with no properties (required: platform, domain, endpoint.)")
            if len(details) == 0:
                raise Exception(
                    "Cannot register a new credential with no details. (required for %s: %s.)" % (credential.path, ','.join(credential.details.keys())))
            credential = Credential(
                *properties, credential, **details)

        self.credentials[name] = credential


class CredentialManager:
    domains = {}

    @classmethod
    def domain(cls, domain: str):
        if not domain in cls.domains:
            cls.domains[domain] = CredentialDomain(domain)
        return cls.domains[domain]

    def __init__(self):
        self.credentials = {}

    def register(self, credential: Union[CredentialFormat, Credential], name: str = None, *properties, **details):
        if name is not None:
            validation.validate_string(
                name, 'credential name', regex=validation.regex.complete.kebabs, min_len=1, max_len=36)

            if name in self.credentials:
                if credential != self.credentials[name]:
                    raise Exception(
                        "Cannot register multiple credentials of the same name in the same manager; already have '%s'.)" % name)
        else:
            name = uuidv4()
            while name in self.credentials:
                name = uuidv4()

        if isinstance(credential, Credential):
            if len(properties) != 0 or len(details) != 0:
                raise Exception(
                    "Cannot register an existing credential with new properties or details.")
        elif isinstance(credential, CredentialFormat):
            if len(properties) != 3:
                raise Exception(
                    "Cannot register a new credential with no properties (required: platform, domain, endpoint.)")
            if len(details) == 0:
                raise Exception(
                    "Cannot register a new credential with no details. (required for %s: %s.)" % (credential.path, ','.join(credential.details.keys())))
            credential = Credential(
                *properties, credential, register=False, **details)

        self.credentials[name] = credential
        credential.domain.register(credential, name)

    @hybridmethod
    def load_credentials(self, file: IO = None, path: str = None):
        try:
            if (file is None) ^ (path is None) == False:
                raise Exception(
                    "Must provide an open file or a filepath (but not both).")

            if path is not None:
                if not os.path.exists(path):
                    raise Exception("File path '%s' does not exist." % path)

                try:
                    file = open(path, 'r')
                except Exception as e:
                    raise Exception(
                        "Failed to open file at '%s'; please make sure it is accessible and not in use." % path)

            conf = configparser.ConfigParser()
            conf.read_file(file)

            for section in conf.sections():
                if not 'platform' in conf[section]:
                    raise Exception("Platform is required.")
                platform = conf[section]['platform']
                del conf[section]['platform']

                if not 'domain' in conf[section]:
                    raise Exception("Domain is required.")
                domain = CredentialManager.domain(conf[section]['domain'])
                del conf[section]['domain']

                if not 'endpoint' in conf[section]:
                    raise Exception("Endpoint is required.")
                endpoint = conf[section]['endpoint']
                del conf[section]['endpoint']

                if not 'format' in conf[section]:
                    raise Exception("Format is required.")
                format = CredentialFormat.format(conf[section]['format'])
                del conf[section]['format']

                name = None
                if 'name' in conf[section]:
                    name = conf[section]['name']
                    del conf[section]['name']

                credential = Credential(
                    platform, domain.domain, endpoint, format, register=False, **dict(conf[section].items()))

                if self == CredentialManager:
                    domain.register(credential, name=name)
                else:
                    self.register(credential, name=name)
        except Exception as e:
            raise Exception("Failed to load credentials: %s" % e) from None
