import pytest
from threading import Thread
import time
from unittest.mock import patch
import sys
import subprocess

from asyncua.tools import uaread, uals, uawrite, uasubscribe, uahistoryread, uaclient, uaserver, uadiscover, uacall, uageneratestructs

@pytest.mark.parametrize("tool", [uaread, uals, uawrite, uasubscribe, uahistoryread, uaclient, uadiscover, uacall, uageneratestructs])
def test_that_tool_can_be_invoked_without_internal_error(tool):
    # It's necessary to mock argv, else the tool is invoked with *pytest's* argv
    with patch.object(sys, 'argv', [""]):
        try:
            tool()
        except SystemExit:
            pass

def test_that_server_can_be_invoked_without_internal_error():
    with patch.object(sys, 'argv', [""]):
        proc = subprocess.Popen(['uaserver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)
        proc.send_signal(subprocess.signal.SIGKILL)
        proc.wait(timeout=1)
        assert proc.returncode == 0

    