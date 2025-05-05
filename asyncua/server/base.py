from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Callable, Optional, ByteString, Any
from pathlib import Path
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

from asyncua.common.callback import CallbackService
from asyncua.common.node import Node
from asyncua.common.session_interface import AbstractSession
from asyncua.crypto.validator import CertificateValidatorMethod
from asyncua.crypto.permission_rules import User
from asyncua.server.address_space import (
    AbstractAddressSpace,
    AttributeService,
    MethodService,
    NodeManagementService,
    ViewService,
    NodeData,
)
from asyncua.server.history import HistoryManager
from asyncua.server.subscription_service import SubscriptionService
from asyncua.ua.attribute_ids import AttributeIds
from asyncua.ua.uaprotocol_auto import UserIdentityToken, UserNameIdentityToken
from asyncua.ua.uatypes import NodeId, DataValue


class AbstractUserManager(ABC):
    @abstractmethod
    def get_user(
        self,
        iserver: AbstractInternalServer,
        username: Optional[str] = None,
        password: Optional[str] = None,
        certificate: Optional[Certificate] = None,
    ) -> Optional[User]:
        pass


class AbstractInternalServer(ABC):
    """
    Provides an interface for the internal server.
    This class is used to define the basic structure and functionality used by:
    - Server
    - History Manager -> _create_subscription() -> Subscription()
    - Internal Session
    - User Manager -> get_user()
    """

    @property
    @abstractmethod
    def isession(self) -> AbstractSession:
        """
        The internal session.
        """
        pass

    @property
    @abstractmethod
    def certificate_validator(self) -> Optional[CertificateValidatorMethod]:
        """
        hook to validate a certificate, raises a ServiceError when not valid
        """
        pass

    @certificate_validator.setter
    @abstractmethod
    def certificate_validator(self, validator: CertificateValidatorMethod) -> None:
        """
        Set the certificate validator method.
        """
        pass

    @property
    @abstractmethod
    def user_manager(self) -> Optional[AbstractUserManager]:
        """
        The user manager.
        """
        pass

    @property
    @abstractmethod
    def history_manager(self) -> HistoryManager:
        """
        The history manager.
        """
        pass

    @property
    @abstractmethod
    def callback_service(self) -> CallbackService:
        """
        The callback service.
        """
        pass

    @property
    @abstractmethod
    def view_service(self) -> ViewService:
        """
        The view service.
        """
        pass

    @property
    @abstractmethod
    def attribute_service(self) -> AttributeService:
        """
        The attribute service.
        """
        pass

    @property
    @abstractmethod
    def node_mgt_service(self) -> NodeManagementService:
        """
        The node management service.
        """
        pass

    @property
    @abstractmethod
    def method_service(self) -> MethodService:
        """
        The method service.
        """
        pass

    @property
    @abstractmethod
    def subscription_service(self) -> SubscriptionService:
        """
        The subscription service.
        """
        pass

    @property
    @abstractmethod
    def aspace(self) -> AbstractAddressSpace:
        """
        The address space.
        """
        pass

    @property
    def allow_remote_admin(self) -> bool:
        return self._allow_remote_admin

    @allow_remote_admin.setter
    def allow_remote_admin(self, value: bool) -> None:
        self._allow_remote_admin = value

    @property
    def supported_tokens(self) -> tuple[UserIdentityToken]:
        return self._supported_tokens

    @supported_tokens.setter
    def supported_tokens(self, value: tuple[UserIdentityToken]) -> None:
        self._supported_tokens: tuple[UserIdentityToken] = value

    @property
    def certificate(self) -> Optional[Certificate]:
        return getattr(self, "_certificate", None)

    @certificate.setter
    def certificate(self, value: Certificate) -> None:
        self._certificate = value

    @property
    def private_key(self) -> Optional[PrivateKeyTypes]:
        return getattr(self, "_private_key", None)

    @private_key.setter
    def private_key(self, value: PrivateKeyTypes) -> None:
        self._private_key = value

    @property
    def match_discovery_endpoint_url(self) -> bool:
        return self._match_discovery_endpoint_url

    @match_discovery_endpoint_url.setter
    def match_discovery_endpoint_url(self, value: bool) -> None:
        self._match_discovery_endpoint_url: bool = value

    @property
    def match_discovery_source_ip(self) -> bool:
        return self._match_discovery_client_ip

    @match_discovery_source_ip.setter
    def match_discovery_source_ip(self, value: bool) -> None:
        self._match_discovery_client_ip: bool = value

    @property
    def disabled_clock(self) -> bool:
        return self._disabled_clock

    @disabled_clock.setter
    def disabled_clock(self, value: bool) -> None:
        self._disabled_clock: bool = value

    @abstractmethod
    async def init(
        self,
        shelf_file: Optional[Path] = None,
    ) -> None:
        """
        Initialize the server.
        """
        pass

    @abstractmethod
    def decrypt_user_token(self, token: UserNameIdentityToken) -> tuple[str | Any]:
        """
        Decrypt the user token.
        """
        pass

    @abstractmethod
    def verify_x509_token(self, isession: AbstractSession, token: UserIdentityToken, signature) -> ByteString:
        """
        Verify the x509 token.
        """
        pass

    @abstractmethod
    def find_servers(self, params: Any, sockname: Optional[str] = None) -> list:
        pass

    @abstractmethod
    async def get_endpoints(self) -> list:
        """
        Get the endpoints.
        """
        pass

    @abstractmethod
    def add_endpoint(self, endpoint: Any) -> None:
        """
        Add an endpoint.
        """
        pass

    @abstractmethod
    async def enable_history_data_change(self, node: Node, period: timedelta, count: int) -> None:
        """
        Enable history data change.
        """
        pass

    @abstractmethod
    async def disable_history_data_change(self, node: Node) -> None:
        """
        Disable history data change.
        """
        pass

    @abstractmethod
    async def enable_history_event(self, node: Node, period: timedelta, count: int) -> None:
        """
        Enable history event.
        """
        pass

    @abstractmethod
    async def disable_history_event(self, node: Node) -> None:
        """
        Disable history event.
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Start the server.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the server.
        """
        pass

    def subscribe_server_callback(self, event, handle):
        """
        Subscribe to server callback.
        """
        self.callback_service.addListener(eventName=event, listener=handle)

    def unsubscribe_server_callback(self, event, handle) -> None:
        """
        Unsubscribe from server callback.
        """
        self.callback_service.removeListener(eventName=event, listener=handle)

    def add_method_callback(self, methodid, callback) -> None:
        """
        Add a method callback.
        """
        return self.aspace.add_method_callback(methodid, callback)

    async def write_attribute_value(
        self, nodeid: NodeId, datavalue: Any, attr: AttributeIds = AttributeIds.Value
    ) -> None:
        await self.aspace.write_attribute_value(nodeid=nodeid, attr=attr, value=datavalue)

    def set_attribute_value_callback(
        self,
        nodeid: NodeId,
        callback: Callable[[NodeId, AttributeIds], DataValue],
        attr: AttributeIds = AttributeIds.Value,
    ) -> None:
        """
        Set attribute value callback.
        """
        self.aspace.set_attribute_value_callback(nodeid=nodeid, attr=attr, callback=callback)

    def set_attribute_value_setter(
        self,
        nodeid: NodeId,
        setter: Callable[[NodeData, AttributeIds, DataValue], None],
        attr=AttributeIds.Value,
    ) -> None:
        """
        Set a setter function for the Attribute. This setter will be called when a new value is set using
        write_attribute_value() instead of directly writing the value. This is useful, for example, if you want to
        intercept writes to certain attributes to perform some kind of validation of the value to be written and return
        appropriate status codes to the client.
        """
        self.aspace.set_attribute_value_setter(nodeid=nodeid, attr=attr, setter=setter)

    def read_attribute_value(self, nodeid: NodeId, attr: AttributeIds = AttributeIds.Value) -> DataValue:
        """
        Read attribute value.
        """
        return self.aspace.read_attribute_value(nodeid=nodeid, attr=attr)
