import asyncio
import logging
from asyncua import Client, ua
from asyncua.common.events import Event, get_filter_from_event_type

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
        if (event.NodeId):             
            conditionId = event.NodeId.to_string()
            conditionKeys = self.currentConditions.keys()
            # A alarm/condition appears with Retain=True and disappears with Retain=False            
            if event.Retain and not conditionId in conditionKeys:                          
                self.currentConditions[conditionId] = event
            if not event.Retain and conditionId in conditionKeys:
                del self.currentConditions[conditionId]                
            _logger.info("Current alarms/conditions: %r", conditionKeys)                


async def main():
    # OPCFoundation/UA-.NETStandard-Samples Quickstart AlarmConditionServer
    url = "opc.tcp://localhost:62544/Quickstarts/AlarmConditionServer"
    async with Client(url=url) as client:
        alarmConditionType = await client.nodes.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "0:ConditionType", 
                                                                "0:AcknowledgeableConditionType", "0:AlarmConditionType"])  

        conditionType = await client.nodes.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "0:ConditionType"])
         
        # Create Operand for necessary field ConditionId
        # Hint: The ConditionId is not a property of the event, but it's NodeId.
        #       ConditionId is named "NodeId" in event field list.
        conditionIdOperand = ua.SimpleAttributeOperand()
        conditionIdOperand.TypeDefinitionId = ua.NodeId(ua.ObjectIds.ConditionType)    
        conditionIdOperand.AttributeId = ua.AttributeIds.NodeId 

        # Add ConditionId to select filter
        evfilter = await get_filter_from_event_type([alarmConditionType])        
        evfilter.SelectClauses.append(conditionIdOperand)
               
        # Create subscription for AlarmConditionType
        msclt = SubHandler()
        sub = await client.create_subscription(0, msclt)      
        handle = await sub.subscribe_events(client.nodes.server, alarmConditionType, evfilter)          

        # Call ConditionRefresh to get the current conditions with retain = true
        # Should also be called after reconnects
        await conditionType.call_method("0:ConditionRefresh", ua.Variant(sub.subscription_id, ua.VariantType.UInt32))     

        await asyncio.sleep(30)  
        await sub.unsubscribe(handle)

if __name__ == "__main__":
    asyncio.run(main())
