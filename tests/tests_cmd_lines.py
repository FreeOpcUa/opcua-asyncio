import unittest
import subprocess

from asyncua import Server


port_num = 48530


class TestCmdLines(unittest.TestCase):

    '''
    Test command lines
    '''
    @classmethod
    def setUpClass(cls):
        cls.srv = Server()
        cls.srv_url = 'opc.tcp://127.0.0.1:{0:d}'.format(port_num)
        cls.srv.set_endpoint(cls.srv_url)
        objects = cls.srv.get_objects_node()
        obj = objects.add_object(4, "directory")
        var = obj.add_variable(4, "variable", 1.999)
        var2 = obj.add_variable(4, "variable2", 1.777)
        var2.set_writable()
        cls.srv.start()

    def test_uals(self):
        s = subprocess.check_output(["python", "tools/uals", "--url", self.srv_url])
        self.assertIn(b"i=85", s)
        self.assertNotIn(b"i=89", s)
        self.assertNotIn(b"1.999", s)
        s = subprocess.check_output(["python", "tools/uals", "--url", self.srv_url, "-d", "3"])
        self.assertIn(b"1.999", s)

    def test_uaread(self):
        s = subprocess.check_output(["python", "tools/uaread", "--url", self.srv_url, "--path", "0:Objects,4:directory,4:variable"])
        self.assertIn(b"1.999", s)

    def test_uawrite(self):
        s = subprocess.check_output(["python", "tools/uawrite", "--url", self.srv_url, "--path", "0:Objects,4:directory,4:variable2", "1.789"])
        s = subprocess.check_output(["python", "tools/uaread", "--url", self.srv_url, "--path", "0:Objects,4:directory,4:variable2"])
        self.assertIn(b"1.789", s)
        self.assertNotIn(b"1.999", s)

    def test_uadiscover(self):
        s = subprocess.check_output(["python", "tools/uadiscover", "--url", self.srv_url])
        self.assertIn(b"opc.tcp://127.0.0.1", s)
        self.assertIn(b"FreeOpcUa", s)
        self.assertIn(b"urn:freeopcua:python:server", s)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()


