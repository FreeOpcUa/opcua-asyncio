"""
Define exceptions to be raised at various places in the stack
"""

class UaError(RuntimeError):
    pass


class UaStatusCodeError(UaError):
    """
    This exception is raised when a bad status code is encountered.

    It exposes the status code number in the `code' property, so the
    user can distinguish between the different status codes and maybe
    handle some of them.

    The list of status error codes can be found in asyncua.ua.status_codes.
    """

    # Dict containing all subclasses keyed to their status code.
    # When instanciating UaStatusCodeError with given code, we will return the
    # appropriate subclass if it exists. See __new__.
    _subclasses = {}

    @classmethod
    def __init_subclass__(cls):
        # Inplace modification of _subclasses
        cls._subclasses[cls.code] = cls

    def __new__(cls, *args):
        """
        Creates a new UaStatusCodeError but returns a more specific subclass
        if possible, e.g.

            UaStatusCodeError(0x80010000) => BadUnexpectedError()
        """

        if args:
            code, *args = args
            # Try to find the subclass with the given code.
            cls = cls._subclasses.get(code, cls)

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
        import asyncua.ua.status_codes as status_codes

        return "{1}({0})".format(*status_codes.get_name_and_doc(self.code))

    @property
    def code(self):
        """
        The code of the status error.
        """
        return self.args[0]


class UaStringParsingError(UaError):
    pass


class UaStructParsingError(UaError):
    pass
