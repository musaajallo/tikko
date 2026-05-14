"""Payroll calc engine — pure functions.

The engine is intentionally decoupled from the ORM and FastAPI so it stays
unit-testable in isolation. F28 (report endpoints) is where DB rows are
adapted into the engine's data classes.
"""

from tikko.payroll.calc import DayMetrics, ShiftSpec, compute_day

__all__ = ["DayMetrics", "ShiftSpec", "compute_day"]
