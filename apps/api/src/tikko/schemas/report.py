"""Attendance report schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ReportEmployee(BaseModel):
    id: str
    employee_code: str
    full_name: str


class AttendanceReportDay(BaseModel):
    date: date
    is_workday: bool
    is_holiday: bool = False
    is_absent: bool
    first_in: datetime | None = None
    last_out: datetime | None = None
    worked_minutes: int
    late_minutes: int
    early_out_minutes: int
    overtime_minutes: int


class AttendanceReportTotals(BaseModel):
    days_worked: int
    days_absent: int
    days_holiday: int = 0
    worked_minutes: int
    late_minutes: int
    early_out_minutes: int
    overtime_minutes: int


class AttendanceReport(BaseModel):
    month: str  # YYYY-MM
    employee: ReportEmployee
    days: list[AttendanceReportDay]
    totals: AttendanceReportTotals
