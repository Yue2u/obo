from fastapi import APIRouter, BackgroundTasks, Request, Depends, Response, encoders
import typing as t
import aioredis

from app.db.session import get_db
from app.db.crud import (
    get_users,
    get_user,
    create_user,
    delete_user,
    edit_user,
    get_user_by_email
)
from app.db.schemas import UserCreate, UserEdit, User, UserOut
from app.core.auth import (
    get_current_active_user,
    get_current_active_superuser,
    set_new_password,
    get_current_user
)
from app.core import security

from app.core import config
from app.api.api_v1.utils import (
    generate_restore_code,
    send_restore_password_email
)

users_router = r = APIRouter()


@r.get(
    "/users",
    response_model=t.List[User],
    response_model_exclude_none=True,
)
async def users_list(
    response: Response,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get all users
    """
    users = get_users(db)
    # This is necessary for react-admin to work
    response.headers["Content-Range"] = f"0-9/{len(users)}"
    return users


@r.get("/users/me", response_model=User, response_model_exclude_none=True)
async def user_me(current_user=Depends(get_current_active_user)):
    """
    Get own user
    """
    return current_user


@r.get(
    "/users/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
)
async def user_details(
    request: Request,
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get any user details
    """
    user = get_user(db, user_id)
    return user
    # return encoders.jsonable_encoder(
    #     user, skip_defaults=True, exclude_none=True,
    # )


@r.post("/users", response_model=User, response_model_exclude_none=True)
async def user_create(
    request: Request,
    user: UserCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new user
    """
    return create_user(db, user)


@r.put(
    "/users/{user_id}", response_model=User, response_model_exclude_none=True
)
async def user_edit(
    request: Request,
    user_id: int,
    user: UserEdit,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing user
    """
    return edit_user(db, user_id, user)


@r.delete(
    "/users/{user_id}", response_model=User, response_model_exclude_none=True
)
async def user_delete(
    request: Request,
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing user
    """
    return delete_user(db, user_id)



@r.post("/restore-password")
async def restore_password(
    email: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    user = get_user_by_email(db, email)
    if not user:
        return {"message": "There isn't any user with this email"}
    code = generate_restore_code()
    background_tasks.add(send_restore_password_email, email, code)
    redis = aioredis.from_url(config.REDIS_URI)
    await redis.set(user.email, str(code))


@r.post("/restore-password-check")
async def restore_password_check(
    email: str,
    code: int,
    db=Depends(get_db)
):
    user = get_user_by_email(db, email)
    if not user:
        return {"detail": "There isn't any user with this email"}
    redis = aioredis.from_url(config.REDIS_URI)
    if not await redis.exists(email):
        return {"detail": "This user didn't try to restore password"}
    saved_code = await redis.get(email, decode_responses=True)
    if code != saved_code:
        return {"detail": "Wrong code!"}

    access_token_expires = timedelta(
        minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    if user.is_superuser:
        permissions = "admin"
    else:
        permissions = "user"
    access_token = security.create_access_token(
        data={"sub": user.email, "permissions": permissions},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@r.post("/set-new-password",
        response_model=User,
        response_model_exclude_none=True)
async def set_new_pass(email: int, new_password: str, user=Depends(get_current_user), db=Depends(get_db)):
    set_new_password(db, email, new_password)
    return user
