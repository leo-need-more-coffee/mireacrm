from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Service(_message.Message):
    __slots__ = ("id", "branch_id", "name", "duration_minutes", "price", "is_active")
    ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DURATION_MINUTES_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    id: str
    branch_id: str
    name: str
    duration_minutes: int
    price: _common_pb2.Money
    is_active: bool
    def __init__(self, id: _Optional[str] = ..., branch_id: _Optional[str] = ..., name: _Optional[str] = ..., duration_minutes: _Optional[int] = ..., price: _Optional[_Union[_common_pb2.Money, _Mapping]] = ..., is_active: _Optional[bool] = ...) -> None: ...

class ConsumptionNorm(_message.Message):
    __slots__ = ("consumable_id", "name", "unit", "amount")
    CONSUMABLE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    consumable_id: str
    name: str
    unit: str
    amount: float
    def __init__(self, consumable_id: _Optional[str] = ..., name: _Optional[str] = ..., unit: _Optional[str] = ..., amount: _Optional[float] = ...) -> None: ...

class GetServiceRequest(_message.Message):
    __slots__ = ("service_id", "branch_id")
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    service_id: str
    branch_id: str
    def __init__(self, service_id: _Optional[str] = ..., branch_id: _Optional[str] = ...) -> None: ...

class GetServiceResponse(_message.Message):
    __slots__ = ("service",)
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    service: Service
    def __init__(self, service: _Optional[_Union[Service, _Mapping]] = ...) -> None: ...

class GetConsumptionNormsRequest(_message.Message):
    __slots__ = ("service_id",)
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    service_id: str
    def __init__(self, service_id: _Optional[str] = ...) -> None: ...

class GetConsumptionNormsResponse(_message.Message):
    __slots__ = ("norms",)
    NORMS_FIELD_NUMBER: _ClassVar[int]
    norms: _containers.RepeatedCompositeFieldContainer[ConsumptionNorm]
    def __init__(self, norms: _Optional[_Iterable[_Union[ConsumptionNorm, _Mapping]]] = ...) -> None: ...
