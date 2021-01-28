import traceback


class strict(object):
    def __init__(self, dtype, value):
        if type(value) is not dtype:
            raise ValueError("When strict types are enabled, initial value must match type (%s)" %
                             traceback.extract_stack()[-3].line)
        self.dtype = dtype
        self.value = value

    def __set__(self, instance, value):
        assert type(value) is self.dtype
        self.value = value


class _st(type):
    def __setattr__(self, attr, value):
        if hasattr(self, attr) and hasattr(getattr(self, attr), '__set__'):
            try:
                getattr(self, attr).__set__(self, value)
            except AssertionError as e:
                if type(getattr(self, attr)) is strict:
                    stack = traceback.extract_stack()
                    cause = stack[-min(2, len(stack))]
                    raise ValueError("Setting value of %s in class %s.%s must match strict type %s: %s does not.\n%s line %d %s:\n\t%s" % (
                        attr, self.__module__, self.__name__, getattr(self, attr).dtype.__name__, str(value), *cause)) from e
        else:
            super().__setattr__(attr, value)


class StrictTypes(metaclass=_st):
    def __setattr__(self, attr, value):
        if attr in self.__dict__ and hasattr(self.__dict__[attr], '__set__'):
            try:
                getattr(self, attr).__set__(self, value)
            except AssertionError as e:
                if type(getattr(self, attr)) is strict:
                    stack = traceback.extract_stack()
                    cause = stack[-min(2, len(stack))]
                    raise ValueError("Setting value of %s in instance of %s.%s must match strict type %s: %s (%s) does not.\n%s line %d %s:\n\t%s" % (
                        attr, self.__class__.__module__, self.__class__.__name__, getattr(self, attr).dtype.__name__, str(value), type(value).__name__, *cause)) from e
        else:
            self.__dict__[attr] = value
