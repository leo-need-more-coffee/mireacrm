from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppointmentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APPOINTMENT_STATUS_UNSPECIFIED: _ClassVar[AppointmentStatus]
    APPOINTMENT_STATUS_SCHEDULED: _ClassVar[AppointmentStatus]
    APPOINTMENT_STATUS_COMPLETED: _ClassVar[AppointmentStatus]
    APPOINTMENT_STATUS_CANCELLED: _ClassVar[AppointmentStatus]
    APPOINTMENT_STATUS_NO_SHOW: _ClassVar[AppointmentStatus]
APPOINTMENT_STATUS_UNSPECIFIED: AppointmentStatus
APPOINTMENT_STATUS_SCHEDULED: AppointmentStatus
APPOINTMENT_STATUS_COMPLETED: AppointmentStatus
APPOINTMENT_STATUS_CANCELLED: AppointmentStatus
APPOINTMENT_STATUS_NO_SHOW: AppointmentStatus

class Appointment(_message.Message):
    __slots__ = ("id", "branch_id", "client_id", "employee_id", "service_id", "period", "status", "price")
    ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    id: str
    branch_id: str
    client_id: str
    employee_id: str
    service_id: str
    period: _common_pb2.TimeRange
    status: AppointmentStatus
    price: _common_pb2.Money
    def __init__(self, id: _Optional[str] = ..., branch_id: _Optional[str] = ..., client_id: _Optional[str] = ..., employee_id: _Optional[str] = ..., service_id: _Optional[str] = ..., period: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ..., status: _Optional[_Union[AppointmentStatus, str]] = ..., price: _Optional[_Union[_common_pb2.Money, _Mapping]] = ...) -> None: ...

class GetAppointmentRequest(_message.Message):
    __slots__ = ("appointment_id",)
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    appointment_id: str
    def __init__(self, appointment_id: _Optional[str] = ...) -> None: ...

class GetAppointmentResponse(_message.Message):
    __slots__ = ("appointment",)
    APPOINTMENT_FIELD_NUMBER: _ClassVar[int]
    appointment: Appointment
    def __init__(self, appointment: _Optional[_Union[Appointment, _Mapping]] = ...) -> None: ...

class ListClientAppointmentsRequest(_message.Message):
    __slots__ = ("client_id", "page")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    page: _common_pb2.PageRequest
    def __init__(self, client_id: _Optional[str] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListClientAppointmentsResponse(_message.Message):
    __slots__ = ("appointments", "page")
    APPOINTMENTS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    appointments: _containers.RepeatedCompositeFieldContainer[Appointment]
    page: _common_pb2.PageResponse
    def __init__(self, appointments: _Optional[_Iterable[_Union[Appointment, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...
