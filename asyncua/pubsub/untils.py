import datetime
from asyncua.ua import VersionTime


def version_time_now():
    # Generates seconds since year 2000 see. Part4 7.38
    VersionTime((datetime.datetime.utcnow() - datetime.datetime(2000, 1, 1, 0, 0)).total_seconds())
