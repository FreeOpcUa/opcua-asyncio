import asyncio
import logging
from asyncua import Client, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class SubHandler:
    def __init__(self):
        self.currentConditions = {}

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operatsion there. Create another
    thread if you need to do such a thing
    """

    def event_notification(self, event):
        _logger.info("New event received: %r", event)
        # To avoid special event for ConditionRefresh 'Condition refresh started for subscription X.'
        if event.NodeId:
            conditionId = event.NodeId.to_string()
            conditionKeys = self.currentConditions.keys()
            # A alarm/condition appears with Retain=True and disappears with Retain=False
            if event.Retain and conditionId not in conditionKeys:
                self.currentConditions[conditionId] = event
            if not event.Retain and conditionId in conditionKeys:
                del self.currentConditions[conditionId]
            _logger.info("Current alarms/conditions: %r", conditionKeys)


async def main():
    # OPCFoundation/UA-.NETStandard-Samples Quickstart AlarmConditionServer
    url = "opc.tcp://localhost:62544/Quickstarts/AlarmConditionServer"
    async with Client(url=url) as client:
        # Standard types in namespace 0 have fixed NodeIds
        conditionType = client.get_node("ns=0;i=2782")
        alarmConditionType = client.get_node("ns=0;i=2915")

        # Create subscription for AlarmConditionType
        msclt = SubHandler()
        sub = await client.create_subscription(0, msclt)
        handle = await sub.subscribe_alarms_and_conditions(client.nodes.server, alarmConditionType)

        # Call ConditionRefresh to get the current conditions with retain = true
        # Should also be called after reconnects
        await conditionType.call_method("0:ConditionRefresh", ua.Variant(sub.subscription_id, ua.VariantType.UInt32))

        await asyncio.sleep(30)
        await sub.unsubscribe(handle)


if __name__ == "__main__":
    asyncio.run(main())
