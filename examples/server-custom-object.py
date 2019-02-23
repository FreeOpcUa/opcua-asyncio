'''
   Show 3 different examples for creating an object:
   1) create a basic object
   2) create a new object type and a instance of the new object type
   3) import a new object from xml address space and create a instance of the new object type
'''
import sys
sys.path.insert(0, "..")
import time


from asyncua import ua, Server


if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()

    # Example 1 - create a basic object
    #-------------------------------------------------------------------------------
    myobj = objects.add_object(idx, "MyObject")    
    #-------------------------------------------------------------------------------


    # Example 2 - create a new object type and a instance of the new object type
    #-------------------------------------------------------------------------------
    types = server.get_node(ua.ObjectIds.BaseObjectType)
    
    object_type_to_derive_from = server.get_root_node().get_child(["0:Types", 
                                                                   "0:ObjectTypes", 
                                                                   "0:BaseObjectType"])
    mycustomobj_type = types.add_object_type(idx, "MyCustomObjectType")
    mycustomobj_type.add_variable(0, "var_should_be_there_after_instantiate", 1.0) # demonstrates instantiate
    
    myobj = objects.add_object(idx, "MyCustomObjectA", mycustomobj_type.nodeid)
    #-------------------------------------------------------------------------------


    # Example 3 - import a new object from xml address space and create a instance of the new object type
    #-------------------------------------------------------------------------------
    # Import customobject type
    server.import_xml('customobject.xml')
        

    # get nodeid of custom object type by one of the following 3 ways:
    # 1) Use node ID
    # 2) Or Full path
    # 3) Or As child from parent
    myobject1_type_nodeid = ua.NodeId.from_string('ns=%d;i=2' % idx)
    myobject2_type_nodeid = server.get_root_node().get_child(["0:Types", "0:ObjectTypes", "0:BaseObjectType", "%d:MyCustomObjectType" % idx]).nodeid
    myobject3_type_nodeid = server.get_node(ua.ObjectIds.BaseObjectType).get_child(["%d:MyCustomObjectType" % idx]).nodeid


    # populating our address space    
    myobj = objects.add_object(idx, "MyCustomObjectB", myobject3_type_nodeid)
    #-------------------------------------------------------------------------------

    
    # starting!
    server.start()

    try:
        while True:
            time.sleep(1)
    finally:
        # close connection, remove subcsriptions, etc
        server.stop()
