import unittest

from opcua import Client
from opcua import Server
from opcua import ua

try:
    from opcua.crypto import uacrypto
    from opcua.crypto import security_policies
except ImportError:
    print("WARNING: CRYPTO NOT AVAILABLE, CRYPTO TESTS DISABLED!!")
    disable_crypto_tests = True
else:
    disable_crypto_tests = False


port_num1 = 48515
port_num2 = 48512

@unittest.skipIf(disable_crypto_tests, "crypto not available")
class TestCryptoConnect(unittest.TestCase):

    '''
    Test connectino with a server supporting crypto 

    '''
    @classmethod
    def setUpClass(cls):
        # start our own server
        cls.srv_crypto = Server()
        cls.uri_crypto = 'opc.tcp://127.0.0.1:{0:d}'.format(port_num1)
        cls.srv_crypto.set_endpoint(cls.uri_crypto)
        # load server certificate and private key. This enables endpoints
        # with signing and encryption.
        cls.srv_crypto.load_certificate("examples/certificate-example.der")
        cls.srv_crypto.load_private_key("examples/private-key-example.pem")
        cls.srv_crypto.start()

        # start a server without crypto
        cls.srv_no_crypto = Server()
        cls.uri_no_crypto = 'opc.tcp://127.0.0.1:{0:d}'.format(port_num2)
        cls.srv_no_crypto.set_endpoint(cls.uri_no_crypto)
        cls.srv_no_crypto.start()

    @classmethod
    def tearDownClass(cls):
        # stop the server 
        cls.srv_no_crypto.stop()
        cls.srv_crypto.stop()

    def test_nocrypto(self):
        clt = Client(self.uri_no_crypto)
        clt.connect()
        try:
            clt.get_objects_node().get_children()
        finally:
            clt.disconnect()

    def test_nocrypto_fail(self):
        clt = Client(self.uri_no_crypto)
        with self.assertRaises(ua.UaError):
            clt.set_security_string("Basic256Sha256,Sign,examples/certificate-example.der,examples/private-key-example.pem")

    def test_basic256sha256(self):
        clt = Client(self.uri_crypto)
        try:
            clt.set_security_string("Basic256Sha256,Sign,examples/certificate-example.der,examples/private-key-example.pem")
            clt.connect()
            self.assertTrue(clt.get_objects_node().get_children())
        finally:
            clt.disconnect()

    def test_basic256sha256_encrypt(self):
        clt = Client(self.uri_crypto)
        try:
            clt.set_security_string("Basic256Sha256,SignAndEncrypt,examples/certificate-example.der,examples/private-key-example.pem")
            clt.connect()
            self.assertTrue(clt.get_objects_node().get_children())
        finally:
            clt.disconnect()

    def test_basic256sha56_encrypt_success(self):
        clt = Client(self.uri_crypto)
        try:
            clt.set_security(security_policies.SecurityPolicyBasic256Sha256,
                             'examples/certificate-example.der',
                             'examples/private-key-example.pem',
                             None,
                             ua.MessageSecurityMode.SignAndEncrypt
                             )
            clt.connect()
            self.assertTrue(clt.get_objects_node().get_children())
        finally:
            clt.disconnect()

    def test_basic256sha56_encrypt_fail(self):
        # FIXME: how to make it fail???
        clt = Client(self.uri_crypto)
        with self.assertRaises(ua.UaError):
            clt.set_security(security_policies.SecurityPolicyBasic256Sha256,
                             'examples/certificate-example.der',
                             'examples/private-key-example.pem',
                             None,
                             ua.MessageSecurityMode.None_
                             )
