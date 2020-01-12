from ..common.events import Event
from .history import HistoryStorageInterface
from motor.motor_asyncio import AsyncIOMotorClient
from asyncua.ua.uatypes import LocalizedText
from asyncua.ua.uatypes import VariantType
import json


class HistoryMongoDb(HistoryStorageInterface):
    """
    Create an interface for storing and tracking event and variable history with the
    mongodb database server.

    In this example I am using a maximum of 5000 results limit and storing the last result
    as an ack of the date of the last event to be fetched.
    The biggest reason was the need that I am having to deploy opcua servers that store
    data every 1 second and can request the track record of at least one year which will add
    up to a total of 31.104.000 samples.

    Limiting this value to stream an http server with an internal opcua client that will
    fetch the samples from the opcua server and feed a graph to an html page.

    """
    async def init(self):
        pass

    async def new_historized_node(self, node_id, period, count=0):
        pass

    async def save_node_value(self, node_id, datavalue):
        pass

    async def read_node_history(self, node_id, start, end, nb_values, session):
        pass

    async def new_historized_event(self, source_id, evtypes, period, count=0):
        pass

    async def save_event(self, event):
        message_event = event.get_event_props_as_fields_dict()
        message = message_event["Message"].Value.Text
        time_stamp = message_event["Time"].Value

        _event = dict()
        _event["message"] = message
        _event["time_stamp"] = time_stamp

        self.collection.insert_one(_event)

    def format_event(self, document):
        event = Event()
        content = LocalizedText(text=json.dumps(document["message"]))
        event.add_property("Message", content, VariantType(21))
        return event

    async def read_event_history(self, source_id, start, end, nb_values, evfilter, session):
        events_query = list()
        if (not nb_values) or nb_values > self.limits_for_request:
            _max_value = 5001
        else:
            _max_value = nb_values + 1

        query = {'$and': [{"time_stamp": {"$gte": start}}, {"time_stamp": {"$lte": end}}]}
        cursor = self.collection.find(query, {"_id": 0}).sort([('sample_datetime', 1)]).limit(_max_value)
        async for document in cursor:
            events_query.append(document)

        events = list(map(self.format_event, events_query))
        length = len(events)

        if length > (_max_value - 1):
            last_event = events_query[length - 1]
            last_time_stamp = last_event["time_stamp"]

            event = Event()
            last_sample = dict()
            last_sample["last_sample"] = last_time_stamp.iso_format()
            content = LocalizedText(text=json.dumps(last_sample))
            event.add_property("Message", content, VariantType(21))

            events.pop(length - 1)
            events.append(event)

        return events, None

    async def stop(self):
        pass

    def __init__(self):
        self.server_database: AsyncIOMotorClient = AsyncIOMotorClient("10.10.20.100:27017")
        self.database = self.server_database["MyHistoryEvents"]
        self.collection = self.database["myevents"]
        self.limits_for_request = 5000
