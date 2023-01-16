import pytest

from asyncua.common.connection import TransportLimits, ua

@pytest.mark.parametrize('transport_limits, ua_hello, expected_ack, expected_transport_limits', [
    (TransportLimits(), ua.Hello(), ua.Acknowledge(0, 65535, 65535, 104857600, 1601), TransportLimits()),
    (TransportLimits(), ua.Hello(0, 100, 200, 1000, 10), ua.Acknowledge(0, 100, 200, 1000, 10), TransportLimits(200, 100, 10, 1000)),
])
def test_create_acknowledge_and_set_limits(transport_limits, ua_hello, expected_ack, expected_transport_limits):
    ua_ack = transport_limits.create_acknowledge_and_set_limits(ua_hello)
    assert ua_ack == expected_ack
    assert transport_limits == expected_transport_limits


@pytest.mark.parametrize('ua_ack, expected_transport_limits', [
    (ua.Acknowledge(0, 65535, 65535, 104857600, 1601), TransportLimits()),
    (ua.Acknowledge(0, 100, 200, 1000, 10), TransportLimits(100, 200, 10, 1000)),
])
def test_update_client_limits(ua_ack, expected_transport_limits):
    transport_limits = TransportLimits()
    transport_limits.update_client_limits(ua_ack)
    assert transport_limits == expected_transport_limits
