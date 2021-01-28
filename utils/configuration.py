from configparser import ConfigParser
import re

from utils.types import StrictTypes, _st


def _configure(inst, path=None, config=None):
    parser = None

    if path is not None and config is not None:
        raise ValueError(
            "Must only provide either config file path or dictionary to configure %s.%s, but not both." % (inst.__module__, inst.__name__))

    if config is not None and type(config) is not dict:
        raise ValueError("Invalid value for configuration provided to %s.%s: expected dictionary." % (
            inst.__module__, inst.__name__))

    if path is not None:
        parser = ConfigParser()

        try:
            parser.read(path)
        except OSError as e:
            raise OSError("Failed to read configuration file provided to %s.%s: %s" % (
                inst.__module__, inst.__name__, e))

    for section in parser:

        if section not in inst._configurable:
            raise KeyError(
                "Unknown configuration section %s provided to %s.%s." % (section, inst.__module__, inst.__name__))

        for key, value in section.items():

            if key not in inst._configurable[section]:
                raise KeyError(
                    "Unknown configuration option %s.%s provided to %s.%s." % (section, key, inst.__module__, inst.__name__))

            meta = inst._configurable[section][key]

            if 'type' in meta:
                dtype = meta['type']

                try:
                    if parser is not None:
                        if dtype == bool:
                            value = parser.getboolean(section, key)
                        elif dtype == int:
                            value = parser.getint(section, key)
                        elif dtype == float:
                            value = parser.getfloat(section, key)

                    assert type(value) == meta['type']
                except ValueError as e:
                    raise ValueError("Invalid value for configuration option %s.%s provided to %s.%s: expected %s." % (
                        section, key, inst.__module__, inst.__name__, dtype.__name__))

                if dtype == str and 'regex' in meta:
                    if re.match(meta['regex'], value) is None:
                        raise ValueError("Invalid value for configuration option %s.%s provided to %s.%s%s: must match pattern %s" % (
                            section, key, inst.__module__, inst.__name__, ' in ' + path if path is not None else '', meta['regex']))

            if section == 'default':
                if not hasattr(inst, key):
                    raise KeyError(
                        "Unknown configuration option %s provided to %s.%s%s." % (key, inst.__module__, inst.__name__, ' in ' + path if path is not None else ''))

                setattr(inst, key, value)

            else:
                if section not in inst._config:
                    inst._config[section] = {}

                inst._config[section][key] = value


class ClassConfigurable(StrictTypes):
    pass


class InstanceConfigurable(StrictTypes):
    pass


class _ClassConfigurableWatcher(_st):
    configurable = []

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        if len(x.__mro__) > 2 and not InstanceConfigurable in bases:
            x._config = {}
            x._configurable = {}
            x.configure = _configure
            cls.configurable.append(x)
        return x


class _InstanceConfigurableWatcher(_st):
    configurable = []

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        if len(x.__mro__) > 2 and not ClassConfigurable in bases:
            cls.configurable.append(x)
        return x


class _ConfigurableWatcher(_ClassConfigurableWatcher, _InstanceConfigurableWatcher, _st):
    pass


class ClassConfigurable(StrictTypes, metaclass=_ClassConfigurableWatcher):
    pass


class InstanceConfigurable(StrictTypes, metaclass=_InstanceConfigurableWatcher):

    def __init__(self):
        if self in _InstanceConfigurableWatcher.configurable:
            self._configurable = {}
            self._config = {}

    def configure(self, path):
        if self in _InstanceConfigurableWatcher.configurable:
            _configure(self, path)


class Configurable(InstanceConfigurable, ClassConfigurable, StrictTypes, metaclass=_ConfigurableWatcher):
    pass


def configurable_classes():
    return _ClassConfigurableWatcher.configurable


def configurable_instances():
    return _InstanceConfigurableWatcher.configurable


def configurable():
    return list(set(configurable_classes() + configurable_instances()))
