import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventEnvelope(_message.Message):
    __slots__ = ("event_id", "routing_key", "occurred_at", "producer", "traceparent", "actor", "branch_opened", "employee_hired", "client_registered", "appointment_created", "appointment_cancelled", "appointment_completed", "consumables_written_off", "stock_low", "invoice_issued", "invoice_paid")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROUTING_KEY_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    PRODUCER_FIELD_NUMBER: _ClassVar[int]
    TRACEPARENT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    BRANCH_OPENED_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_HIRED_FIELD_NUMBER: _ClassVar[int]
    CLIENT_REGISTERED_FIELD_NUMBER: _ClassVar[int]
    APPOINTMENT_CREATED_FIELD_NUMBER: _ClassVar[int]
    APPOINTMENT_CANCELLED_FIELD_NUMBER: _ClassVar[int]
    APPOINTMENT_COMPLETED_FIELD_NUMBER: _ClassVar[int]
    CONSUMABLES_WRITTEN_OFF_FIELD_NUMBER: _ClassVar[int]
    STOCK_LOW_FIELD_NUMBER: _ClassVar[int]
    INVOICE_ISSUED_FIELD_NUMBER: _ClassVar[int]
    INVOICE_PAID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    routing_key: str
    occurred_at: _timestamp_pb2.Timestamp
    producer: str
    traceparent: str
    actor: str
    branch_opened: BranchOpened
    employee_hired: EmployeeHired
    client_registered: ClientRegistered
    appointment_created: AppointmentCreated
    appointment_cancelled: AppointmentCancelled
    appointment_completed: AppointmentCompleted
    consumables_written_off: ConsumablesWrittenOff
    stock_low: StockLow
    invoice_issued: InvoiceIssued
    invoice_paid: InvoicePaid
    def __init__(self, event_id: _Optional[str] = ..., routing_key: _Optional[str] = ..., occurred_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., producer: _Optional[str] = ..., traceparent: _Optional[str] = ..., actor: _Optional[str] = ..., branch_opened: _Optional[_Union[BranchOpened, _Mapping]] = ..., employee_hired: _Optional[_Union[EmployeeHired, _Mapping]] = ..., client_registered: _Optional[_Union[ClientRegistered, _Mapping]] = ..., appointment_created: _Optional[_Union[AppointmentCreated, _Mapping]] = ..., appointment_cancelled: _Optional[_Union[AppointmentCancelled, _Mapping]] = ..., appointment_completed: _Optional[_Union[AppointmentCompleted, _Mapping]] = ..., consumables_written_off: _Optional[_Union[ConsumablesWrittenOff, _Mapping]] = ..., stock_low: _Optional[_Union[StockLow, _Mapping]] = ..., invoice_issued: _Optional[_Union[InvoiceIssued, _Mapping]] = ..., invoice_paid: _Optional[_Union[InvoicePaid, _Mapping]] = ...) -> None: ...

class BranchOpened(_message.Message):
    __slots__ = ("branch_id", "company_id", "name")
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    COMPANY_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    company_id: str
    name: str
    def __init__(self, branch_id: _Optional[str] = ..., company_id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class EmployeeHired(_message.Message):
    __slots__ = ("employee_id", "branch_id", "role")
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    employee_id: str
    branch_id: str
    role: str
    def __init__(self, employee_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., role: _Optional[str] = ...) -> None: ...

class ClientRegistered(_message.Message):
    __slots__ = ("client_id", "branch_id")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    branch_id: str
    def __init__(self, client_id: _Optional[str] = ..., branch_id: _Optional[str] = ...) -> None: ...

class AppointmentCreated(_message.Message):
    __slots__ = ("appointment_id", "branch_id", "client_id", "employee_id", "service_id", "period")
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    appointment_id: str
    branch_id: str
    client_id: str
    employee_id: str
    service_id: str
    period: _common_pb2.TimeRange
    def __init__(self, appointment_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., employee_id: _Optional[str] = ..., service_id: _Optional[str] = ..., period: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ...) -> None: ...

class AppointmentCancelled(_message.Message):
    __slots__ = ("appointment_id", "branch_id", "client_id", "reason")
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    appointment_id: str
    branch_id: str
    client_id: str
    reason: str
    def __init__(self, appointment_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class AppointmentCompleted(_message.Message):
    __slots__ = ("appointment_id", "branch_id", "client_id", "employee_id", "service_id")
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    appointment_id: str
    branch_id: str
    client_id: str
    employee_id: str
    service_id: str
    def __init__(self, appointment_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., employee_id: _Optional[str] = ..., service_id: _Optional[str] = ...) -> None: ...

class ConsumablesWrittenOff(_message.Message):
    __slots__ = ("appointment_id", "branch_id", "items")
    class Item(_message.Message):
        __slots__ = ("consumable_id", "unit", "amount")
        CONSUMABLE_ID_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        AMOUNT_FIELD_NUMBER: _ClassVar[int]
        consumable_id: str
        unit: str
        amount: float
        def __init__(self, consumable_id: _Optional[str] = ..., unit: _Optional[str] = ..., amount: _Optional[float] = ...) -> None: ...
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    appointment_id: str
    branch_id: str
    items: _containers.RepeatedCompositeFieldContainer[ConsumablesWrittenOff.Item]
    def __init__(self, appointment_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ConsumablesWrittenOff.Item, _Mapping]]] = ...) -> None: ...

class StockLow(_message.Message):
    __slots__ = ("consumable_id", "branch_id", "name", "unit", "remaining", "threshold")
    CONSUMABLE_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    REMAINING_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    consumable_id: str
    branch_id: str
    name: str
    unit: str
    remaining: float
    threshold: float
    def __init__(self, consumable_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., name: _Optional[str] = ..., unit: _Optional[str] = ..., remaining: _Optional[float] = ..., threshold: _Optional[float] = ...) -> None: ...

class InvoiceIssued(_message.Message):
    __slots__ = ("invoice_id", "appointment_id", "branch_id", "client_id", "total")
    INVOICE_ID_FIELD_NUMBER: _ClassVar[int]
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    invoice_id: str
    appointment_id: str
    branch_id: str
    client_id: str
    total: _common_pb2.Money
    def __init__(self, invoice_id: _Optional[str] = ..., appointment_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., total: _Optional[_Union[_common_pb2.Money, _Mapping]] = ...) -> None: ...

class InvoicePaid(_message.Message):
    __slots__ = ("invoice_id", "branch_id", "client_id", "employee_id", "total", "employee_commission")
    INVOICE_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_COMMISSION_FIELD_NUMBER: _ClassVar[int]
    invoice_id: str
    branch_id: str
    client_id: str
    employee_id: str
    total: _common_pb2.Money
    employee_commission: _common_pb2.Money
    def __init__(self, invoice_id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., employee_id: _Optional[str] = ..., total: _Optional[_Union[_common_pb2.Money, _Mapping]] = ..., employee_commission: _Optional[_Union[_common_pb2.Money, _Mapping]] = ...) -> None: ...
