How to generate Python from UA-Nodeset:

clone/download https://github.com/OPCFoundation/UA-Nodeset.git and copy it into "opcua-asyncio\schemas"
now there should be an "UA-Nodeset-master"-folder in "opcua-asyncio\schemas"

run generate_address_space.py (check for logs or errors)
run ...
run ...

Path to the .pickle file: opcua-asyncio/asyncua/binary_address_space.pickle
Path to the .xml Nodesets: opcua-asyncio/schemas/UA-Nodeset-master/Schema/
Path to the standard_address_space.py files: opcua-asyncio/asyncua/server/standard_address_space/