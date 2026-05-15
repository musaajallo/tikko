"""Employees: register, list, retrieve, update, delete, sync to devices."""

from __future__ import annotations

import asyncio
import csv
import io

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from tikko.audit import log_audit
from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.models.department import Department
from tikko.models.device import Device
from tikko.models.employee import Employee
from tikko.models.employee_template import EmployeeTemplate
from tikko.models.shift_rule import ShiftRule


def _emp_snapshot(emp: Employee) -> dict[str, object | None]:
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "status": emp.status,
        "shift_rule_id": emp.shift_rule_id,
        "department_id": emp.department_id,
    }
from tikko.schemas.employee import (
    EmployeeCreate,
    EmployeeImportResult,
    EmployeeImportRowResult,
    EmployeeList,
    EmployeeRead,
    EmployeeSyncEntry,
    EmployeeSyncRequest,
    EmployeeSyncResult,
    EmployeeUpdate,
    TemplateList,
    TemplatePullResult,
    TemplatePushEntry,
    TemplatePushRequest,
    TemplatePushResult,
    TemplateRead,
)
from tikko.settings import get_settings
from tikko.zk.client import RawTemplate, ZKClient, ZKConnectionError

router = APIRouter(prefix="/employees", tags=["employees"])

_manage_employees = require_capability("manage_employees")
_view_employees = require_capability("view_employees")
_sync_employees = require_capability("sync_employees")
_manage_employee_templates = require_capability("manage_employee_templates")


@router.post(
    "",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_employees],
)
async def create_employee(
    payload: EmployeeCreate, session: SessionDep, current: CurrentUserDep
) -> Employee:
    if payload.department_id is not None:
        dept = await session.get(Department, payload.department_id)
        if dept is None:
            raise HTTPException(status_code=404, detail="department not found")
    employee = Employee(
        employee_code=payload.employee_code,
        full_name=payload.full_name,
        status=payload.status,
        department_id=payload.department_id,
    )
    session.add(employee)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"employee_code {payload.employee_code!r} already exists",
        ) from exc
    await log_audit(
        session,
        actor=current,
        action="create_employee",
        resource_type="employee",
        resource_id=employee.id,
        after=_emp_snapshot(employee),
    )
    return employee


@router.get("", response_model=EmployeeList, dependencies=[_view_employees])
async def list_employees(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> EmployeeList:
    offset = (page - 1) * page_size
    result = await session.execute(
        select(Employee)
        .order_by(Employee.created_at)
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()
    total = await session.scalar(select(func.count()).select_from(Employee))
    return EmployeeList(
        items=[EmployeeRead.model_validate(e) for e in items],
        total=total or 0,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeRead,
    dependencies=[_view_employees],
)
async def get_employee(employee_id: str, session: SessionDep) -> Employee:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    return employee


@router.patch(
    "/{employee_id}", response_model=EmployeeRead, dependencies=[_manage_employees]
)
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    session: SessionDep,
    current: CurrentUserDep,
) -> Employee:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    before = _emp_snapshot(employee)
    if payload.full_name is not None:
        employee.full_name = payload.full_name
    if payload.status is not None:
        employee.status = payload.status
    # `shift_rule_id` is nullable; "not provided" vs "set to null" matters.
    # Use model_fields_set so callers can detach with an explicit None.
    if "shift_rule_id" in payload.model_fields_set:
        if payload.shift_rule_id is not None:
            rule = await session.get(ShiftRule, payload.shift_rule_id)
            if rule is None:
                raise HTTPException(
                    status_code=404, detail="shift rule not found"
                )
        employee.shift_rule_id = payload.shift_rule_id
    if "department_id" in payload.model_fields_set:
        if payload.department_id is not None:
            dept = await session.get(Department, payload.department_id)
            if dept is None:
                raise HTTPException(
                    status_code=404, detail="department not found"
                )
        employee.department_id = payload.department_id

    await session.flush()
    after = _emp_snapshot(employee)
    if before != after:
        await log_audit(
            session,
            actor=current,
            action="update_employee",
            resource_type="employee",
            resource_id=employee.id,
            before=before,
            after=after,
        )
    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_manage_employees],
)
async def delete_employee(
    employee_id: str, session: SessionDep, current: CurrentUserDep
) -> Response:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    before = _emp_snapshot(employee)
    await session.delete(employee)
    await log_audit(
        session,
        actor=current,
        action="delete_employee",
        resource_type="employee",
        resource_id=employee_id,
        before=before,
    )
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{employee_id}/sync",
    response_model=EmployeeSyncResult,
    dependencies=[_sync_employees],
)
async def sync_employee(
    employee_id: str,
    payload: EmployeeSyncRequest,
    session: SessionDep,
) -> EmployeeSyncResult:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    devices_result = await session.execute(
        select(Device).where(Device.id.in_(payload.device_ids))
    )
    by_id = {d.id: d for d in devices_result.scalars().all()}

    missing = [d for d in payload.device_ids if d not in by_id]
    if missing:
        raise HTTPException(
            status_code=400, detail=f"unknown device_ids: {missing}"
        )

    settings = get_settings()
    results: list[EmployeeSyncEntry] = []
    # Iterate in request order — the in_() query above returns rows in arbitrary
    # order, but the caller asked for a specific sequence.
    for device_id in payload.device_ids:
        device = by_id[device_id]
        zk_client = ZKClient(
            host=device.host,
            port=device.port,
            timeout=settings.zk_connect_timeout_sec,
        )
        try:
            await asyncio.to_thread(
                zk_client.set_user, employee.employee_code, employee.full_name
            )
        except ZKConnectionError as exc:
            results.append(
                EmployeeSyncEntry(
                    device_id=device.id, status="failed", error=str(exc)
                )
            )
        else:
            results.append(
                EmployeeSyncEntry(device_id=device.id, status="synced")
            )

    return EmployeeSyncResult(results=results)


@router.post(
    "/{employee_id}/templates/pull",
    response_model=TemplatePullResult,
    dependencies=[_manage_employee_templates],
)
async def pull_templates(
    employee_id: str,
    session: SessionDep,
    from_device_id: str = Query(..., description="Source device to read templates from"),
) -> TemplatePullResult:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    device = await session.get(Device, from_device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="source device not found")

    settings = get_settings()
    zk_client = ZKClient(
        host=device.host,
        port=device.port,
        timeout=settings.zk_connect_timeout_sec,
    )

    try:
        raw_templates = await asyncio.to_thread(
            zk_client.get_user_templates, employee.employee_code
        )
    except ZKConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    # Replace any existing rows for (employee, source_device) so a re-pull
    # reflects the device's current enrollment state rather than accumulating.
    await session.execute(
        delete(EmployeeTemplate).where(
            EmployeeTemplate.employee_id == employee.id,
            EmployeeTemplate.source_device_id == device.id,
        )
    )
    for raw in raw_templates:
        session.add(
            EmployeeTemplate(
                employee_id=employee.id,
                source_device_id=device.id,
                finger_id=raw.finger_id,
                template_data=raw.data,
            )
        )
    await session.flush()

    return TemplatePullResult(
        stored=len(raw_templates),
        fingers=[t.finger_id for t in raw_templates],
    )


@router.post(
    "/{employee_id}/templates/push",
    response_model=TemplatePushResult,
    dependencies=[_manage_employee_templates],
)
async def push_templates(
    employee_id: str,
    payload: TemplatePushRequest,
    session: SessionDep,
) -> TemplatePushResult:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    devices_result = await session.execute(
        select(Device).where(Device.id.in_(payload.device_ids))
    )
    by_id = {d.id: d for d in devices_result.scalars().all()}
    missing = [d for d in payload.device_ids if d not in by_id]
    if missing:
        raise HTTPException(
            status_code=400, detail=f"unknown device_ids: {missing}"
        )

    # For each finger, pick the most recently captured template across all
    # source devices. If two source rows tie on captured_at, ORM ordering by id
    # is stable enough that the outcome is deterministic across a single run.
    stored = (
        await session.execute(
            select(EmployeeTemplate)
            .where(EmployeeTemplate.employee_id == employee.id)
            .order_by(EmployeeTemplate.captured_at.desc())
        )
    ).scalars().all()
    latest_per_finger: dict[int, EmployeeTemplate] = {}
    for row in stored:
        latest_per_finger.setdefault(row.finger_id, row)
    raw = [
        RawTemplate(finger_id=fid, data=row.template_data)
        for fid, row in sorted(latest_per_finger.items())
    ]

    settings = get_settings()
    results: list[TemplatePushEntry] = []
    for device_id in payload.device_ids:
        device = by_id[device_id]
        zk_client = ZKClient(
            host=device.host,
            port=device.port,
            timeout=settings.zk_connect_timeout_sec,
        )
        try:
            # Ensure the user record exists on the device before writing
            # templates. pyzk needs an enrolled user for save_user_template
            # to take effect; set_user is idempotent so retrying is fine.
            await asyncio.to_thread(
                zk_client.set_user, employee.employee_code, employee.full_name
            )
            await asyncio.to_thread(
                zk_client.save_user_templates, employee.employee_code, raw
            )
        except ZKConnectionError as exc:
            results.append(
                TemplatePushEntry(
                    device_id=device.id,
                    status="failed",
                    fingers_pushed=0,
                    error=str(exc),
                )
            )
        else:
            results.append(
                TemplatePushEntry(
                    device_id=device.id,
                    status="pushed",
                    fingers_pushed=len(raw),
                )
            )

    return TemplatePushResult(results=results)


@router.get(
    "/{employee_id}/templates",
    response_model=TemplateList,
    dependencies=[_view_employees],
)
async def list_templates(employee_id: str, session: SessionDep) -> TemplateList:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    result = await session.execute(
        select(EmployeeTemplate)
        .where(EmployeeTemplate.employee_id == employee_id)
        .order_by(EmployeeTemplate.source_device_id, EmployeeTemplate.finger_id)
    )
    items = result.scalars().all()
    return TemplateList(
        items=[TemplateRead.model_validate(item) for item in items],
        total=len(items),
    )


_IMPORT_REQUIRED = ("employee_code", "full_name")
_IMPORT_OPTIONAL = ("status", "department_id", "department_name")
_IMPORT_MAX_BYTES = 2 * 1024 * 1024  # 2 MiB ceiling — generous for thousands of rows


@router.post(
    "/import",
    response_model=EmployeeImportResult,
    dependencies=[_manage_employees],
)
async def import_employees(
    session: SessionDep,
    current: CurrentUserDep,
    file: UploadFile = File(..., description="CSV with employee_code,full_name[,status][,department_id|department_name]"),
) -> EmployeeImportResult:
    """Bulk-create employees from a CSV upload.

    The CSV must have a header row. Required columns: employee_code, full_name.
    Optional: status (active/inactive/terminated), and either department_id (UUID)
    or department_name (looked up case-insensitively). Unknown extra columns are
    ignored so operators can keep their own bookkeeping fields in the same file.

    Each row is processed independently — one failure does not stop the rest.
    Returns a per-row outcome so the UI can render success / skip / error in
    place.
    """
    raw = await file.read()
    if len(raw) > _IMPORT_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV exceeds {_IMPORT_MAX_BYTES} bytes",
        )
    try:
        text = raw.decode("utf-8-sig")  # tolerate Excel BOM
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV must be UTF-8 encoded",
        ) from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV is empty",
        )
    missing = [c for c in _IMPORT_REQUIRED if c not in reader.fieldnames]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"missing required column(s): {', '.join(missing)}",
        )

    # Build a lowercase-name -> id lookup once so per-row dept resolution is O(1).
    dept_rows = (await session.execute(select(Department))).scalars().all()
    dept_by_name = {d.name.strip().lower(): d.id for d in dept_rows}
    dept_ids = {d.id for d in dept_rows}

    rows: list[EmployeeImportRowResult] = []
    created = skipped = failed = 0

    for row_num, raw_row in enumerate(reader, start=1):
        # Strip every value so trailing newlines / Excel padding don't leak in.
        row = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items()}
        code = row.get("employee_code") or ""
        name = row.get("full_name") or ""

        if not code or not name:
            failed += 1
            rows.append(
                EmployeeImportRowResult(
                    row=row_num,
                    status="failed",
                    employee_code=code or None,
                    error="employee_code and full_name are required",
                )
            )
            continue
        if not code.isdigit():
            failed += 1
            rows.append(
                EmployeeImportRowResult(
                    row=row_num,
                    status="failed",
                    employee_code=code,
                    error="employee_code must be digits only",
                )
            )
            continue

        status_value = (row.get("status") or "active").lower()
        if status_value not in {"active", "inactive", "terminated"}:
            failed += 1
            rows.append(
                EmployeeImportRowResult(
                    row=row_num,
                    status="failed",
                    employee_code=code,
                    error=f"unknown status {status_value!r}",
                )
            )
            continue

        # Resolve department: id takes precedence over name when both supplied.
        dept_id: str | None = None
        raw_dept_id = row.get("department_id")
        raw_dept_name = row.get("department_name")
        if raw_dept_id:
            if raw_dept_id not in dept_ids:
                failed += 1
                rows.append(
                    EmployeeImportRowResult(
                        row=row_num,
                        status="failed",
                        employee_code=code,
                        error=f"unknown department_id {raw_dept_id}",
                    )
                )
                continue
            dept_id = raw_dept_id
        elif raw_dept_name:
            resolved = dept_by_name.get(raw_dept_name.lower())
            if resolved is None:
                failed += 1
                rows.append(
                    EmployeeImportRowResult(
                        row=row_num,
                        status="failed",
                        employee_code=code,
                        error=f"unknown department_name {raw_dept_name!r}",
                    )
                )
                continue
            dept_id = resolved

        # Skip-on-duplicate — operators re-running an import shouldn't see a
        # wall of red. The dedupe key is employee_code (unique in the DB).
        existing = await session.scalar(
            select(Employee).where(Employee.employee_code == code)
        )
        if existing is not None:
            skipped += 1
            rows.append(
                EmployeeImportRowResult(
                    row=row_num,
                    status="skipped",
                    employee_id=existing.id,
                    employee_code=code,
                    error="employee_code already exists",
                )
            )
            continue

        employee = Employee(
            employee_code=code,
            full_name=name,
            status=status_value,
            department_id=dept_id,
        )
        session.add(employee)
        try:
            await session.flush()
        except IntegrityError:
            # A race against another concurrent import or a duplicate later in
            # the same file — recover by rolling the row back and skipping.
            await session.rollback()
            failed += 1
            rows.append(
                EmployeeImportRowResult(
                    row=row_num,
                    status="failed",
                    employee_code=code,
                    error="conflict on insert",
                )
            )
            continue
        await log_audit(
            session,
            actor=current,
            action="create_employee",
            resource_type="employee",
            resource_id=employee.id,
            after=_emp_snapshot(employee),
        )
        created += 1
        rows.append(
            EmployeeImportRowResult(
                row=row_num,
                status="created",
                employee_id=employee.id,
                employee_code=code,
            )
        )

    return EmployeeImportResult(
        created=created, skipped=skipped, failed=failed, rows=rows
    )
