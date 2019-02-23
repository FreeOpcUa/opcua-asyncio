import unittest
import logging
import sys
sys.path.insert(0, "..")
sys.path.insert(0, ".")


from tests_cmd_lines import TestCmdLines
from tests_server import TestServer, TestServerCaching, TestServerStartError
from tests_client import TestClient
from tests_standard_address_space import StandardAddressSpaceTests
from tests_unit import TestUnit, TestMaskEnum
from tests_history import TestHistory, TestHistorySQL, TestHistoryLimits, TestHistorySQLLimits
from tests_crypto_connect import TestCryptoConnect
from tests_uaerrors import TestUaErrors
from tests_custom_structures import TypeDictionaryBuilderTest


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    #l = logging.getLogger("asyncua.server.internal_subscription")
    #l.setLevel(logging.DEBUG)
    #l = logging.getLogger("asyncua.server.internal_server")
    #l.setLevel(logging.DEBUG)

    unittest.main(verbosity=3)
