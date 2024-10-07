from asyncua import ua
from asyncua.server.users import UserRole

WRITE_TYPES = [
    ua.ObjectIds.WriteRequest_Encoding_DefaultBinary,
    ua.ObjectIds.RegisterServerRequest_Encoding_DefaultBinary,
    ua.ObjectIds.RegisterServer2Request_Encoding_DefaultBinary,
    ua.ObjectIds.AddNodesRequest_Encoding_DefaultBinary,
    ua.ObjectIds.DeleteNodesRequest_Encoding_DefaultBinary,
    ua.ObjectIds.AddReferencesRequest_Encoding_DefaultBinary,
    ua.ObjectIds.DeleteReferencesRequest_Encoding_DefaultBinary,
]

READ_TYPES = [
    ua.ObjectIds.CreateSessionRequest_Encoding_DefaultBinary,
    ua.ObjectIds.CloseSessionRequest_Encoding_DefaultBinary,
    ua.ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary,
    ua.ObjectIds.ReadRequest_Encoding_DefaultBinary,
    ua.ObjectIds.BrowseRequest_Encoding_DefaultBinary,
    ua.ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.FindServersRequest_Encoding_DefaultBinary,
    ua.ObjectIds.TranslateBrowsePathsToNodeIdsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.CreateSubscriptionRequest_Encoding_DefaultBinary,
    ua.ObjectIds.DeleteSubscriptionsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.CreateMonitoredItemsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.ModifyMonitoredItemsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.DeleteMonitoredItemsRequest_Encoding_DefaultBinary,
    ua.ObjectIds.HistoryReadRequest_Encoding_DefaultBinary,
    ua.ObjectIds.PublishRequest_Encoding_DefaultBinary,
    ua.ObjectIds.RepublishRequest_Encoding_DefaultBinary,
    ua.ObjectIds.CloseSecureChannelRequest_Encoding_DefaultBinary,
    ua.ObjectIds.CallRequest_Encoding_DefaultBinary,
    ua.ObjectIds.SetMonitoringModeRequest_Encoding_DefaultBinary,
    ua.ObjectIds.SetPublishingModeRequest_Encoding_DefaultBinary,
    ua.ObjectIds.RegisterNodesRequest_Encoding_DefaultBinary,
    ua.ObjectIds.UnregisterNodesRequest_Encoding_DefaultBinary,
]


class PermissionRuleset:
    """
    Base class for permission ruleset
    """

    def check_validity(self, user, action_type, body):
        raise NotImplementedError


class SimpleRoleRuleset(PermissionRuleset):
    """
    Standard simple role-based ruleset.
    Admins alone can write, admins and users can read, and anonymous users can't do anything.
    """

    def __init__(self):
        write_ids = list(map(ua.NodeId, WRITE_TYPES))
        read_ids = list(map(ua.NodeId, READ_TYPES))
        self._permission_dict = {
            UserRole.Admin: set().union(write_ids, read_ids),
            UserRole.User: set().union(read_ids),
            UserRole.Anonymous: set()
        }

    def check_validity(self, user, action_type_id, body):
        if action_type_id in self._permission_dict[user.role]:
            return True
        else:
            return False
