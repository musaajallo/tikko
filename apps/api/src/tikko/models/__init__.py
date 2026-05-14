"""ORM models. Import here so Base.metadata sees every model on first import."""

from tikko.models.attendance import AttendanceLog
from tikko.models.device import Device
from tikko.models.employee import Employee
from tikko.models.employee_template import EmployeeTemplate
from tikko.models.leave_request import LeaveRequest
from tikko.models.user import User

__all__ = [
    "AttendanceLog",
    "Device",
    "Employee",
    "EmployeeTemplate",
    "LeaveRequest",
    "User",
]
