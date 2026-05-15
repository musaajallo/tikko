"""ORM models. Import here so Base.metadata sees every model on first import."""

from tikko.models.attendance import AttendanceLog
from tikko.models.device import Device
from tikko.models.employee import Employee
from tikko.models.employee_template import EmployeeTemplate
from tikko.models.leave_request import LeaveRequest
from tikko.models.shift_rule import ShiftRule
from tikko.models.user import User
from tikko.models.user_totp import UserTOTP
from tikko.models.user_totp_recovery_code import UserTOTPRecoveryCode

__all__ = [
    "AttendanceLog",
    "Device",
    "Employee",
    "EmployeeTemplate",
    "LeaveRequest",
    "ShiftRule",
    "User",
    "UserTOTP",
    "UserTOTPRecoveryCode",
]
