"""`/users` — admin views over the user table.

This is the third-person view (admin manages other users). First-person stuff
lives under `/auth/*` (login, change-password, TOTP) and `/me/*` (own attendance,
own leave).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from tikko.auth import require_role
from tikko.db import SessionDep
from tikko.models.user import User
from tikko.schemas.user import UserList, UserRead, UserRoleUpdate

router = APIRouter(prefix="/users", tags=["users"])

_admin_only = Depends(require_role("admin"))


@router.get("", response_model=UserList, dependencies=[_admin_only])
async def list_users(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> UserList:
    offset = (page - 1) * page_size
    items = (
        await session.execute(
            select(User).order_by(User.created_at).offset(offset).limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(select(func.count()).select_from(User))
    return UserList(
        items=[UserRead.model_validate(u) for u in items],
        total=total or 0,
    )


@router.patch(
    "/{user_id}/role", response_model=UserRead, dependencies=[_admin_only]
)
async def update_user_role(
    user_id: str, payload: UserRoleUpdate, session: SessionDep
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    # Refuse to leave the system with zero admins — if this user is currently
    # the only admin and the new role isn't admin, that's a lockout.
    if user.role == "admin" and payload.role != "admin":
        other_admins = (
            await session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == "admin", User.id != user_id)
            )
        ) or 0
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="cannot demote the last admin",
            )

    user.role = payload.role
    await session.flush()
    return user
