## How to update the UA-Nodesets from the OPC Foundation

1) Have a working internet connection (otherwise it will regenerate the old set or fail)
2) run update_ua_nodeset.py
3) That's it

Path to the .pickle file: opcua-asyncio/asyncua/binary_address_space.pickle
Path to the .xml Nodesets: opcua-asyncio/schemas/UA-Nodeset-master/Schema/
Path to the standard_address_space.py files: opcua-asyncio/asyncua/server/standard_address_space/


##Warnings:
- don't put your own created inside UA-Nodeset or UA-Nodeset folder! Make a seperate folder instead like "private-Nodeset"
- don't rename the Nodeset folder. Keep them as is to reduce memory waste and confusion
- in case of questions you can find help here:
    - our Github Discussions: https://github.com/FreeOpcUa/opcua-asyncio/discussions
    - our Gitter Channel: https://gitter.im/FreeOpcUa/opcua-asyncio
- in case of Bugs with the updater, please make an issue: https://github.com/FreeOpcUa/opcua-asyncio/issues
