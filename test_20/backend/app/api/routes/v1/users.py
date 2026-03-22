# ruff: noqa: I001 - Imports structured for Jinja2 template conditionals
"""User management routes."""

from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from app.api.deps import (
    DBSession,
    RoleChecker,
    UserSvc,
    get_current_user,
)
from app.db.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()


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


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DBSession = None,
):
    """Upload or replace avatar image for the current user."""
    ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB

    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")

    data = await file.read()
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=413, detail="Avatar image too large. Maximum 2MB.")

    from app.services.file_storage import get_file_storage
    storage = get_file_storage()

    # Delete old avatar if exists
    if current_user.avatar_url:
        try:
            await storage.delete(current_user.avatar_url)
        except Exception:
            pass

    filename = file.filename or "avatar.jpg"
    storage_path = await storage.save(f"avatars/{current_user.id}", filename, data)
    current_user.avatar_url = storage_path
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("", response_model=Page[UserRead])
async def read_users(
    db: DBSession,
    current_user: Annotated[User, Depends(RoleChecker(UserRole.ADMIN))],
):
    """Get all users (admin only)."""
    return await paginate(db, select(User))


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


@router.get("/avatar/{user_id}")
async def get_avatar(
    user_id: UUID,
    user_service: UserSvc,
):
    """Get user avatar image."""
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
