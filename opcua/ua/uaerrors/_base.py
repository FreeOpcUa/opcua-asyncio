"""
Define exceptions to be raised at various places in the stack
"""


class _AutoRegister(type):
    def __new__(mcs, name, bases, dict):
        SubClass = type.__new__(mcs, name, bases, dict)

        # register subclass in bases
        for base in bases:
            try:
                subclasses = base._subclasses
                code = dict['code']
            except (AttributeError, KeyError):
                pass
            else:
                subclasses[code] = SubClass

        return SubClass


class UaError(RuntimeError):
    pass


class UaStatusCodeError(_AutoRegister("Meta", (UaError,), {})):
    """
    This exception is raised when a bad status code is encountered.

    It exposes the status code number in the `code' property, so the
    user can distinguish between the different status codes and maybe
    handle some of them.

    The list of status error codes can be found in opcua.ua.status_codes.
    """

    # Dict containing all subclasses keyed to their status code.
    _subclasses = {}

    def __new__(cls, *args):
        """
        Creates a new UaStatusCodeError but returns a more specific subclass
        if possible, e.g.

            UaStatusCodeError(0x80010000) => BadUnexpectedError()
        """

        # switch class to a more appropriate subclass
        if len(args) >= 1:
            code = args[0]
            try:
                cls = cls._subclasses[code]
            except (KeyError, AttributeError):
                pass
            else:
                args = args[1:]

        return UaError.__new__(cls, *args)

    def __init__(self, code=None):
        """
        :param code: The code of the exception. Only needed when not instanciating
                     a concrete subclass such as BadInternalError.
        """
        if code is None:
            if type(self) is UaStatusCodeError:
                raise TypeError("UaStatusCodeError(code) cannot be instantiated without a status code.")
        UaError.__init__(self, code)

    def __str__(self):
        # import here to avoid circular import problems
        import opcua.ua.status_codes as status_codes

        return "{1}({0})".format(*status_codes.get_name_and_doc(self.code))

    @property
    def code(self):
        """
        The code of the status error.
        """
        return self.args[0]


class UaStringParsingError(UaError):
    pass
