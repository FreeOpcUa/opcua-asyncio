import sys
sys.path.insert(0, "../..")
import time


from asyncua.sync import Server


if __name__ == "__main__":
    # set up our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # populating our address space
    myobj = server.nodes.objects.add_object(idx, "MyObject")
    myvar = myobj.add_variable(idx, "MyVariable", 6.7)
    myvar.set_writable()    # Set MyVariable to be writable by clients

    # starting!
    server.start()

    try:
        count = 0
        while True:
            time.sleep(1)
            count += 0.1
            myvar.write_value(count)
    finally:
        #close connection, remove subscriptions, etc
        server.stop()
