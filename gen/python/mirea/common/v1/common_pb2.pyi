import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Money(_message.Message):
    __slots__ = ("amount_kopecks", "currency_code")
    AMOUNT_KOPECKS_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_CODE_FIELD_NUMBER: _ClassVar[int]
    amount_kopecks: int
    currency_code: str
    def __init__(self, amount_kopecks: _Optional[int] = ..., currency_code: _Optional[str] = ...) -> None: ...

class TimeRange(_message.Message):
    __slots__ = ("start_at", "end_at")
    START_AT_FIELD_NUMBER: _ClassVar[int]
    END_AT_FIELD_NUMBER: _ClassVar[int]
    start_at: _timestamp_pb2.Timestamp
    end_at: _timestamp_pb2.Timestamp
    def __init__(self, start_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PageRequest(_message.Message):
    __slots__ = ("limit", "cursor")
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    limit: int
    cursor: str
    def __init__(self, limit: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class PageResponse(_message.Message):
    __slots__ = ("next_cursor",)
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    next_cursor: str
    def __init__(self, next_cursor: _Optional[str] = ...) -> None: ...
