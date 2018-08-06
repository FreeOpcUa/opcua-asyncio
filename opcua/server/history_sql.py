import logging
from datetime import timedelta
from datetime import datetime
from threading import Lock
import sqlite3

from opcua import ua
from ..ua.ua_binary import variant_from_binary, variant_to_binary
from ..common import Buffer, Event, get_event_properties_from_type_node
from .history import HistoryStorageInterface

__all__ = ["HistorySQLite"]


class HistorySQLite(HistoryStorageInterface):
    """
    history backend which stores data values and object events in a SQLite database
    this backend is intended to only be accessed via OPC UA, therefore all UA Variants saved in
    the history database are in binary format (SQLite BLOBs)
    note that PARSE_DECLTYPES is active so certain data types (such as datetime) will not be BLOBs
    """

    def __init__(self, path="history.db"):
        self.logger = logging.getLogger(__name__)
        self._datachanges_period = {}
        self._db_file = path
        self._lock = Lock()
        self._event_fields = {}
        self._conn = sqlite3.connect(self._db_file, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)

    def new_historized_node(self, node_id, period, count=0):
        with self._lock:
            _c_new = self._conn.cursor()
            table = self._get_table_name(node_id)
            self._datachanges_period[node_id] = period, count
            # create a table for the node which will store attributes of the DataValue object
            # note: Value/VariantType TEXT is only for human reading, the actual data is stored in VariantBinary column
            try:
                _c_new.execute('CREATE TABLE "{tn}" (_Id INTEGER PRIMARY KEY NOT NULL,'
                               ' ServerTimestamp TIMESTAMP,'
                               ' SourceTimestamp TIMESTAMP,'
                               ' StatusCode INTEGER,'
                               ' Value TEXT,'
                               ' VariantType TEXT,'
                               ' VariantBinary BLOB)'.format(tn=table))

            except sqlite3.Error as e:
                self.logger.info("Historizing SQL Table Creation Error for %s: %s", node_id, e)

            self._conn.commit()

    def save_node_value(self, node_id, datavalue):
        with self._lock:
            _c_sub = self._conn.cursor()
            table = self._get_table_name(node_id)
            # insert the data change into the database
            try:
                _c_sub.execute('INSERT INTO "{tn}" VALUES (NULL, ?, ?, ?, ?, ?, ?)'.format(tn=table),
                               (
                                   datavalue.ServerTimestamp,
                                   datavalue.SourceTimestamp,
                                   datavalue.StatusCode.value,
                                   str(datavalue.Value.Value),
                                   datavalue.Value.VariantType.name,
                                   sqlite3.Binary(variant_to_binary(datavalue.Value))
                               )
                              )
            except sqlite3.Error as e:
                self.logger.error("Historizing SQL Insert Error for %s: %s", node_id, e)
            self._conn.commit()
            # get this node's period from the period dict and calculate the limit
            period, count = self._datachanges_period[node_id]

            def execute_sql_delete(condition, args):
                query = ('DELETE FROM "{tn}" WHERE ' + condition).format(tn=table)
                try:
                    _c_sub.execute(query, args)
                except sqlite3.Error as e:
                    self.logger.error("Historizing SQL Delete Old Data Error for %s: %s", node_id, e)
                self._conn.commit()

            if period:
                # after the insert, if a period was specified delete all records older than period
                date_limit = datetime.utcnow() - period
                execute_sql_delete("SourceTimestamp < ?", (date_limit,))

            if count:
                # ensure that no more than count records are stored for the specified node
                execute_sql_delete('SourceTimestamp = (SELECT CASE WHEN COUNT(*) > ? '
                                   'THEN MIN(SourceTimestamp) ELSE NULL END FROM "{tn}")', (count,))

    def read_node_history(self, node_id, start, end, nb_values):
        with self._lock:
            _c_read = self._conn.cursor()
            table = self._get_table_name(node_id)
            start_time, end_time, order, limit = self._get_bounds(start, end, nb_values)
            cont = None
            results = []
            # select values from the database; recreate UA Variant from binary
            try:
                for row in _c_read.execute('SELECT * FROM "{tn}" WHERE "SourceTimestamp" BETWEEN ? AND ? '
                                           'ORDER BY "_Id" {dir} LIMIT ?'.format(tn=table, dir=order),
                                           (start_time, end_time, limit,)):
                    # rebuild the data value object
                    dv = ua.DataValue(variant_from_binary(Buffer(row[6])))
                    dv.SourceTimestamp = row[1]
                    dv.SourceTimestamp = row[2]
                    dv.StatusCode = ua.StatusCode(row[3])
                    results.append(dv)

            except sqlite3.Error as e:
                self.logger.error("Historizing SQL Read Error for %s: %s", node_id, e)

            if nb_values:
                if len(results) > nb_values:
                    cont = results[nb_values].SourceTimestamp
                results = results[:nb_values]
            return results, cont

    def new_historized_event(self, source_id, evtypes, period, count=0):
        with self._lock:
            _c_new = self._conn.cursor()
            # get all fields for the event type nodes
            ev_fields = self._get_event_fields(evtypes)
            self._datachanges_period[source_id] = period
            self._event_fields[source_id] = ev_fields
            table = self._get_table_name(source_id)
            columns = self._get_event_columns(ev_fields)
            # create a table for the event which will store fields generated by the source object's events
            # note that _Timestamp is for SQL query, _EventTypeName is for debugging, be careful not to create event
            # properties with these names
            try:
                _c_new.execute(
                    'CREATE TABLE "{tn}" (_Id INTEGER PRIMARY KEY NOT NULL, _Timestamp TIMESTAMP, _EventTypeName TEXT, {co})'
                    .format(tn=table, co=columns)
                )
            except sqlite3.Error as e:
                self.logger.info("Historizing SQL Table Creation Error for events from %s: %s", source_id, e)
            self._conn.commit()

    def save_event(self, event):
        with self._lock:
            _c_sub = self._conn.cursor()
            table = self._get_table_name(event.SourceNode)
            columns, placeholders, evtup = self._format_event(event)
            event_type = event.EventType  # useful for troubleshooting database
            # insert the event into the database
            try:
                _c_sub.execute(
                    'INSERT INTO "{tn}" ("_Id", "_Timestamp", "_EventTypeName", {co}) VALUES (NULL, "{ts}", "{et}", {pl})'
                    .format(tn=table, co=columns, ts=event.Time, et=event_type, pl=placeholders), evtup
                )
            except sqlite3.Error as e:
                self.logger.error("Historizing SQL Insert Error for events from %s: %s", event.SourceNode, e)
            self._conn.commit()
            # get this node's period from the period dict and calculate the limit
            period = self._datachanges_period[event.SourceNode]
            if period:
                # after the insert, if a period was specified delete all records older than period
                date_limit = datetime.utcnow() - period
                try:
                    _c_sub.execute('DELETE FROM "{tn}" WHERE Time < ?'.format(tn=table),
                                   (date_limit.isoformat(' '),))
                except sqlite3.Error as e:
                    self.logger.error("Historizing SQL Delete Old Data Error for events from %s: %s",
                                      event.SourceNode, e)
                self._conn.commit()

    def read_event_history(self, source_id, start, end, nb_values, evfilter):
        with self._lock:
            _c_read = self._conn.cursor()
            table = self._get_table_name(source_id)
            start_time, end_time, order, limit = self._get_bounds(start, end, nb_values)
            clauses, clauses_str = self._get_select_clauses(source_id, evfilter)
            cont = None
            cont_timestamps = []
            results = []
            # select events from the database; SQL select clause is built from EventFilter and available fields
            try:
                for row in _c_read.execute(
                        'SELECT "_Timestamp", {cl} FROM "{tn}" WHERE "_Timestamp" BETWEEN ? AND ? ORDER BY "_Id" {dir} LIMIT ?'
                        .format(cl=clauses_str, tn=table, dir=order), (start_time, end_time, limit)):
                    fdict = {}
                    cont_timestamps.append(row[0])
                    for i, field in enumerate(row[1:]):
                        if field is not None:
                            fdict[clauses[i]] = variant_from_binary(Buffer(field))
                        else:
                            fdict[clauses[i]] = ua.Variant(None)
                    results.append(Event.from_field_dict(fdict))
            except sqlite3.Error as e:
                self.logger.error("Historizing SQL Read Error events for node %s: %s", source_id, e)
            if nb_values:
                if len(results) > nb_values:  # start > ua.get_win_epoch() and
                    cont = cont_timestamps[nb_values]
                results = results[:nb_values]
            return results, cont

    def _get_table_name(self, node_id):
        return str(node_id.NamespaceIndex) + "_" + str(node_id.Identifier)

    def _get_event_fields(self, evtypes):
        """
        Get all fields from the event types that are to be historized
        Args:
            evtypes: List of event type nodes

        Returns: List of fields for all event types
        """
        # get all fields from the event types that are to be historized
        ev_aggregate_fields = []
        for event_type in evtypes:
            ev_aggregate_fields.extend((get_event_properties_from_type_node(event_type)))
        ev_fields = []
        for field in set(ev_aggregate_fields):
            ev_fields.append(field.get_display_name().Text)
        return ev_fields

    @staticmethod
    def _get_bounds(start, end, nb_values):
        order = "ASC"
        if start is None or start == ua.get_win_epoch():
            order = "DESC"
            start = ua.get_win_epoch()
        if end is None or end == ua.get_win_epoch():
            end = datetime.utcnow() + timedelta(days=1)
        if start < end:
            start_time = start.isoformat(" ")
            end_time = end.isoformat(" ")
        else:
            order = "DESC"
            start_time = end.isoformat(" ")
            end_time = start.isoformat(" ")
        if nb_values:
            limit = nb_values + 1  # add 1 to the number of values for retrieving a continuation point
        else:
            limit = -1  # in SQLite a LIMIT of -1 returns all results
        return start_time, end_time, order, limit

    def _format_event(self, event):
        """
        Convert an event object triggered by the subscription into ordered lists for the SQL insert string

        Args:
            event: The event returned by the subscription

        Returns: List of event fields (SQL column names), List of '?' placeholders, Tuple of variant binaries
        """
        placeholders = []
        ev_variant_binaries = []
        ev_variant_dict = event.get_event_props_as_fields_dict()
        names = list(ev_variant_dict.keys())
        names.sort()  # sort alphabetically since dict is not sorted
        # split dict into two synchronized lists which will be converted to SQL strings
        # note that the variants are converted to binary objects for storing in SQL BLOB format
        for name in names:
            variant = ev_variant_dict[name]
            placeholders.append("?")
            ev_variant_binaries.append(sqlite3.Binary(variant_to_binary(variant)))
        return self._list_to_sql_str(names), self._list_to_sql_str(placeholders, False), tuple(ev_variant_binaries)

    def _get_event_columns(self, ev_fields):
        fields = []
        for field in ev_fields:
            fields.append(field + " BLOB")
        return self._list_to_sql_str(fields, False)

    def _get_select_clauses(self, source_id, evfilter):
        s_clauses = []
        for select_clause in evfilter.SelectClauses:
            try:
                if not select_clause.BrowsePath:
                    s_clauses.append(select_clause.Attribute.name)
                else:
                    name = select_clause.BrowsePath[0].Name
                    s_clauses.append(name)
            except AttributeError:
                self.logger.warning("Historizing SQL OPC UA Select Clause Warning for node %s,"
                                    " Clause: %s:", source_id, select_clause)
        # remove select clauses that the event type doesn't have; SQL will error because the column doesn't exist
        clauses = [x for x in s_clauses if x in self._event_fields[source_id]]
        return clauses, self._list_to_sql_str(clauses)

    @staticmethod
    def _list_to_sql_str(ls, quotes=True):
        items = [f'"{item}"' if quotes else str(item) for item in ls]
        return ", ".join(items)

    def stop(self):
        with self._lock:
            self._conn.close()
            self.logger.info('Historizing SQL connection closed')
