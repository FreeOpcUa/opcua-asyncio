import asyncio
from typing import Any

import pytest

from asyncua import Client, Server, ua
from asyncua.server.address_space import AddressSpace
from asyncua.server.subscription_service import SubscriptionService
from asyncua.server.uaprocessor import PublishRequestData

from .conftest import find_free_port


async def _callback(*args: Any) -> None:
    pass


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, 1, 2, 10, 15, 20])
async def test_publish_notification_limit(limit: int) -> None:
    service = SubscriptionService(AddressSpace())
    params = ua.CreateSubscriptionParameters()
    params.MaxNotificationsPerPublish = limit
    params.PublishingEnabled = True
    result = await service.create_subscription(params, _callback, ua.NodeId(1))
    sub = service.subscriptions[result.SubscriptionId]
    sub._triggered_datachanges = {
        1: [ua.MonitoredItemNotification(ClientHandle=i) for i in range(7)],
        2: [ua.MonitoredItemNotification(ClientHandle=i) for i in range(7, 12)],
    }
    sub._triggered_events = {3: [ua.EventFieldList(ClientHandle=i) for i in range(12, 15)]}
    received = []
    for _ in range(16):
        response = sub._pop_publish_result()
        batch = []
        for notification in response.NotificationMessage.NotificationData:
            if isinstance(notification, ua.DataChangeNotification):
                batch.extend(item.ClientHandle for item in notification.MonitoredItems)
            elif isinstance(notification, ua.EventNotificationList):
                batch.extend(item.ClientHandle for item in notification.Events)
        assert len(batch) <= (limit or 15)
        received.extend(batch)
        assert response.MoreNotifications == (len(received) < 15)
        if not response.MoreNotifications:
            break
    assert received == list(range(15))
    assert not sub._triggered_datachanges
    assert not sub._triggered_events


@pytest.mark.asyncio
async def test_modify_limit_and_disabled_publishing() -> None:
    service = SubscriptionService(AddressSpace())
    params = ua.CreateSubscriptionParameters(PublishingEnabled=False, MaxNotificationsPerPublish=1)
    result = await service.create_subscription(params, _callback, ua.NodeId(1))
    sub = service.subscriptions[result.SubscriptionId]
    sub._triggered_events = {1: [ua.EventFieldList(ClientHandle=i) for i in range(3)]}
    sub._triggered_statuschanges = [ua.StatusCode()]
    response = sub._pop_publish_result()
    assert not response.MoreNotifications
    assert len(sub._triggered_events[1]) == 3
    assert isinstance(response.NotificationMessage.NotificationData[0], ua.StatusChangeNotification)
    service.modify_subscription(
        ua.ModifySubscriptionParameters(SubscriptionId=result.SubscriptionId, MaxNotificationsPerPublish=2)
    )
    sub._publishing_enabled = True
    response = sub._pop_publish_result()
    assert len(response.NotificationMessage.NotificationData[0].Events) == 2
    assert response.MoreNotifications
    service.modify_subscription(
        ua.ModifySubscriptionParameters(SubscriptionId=result.SubscriptionId, MaxNotificationsPerPublish=0)
    )
    response = sub._pop_publish_result()
    assert len(response.NotificationMessage.NotificationData[0].Events) == 1
    assert not response.MoreNotifications


@pytest.mark.asyncio
@pytest.mark.parametrize("with_requests", [False, True])
async def test_publish_drains_available_requests(with_requests: bool) -> None:
    responses: list[ua.PublishResult] = []
    requests = [PublishRequestData(), PublishRequestData()]
    consumed: list[PublishRequestData | None] = []

    async def callback(response: ua.PublishResult, request: PublishRequestData | None = None) -> None:
        responses.append(response)
        consumed.append(request)

    def request_callback(subscription_id: int) -> PublishRequestData | None:
        return requests.pop(0) if requests else None

    service = SubscriptionService(AddressSpace())
    params = ua.CreateSubscriptionParameters(
        PublishingEnabled=True, MaxNotificationsPerPublish=2, RequestedLifetimeCount=100
    )
    result = await service.create_subscription(
        params, callback, ua.NodeId(1), request_callback if with_requests else None
    )
    sub = service.subscriptions[result.SubscriptionId]
    sub._triggered_datachanges = {1: [ua.MonitoredItemNotification(ClientHandle=i) for i in range(5)]}
    assert await sub.publish_results()
    if with_requests:
        assert len(responses) == 2
        assert len(sub._triggered_datachanges[1]) == 1
        assert not await sub.publish_results()
        assert len(responses) == 2
        assert await sub.publish_results(PublishRequestData())
        assert len({id(request) for request in consumed}) == 3
        assert [response.NotificationMessage.SequenceNumber for response in responses] == [1, 2, 3]
        assert sub.republish(1).NotificationData[0].MonitoredItems[0].ClientHandle == 0
    assert [len(response.NotificationMessage.NotificationData[0].MonitoredItems) for response in responses] == [2, 2, 1]
    assert [response.MoreNotifications for response in responses] == [True, True, False]


@pytest.mark.asyncio
async def test_notification_limit_over_tcp() -> None:
    server = Server()
    await server.init()
    endpoint = f"opc.tcp://127.0.0.1:{find_free_port()}"
    server.set_endpoint(endpoint)
    nodes = [await server.nodes.objects.add_variable(2, f"Limited{i}", i) for i in range(5)]
    batches: list[list[int]] = []
    more: list[bool] = []
    complete = asyncio.Event()

    async def callback(response: ua.PublishResult) -> None:
        for notification in response.NotificationMessage.NotificationData:
            if isinstance(notification, ua.DataChangeNotification):
                batches.append([item.ClientHandle for item in notification.MonitoredItems])
                more.append(response.MoreNotifications)
                if sum(map(len, batches)) == 5:
                    complete.set()

    async with server:
        async with Client(endpoint) as client:
            subscription = await client.uaclient.create_subscription(
                ua.CreateSubscriptionParameters(
                    RequestedPublishingInterval=50,
                    RequestedLifetimeCount=1000,
                    RequestedMaxKeepAliveCount=20,
                    MaxNotificationsPerPublish=2,
                    PublishingEnabled=False,
                ),
                callback,
            )
            try:
                items = [
                    ua.MonitoredItemCreateRequest(
                        ItemToMonitor=ua.ReadValueId(NodeId=node.nodeid, AttributeId=ua.AttributeIds.Value),
                        MonitoringMode=ua.MonitoringMode.Reporting,
                        RequestedParameters=ua.MonitoringParameters(ClientHandle=i, QueueSize=1),
                    )
                    for i, node in enumerate(nodes)
                ]
                results = await client.uaclient.create_monitored_items(
                    ua.CreateMonitoredItemsParameters(SubscriptionId=subscription.SubscriptionId, ItemsToCreate=items)
                )
                for result in results:
                    result.StatusCode.check()
                await client.uaclient.set_publishing_mode(
                    ua.SetPublishingModeParameters(
                        PublishingEnabled=True, SubscriptionIds=[subscription.SubscriptionId]
                    )
                )
                await asyncio.wait_for(complete.wait(), 5)
                assert batches == [[0, 1], [2, 3], [4]]
                assert more == [True, True, False]
            finally:
                await client.uaclient.delete_subscriptions([subscription.SubscriptionId])
