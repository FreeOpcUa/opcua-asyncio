from ..common.events import Event
from .history import HistoryStorageInterface
from motor.motor_asyncio import AsyncIOMotorClient
from asyncua.ua.uatypes import LocalizedText
from asyncua.ua.uatypes import VariantType
import json
from asyncua.server.internal_session import InternalSession


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

    async def read_event_history(self, source_id, start, end, nb_values, evfilter, session: InternalSession):
        # create the variables
        _session_id = str(session.session_id)
        events_query = list()
        query = {'$and': [{"time_stamp": {"$gte": start}}, {"time_stamp": {"$lte": end}}]}

        # limits the number of requests per query
        if (not nb_values) or nb_values > self.limits_for_request:
            _max_value = self.limits_for_request + 1
        else:
            _max_value = nb_values + 1

        # check if the session exists, otherwise create a data key for it
        if _session_id not in self.clients_session_packages:
            self.clients_session_packages[_session_id] = dict()
            self.clients_session_packages[_session_id]["isFirstRequest"] = True
            self.clients_session_packages[_session_id]["length"] = 0
            self.clients_session_packages[_session_id]["count_pages"] = 0
            self.clients_session_packages[_session_id]["pages"] = 0

        # if the session already exists it means it's a next appointment
        else:
            self.clients_session_packages[_session_id]["count_pages"] += 1

        # create initial query data, return number of documents, calculate number of required pages.
        if self.clients_session_packages[_session_id]["isFirstRequest"]:
            length_request = await self.collection.count_documents(query)
            pages = round(length_request / (_max_value - 1))
            missing = length_request % (_max_value - 1)

            if missing > 0:
                pages += 1

            self.clients_session_packages[_session_id]["length"] = length_request
            self.clients_session_packages[_session_id]["pages"] = pages
            self.clients_session_packages[_session_id]["isFirstRequest"] = False

        # execute the query by sorting by date and limiting the cursor to only the number requested by the client
        cursor = self.collection.find(query, {"_id": 0}).sort([('sample_datetime', 1)]).limit(_max_value)
        async for document in cursor:
            events_query.append(document)

        events = list(map(self.format_event, events_query))
        length = len(events)

        # if the query returns one more format document and event to display pagination data
        if length > (_max_value - 1):
            last_event = events_query[length - 1]
            last_time_stamp = last_event["time_stamp"]

            last_sample = dict()
            last_sample["pages"] = self.clients_session_packages[_session_id]["pages"]
            last_sample["count"] = self.clients_session_packages[_session_id]["count_pages"]
            last_sample["length"] = self.clients_session_packages[_session_id]["length"]
            last_sample["last_sample"] = last_time_stamp.isoformat()

            event = Event()
            content = LocalizedText(text=json.dumps(last_sample))
            event.add_property("Message", content, VariantType(21))

            events.pop(length - 1)
            events.append(event)

        pages = self.clients_session_packages[_session_id]["pages"]
        count_pages = self.clients_session_packages[_session_id]["count_pages"]

        # check if the query number is equal to the number of pages, if yes delete the session
        if count_pages >= (pages - 1):
            if _session_id in self.clients_session_packages:
                del self.clients_session_packages[_session_id]

        return events, None

    async def stop(self):
        pass

    def __init__(self):
        self.server_database: AsyncIOMotorClient = AsyncIOMotorClient("10.10.20.100:27017")
        self.database = self.server_database["MyHistoryEvents"]
        self.collection = self.database["myevents"]
        self.limits_for_request = 5000
        self.clients_session_packages = dict()
