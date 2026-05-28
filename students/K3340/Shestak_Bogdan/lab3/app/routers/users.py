from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import User, UserRead, UserChangePassword
from app.auth.dependencies import get_current_user
from app.auth.password import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)) -> List[User]:
    return session.exec(select(User)).all()


@router.patch("/me/password", response_model=UserRead)
def change_password(
    data: UserChangePassword,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль",
        )

    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user