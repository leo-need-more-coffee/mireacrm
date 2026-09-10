import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SlotChanged(_message.Message):
    __slots__ = ("branch_id", "employee_id", "period", "is_taken", "appointment_id")
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    IS_TAKEN_FIELD_NUMBER: _ClassVar[int]
    APPOINTMENT_ID_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    employee_id: str
    period: _common_pb2.TimeRange
    is_taken: bool
    appointment_id: str
    def __init__(self, branch_id: _Optional[str] = ..., employee_id: _Optional[str] = ..., period: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ..., is_taken: _Optional[bool] = ..., appointment_id: _Optional[str] = ...) -> None: ...

class BranchAlert(_message.Message):
    __slots__ = ("branch_id", "severity", "title", "body", "raised_at")
    class Severity(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SEVERITY_UNSPECIFIED: _ClassVar[BranchAlert.Severity]
        SEVERITY_INFO: _ClassVar[BranchAlert.Severity]
        SEVERITY_WARNING: _ClassVar[BranchAlert.Severity]
        SEVERITY_CRITICAL: _ClassVar[BranchAlert.Severity]
    SEVERITY_UNSPECIFIED: BranchAlert.Severity
    SEVERITY_INFO: BranchAlert.Severity
    SEVERITY_WARNING: BranchAlert.Severity
    SEVERITY_CRITICAL: BranchAlert.Severity
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    RAISED_AT_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    severity: BranchAlert.Severity
    title: str
    body: str
    raised_at: _timestamp_pb2.Timestamp
    def __init__(self, branch_id: _Optional[str] = ..., severity: _Optional[_Union[BranchAlert.Severity, str]] = ..., title: _Optional[str] = ..., body: _Optional[str] = ..., raised_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Heartbeat(_message.Message):
    __slots__ = ("service", "version", "sent_at")
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SENT_AT_FIELD_NUMBER: _ClassVar[int]
    service: str
    version: str
    sent_at: _timestamp_pb2.Timestamp
    def __init__(self, service: _Optional[str] = ..., version: _Optional[str] = ..., sent_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
