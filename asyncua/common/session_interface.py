from abc import ABC, abstractmethod
from typing import List
from asyncua import ua


class AbstractSession(ABC):
    """
    An abstract interface for the sessionbased Service Sets like:
    NodeManagement, View, Attribute, Method, MonitoredItem and Subscription
    """

    # View Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.8.1/

    @abstractmethod
    async def browse(self, parameters: ua.BrowseParameters) -> List[ua.BrowseResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.8.2/

        This Service is used to discover the References of a specified Node.
        The browse can be further limited by the use of a View.
        This Browse Service also supports a primitive filtering capability.
        """

    @abstractmethod
    async def browse_next(self, parameters: ua.BrowseNextParameters) -> List[ua.BrowseResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.8.3/

        This Service is used to request the next set of Browse or BrowseNext response information that is too large to be sent in a single response.
        “Too large” in this context means that the Server is not able to return a larger response or that the number of results
        to return exceeds the maximum number of results to return that was specified by the Client in the original Browse request.
        The BrowseNext shall be submitted on the same Session that was used to submit the Browse or BrowseNext that is being continued.
        """

    @abstractmethod
    async def translate_browsepaths_to_nodeids(self, browse_paths: List[ua.BrowsePath]) -> List[ua.BrowsePathResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.8.4/

        This Service is used to request that the Server translates one or more browse paths to NodeIds.
        Each browse path is constructed of a starting Node and a RelativePath.
        The specified starting Node identifies the Node from which the RelativePath is based.
        The RelativePath contains a sequence of ReferenceTypes and BrowseNames.
        """

    @abstractmethod
    async def register_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.8.5/

        A Server often has no direct access to the information that it manages.
        Variables or services might be in underlying systems where additional effort is required to establish a connection to these systems.
        The RegisterNodes Service can be used by Clients to register the Nodes that they know they will access repeatedly (e.g. Write, Call).
        It allows Servers to set up anything needed so that the access operations will be more efficient.
        Clients can expect performance improvements when using registered NodeIds, but the optimization measures are vendor-specific.
        For Variable Nodes Servers shall concentrate their optimization efforts on the Value Attribute.
        """

    @abstractmethod
    async def unregister_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.8.6/

        This Service is used to unregister NodeIds that have been obtained via the RegisterNodes service.
        """

    # Attribute Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.10.1/

    @abstractmethod
    async def read(self, parameters: ua.ReadParameters) -> List[ua.DataValue]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.10.2/

        This Service is used to read one or more Attributes of one or more Nodes.
        For constructed Attribute values whose elements are indexed, such as an array,
        this Service allows Clients to read the entire set of indexed values as a composite,
        to read individual elements or to read ranges of elements of the composite.
        """

    @abstractmethod
    async def write(self, parameters: ua.WriteParameters) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.10.4/

        This Service is used to write values to one or more Attributes of one or more Nodes.
        For constructed Attribute values whose elements are indexed, such as an array,
        this Service allows Clients to write the entire set of indexed values as a composite,
        to write individual elements or to write ranges of elements of the composite.
        """

    @abstractmethod
    async def history_read(self, params: ua.HistoryReadParameters) -> List[ua.HistoryReadResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.10.3/

        This Service is used to read historical values or Events of one or more Nodes.
        For constructed Attribute values whose elements are indexed, such as an array,
        this Service allows Clients to read the entire set of indexed values as a composite,
        to read individual elements or to read ranges of elements of the composite.
        Servers may make historical values available to Clients using this Service,
        although the historical values themselves are not visible in the AddressSpace.
        """

    # NodeManagement Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.7.1/

    @abstractmethod
    async def add_nodes(self, params: ua.AddNodesParameters) -> List[ua.AddNodesResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.7.2/

        This Service is used to add one or more Nodes into the AddressSpace hierarchy.
        Using this Service, each Node is added as the TargetNode of a HierarchicalReference to ensure that
        the AddressSpace is fully connected and that the Node is added as a child within the AddressSpace hierarchy (see OPC 10000-3).
        """

    @abstractmethod
    async def add_references(self, refs: List[ua.AddReferencesItem]) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.7.3/

        This Service is used to add one or more References to one or more Nodes.
        The NodeClass is an input parameter that is used to validate that the Reference to be added matches the NodeClass of the TargetNode.
        This parameter is not validated if the Reference refers to a TargetNode in a remote Server.
        """

    @abstractmethod
    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.7.4/

        This Service is used to delete one or more Nodes from the AddressSpace.
        """

    @abstractmethod
    async def delete_references(self, refs: List[ua.DeleteReferencesItem]) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.7.5/

        This Service is used to delete one or more References of a Node.
        """

    # Method Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.11.1/

    @abstractmethod
    async def call(self, methodstocall: List[ua.CallMethodRequest]) -> List[ua.CallMethodResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.11.2/

        This Service is used to call (invoke) a list of Methods.
        """

    # Subscription Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.13.1/

    @abstractmethod
    async def create_subscription(self, params: ua.CreateSubscriptionParameters) -> ua.CreateSubscriptionResult:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.13.2/

        This Service is used to create a Subscription.

        Subscriptions monitor a set of MonitoredItems for Notifications and return them to the Client in response to Publish requests.
        """

    @abstractmethod
    async def modify_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.13.3/

        This Service is used to modify a Subscription.
        """

    @abstractmethod
    async def delete_subscriptions(self, params: ua.DeleteSubscriptionsParameters) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.13.8/

        This Service is invoked to delete one or more Subscriptions that belong to the Client's Session.
        """

    # MonitoredItem Service Set: https://reference.opcfoundation.org/Core/Part4/v104/5.12.1/

    @abstractmethod
    async def create_monitored_items(self, params: ua.CreateMonitoredItemsParameters) -> List[ua.MonitoredItemCreateResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.12.2/

        This Service is used to create and add one or more MonitoredItems to a Subscription.

        A MonitoredItem is deleted automatically by the Server when the Subscription is deleted.

        Deleting a MonitoredItem causes its entire set of triggered item links to be deleted,
        but has no effect on the MonitoredItems referenced by the triggered items.
        """

    @abstractmethod
    async def modify_monitored_items(self, params: ua.ModifyMonitoredItemsParameters) -> List[ua.MonitoredItemModifyResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.12.3/

        This Service is used to modify MonitoredItems of a Subscription.
        Changes to the MonitoredItem settings shall be applied immediately by the Server.
        They take effect as soon as practical but not later than twice the new revisedSamplingInterval.
        """

    @abstractmethod
    async def delete_monitored_items(self, params: ua.DeleteMonitoredItemsParameters) -> List[ua.StatusCode]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.12.6/

        This Service is used to remove one or more MonitoredItems of a Subscription.
        When a MonitoredItem is deleted, its triggered item links are also deleted.
        """

    @abstractmethod
    async def transfer_subscriptions(self, params: ua.TransferSubscriptionsParameters) -> List[ua.TransferResult]:
        """
        https://reference.opcfoundation.org/Core/Part4/v104/5.13.7/

        This Service is used to transfer a Subscription and its MonitoredItems from one Session to another.
        For example, a Client may need to reopen a Session and then transfer its Subscriptions to that Session.
        It may also be used by one Client to take over a Subscription from another Client by transferring the Subscription to its Session.
        """
