"""
Creates the StatusCode Enum with generated data
"""

import warnings

from asyncua.ua.uaerrors import UaStatusCodeError
from enum import IntEnum
from asyncua.ua._generated import doc_dict
from asyncua.ua._generated import code_list


__all__ = [
    'StatusCodes',
    'get_name_and_doc',
]


class StatusEnum(IntEnum):

    @classmethod
    def _missing_(cls, value):
        # catch custom status codes and return them as either Bad, Uncertain or Good
        if value & 1 << 31:
            return cls.Bad
        elif value & 1 << 30:
            return cls.Uncertain
        else:
            return cls.Good

    @classmethod
    def default(cls):
        return cls.Good

    @property
    def doc(self):
        return doc_dict[self.value]

    def is_good(self):
        """
        Raises an exception if the status code is anything else than 0 (good).
        """
        # apply mask and compare result
        return not (3 << 30) & self.value

    def check(self):
        """
        Raises an exception if the status code is anything else than 0 (good).
        """
        if not self.is_good():
            raise UaStatusCodeError(self.value)


StatusCodes = StatusEnum('StatusCodes', names=code_list, module=__name__)


def get_name_and_doc(code):
    """
    Returns the name and documentation string of the status code
    """
    warnings.warn("Please use code.name and code.doc instead of get_name_and_doc.", DeprecationWarning)

    if not isinstance(code, StatusCodes):
        try:
            code = StatusCodes(code)
        except ValueError:
            if code & 1 << 31:
                return 'Bad', f'Unknown StatusCode value: {code}'
            elif code & 1 << 30:
                return 'UncertainIn', f'Unknown StatusCode value: {code}'
            else:
                return 'Good', f'Unknown StatusCode value: {code}'
    
    return code.name, code.doc
