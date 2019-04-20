from asyncua import Client


class HelloClient:
    def __init__(self, endpoint):
        self.client = Client(endpoint)

    def __enter__(self):
        self.client.connect()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()


if __name__ == '__main__':
    with HelloClient("opc.tcp://localhost:40840/freeopcua/server/") as client:
        root = client.get_root_node()
        print("Root node is: ", root)
        objects = client.get_objects_node()
        print("Objects node is: ", objects)

        hellower = objects.get_child("0:Hellower")
        print("Hellower is: ", hellower)

        resulting_text = hellower.call_method("0:SayHello", False)
        print(resulting_text)

        resulting_text = hellower.call_method("1:SayHello2", True)
        print(resulting_text)

        resulting_array = hellower.call_method("1:SayHelloArray", False)
        print(resulting_array)
