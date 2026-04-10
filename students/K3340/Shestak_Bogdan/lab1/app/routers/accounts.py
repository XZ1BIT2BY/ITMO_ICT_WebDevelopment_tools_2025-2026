from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import Account, User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/", response_model=List[Account])
def list_accounts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Account]:
    return session.exec(select(Account).where(Account.user_id == current_user.id)).all()


@router.get("/{account_id}", response_model=Account)
def get_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = session.get(Account, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
    return account


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(
    account: Account,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    account.user_id = current_user.id
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.patch("/{account_id}", response_model=Account)
def update_account(
    account_id: int,
    data: Account,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = session.get(Account, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)

    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    account = session.get(Account, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
    session.delete(account)
    session.commit()