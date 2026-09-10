from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PreferredChannel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PREFERRED_CHANNEL_UNSPECIFIED: _ClassVar[PreferredChannel]
    PREFERRED_CHANNEL_SMS: _ClassVar[PreferredChannel]
    PREFERRED_CHANNEL_EMAIL: _ClassVar[PreferredChannel]
    PREFERRED_CHANNEL_TELEGRAM: _ClassVar[PreferredChannel]
PREFERRED_CHANNEL_UNSPECIFIED: PreferredChannel
PREFERRED_CHANNEL_SMS: PreferredChannel
PREFERRED_CHANNEL_EMAIL: PreferredChannel
PREFERRED_CHANNEL_TELEGRAM: PreferredChannel

class ClientContacts(_message.Message):
    __slots__ = ("client_id", "full_name", "phone", "email", "telegram", "preferred")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    TELEGRAM_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    full_name: str
    phone: str
    email: str
    telegram: str
    preferred: PreferredChannel
    def __init__(self, client_id: _Optional[str] = ..., full_name: _Optional[str] = ..., phone: _Optional[str] = ..., email: _Optional[str] = ..., telegram: _Optional[str] = ..., preferred: _Optional[_Union[PreferredChannel, str]] = ...) -> None: ...

class GetClientContactsRequest(_message.Message):
    __slots__ = ("client_id",)
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    def __init__(self, client_id: _Optional[str] = ...) -> None: ...

class GetClientContactsResponse(_message.Message):
    __slots__ = ("contacts",)
    CONTACTS_FIELD_NUMBER: _ClassVar[int]
    contacts: ClientContacts
    def __init__(self, contacts: _Optional[_Union[ClientContacts, _Mapping]] = ...) -> None: ...

class AddLoyaltyPointsRequest(_message.Message):
    __slots__ = ("client_id", "paid", "invoice_id")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    PAID_FIELD_NUMBER: _ClassVar[int]
    INVOICE_ID_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    paid: _common_pb2.Money
    invoice_id: str
    def __init__(self, client_id: _Optional[str] = ..., paid: _Optional[_Union[_common_pb2.Money, _Mapping]] = ..., invoice_id: _Optional[str] = ...) -> None: ...

class AddLoyaltyPointsResponse(_message.Message):
    __slots__ = ("points_added", "points_balance")
    POINTS_ADDED_FIELD_NUMBER: _ClassVar[int]
    POINTS_BALANCE_FIELD_NUMBER: _ClassVar[int]
    points_added: int
    points_balance: int
    def __init__(self, points_added: _Optional[int] = ..., points_balance: _Optional[int] = ...) -> None: ...
