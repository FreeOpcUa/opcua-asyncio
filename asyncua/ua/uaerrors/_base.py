"""
Define exceptions to be raised at various places in the stack
"""

from typing import ClassVar


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
    _subclasses: ClassVar = {}

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


class UaStatusCodeErrors(UaStatusCodeError):
    def __new__(cls, *args):
        # use the default implementation
        self = UaError.__new__(cls, *args)
        return self

    def __init__(self, codes):
        """
        :param codes: The codes of the results.
        """
        self.codes = codes

    def __str__(self):
        # import here to avoid circular import problems
        import asyncua.ua.status_codes as status_codes

        return "[{0}]".format(
            ", ".join(["{1}({0})".format(*status_codes.get_name_and_doc(code)) for code in self.codes])
        )

    @property
    def code(self):
        """
        The code of the status error.
        """
        # import here to avoid circular import problems
        from asyncua.ua.uatypes import StatusCode

        error_codes = [code for code in self.codes if not StatusCode(code).is_good()]
        return error_codes[0] if len(error_codes) > 0 else None


class UaStringParsingError(UaError):
    pass


class UaStructParsingError(UaError):
    pass


class UaInvalidParameterError(UaError):
    pass
