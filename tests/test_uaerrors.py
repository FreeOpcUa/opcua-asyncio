import pytest

import asyncua.ua.uaerrors as uaerrors
from asyncua.ua.uaerrors import UaStatusCodeError

status_code_bad_internal = 0x80020000
status_code_unknown = "Definitely Not A Status Code"


@pytest.fixture()
def errors():
    return {
        "direct": uaerrors.BadInternalError(),
        "indirect": UaStatusCodeError(status_code_bad_internal),
        "unknown": UaStatusCodeError(status_code_unknown),
    }


def test_subclass_selection(errors):
    assert type(errors["direct"]) is uaerrors.BadInternalError
    assert type(errors["indirect"]) is uaerrors.BadInternalError
    assert type(errors["unknown"]) is UaStatusCodeError


def test_code(errors):
    assert errors["direct"].code == status_code_bad_internal
    assert errors["indirect"].code == status_code_bad_internal
    assert errors["unknown"].code == status_code_unknown


def test_string_repr(errors):
    assert "BadInternal" in str(errors["direct"])
    assert "BadInternal" in str(errors["indirect"])
