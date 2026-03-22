{%- if cookiecutter.use_jwt %}
# ruff: noqa: I001 - Imports structured for Jinja2 template conditionals
"""User management routes."""

from typing import Annotated
{%- if cookiecutter.use_postgresql %}

from uuid import UUID
{%- endif %}

from fastapi import APIRouter, Depends, UploadFile, File, status
{%- if cookiecutter.enable_pagination %}
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
{%- endif %}

from app.api.deps import (
    DBSession,
    RoleChecker,
    UserSvc,
    get_current_user,
)
from app.db.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()


{%- if cookiecutter.use_postgresql %}


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user.

    Returns the authenticated user's profile including their role.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserSvc,
):
    """Update current user.

    Users can update their own profile (email, full_name).
    Role changes require admin privileges.
    """
    # Prevent non-admin users from changing their own role
    if user_in.role is not None and not current_user.has_role(UserRole.ADMIN):
        user_in.role = None
    user = await user_service.update(current_user.id, user_in)
    return user


{%- if cookiecutter.enable_ai_agent and cookiecutter.enable_conversation_persistence %}


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DBSession = None,
):
    """Upload or replace avatar image for the current user."""
    from fastapi import HTTPException
    ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Avatar image too large. Maximum 2MB.")
    from app.services.file_storage import get_file_storage
    storage = get_file_storage()
    import contextlib
    if current_user.avatar_url:
        with contextlib.suppress(Exception):
            await storage.delete(current_user.avatar_url)
    storage_path = await storage.save(f"avatars/{current_user.id}", file.filename or "avatar.jpg", data)
    current_user.avatar_url = storage_path
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/avatar/{user_id}")
async def get_avatar(user_id: UUID, user_service: UserSvc):
    """Get user avatar image."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from app.services.file_storage import get_file_storage
    user = await user_service.get_by_id(user_id)
    if not user.avatar_url:
        raise HTTPException(status_code=404, detail="No avatar set")
    storage = get_file_storage()
    file_path = storage.get_full_path(user.avatar_url)
    if not file_path:
        raise HTTPException(status_code=404, detail="Avatar file not found")
    return FileResponse(path=file_path, media_type="image/jpeg")
{%- endif %}


{%- if cookiecutter.enable_pagination %}


@router.get("", response_model=Page[UserRead])
async def read_users(
    db: DBSession,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get all users (admin only)."""
    return await paginate(db, select(User))


{%- else %}


@router.get("", response_model=list[UserRead])
async def read_users(
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
    skip: int = 0,
    limit: int = 100,
):
    """Get all users (admin only)."""
    users = await user_service.get_multi(skip=skip, limit=limit)
    return users


{%- endif %}


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user = await user_service.get_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_by_id(
    user_id: UUID,
    user_in: UserUpdate,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Update user by ID (admin only).

    Admins can update any user including their role.

    Raises NotFoundError if user does not exist.
    """
    user = await user_service.update(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: UUID,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Delete user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    await user_service.delete(user_id)


{%- elif cookiecutter.use_mongodb %}


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user.

    Returns the authenticated user's profile including their role.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserSvc,
):
    """Update current user.

    Users can update their own profile (email, full_name).
    Role changes require admin privileges.
    """
    # Prevent non-admin users from changing their own role
    if user_in.role is not None and not current_user.has_role(UserRole.ADMIN):
        user_in.role = None
    user = await user_service.update(str(current_user.id), user_in)
    return user


@router.get("", response_model=list[UserRead])
async def read_users(
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
    skip: int = 0,
    limit: int = 100,
):
    """Get all users (admin only)."""
    users = await user_service.get_multi(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: str,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user = await user_service.get_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_by_id(
    user_id: str,
    user_in: UserUpdate,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Update user by ID (admin only).

    Admins can update any user including their role.

    Raises NotFoundError if user does not exist.
    """
    user = await user_service.update(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: str,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Delete user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    await user_service.delete(user_id)


{%- elif cookiecutter.use_sqlite %}


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user.

    Returns the authenticated user's profile including their role.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserSvc,
):
    """Update current user.

    Users can update their own profile (email, full_name).
    Role changes require admin privileges.
    """
    # Prevent non-admin users from changing their own role
    if user_in.role is not None and not current_user.has_role(UserRole.ADMIN):
        user_in.role = None
    user = user_service.update(current_user.id, user_in)
    return user


{%- if cookiecutter.enable_pagination %}


@router.get("", response_model=Page[UserRead])
def read_users(
    db: DBSession,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get all users (admin only)."""
    return paginate(db, select(User))


{%- else %}


@router.get("", response_model=list[UserRead])
def read_users(
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
    skip: int = 0,
    limit: int = 100,
):
    """Get all users (admin only)."""
    users = user_service.get_multi(skip=skip, limit=limit)
    return users


{%- endif %}


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: str,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user = user_service.get_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user_by_id(
    user_id: str,
    user_in: UserUpdate,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Update user by ID (admin only).

    Admins can update any user including their role.

    Raises NotFoundError if user does not exist.
    """
    user = user_service.update(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: str,
    user_service: UserSvc,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Delete user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user_service.delete(user_id)


{%- endif %}
{%- else %}
"""User routes - not configured."""
{%- endif %}
