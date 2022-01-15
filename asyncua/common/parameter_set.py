from asyncore import dispatcher
from asyncua import Node, Server, ua
from asyncua.common.callback import CallbackType, CallbackService, ServerItemCallback

class ParameterSet:
    """
    Parmeter set for easy access of parameters
 
    A parameter set is an object only containing variables. 
    This class can be used for e.g. devices or state machines.

    @param node: the node to the object representing the parameter set
    @param subscribe: subscribe to value changes of the parameters
    @param notifier: method to be called when a value in the parameter set changes 
    @param source: server or client object as source of the information
    """
    def __init__(self, node : Node, subscribe=False, notifier=None, source=None, interval=100):
        self._parameters = {}
        self._node = node
        self._source = source
        self.name = ''
        self._notify_data_change = notifier
        self._subscribe_data_change = subscribe
        self._parameter_nodes = []
        self._subscribe = subscribe
        self._parameter_ids = []
        self._subscription_interval = interval
        self._subscription = None

    async def init(self):
        # Get the ParameterSet name
        bn = await self._node.read_browse_name()
        self.name = bn.Name

        # Browse ParameterSet object
        parameters = await self._node.get_children(refs=33)
        for p in parameters:
            bn = await p.read_browse_name()
            val = await p.read_value()
            # Add the parameter to parameter dictionary 
            self._parameters[bn.Name] = {'Name': bn.Name, 'Default': val, 'Node': p, 'Value': val} # TODO: add unit and range information 
            self._parameter_nodes.append(p)
            self._parameter_ids.append(p.nodeid)
            setattr(p, 'value', val)
            # Add parameter node as an class attribute 
            setattr(self, bn.Name, p) 
            
        if self._subscribe_data_change and self._source:
            self._subscription = await self._source.create_subscription(self._subscription_interval, self)
            self._state_change_subscription = await self._subscription.subscribe_data_change(self._parameter_nodes)

        return self._parameters

    async def datachange_notification(self, node, val, data): 
        for p in self._parameters: 
            if self._parameters[p]['Node'] == node: 
                self._parameters[p]['Node'].value = val
                self._parameters[p]['Value'] = val 

        if self._notify_data_change: 
            await self._notify_data_change(node, val)
    
    async def update_subscription_interval(self, interval): 
        if self._subscription: 
            p = ua.ModifySubscriptionParameters()
            p.RequestedPublishingInterval = interval 
            p.SubscriptionId = self._subscription.subscription_id
            self._subscription_interval = interval
            await self._subscription.update(p)
            
    def get_parameter_list(self): 
        return self._parameter_nodes

    def get_parameter_node(self, name): 
        return self._parameters[name]['Node']

    async def get_parameter_dict(self): 
        """ 
        Return the parameter dict with current values 
        """
        for p in self._parameters:
            node = self._parameters[p]['Node']
            self._parameters[p]['Value'] = await node.read_value()
        return self._parameters

    async def read_value(self, name: str):
        """
        Read the value for the parameter with the given name

        @param name: name of the parameters
        """
        return await self._parameters[name]['Node'].read_value()
    
    def get_value(self, name): 
        """
        Read the value for the parameter with the given name. 

        @param name: name of the parameters
        """
        return self._parameters[name]['Value']
    
    async def set_value(self, name, val, varianttype=None): 
        """
        Write the value for the parameter with the given name

        @param val: value of the parameter 
        @param varianttype: type of the parameter
        """
        if not varianttype: 
            self._parameters[name]['Node'].value = val
        else: 
            self._parameters[name]['Node'].value = ua.Variant(val, varianttype)

        await self._parameters[name]['Node'].write_value(val, varianttype)

    async def set_default_value(self, name, val=None): 
        """
        Set the default value to a parameter

        @param name: name of the parameter 
        @param val: if this is given default and current value is set to it 
        """
        if val:
            self._parameters[name]['Devault'] = val
            await self._parameters[name]['Node'].write_value(val)
        else: 
            val = self._parameters[name]['Default']
            await self._parameters[name]['Node'].write_value(val)

    async def print_parameter_list(self):
        """
        Print the parameter list
        """
        s = '\n#####################################################\n'
        s += '|{:^51}|'.format(self.name)
        s += '\n-----------------------------------------------------\n'
        s += '|{:^30}|{:^20}|'.format('Name', 'Value')
        s += '\n#####################################################'
        print(s)
        for p in self._parameters: 
            name = self._parameters[p]['Name']
            node = self._parameters[p]['Node']
            value = await node.read_value()
            typedefinition = await node.read_type_definition()
            if value != None: 
                s = '|{:^30}|{:^20}|'.format(name, value)
            else: 
                nan = 'nan'
                s = f'|{name:^30}|{nan:^20}|'
            s += '\n-----------------------------------------------------'
            print(s)

        print()
