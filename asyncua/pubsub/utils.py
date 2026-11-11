import datetime

from asyncua.ua import VersionTime


def version_time_now() -> VersionTime:
    # Generates seconds since year 2000 see. Part4 7.38
    return VersionTime(
        (datetime.datetime.now(datetime.UTC) - datetime.datetime(2000, 1, 1, 0, 0, 0, 0, datetime.UTC)).total_seconds()
    )
