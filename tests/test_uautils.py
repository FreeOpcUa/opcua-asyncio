from dataclasses import dataclass
from asyncua.common.ua_utils import copy_dataclass_attr


def test_copy_dataclass_attr() -> None:
    @dataclass
    class A:
        x: int = 1
        y: int = 2

    @dataclass
    class B:
        y: int = 12
        z: int = 13

    b = B()
    a = A()

    assert a.y != b.y
    copy_dataclass_attr(a, b)
    assert a.y == b.y == 2
    assert a.x == 1
    assert b.z == 13

    b.y = 9
    copy_dataclass_attr(b, a)
    assert a.y == b.y == 9
    assert a.x == 1
    assert b.z == 13
