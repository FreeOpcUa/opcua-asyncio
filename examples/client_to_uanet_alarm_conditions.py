import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.subscription import OpcEvent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


async def consume_conditions(sub) -> None:
    current_conditions: dict[str, object] = {}
    async for event in sub:
        if not isinstance(event, OpcEvent):
            continue
        evt = event.event
        _logger.info("New event received: %r", evt)
        if evt.NodeId is None:
            continue
        condition_id = evt.NodeId.to_string()
        if evt.Retain and condition_id not in current_conditions:
            current_conditions[condition_id] = evt
        elif not evt.Retain and condition_id in current_conditions:
            del current_conditions[condition_id]
        _logger.info("Current alarms/conditions: %r", list(current_conditions.keys()))


async def main() -> None:
    url = "opc.tcp://localhost:62544/Quickstarts/AlarmConditionServer"
    async with Client(url=url) as client:
        condition_type = client.get_node("ns=0;i=2782")
        alarm_condition_type = client.get_node("ns=0;i=2915")

        async with await client.create_subscription(0) as sub:
            await sub.subscribe_alarms_and_conditions(client.nodes.server, alarm_condition_type)

            await condition_type.call_method(
                "0:ConditionRefresh", ua.Variant(sub.subscription_id, ua.VariantType.UInt32)
            )

            consumer = asyncio.create_task(consume_conditions(sub))
            try:
                await asyncio.sleep(30)
            finally:
                consumer.cancel()


if __name__ == "__main__":
    asyncio.run(main())
