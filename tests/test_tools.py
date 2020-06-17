import pytest
from unittest.mock import patch
import sys

from asyncua.tools import uaread, uals, uawrite, uasubscribe, uahistoryread, uaclient, uaserver, uadiscover, uacall, uageneratestructs

tools = [uaread, uals, uawrite, uasubscribe, uahistoryread, uaclient, uaserver, uadiscover, uacall, uageneratestructs]

@pytest.mark.parametrize("tool", tools)
def test_that_tool_can_be_invoked_without_internal_error(tool):
    mock_argv = [""]

    # It's necessary to mock argv, else the tool is invoked with *pytest's* argv
    with patch.object(sys, 'argv', mock_argv):
        try:
            tool()
        except SystemExit:
            pass
