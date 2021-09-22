import pytest
from itertools import chain

from asyncua import ua, Client
from asyncua.client.ua_client import UASocketProtocol
from asyncua.common.subscription import Subscription
from asyncua.crypto import security_policies
from asyncua.ua.uaerrors import BadSessionClosed
from asyncua.client.ha.ha_client import (
    ConnectionStates,
    HaClient,
    HaMode,
    HaSecurityConfig,
)
from asyncua.client.ha.common import ClientNotFound
from asyncua.crypto.uacrypto import CertProperties
from .test_subscriptions import MySubHandler
from .conftest import (
    wait_clients_socket,
    wait_for_status_change,
    wait_mode_in_real_map,
    wait_node_in_real_map,
    wait_sub_in_real_map,
)


class TestHaClient:
    @pytest.mark.asyncio
    async def test_init_ha_client(self, ha_client):
        # check init parameters are set
        ha_config = ha_client._config
        urls = set(ha_client.urls)
        assert not ha_client.sub_names
        assert not ha_client.url_to_reset
        assert next(ha_client._gen_sub) == "sub_0"
        assert len(ha_client.get_clients()) == 2
        # check lower level clients have their parameters passed
        for client in ha_client.get_clients():
            url = client.server_url.geturl()
            assert url in urls
            urls.remove(url)
            assert client.session_timeout == ha_config.session_timeout * 1000
            assert client.session_timeout == ha_client.session_timeout * 1000
            assert client.secure_channel_timeout == ha_config.secure_channel_timeout * 1000
            assert client.uaclient._timeout == ha_config.request_timeout
            assert client.description == ha_config.session_name
            # ideal map is empty at startup
            assert not ha_client.ideal_map[url]
        assert not urls

    @pytest.mark.asyncio
    async def test_clients_connected(self, ha_client):
        # check lower level clients are connected
        await ha_client.start()
        await wait_clients_socket(ha_client, UASocketProtocol.OPEN)
        for client, srv_info in ha_client.clients.items():
            # TODO: Enable this when freeopcua server fully supports Service Levels
            # assert srv_info.status == 255
            assert srv_info.status
            assert srv_info.url == client.server_url.geturl()

        await ha_client.stop()
        await wait_clients_socket(ha_client, UASocketProtocol.CLOSED)

    @pytest.mark.asyncio
    async def test_all_tasks_running(self, ha_client):
        # check all tasks are running
        await ha_client.start()
        tasks = list(
            chain(
                ha_client._manager_task.values(),
                ha_client._keepalive_task.values(),
                ha_client._manager_task.values(),
                ha_client._reconciliator_task.values(),
            )
        )
        task_objs = list(
            chain(
                ha_client._manager_task,
                ha_client._keepalive_task,
                ha_client._manager_task,
                ha_client._reconciliator_task,
            )
        )
        task_count = 0
        for obj in task_objs:
            task_count += 1
            assert not obj.stop_event.is_set()
        assert task_count == 5

        for task in tasks:
            assert not task.done()
            assert not task.cancelled()

        await ha_client.stop()

        for obj in task_objs:
            assert obj.stop_event.is_set()

        for task in tasks:
            assert task.done()

    @pytest.mark.asyncio
    async def test_subscription(self, ha_client, srv_variables):

        await ha_client.start()
        node, values = [(n, v) for n, v in srv_variables.items()][0]

        myhandler = MySubHandler()
        sub = await ha_client.create_subscription(100, myhandler)
        await ha_client.subscribe_data_change(sub, [node])

        # the subscription is immediately available in ideal_map
        for c in ha_client.get_clients():
            url = c.server_url.geturl()
            assert sub in ha_client.ideal_map[url]

        # keepalive (status change) and reconciliator (real_mode_for_sub)
        # must both run once to assess the outcome.
        await wait_sub_in_real_map(ha_client, sub)
        for c in ha_client.get_clients():
            await wait_for_status_change(ha_client, c, 255)

        primary = await ha_client.get_serving_client(ha_client.get_clients(), None)
        await wait_mode_in_real_map(
            ha_client, primary, sub, mode="publishing", value=True
        )

        node_id, val, data = await myhandler.result()
        assert node_id == node
        assert val == values

        # real map data are OK
        monitoring = {ua.MonitoringMode.Reporting, ua.MonitoringMode.Disabled}
        publishing = {True, False}
        node_str = None

        for vsub in ha_client.reconciliator.real_map.values():
            vs = vsub[sub]
            node_str = node.nodeid.to_string()
            assert next(iter(vs.nodes)) == node_str
            assert vs.nodes[node_str].queuesize == 0
            assert vs.nodes[node_str].attr == ua.AttributeIds.Value
            assert vs.period == 100
            assert vs.handler == myhandler
            assert vs.monitoring in monitoring
            monitoring.remove(vs.monitoring)
            assert vs.publishing in publishing
            publishing.remove(vs.publishing)

        # in warm mode: 1 client publishes / 1 client monitor
        assert not publishing
        assert not monitoring

        # unsubscribe remove nodes from real map
        await ha_client.unsubscribe([node])
        await wait_node_in_real_map(ha_client, sub, node_str, negation=True)

        # delete subscription removes vs from real map
        await ha_client.delete_subscriptions([sub])
        await wait_sub_in_real_map(ha_client, sub, negation=True)

    @pytest.mark.asyncio
    async def test_reconnect(self, ha_client):
        await ha_client.start()
        await wait_clients_socket(ha_client, UASocketProtocol.OPEN)

        first_client = next(iter(ha_client.get_clients()))
        socket = first_client.uaclient.protocol
        await ha_client.reconnect(first_client)

        assert first_client.server_url.geturl() in ha_client.url_to_reset
        await wait_clients_socket(ha_client, UASocketProtocol.OPEN)
        new_socket = first_client.uaclient.protocol
        assert socket != new_socket

        # urls to reconnect should only be added once
        await ha_client.reconciliator.stop()
        await ha_client.reconnect(first_client)
        await ha_client.reconnect(first_client)
        assert len(ha_client.url_to_reset) == 2

    @pytest.mark.asyncio
    async def test_failover_warm(self, ha_client, srv_variables):
        await ha_client.start()
        node, values = [(n, v) for n, v in srv_variables.items()][0]

        myhandler = MySubHandler()
        sub = await ha_client.create_subscription(100, myhandler)
        await ha_client.subscribe_data_change(sub, [node])

        # data collected by sub handler is correct
        await wait_sub_in_real_map(ha_client, sub)
        node_id, val, data = await myhandler.result()
        assert node_id == node
        assert val == values

        # real map data are OK
        reconciliator = ha_client.reconciliator
        _url = None
        for _url, vsub in reconciliator.real_map.items():
            vs = vsub[sub]
            if vs.publishing:
                break

        primary_client = ha_client.get_client_by_url(_url)
        secondary_client = set(ha_client.get_clients()) - {primary_client}
        await ha_client.failover_warm(secondary_client.pop(), {primary_client})

        # hack to wait for the next reconciliator iteration
        sub2 = await ha_client.create_subscription(100, myhandler)
        await wait_sub_in_real_map(ha_client, sub2)

        for _url, vsub in reconciliator.real_map.items():
            vs = vsub[sub]
            if vs.publishing:
                break

        new_primary = ha_client.get_client_by_url(_url)
        assert primary_client != new_primary

    @pytest.mark.asyncio
    async def test_security(self, ha_config, ha_servers, client_key_and_cert):
        # check security can be set via method and constructor
        ha_clients = []
        srv1, srv2 = ha_servers
        srv1_port = srv1.endpoint.port
        srv2_port = srv2.endpoint.port

        ha_config = ha_config(srv1_port, srv2_port)
        ha_c1 = HaClient(ha_config)
        key, cert = client_key_and_cert

        security_policy = security_policies.SecurityPolicyBasic256Sha256
        user_key = CertProperties(key, "PEM")
        user_cert = CertProperties(cert, "DER")
        security_mode = ua.MessageSecurityMode.SignAndEncrypt
        ha_c1.set_security(security_policy, user_cert, user_key, mode=security_mode)
        ha_clients.append(ha_c1)

        ha_security = HaSecurityConfig(
            security_policy, user_cert, user_key, mode=security_mode
        )
        ha_clients.append(HaClient(ha_config, ha_security))

        for ha_client in ha_clients:
            assert ha_client.security_config.policy == security_policy
            assert ha_client.security_config.mode == security_mode
            assert ha_client.security_config.certificate == user_cert
            assert ha_client.security_config.private_key == user_key

            await ha_client.start()
            await wait_clients_socket(ha_client, UASocketProtocol.OPEN)

            for client in ha_client.get_clients():
                assert isinstance(client.security_policy, ua.SecurityPolicy)
                assert isinstance(client.uaclient.security_policy, ua.SecurityPolicy)
                assert client.security_policy.Mode == security_mode
                assert client.security_policy.peer_certificate

                # security policy should be cleared once reconnect is called
                policy = client.security_policy
                await ha_client.reconnect(client)
                assert client.security_policy != policy
                assert client.security_policy.Mode == security_mode
                assert client.security_policy.peer_certificate
            await ha_client.stop()

    @pytest.mark.asyncio
    async def test_group_clients_by_health(self, ha_client, ha_servers):
        srv1, srv2 = ha_servers
        # srv2 service level is already 255
        slevel = srv1.get_node(ua.NodeId(ua.ObjectIds.Server_ServiceLevel))
        await ha_client.start()
        for c in ha_client.get_clients():
            await wait_for_status_change(ha_client, c, 255)

        # if all clients are 255, group client should return them all
        healthy, unhealthy = await ha_client.group_clients_by_health()
        assert len(healthy) == 2
        assert not unhealthy

        # the service level is considered (by default) unhealthy below 200,
        # so change to unhealthy for srv1 and client1
        clients = ha_client.get_clients()
        await slevel.write_value(ua.Variant(199, ua.VariantType.Byte))
        await wait_for_status_change(ha_client, clients[0], 199)
        healthy, unhealthy = await ha_client.group_clients_by_health()
        assert clients[0] == unhealthy[0]
        assert clients[1] == healthy[0]

        # now try with a custom HEALTHY_STATE value
        ha_client.HEALTHY_STATE = 4
        healthy, unhealthy = await ha_client.group_clients_by_health()
        assert len(healthy) == 2
        assert not unhealthy

        await slevel.write_value(ua.Variant(3, ua.VariantType.Byte))
        await wait_for_status_change(ha_client, clients[0], 3)
        healthy, unhealthy = await ha_client.group_clients_by_health()
        assert clients[0] == unhealthy[0]
        assert clients[1] == healthy[0]

        # set back the value to 255 since the fixture as a wide scope
        await slevel.write_value(ua.Variant(255, ua.VariantType.Byte))

    @pytest.mark.asyncio
    async def test_ha_mode(self, ha_config, ha_servers):
        # WARM is the only mode supported at the moment.
        srv1, srv2 = ha_servers
        port1, port2 = srv1.endpoint.port, srv2.endpoint.port
        config = ha_config(port1, port2, ha_mode=HaMode.WARM)
        ha_client = HaClient(config)
        assert ha_client.ha_mode == "warm"

        for ha in (HaMode.COLD, HaMode.HOT_A, HaMode.HOT_B):
            config = ha_config(port1, port2, ha_mode=ha)
            with pytest.raises(NotImplementedError):
                ha_client = HaClient(config)

    @pytest.mark.asyncio
    async def test_get_client_by_url(self, ha_client):
        urls = [srv_info.url for srv_info in ha_client.clients.values()]
        for url in urls:
            assert isinstance(ha_client.get_client_by_url(url), Client)
        with pytest.raises(ClientNotFound):
            ha_client.get_client_by_url("opc.tcp://not_found")


class TestKeepAlive:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("excp", [Exception(), BadSessionClosed()])
    async def test_service_level_no_data(self, excp, ha_client, mocker):
        mock_read = mocker.patch.object(Client, "read_values")
        mock_read.return_value = excp
        await ha_client.start()
        for client in ha_client.get_clients():
            await wait_for_status_change(ha_client, client, ConnectionStates.NO_DATA)


class TestHaManager:
    @pytest.mark.asyncio
    async def test_reconnect(self, ha_client):
        await ha_client.start()
        await wait_clients_socket(ha_client, UASocketProtocol.OPEN)
        for c in ha_client.get_clients():
            await c.disconnect()
        # the HaManager task should reconnect all the clients automagically
        await wait_clients_socket(ha_client, UASocketProtocol.OPEN)


class TestReconciliator:
    @pytest.mark.asyncio
    async def test_resubscribe(self, ha_client, srv_variables):
        """
        Here we test that when the HaClient reconnect a client,
        Reconciliator drop any existing subscription and create new one.
        """
        await ha_client.start()
        for c in ha_client.get_clients():
            await wait_for_status_change(ha_client, c, 255)

        node, values = [(n, v) for n, v in srv_variables.items()][0]
        node_str = node.nodeid.to_string()

        # create sub and add node to datachange
        myhandler = MySubHandler()
        sub = await ha_client.create_subscription(100, myhandler)
        await ha_client.subscribe_data_change(sub, [node])
        # wait for the node to appear in real map
        await wait_node_in_real_map(ha_client, sub, node_str)

        # the reconciliator subscription and handle trackers must be up-to-date.
        reconciliator = ha_client.reconciliator
        clients = ha_client.get_clients()
        for client in clients:
            url = client.server_url.geturl()
            assert sub in reconciliator.name_to_subscription[url]
            assert isinstance(
                reconciliator.name_to_subscription[url][sub], Subscription
            )
            assert isinstance(reconciliator.node_to_handle[url][node_str], int)

        primary = await ha_client.get_serving_client(ha_client.get_clients(), None)
        # let's save the primary sub/handle for future comparison
        primary_url = primary.server_url.geturl()
        real_sub = reconciliator.name_to_subscription[primary_url][sub]
        real_handle = reconciliator.node_to_handle[primary_url][node_str]

        # Add to url_to_reset triggers reconciliator to resub
        async with ha_client._url_to_reset_lock:
            ha_client.url_to_reset.add(primary_url)

        # hack to wait for the reconciliator iteration
        sub2 = await ha_client.create_subscription(100, myhandler)
        await wait_sub_in_real_map(ha_client, sub2)

        new_real_handle = reconciliator.node_to_handle[primary_url][node_str]
        new_real_sub = reconciliator.name_to_subscription[primary_url][sub]
        # Once resub, the low-level client subscription must be brand new.
        assert real_sub != new_real_sub
        # However we haven't deleted the MI, so the server returns the same handle
        assert real_handle == new_real_handle

    @pytest.mark.asyncio
    async def test_subscribe_mi_with_batch(self, ha_client, srv_variables, mocker):
        """
        Ensure we are not exceding the threshold of MonitoredItems
        per request when subscribing/unsubscribing.
        """
        await ha_client.start()

        reconciliator = ha_client.reconciliator
        reconciliator.BATCH_MI_SIZE = 1
        myhandler = MySubHandler()
        sub = await ha_client.create_subscription(100, myhandler)
        await wait_sub_in_real_map(ha_client, sub)

        # once the real subscription is created patch it for one client
        first_client = next(iter(ha_client.get_clients()))
        url = first_client.server_url.geturl()
        real_sub = reconciliator.name_to_subscription[url][sub]

        mock_subscribe_data_change = mocker.patch.object(
            real_sub, "subscribe_data_change", wraps=real_sub.subscribe_data_change
        )
        mock_unsubscribe = mocker.patch.object(
            real_sub, "unsubscribe", wraps=real_sub.unsubscribe
        )

        node_list = [n.nodeid.to_string() for n in srv_variables]

        # wait for the node to appear in real map
        await ha_client.subscribe_data_change(sub, node_list)
        for n in node_list:
            await wait_node_in_real_map(ha_client, sub, n)
        assert mock_subscribe_data_change.call_count == 2

        await ha_client.unsubscribe(node_list)
        for n in node_list:
            await wait_node_in_real_map(ha_client, sub, n, negation=True)
        assert mock_unsubscribe.call_count == 2

        reconciliator.BATCH_MI_SIZE = 2
        mock_subscribe_data_change.reset_mock()
        mock_unsubscribe.reset_mock()

        await ha_client.subscribe_data_change(sub, node_list)
        # wait for the node to appear in real map
        for n in node_list:
            await wait_node_in_real_map(ha_client, sub, n)
        assert mock_subscribe_data_change.call_count == 1

        await ha_client.unsubscribe(node_list)
        for n in node_list:
            await wait_node_in_real_map(ha_client, sub, n, negation=True)
        assert mock_unsubscribe.call_count == 1

    @pytest.mark.asyncio
    async def test_remove_bad_nodes_from_both_maps(
        self, ha_client, srv_variables, mocker
    ):
        """
        When a server respond to a MI request with BadUnknownId, make sure
        we remove the faulty node from the ideal and the real map. Otherwhise,
        the ideal_map is bad, and Reconciliator would try to comply indefinitely.
        """
        await ha_client.start()
        node, values = [(n, v) for n, v in srv_variables.items()][0]
        node_str = node.nodeid.to_string()
        myhandler = MySubHandler()
        sub = await ha_client.create_subscription(100, myhandler)
        node_fake = f"{node_str}0"
        node_list = [node_str, node_fake]
        await ha_client.subscribe_data_change(sub, node_list)
        await wait_node_in_real_map(ha_client, sub, node_str)
        reconciliator = ha_client.reconciliator

        for c in ha_client.get_clients():
            url = c.server_url.geturl()
            assert node_str in reconciliator.real_map[url][sub].nodes
            assert node_str in ha_client.ideal_map[url][sub].nodes
            assert node_fake not in reconciliator.real_map[url][sub].nodes
            assert node_fake not in ha_client.ideal_map[url][sub].nodes
