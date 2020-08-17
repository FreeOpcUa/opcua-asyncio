import sys
sys.path.insert(0, "..")
import logging
from datetime import datetime
import asyncio

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()


from asyncua import ua, uamethod, Server
from asyncua.common.callback import CallbackType



def create_monitored_items(event, dispatcher):
    print("Monitored Item")     

    for idx in range(len(event.response_params)) :
        if (event.response_params[idx].StatusCode.is_good()) :
            nodeId = event.request_params.ItemsToCreate[idx].ItemToMonitor.NodeId
            print(f"Node {nodeId} was created")
         
    
def modify_monitored_items(event, dispatcher):
    print('modify_monitored_items')


def delete_monitored_items(event, dispatcher):
    print('delete_monitored_items')


async def main():
    # optional: setup logging
    logging.basicConfig(level=logging.WARN)
    #logger = logging.getLogger("asyncua.address_space")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.internal_server")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.uaprocessor")
    # logger.setLevel(logging.DEBUG)
    logger = logging.getLogger("asyncua.subscription_service")
    logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server()
    await server.init()
    #await server.disable_clock()
    #server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("FreeOpcUa Example Server")

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.nodes.objects

    # populating our address space
    myfolder = await objects.add_folder(idx, "myEmptyFolder")
    myobj = await objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()    # Set MyVariable to be writable by clients
   

    # starting!
    await server.start()
    
    # Create Callback for item event 
    server.subscribe_server_callback(CallbackType.ItemSubscriptionCreated, create_monitored_items)
    server.subscribe_server_callback(CallbackType.ItemSubscriptionModified, modify_monitored_items)
    server.subscribe_server_callback(CallbackType.ItemSubscriptionDeleted, delete_monitored_items)
    
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
