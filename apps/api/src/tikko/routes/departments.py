"""Departments: CRUD with a self-referential parent FK for org hierarchy.

Per-employee assignment lives on `PATCH /employees/:id` (`department_id`),
mirroring the shift-rule pattern.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from tikko.auth import require_capability
from tikko.db import SessionDep
from tikko.models.department import Department
from tikko.models.employee import Employee
from tikko.schemas.department import (
    DepartmentCreate,
    DepartmentList,
    DepartmentRead,
    DepartmentUpdate,
)

router = APIRouter(prefix="/departments", tags=["departments"])

_manage_departments = require_capability("manage_departments")
_view_departments = require_capability("view_departments")


async def _validate_parent(
    session: SessionDep, parent_id: str | None, self_id: str | None = None
) -> None:
    """Reject unknown parents and prevent a department from parenting itself.

    A full cycle check across many levels would need a recursive CTE; the
    self-loop guard catches the common mistake without that complexity. Deeper
    cycles are still possible if an operator wires them up by hand, but the UI
    won't let them and the dept tree is shallow in practice.
    """
    if parent_id is None:
        return
    if self_id is not None and parent_id == self_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="department cannot be its own parent",
        )
    parent = await session.get(Department, parent_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="parent department not found")


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_departments],
)
async def create_department(
    payload: DepartmentCreate, session: SessionDep
) -> Department:
    await _validate_parent(session, payload.parent_id)
    dept = Department(name=payload.name, parent_id=payload.parent_id)
    session.add(dept)
    await session.flush()
    return dept


@router.get("", response_model=DepartmentList, dependencies=[_view_departments])
async def list_departments(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> DepartmentList:
    offset = (page - 1) * page_size
    items = (
        await session.execute(
            select(Department)
            .order_by(Department.name)
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(select(func.count()).select_from(Department))
    return DepartmentList(
        items=[DepartmentRead.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get(
    "/{department_id}", response_model=DepartmentRead, dependencies=[_view_departments]
)
async def get_department(department_id: str, session: SessionDep) -> Department:
    dept = await session.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="department not found")
    return dept


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
    dependencies=[_manage_departments],
)
async def update_department(
    department_id: str, payload: DepartmentUpdate, session: SessionDep
) -> Department:
    dept = await session.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="department not found")

    if payload.name is not None:
        dept.name = payload.name
    if "parent_id" in payload.model_fields_set:
        await _validate_parent(session, payload.parent_id, self_id=dept.id)
        dept.parent_id = payload.parent_id

    await session.flush()
    return dept


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_manage_departments],
)
async def delete_department(department_id: str, session: SessionDep) -> Response:
    dept = await session.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="department not found")

    # Refuse if employees are still assigned — operator must reassign first,
    # same defensive contract as shift_rules so deletes never silently nuke FKs.
    assigned = await session.scalar(
        select(func.count())
        .select_from(Employee)
        .where(Employee.department_id == department_id)
    )
    if assigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{assigned} employee(s) still assigned to this department",
        )
    # Refuse if child departments still point at this one for the same reason.
    children = await session.scalar(
        select(func.count())
        .select_from(Department)
        .where(Department.parent_id == department_id)
    )
    if children:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{children} child department(s) still reference this parent",
        )

    await session.delete(dept)
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
