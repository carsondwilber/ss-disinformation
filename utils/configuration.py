from configparser import ConfigParser
import re

from utils.types import StrictTypes, _st


def _add_trigger(inst, key, trigger):
    if key not in inst.triggers:
        inst.triggers[key] = []
    inst.triggers[key].append(trigger)


def _fire_triggers(inst, key, old_value, new_value):
    if key in inst.triggers:
        for trigger in inst.triggers[key]:
            if type(trigger) is classmethod:
                trigger.__get__(inst, inst)(key, old_value, new_value)
            else:
                trigger(key, old_value, new_value)


def _validate(inst, path=None, config=None):
    parser = None

    if path is not None and config is not None:
        raise ValueError(
            "Must only provide either config file path or dictionary to configure %s.%s, but not both." % (inst.__module__, inst.__name__))

    if config is not None and type(config) is not dict:
        raise ValueError("Invalid value for configuration provided to %s.%s: expected dictionary." % (
            inst.__module__, inst.__name__))

    if config is not None:
        parser = config
    else:  # if path is not None:
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

        for key, value in parser[section].items():

            if key not in inst._configurable[section]:
                raise KeyError(
                    "Unknown configuration option %s.%s provided to %s.%s." % (section, key, inst.__module__, inst.__name__))

            if section == 'default' and not hasattr(inst, key):
                raise KeyError(
                    "Unknown configuration option %s provided to %s.%s%s." % (key, inst.__module__, inst.__name__, ' in ' + path if path is not None else ''))

            meta = inst._configurable[section][key]

            if 'type' in meta:
                dtype = meta['type']

                try:
                    if type(parser) is ConfigParser:
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


def _configure(inst, path=None, config=None):
    validated = _validate(inst, path, config)

    to_trigger = {}

    for section in validated:
        for key in section:
            old_value = None

            if section == 'default':
                old_value = getattr(inst, key)
                setattr(inst, key, value)
            else:
                if section in inst._config:
                    if key in inst._config[section]:
                        old_value = inst._config[section][key]
                else:
                    inst._config[section] = {}

                inst._config[section][key] = value

            if key in inst.triggers:
                to_trigger[key] = (old_value, value)

    for key in to_trigger:
        _fire_triggers(inst, key, *to_trigger[key])


class TriggerableConfiguration:
    def __init__(self, configuration, triggers):
        self.configuration = configuration
        self.triggers = triggers


class ClassConfigurable(StrictTypes):
    pass


class InstanceConfigurable(StrictTypes):
    pass


class Configurable(InstanceConfigurable, ClassConfigurable, StrictTypes):
    pass


class _ClassConfigurableWatcher(_st):
    class_configurable = []

    def __new__(cls, name, bases, dct):
        is_configurable = (ClassConfigurable in bases and not InstanceConfigurable in bases) or Configurable in bases  # noqa

        if is_configurable:
            dct['_config'] = {}
            dct['configure'] = _configure
            dct['add_trigger'] = _add_trigger
            dct['triggers'] = {}

            if '_configurable' in dct:
                value = dct['_configurable']
                if type(value) == TriggerableConfiguration:
                    dct['_configurable'] = value.configuration
                    dct['triggers'] = value.triggers

        x = super().__new__(cls, name, bases, dct)

        if is_configurable:
            cls.class_configurable.append(x)

        return x

    def __setattr__(cls, name, value):
        if name == '_configurable':
            if type(value) == TriggerableConfiguration:
                cls._configurable = value.configuration
                cls.triggers = value.triggers
            return

        if name in cls._configurable['default']:
            _validate(cls, config={'default': {name: value}})

        old_value = getattr(cls, name)
        super().__setattr__(name, value)
        _fire_triggers(cls, name, old_value, value)


class _InstanceConfigurableWatcher(_st):
    instance_configurable = []

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        if (InstanceConfigurable in bases and not ClassConfigurable in bases) or Configurable in bases:
            cls.instance_configurable.append(x)
        return x


class _ConfigurableWatcher(_ClassConfigurableWatcher, _InstanceConfigurableWatcher, _st):
    pass


class ClassConfigurable(StrictTypes, metaclass=_ClassConfigurableWatcher):
    pass


class InstanceConfigurable(StrictTypes, metaclass=_InstanceConfigurableWatcher):

    def __init__(self):
        if self.__class__ in _InstanceConfigurableWatcher.instance_configurable:
            self._configurable = {}
            self._config = {}
            self.triggers = {}

    def configure(self, path=None, config=None):
        if self.__class__ in _InstanceConfigurableWatcher.instance_configurable:
            _configure(self, path, config)

    def add_trigger(self, key, trigger):
        if self.__class__ in _InstanceConfigurableWatcher.instance_configurable:
            _add_trigger(self, key, trigger)


class Configurable(ClassConfigurable, InstanceConfigurable, StrictTypes, metaclass=_ConfigurableWatcher):
    pass


def configurable_classes():
    return _ClassConfigurableWatcher.class_configurable


def configurable_instances():
    return _InstanceConfigurableWatcher.instance_configurable


def configurable():
    return list(set(configurable_classes() + configurable_instances()))
