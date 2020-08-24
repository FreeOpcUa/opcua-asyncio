from asyncua import Server, Client
from asyncua.common.callback import CallbackType
import logging
import pytest

_logger = logging.getLogger()
pytestmark = pytest.mark.asyncio

port_num = 48560


def create_monitored_items(event, dispatcher):
    print("Monitored Item")

    for idx in range(len(event.response_params)):
        if (event.response_params[idx].StatusCode.is_good()):
            nodeId = event.request_params.ItemsToCreate[idx].ItemToMonitor.NodeId
            print(f"Node {nodeId} was created")


def modify_monitored_items(event, dispatcher):
    print('modify_monitored_items')


def delete_monitored_items(event, dispatcher):
    print('delete_monitored_items')


def write_items(event, dispatcher):
    print('write', event.response_params)


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def datachange_notification(self, node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        _logger.info('datachange_notification %r %s', node, val)


async def test_write_callback(mocker):
    server = Server()
    idx = 0
    # get Objects node, this is where we should put our custom stuff
    opc_url = f"opc.tcp://127.0.0.1:{port_num}/freeopcua/server/"
    server.set_endpoint(opc_url)
    await server.init()
    objects = server.nodes.objects

    # populating our address space
    myobj = await objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()  # Set MyVariable to be writable by clients

    # starting!
    await server.start()

    mocked_create_monitored_items = mocker.patch('tests.test_callback_service.create_monitored_items')
    mocked_write_items = mocker.patch('tests.test_callback_service.write_items')
    # Create Callback for item event
    server.subscribe_server_callback(CallbackType.ItemSubscriptionCreated, mocked_create_monitored_items)
    server.subscribe_server_callback(CallbackType.PreWrite, mocked_write_items)

    assert not mocked_create_monitored_items.called
    assert not mocked_write_items.called

    client = Client(opc_url)
    async with client:
        var = await client.nodes.objects.get_child([f"{idx}:MyObject", f"{idx}:MyVariable"])
        handler = SubscriptionHandler()
        # We create a Client Subscription.
        subscription = await client.create_subscription(500, handler)
        nodes = [
            var
        ]
        await subscription.subscribe_data_change(nodes)
        assert mocked_create_monitored_items.called
        await subscription.delete()

        await var.set_value(69.0)
        assert mocked_write_items.called


