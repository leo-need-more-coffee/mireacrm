from mirea.common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EmployeeRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EMPLOYEE_ROLE_UNSPECIFIED: _ClassVar[EmployeeRole]
    EMPLOYEE_ROLE_ADMIN: _ClassVar[EmployeeRole]
    EMPLOYEE_ROLE_MANAGER: _ClassVar[EmployeeRole]
    EMPLOYEE_ROLE_SPECIALIST: _ClassVar[EmployeeRole]
EMPLOYEE_ROLE_UNSPECIFIED: EmployeeRole
EMPLOYEE_ROLE_ADMIN: EmployeeRole
EMPLOYEE_ROLE_MANAGER: EmployeeRole
EMPLOYEE_ROLE_SPECIALIST: EmployeeRole

class Company(_message.Message):
    __slots__ = ("id", "name", "inn")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    INN_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    inn: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., inn: _Optional[str] = ...) -> None: ...

class Branch(_message.Message):
    __slots__ = ("id", "company_id", "name", "address", "timezone")
    ID_FIELD_NUMBER: _ClassVar[int]
    COMPANY_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    id: str
    company_id: str
    name: str
    address: str
    timezone: str
    def __init__(self, id: _Optional[str] = ..., company_id: _Optional[str] = ..., name: _Optional[str] = ..., address: _Optional[str] = ..., timezone: _Optional[str] = ...) -> None: ...

class Employee(_message.Message):
    __slots__ = ("id", "branch_id", "full_name", "role", "is_active")
    ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    id: str
    branch_id: str
    full_name: str
    role: EmployeeRole
    is_active: bool
    def __init__(self, id: _Optional[str] = ..., branch_id: _Optional[str] = ..., full_name: _Optional[str] = ..., role: _Optional[_Union[EmployeeRole, str]] = ..., is_active: _Optional[bool] = ...) -> None: ...

class WorkShift(_message.Message):
    __slots__ = ("period",)
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    period: _common_pb2.TimeRange
    def __init__(self, period: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ...) -> None: ...

class GetBranchRequest(_message.Message):
    __slots__ = ("branch_id",)
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    def __init__(self, branch_id: _Optional[str] = ...) -> None: ...

class GetBranchResponse(_message.Message):
    __slots__ = ("branch",)
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    branch: Branch
    def __init__(self, branch: _Optional[_Union[Branch, _Mapping]] = ...) -> None: ...

class GetEmployeeScheduleRequest(_message.Message):
    __slots__ = ("employee_id", "period")
    EMPLOYEE_ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    employee_id: str
    period: _common_pb2.TimeRange
    def __init__(self, employee_id: _Optional[str] = ..., period: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ...) -> None: ...

class GetEmployeeScheduleResponse(_message.Message):
    __slots__ = ("employee", "shifts")
    EMPLOYEE_FIELD_NUMBER: _ClassVar[int]
    SHIFTS_FIELD_NUMBER: _ClassVar[int]
    employee: Employee
    shifts: _containers.RepeatedCompositeFieldContainer[WorkShift]
    def __init__(self, employee: _Optional[_Union[Employee, _Mapping]] = ..., shifts: _Optional[_Iterable[_Union[WorkShift, _Mapping]]] = ...) -> None: ...

class ListEmployeesRequest(_message.Message):
    __slots__ = ("branch_id", "role", "page")
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    role: EmployeeRole
    page: _common_pb2.PageRequest
    def __init__(self, branch_id: _Optional[str] = ..., role: _Optional[_Union[EmployeeRole, str]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListEmployeesResponse(_message.Message):
    __slots__ = ("employees", "page")
    EMPLOYEES_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    employees: _containers.RepeatedCompositeFieldContainer[Employee]
    page: _common_pb2.PageResponse
    def __init__(self, employees: _Optional[_Iterable[_Union[Employee, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...
