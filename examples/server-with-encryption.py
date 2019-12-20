import sys
import time

sys.path.insert(0, "..")

from asyncua import Server


if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # load server certificate and private key. This enables endpoints
    # with signing and encryption.
    server.load_certificate("certificate-example.der")
    server.load_private_key("private-key-example.pem")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()

    # populating our address space
    myobj = objects.add_object(idx, "MyObject")
    myvar = myobj.add_variable(idx, "MyVariable", 6.7)
    myvar.set_writable()    # Set MyVariable to be writable by clients

    # starting!
    server.start()
    try:
        count = 0
        while True:
            time.sleep(1)
            count += 0.1
            myvar.write(count)
    finally:
        #close connection, remove subcsriptions, etc
        server.stop()
